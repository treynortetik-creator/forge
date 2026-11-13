// A palette LUT fitted from 3D renders to a painted reference.
// Per-channel histogram matching over the opaque pixels (so the render keeps its own shading structure but takes the painting's palette).
// Lesson: fitted on SEVERAL directions pooled (each render weighted equally), not the S idle alone: the S-only fit matched the front (p90 169) and left
// the back and sides murky (p90 106). Output: lut.json {r,g,b: 256 ints}, apply it per channel to straight-alpha RGBA frames (finish-frames.mjs does NOT apply LUTs; this is the toon-look route, see references/look-recipes.md).
//   node fitlut.mjs <out.json> <painting.png> <render1.png> [render2.png ...]
//   node fitlut.mjs <render.png> <painting.png> <out.json>            (the r1 single-render form)
import fs from 'node:fs';
import sharp from 'sharp';
let args = process.argv.slice(2), out, ref, srcs;
// --trim a: per-direction LUTs for the sources named `<char>-<clip>-<dir>-<i>.png`: own = that direction's histogram match, final = a * own + (1 - a) * pooled.
// The pooled LUT alone still left the front 20 luminance points hot and the NE view cold; the trim pulls each facing toward the painting's value distribution.
let trim = 0; { const k = args.indexOf('--trim'); if (k >= 0) { trim = +args[k + 1]; args.splice(k, 2); } }
if (args[0].endsWith('.json')) { out = args[0]; ref = args[1]; srcs = args.slice(2); } else { srcs = [args[0]]; ref = args[1]; out = args[2]; }
const px = async (f) => { const { data, info } = await sharp(f).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); const ch = [new Float64Array(256), new Float64Array(256), new Float64Array(256)]; let n = 0; for (let i = 0; i < info.width * info.height; i++) if (data[i * 4 + 3] > 200) { for (let c = 0; c < 3; c++) ch[c][data[i * 4 + c]]++; n++; } return { ch, n }; };
const pool = async (files) => { const acc = [new Float64Array(256), new Float64Array(256), new Float64Array(256)]; for (const f of files) { const { ch, n } = await px(f); for (let c = 0; c < 3; c++) for (let v = 0; v < 256; v++) acc[c][v] += ch[c][v] / n; } return { ch: acc, n: files.length }; };
const cdf = ({ ch, n }) => ch.map((h) => { const o = new Float64Array(256); let a = 0; for (let v = 0; v < 256; v++) { a += h[v]; o[v] = a / n; } return o; });
const A = cdf(await pool(srcs)), B = cdf(await px(ref));
const lut = { r: [], g: [], b: [] };
['r', 'g', 'b'].forEach((k, c) => { let j = 0; for (let v = 0; v < 256; v++) { while (j < 255 && B[c][j] < A[c][v]) j++; lut[k].push(j); } });
const mk = (A) => { const l = { r: [], g: [], b: [] }; ['r', 'g', 'b'].forEach((k, c) => { let j = 0; for (let v = 0; v < 256; v++) { while (j < 255 && B[c][j] < A[c][v]) j++; l[k].push(j); } }); return l; };
if (trim > 0) {
  lut.dirs = {};
  for (const f of srcs) {
    const m = /-(e|ne|n|nw|w|sw|s|se)-\d+\.png$/.exec(f); if (!m) continue;
    const own = mk(cdf(await px(f)));
    lut.dirs[m[1]] = Object.fromEntries(['r', 'g', 'b'].map((k) => [k, own[k].map((v, i) => Math.round(trim * v + (1 - trim) * lut[k][i]))]));
  }
}
fs.writeFileSync(out, JSON.stringify(lut));
console.log('wrote', out, 'from', srcs.length, 'render(s)');
