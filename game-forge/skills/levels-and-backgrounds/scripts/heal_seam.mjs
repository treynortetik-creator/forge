#!/usr/bin/env node
// heal_seam.mjs: measure and heal the wrap seam of a tiling floor/wall image (left edge == right edge, optionally top == bottom).
// Needs: npm i sharp (Node 18+).
//   node heal_seam.mjs <in.png> --measure [--axes x|xy]          print the seam ratio only
//   node heal_seam.mjs <in.png> [--mode mirror|offset] [--band 64] [--axes x|xy] [--out healed.png | --inplace]
// Seam ratio = mean |first column - last column| / mean |neighbouring columns| (inner floor 0.75). ~1 = invisible, >> 1 = visible.
//   Our floors/walls failed at 1.6+ and a healed wall went from 2.2 to 0.03; we gated tiles at < 1.6 (a loose gate: aim < 1.2 on busy art).
// Modes (both blend over a smoothstep ramp of --band px at each edge):
//   mirror (default, <= ~64 px): each edge strip blends from the original (at distance band) to the AVERAGE of the two edges, so column 0 == column w-1
//     exactly. Cheap and exact, but it smears detail that touches the edge; good on walls and floors with a quiet border.
//   offset (try --band 80, --axes xy): out = img*m + roll(img, w/2, h/2)*(1-m), m = 0 at the borders ramping to 1. The borders come from the image
//     CENTRE (continuous across a wrap by construction), the ghosting is confined to the band. Better on busy art, but ghosting is visible if
//     a distinct object sits in the band: look at the output.
// The original is never overwritten unless --inplace; with --inplace a copy is kept as <name>.preheal.png.
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';

const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf(n); if (i < 0) return d; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const bool = (n) => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
const measureOnly = bool('--measure'), inplace = bool('--inplace');
const mode = flag('--mode', 'mirror'), B = +flag('--band', mode === 'offset' ? 80 : 64), AX = flag('--axes', mode === 'offset' ? 'xy' : 'x');
const outArg = flag('--out', null);
const f = argv[0];
if (!f || !['mirror', 'offset'].includes(mode) || !['x', 'xy'].includes(AX)) { console.error(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(1, 17).join('\n')); process.exit(2); }

function ratioAxis(data, w, h, c, axis) {
  const at = (x, y, k) => data[(y * w + x) * c + k];
  const lenA = axis === 'x' ? w : h, lenB = axis === 'x' ? h : w;
  const get = (a, b, k) => (axis === 'x' ? at(a, b, k) : at(b, a, k));
  let edge = 0, inner = 0, nEdge = 0, nInner = 0;
  for (let b = 0; b < lenB; b++) for (let k = 0; k < Math.min(c, 3); k++) {
    edge += Math.abs(get(0, b, k) - get(lenA - 1, b, k)); nEdge++;
    for (let a = 0; a < lenA - 1; a++) { inner += Math.abs(get(a, b, k) - get(a + 1, b, k)); nInner++; }
  }
  return (edge / nEdge) / Math.max(inner / nInner, 0.75);
}
const seamReport = async (input) => {
  const { data, info } = await sharp(input).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { x: +ratioAxis(data, info.width, info.height, info.channels, 'x').toFixed(2), y: AX === 'xy' ? +ratioAxis(data, info.width, info.height, info.channels, 'y').toFixed(2) : null };
};

console.log('before', await seamReport(f));
if (measureOnly) process.exit(0);
const { data, info } = await sharp(f).removeAlpha().raw().toBuffer({ resolveWithObject: true });
const { width: w, height: h, channels: c } = info;
const smooth = (t) => t * t * (3 - 2 * t);
const out = Buffer.from(data);
if (mode === 'mirror') {
  for (let y = 0; y < h; y++) for (let x = 0; x < B; x++) { const s = smooth(x / B);
    for (let k = 0; k < c; k++) { const L = data[(y * w + x) * c + k], R = data[(y * w + (w - 1 - x)) * c + k], M = (L + R) / 2;
      out[(y * w + x) * c + k] = Math.round(L * s + M * (1 - s)); out[(y * w + (w - 1 - x)) * c + k] = Math.round(R * s + M * (1 - s)); } }
  if (AX === 'xy') for (let x = 0; x < w; x++) for (let y = 0; y < B; y++) { const s = smooth(y / B);
    for (let k = 0; k < c; k++) { const T = out[(y * w + x) * c + k], Bt = out[((h - 1 - y) * w + x) * c + k], M = (T + Bt) / 2;
      out[(y * w + x) * c + k] = Math.round(T * s + M * (1 - s)); out[((h - 1 - y) * w + x) * c + k] = Math.round(Bt * s + M * (1 - s)); } }
} else {
  const ramp = (i, n) => smooth(Math.min(1, Math.min(i, n - 1 - i) / B));
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const m = ramp(x, w) * (AX === 'xy' ? ramp(y, h) : 1);
    const x2 = (x + (w >> 1)) % w, y2 = AX === 'xy' ? (y + (h >> 1)) % h : y;
    for (let k = 0; k < c; k++) out[(y * w + x) * c + k] = Math.round(data[(y * w + x) * c + k] * m + data[(y2 * w + x2) * c + k] * (1 - m)); }
}
const dest = inplace ? f : (outArg ?? path.join(path.dirname(f), path.basename(f, path.extname(f)) + '.healed.png'));
if (inplace) fs.copyFileSync(f, f.replace(/\.[^.]+$/, '') + '.preheal.png');
await sharp(out, { raw: { width: w, height: h, channels: c } }).png().toFile(dest + '.tmp'); fs.renameSync(dest + '.tmp', dest);
console.log('after ', await seamReport(dest), '->', dest);
