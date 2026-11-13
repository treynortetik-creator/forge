#!/usr/bin/env node
// purity-check.mjs - fail the build when the deterministic simulation touches anything non-deterministic.
// Generalised from a vitest test we ran in both games (tests/purity.test.ts). No dependencies.
//
// Usage:
//   node purity-check.mjs <dir> [<dir> ...] [--strict-math <dir> ...] [--ext ts,tsx,js,mjs]
//
//   <dir>              scanned for: Math.random, Date.now, new Date, performance.now, importing the
//                      renderer ('phaser'), and the DOM (window., document.)
//   --strict-math <d>  ALSO scanned for implementation-approximated Math (sin cos tan asin acos atan
//                      atan2 sinh cosh tanh exp log log2 log10 pow hypot cbrt, and the ** operator).
//                      V8 and JavaScriptCore can differ in the last bits of these, so a replay recorded
//                      in Node can diverge in Chrome or Safari. Ship your own polynomial sin/cos/atan2
//                      built from + - * / sqrt, and test it against Math within 1e-9.
//   --ext              file extensions to scan (default ts,tsx,js,mjs)
//
// Exit 0 = clean, 1 = violations (each printed as file:line: match), 2 = usage error.
// Comments are stripped before matching, so mentioning Math.random in a comment is fine.
import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, extname } from 'node:path';

const args = process.argv.slice(2);
const plain = [], strict = [];
let exts = ['ts', 'tsx', 'js', 'mjs'];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--strict-math') strict.push(args[++i]);
  else if (args[i] === '--ext') exts = (args[++i] || '').split(',');
  else plain.push(args[i]);
}
if (!plain.length && !strict.length) { console.error('usage: purity-check.mjs <dir>... [--strict-math <dir>...] [--ext ts,js]'); process.exit(2); }

const IMPURE = /Math\.random|Date\.now|new Date|performance\.now|from ['"]phaser['"]|\bwindow\.|\bdocument\./;
const APPROX = /Math\.(sin|cos|tan|asin|acos|atan|atan2|sinh|cosh|tanh|asinh|acosh|atanh|exp|expm1|log|log1p|log2|log10|pow|hypot|cbrt)\b|\*\*/;

function walk(dir) {
  if (!existsSync(dir)) { console.error(`no such directory: ${dir}`); process.exit(2); }
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (f === 'node_modules') return [];
    return statSync(p).isDirectory() ? walk(p) : exts.includes(extname(p).slice(1)) ? [p] : [];
  });
}
// Blank out comments but keep newlines so reported line numbers stay right.
const stripComments = (s) => s.replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, (m) => m.replace(/[^\n]/g, ' '));

let bad = 0;
const scan = (dirs, re, label) => {
  for (const d of dirs) for (const f of walk(d)) {
    const lines = stripComments(readFileSync(f, 'utf8')).split('\n');
    lines.forEach((ln, i) => { const m = re.exec(ln); if (m) { bad++; console.log(`${f}:${i + 1}: [${label}] ${m[0]}`); } });
  }
};
scan([...plain, ...strict], IMPURE, 'impure');
scan(strict, APPROX, 'approximated-math');
console.log(bad ? `purity-check: ${bad} violation(s)` : 'purity-check: clean');
process.exit(bad ? 1 : 0);
