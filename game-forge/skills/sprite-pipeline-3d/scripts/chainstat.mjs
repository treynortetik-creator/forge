// Pose-to-pose jump between consecutive attack frames (alpha-mask XOR / mean area, 0 = identical, ~1 = nothing in common), per segment and at the hit-to-hit joins.
//   node chainstat.mjs <frame dir> <char> <dir> <seg,sizes,...> [clip=attack]      e.g.  frames/ hero se 4,4,4,4,4
// Needs `npm i sharp` (not vendored). Frames are <char>-<clip>-<dir>-<i>.png in cell space; segment sizes are the frame counts of each hit in a combo clip.
import fs from 'node:fs';
import sharp from 'sharp';
const [dir, char, d, segS, clip = 'attack'] = process.argv.slice(2);
const segs = segS.split(',').map(Number), N = segs.reduce((a, b) => a + b, 0);
const mask = async (i) => { const { data, info } = await sharp(`${dir}/${char}-${clip}-${d}-${i}.png`).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); const m = new Uint8Array(info.width * info.height); for (let k = 0; k < m.length; k++) m[k] = data[k * 4 + 3] >= 128 ? 1 : 0; return m; };
const M = []; for (let i = 0; i < N; i++) M.push(await mask(i));
const xor = (a, b) => { let x = 0, s = 0; for (let k = 0; k < a.length; k++) { x += a[k] ^ b[k]; s += a[k] + b[k]; } return +(2 * x / Math.max(1, s)).toFixed(3); };
let o = 0; const within = [], joins = [];
segs.forEach((n, si) => { const w = []; for (let j = 1; j < n; j++) w.push(xor(M[o + j - 1], M[o + j])); within.push(w); if (si < segs.length - 1) joins.push(xor(M[o + n - 1], M[o + n])); o += n; });
const flat = within.flat();
console.log(JSON.stringify({ dir: d, within, joins, meanWithin: +(flat.reduce((a, b) => a + b, 0) / flat.length).toFixed(3), maxWithin: Math.max(...flat), meanJoin: +(joins.reduce((a, b) => a + b, 0) / joins.length).toFixed(3), maxJoin: Math.max(...joins) }));
