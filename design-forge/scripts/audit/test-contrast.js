#!/usr/bin/env node
/*
 * test-contrast.js — test the colour maths IN measure.js, not a copy of it.
 *
 * 🔴 WHY THIS WAS REWRITTEN. The previous version re-implemented lum/contrast/over
 * locally, verified ITS OWN copies against reference values, and then merely checked
 * that measure.js contained the substrings '0.2126', '12.92' and so on. An inverted
 * comparison, a broken sort or a sign flip in the real functions passed that "test"
 * as long as the constants appeared anywhere in the file — including in a comment.
 *
 * So this extracts the actual function sources out of measure.js and evaluates them.
 * Delete the implementation and the extraction fails loudly instead of going green.
 */
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, 'measure.js'), 'utf8');
let fails = 0, run = 0;
const check = (name, cond, detail = '') => {
  run++;
  if (cond) console.log(`  ok   ${name}`);
  else { console.log(`  FAIL ${name}  ${detail}`); fails++; }
};

/* Pull a `const name = ...;` arrow/function declaration out of the source by
   brace/paren balance, so we evaluate the shipped code rather than a copy. */
function extract(name) {
  const start = SRC.search(new RegExp(`const\\s+${name}\\s*=`));
  if (start === -1) throw new Error(`could not find "${name}" in measure.js`);
  let i = SRC.indexOf('=', start) + 1, depth = 0, inStr = null;
  for (; i < SRC.length; i++) {
    const c = SRC[i], prev = SRC[i - 1];
    if (inStr) { if (c === inStr && prev !== '\\') inStr = null; continue; }
    if (c === '"' || c === "'" || c === '`') { inStr = c; continue; }
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c)) depth--;
    else if (c === ';' && depth === 0) break;
  }
  return SRC.slice(start, i + 1);
}

const names = ['over', 'hexToRgb', 'lum', 'contrast'];
let src;
try {
  src = names.map(extract).join('\n');
} catch (e) {
  console.log(`  FAIL could not extract from measure.js: ${e.message}`);
  process.exit(1);
}
const { over, hexToRgb, lum, contrast } = new Function(
  `${src}\nreturn { over, hexToRgb, lum, contrast };`)();
console.log(`\nextracted ${names.length} functions from measure.js (${src.length} chars)\n`);

const near = (a, b, tol = 0.01) => Math.abs(a - b) < tol;

console.log('reference contrast pairs');
check('black on white is 21:1', near(contrast(hexToRgb('#000'), hexToRgb('#fff')), 21.0, 0.001));
check('white on white is 1:1', near(contrast(hexToRgb('#fff'), hexToRgb('#fff')), 1.0, 0.001));
check('#767676 on white is the 4.5 boundary',
  near(contrast(hexToRgb('#767676'), hexToRgb('#fff')), 4.542));
check('#595959 on white is the 7.0 boundary',
  near(contrast(hexToRgb('#595959'), hexToRgb('#fff')), 7.005));
check('#949494 on white is the 3.0 boundary',
  near(contrast(hexToRgb('#949494'), hexToRgb('#fff')), 3.033));

console.log('\nproperties a copy-paste test would miss');
check('contrast is symmetric',
  near(contrast([10, 20, 30], [200, 200, 200]), contrast([200, 200, 200], [10, 20, 30]), 1e-9));
check('contrast is never below 1', contrast([120, 120, 120], [121, 121, 121]) >= 1.0);
check('lum is monotonic in brightness', lum([0, 0, 0]) < lum([128, 128, 128]) && lum([128, 128, 128]) < lum([255, 255, 255]));
check('lum of white is 1', near(lum([255, 255, 255]), 1.0, 1e-9));
check('lum of black is 0', near(lum([0, 0, 0]), 0.0, 1e-9));
check('green weighs more than red, red more than blue',
  lum([0, 255, 0]) > lum([255, 0, 0]) && lum([255, 0, 0]) > lum([0, 0, 255]));

console.log('\nhex parsing');
check('3-digit hex expands', JSON.stringify(hexToRgb('#abc')) === JSON.stringify(hexToRgb('#aabbcc')));
check('a leading # is optional', JSON.stringify(hexToRgb('fff')) === JSON.stringify(hexToRgb('#fff')));

console.log('\nalpha compositing');
const scrim = over([0, 0, 0, 0.6], [255, 255, 255]);
check('60% black over white composites to #666',
  scrim.every((c, i) => Math.abs(c - [102, 102, 102][i]) <= 1), JSON.stringify(scrim));
check('#888 on that scrim is ~1.62:1, not the 5.92 an uncomposited read gives',
  near(contrast(hexToRgb('#888888'), scrim), 1.62, 0.02),
  String(contrast(hexToRgb('#888888'), scrim)));
check('a fully opaque foreground passes through unchanged',
  JSON.stringify(over([1, 2, 3], [9, 9, 9])) === JSON.stringify([1, 2, 3]));
check('a fully transparent foreground yields the backdrop',
  over([0, 0, 0, 0], [200, 100, 50]).every((c, i) => Math.abs(c - [200, 100, 50][i]) <= 1));

console.log(`\n${run - fails}/${run} passed`);
process.exit(fails ? 1 : 0);
