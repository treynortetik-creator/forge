// finish-frames.mjs: raw super-sampled renders (bake_sprites.py) -> final cell-size sprite frames + frames.json.
//
//   node finish-frames.mjs --render <render_dir> --out <frames_dir> [--look hatch|toon] [--ramp ramp.json] [--levels 10]
//                          [--line-dark 1.0] [--alpha-floor 4] [--mirror w=e,nw=ne,sw=se] [--no-ramp]
//
// Reads <render_dir>/meta.json and <render_dir>/raw/<name>-<clip>-<dir>-<i>.png, writes <frames_dir>/<name>-<clip>-<dir>-<i>.png (cell space) and
// <frames_dir>/frames.json (clips, fps, loop, hitFrames, per-frame sockets, mirrorOf, ONE shared crop box per cell size, symmetric about the centre
// column so a flipX mirror keeps the feet on the anchor).
//
// Steps per frame (the order matters; each one is a lesson, see references/ink-bake.md):
//   1. down-sample by the integer SUPER factor. hatch look: AREA (box) average, alpha = 50% coverage so the outline stays crisp, colour = mean of the
//      opaque sub-pixels. toon look: Lanczos. (A hatch bake averaged with Lanczos rings; area average turns fine hatching into soft ink grey.)
//   2. --line-dark k (hatch only, needs the .ln.png sidecars from `bake_sprites.py --line-pass`): pull exactly the pixels the defining-line layer covers
//      toward ink by k * core(coverage). Value only, the line never gets wider.
//   3. alpha floor: alpha 1..3 is a resample residue (a faint rectangle around the cell); clamp it to nothing.
//   4. ramp projection (hatch look, unless --no-ramp): snap every opaque pixel onto a Lab polyline through the ramp stops (default: 5 ink -> paper stops)
//      and quantise to --levels steps along it, so the whole sheet uses at most N colours.
// Needs: node >= 18 and `npm i sharp` (not vendored). Pure JS otherwise. Tested here against bake_sprites.py output of the standin character (Node 22 + sharp).
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require('sharp');

const o = {}; const av = process.argv.slice(2);
for (let i = 0; i < av.length; i++) if (av[i].startsWith('--')) o[av[i].slice(2)] = (av[i + 1] === undefined || av[i + 1].startsWith('--')) ? true : av[++i];
if (!o.render || !o.out) { console.error('usage: node finish-frames.mjs --render <render_dir> --out <frames_dir> [--look hatch|toon] [--ramp ramp.json] [--levels 10] [--line-dark 1.0] [--mirror w=e,..] [--no-ramp]'); process.exit(2); }

const meta = JSON.parse(await fsp.readFile(path.join(o.render, 'meta.json'), 'utf8'));
const look = o.look ?? meta.look;
const hatch = look === 'hatch';
const SUP = meta.super, char = meta.name;
const LEVELS = +(o.levels ?? 10), LINE_DARK = +(o['line-dark'] ?? 0), FLOOR = +(o['alpha-floor'] ?? 4);
const mirror = Object.fromEntries((typeof o.mirror === 'string' ? o.mirror : '').split(',').filter(Boolean).map((p) => p.split('=')));
const RAMP = o.ramp ? JSON.parse(await fsp.readFile(o.ramp, 'utf8')) : [[0x12, 0x0A, 0x10], [0x4A, 0x3F, 0x35], [0x8C, 0x7E, 0x6A], [0xCD, 0xBF, 0xA4], [0xE8, 0xDC, 0xC4]];
const LINE_INK = RAMP[0];

// ---------------------------------------------------------------- colour: sRGB <-> Lab, projection onto the ramp polyline
const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
const unlin = (v) => Math.max(0, Math.min(255, Math.round(255 * (v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055))));
function rgbToLab(r, g, b) {
  const R = lin(r), G = lin(g), B = lin(b);
  let x = (0.4124564 * R + 0.3575761 * G + 0.1804375 * B) / 0.95047, y = 0.2126729 * R + 0.7151522 * G + 0.072175 * B, z = (0.0193339 * R + 0.119192 * G + 0.9503041 * B) / 1.08883;
  const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
  x = f(x); y = f(y); z = f(z);
  return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}
function labToRgb(L, a, b) {
  const fy = (L + 16) / 116, fx = fy + a / 500, fz = fy - b / 200;
  const fi = (t) => (t ** 3 > 216 / 24389 ? t ** 3 : (116 * t - 16) / (24389 / 27));
  const X = fi(fx) * 0.95047, Y = fi(fy), Z = fi(fz) * 1.08883;
  return [unlin(3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z), unlin(-0.969266 * X + 1.8760108 * Y + 0.041556 * Z), unlin(0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z)];
}
const RAMP_LAB = RAMP.map((c) => rgbToLab(...c)), SEGS = RAMP.length - 1;
/** Nearest point on the Lab polyline through the ramp stops: t in 0..SEGS along the ramp, d = Lab distance to it. */
export function rampProject(r, g, b) {
  const p = rgbToLab(r, g, b); let best = { t: 0, d: 1e9 };
  for (let k = 0; k < SEGS; k++) {
    const a = RAMP_LAB[k], q = RAMP_LAB[k + 1], ab = [q[0] - a[0], q[1] - a[1], q[2] - a[2]];
    const u = Math.max(0, Math.min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1] + (p[2] - a[2]) * ab[2]) / (ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)));
    const d = Math.hypot(p[0] - a[0] - u * ab[0], p[1] - a[1] - u * ab[1], p[2] - a[2] - u * ab[2]);
    if (d < best.d) best = { t: k + u, d };
  }
  return best;
}
const rampColor = (t) => { const k = Math.min(SEGS - 1, Math.floor(t)), u = t - k, a = RAMP_LAB[k], q = RAMP_LAB[k + 1]; return labToRgb(a[0] + u * (q[0] - a[0]), a[1] + u * (q[1] - a[1]), a[2] + u * (q[2] - a[2])); };
const cache = new Map();
function snapRampPx(r, g, b) {
  const key = (r << 16) | (g << 8) | b; let v = cache.get(key);
  if (!v) { const { t } = rampProject(r, g, b); v = rampColor(Math.round((t / SEGS) * (LEVELS - 1)) / (LEVELS - 1) * SEGS); cache.set(key, v); }
  return v;
}

// ---------------------------------------------------------------- per-frame passes
const readRGBA = async (f) => { const { data, info } = await sharp(f).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); return { data, w: info.width, h: info.height }; };
function boxAverage(src, sw, sh, sup) {
  const w = Math.floor(sw / sup), h = Math.floor(sh / sup), out = Buffer.alloc(w * h * 4), n = sup * sup;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let na = 0, r = 0, g = 0, b = 0;
    for (let yy = 0; yy < sup; yy++) for (let xx = 0; xx < sup; xx++) { const i = (((y * sup + yy) * sw) + x * sup + xx) * 4; if (src[i + 3] < 128) continue; na++; r += src[i]; g += src[i + 1]; b += src[i + 2]; }
    if (na / n < 0.5) continue;
    const q = (y * w + x) * 4; out[q] = Math.round(r / na); out[q + 1] = Math.round(g / na); out[q + 2] = Math.round(b / na); out[q + 3] = 255;
  }
  return { data: out, w, h };
}
/** coverage lc (area average of the super-sampled line layer) pulls colour toward line ink by k*core(lc); core = 0 below lc 0.3, 1 above 0.8 */
function darkenLines(data, w, h, ln, lnW, sup, k) {
  const n = sup * sup;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let sa = 0;
    for (let yy = 0; yy < sup; yy++) for (let xx = 0; xx < sup; xx++) sa += ln[(((y * sup + yy) * lnW) + x * sup + xx) * 4 + 3];
    const lc = sa / n / 255;
    if (lc <= 0.004) continue;
    const t = Math.min(1, k * Math.max(0, Math.min(1, (lc - 0.3) / 0.5))), q = (y * w + x) * 4;
    if (t <= 0 || data[q + 3] === 0) continue;
    for (let c = 0; c < 3; c++) data[q + c] = Math.round(data[q + c] + (LINE_INK[c] - data[q + c]) * t);
  }
}
function alphaBox(data, w, h, t = 24) {
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (data[(y * w + x) * 4 + 3] >= t) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return x1 < 0 ? null : { x0, y0, x1, y1 };
}

// ---------------------------------------------------------------- main
await fsp.rm(o.out, { recursive: true, force: true });
await fsp.mkdir(o.out, { recursive: true });
const boxes = {}, clips = {}; let nframes = 0;
for (const [clip, c] of Object.entries(meta.clips)) {
  const cell = c.cell ?? meta.cell, ck = cell.join('x');
  clips[clip] = { fps: c.fps, loop: !!c.loop, n: c.frameList ? c.frameList.length : c.n, cell, ...(c.hitFrames ? { hitFrames: c.hitFrames } : {}), ...(c.segments ? { segments: c.segments } : {}), dirs: {} };
  for (const d of Object.keys(c.dirs)) {
    if (mirror[d]) continue;
    clips[clip].dirs[d] = { sockets: c.dirs[d].sockets };
    for (let i = 0; i < c.dirs[d].frames; i++) {
      const name = `${char}-${clip}-${d}-${i}`, src = path.join(o.render, 'raw', name + '.png');
      let data, w, h;
      if (hatch) {
        const r = await readRGBA(src);
        if (r.w !== cell[0] * SUP || r.h !== cell[1] * SUP) throw new Error(`${src}: ${r.w}x${r.h} is not ${SUP} x cell ${cell.join('x')}`);
        ({ data, w, h } = boxAverage(r.data, r.w, r.h, SUP));
        const lnf = path.join(o.render, 'raw', name + '.ln.png');
        if (LINE_DARK > 0 && fs.existsSync(lnf)) { const ln = await readRGBA(lnf); darkenLines(data, w, h, ln.data, ln.w, SUP, LINE_DARK); }
      } else {
        const r = await sharp(src).ensureAlpha().resize(cell[0], cell[1], { kernel: 'lanczos3' }).raw().toBuffer({ resolveWithObject: true });
        data = r.data; w = r.info.width; h = r.info.height;
      }
      for (let k = 0; k < data.length; k += 4) if (data[k + 3] > 0 && data[k + 3] < FLOOR) data[k] = data[k + 1] = data[k + 2] = data[k + 3] = 0;
      if (hatch && !o['no-ramp']) for (let k = 0; k < data.length; k += 4) { if (data[k + 3] === 0) continue; const v = snapRampPx(data[k], data[k + 1], data[k + 2]); data[k] = v[0]; data[k + 1] = v[1]; data[k + 2] = v[2]; }
      const bb = alphaBox(data, w, h);
      if (bb) { const b = (boxes[ck] ??= { x0: 1e9, y0: 1e9, x1: -1, y1: -1 }); b.x0 = Math.min(b.x0, bb.x0); b.y0 = Math.min(b.y0, bb.y0); b.x1 = Math.max(b.x1, bb.x1); b.y1 = Math.max(b.y1, bb.y1); }
      await sharp(data, { raw: { width: w, height: h, channels: 4 } }).png({ compressionLevel: 9 }).toFile(path.join(o.out, name + '.png'));
      nframes++;
    }
  }
}
const box = {};
for (const [ck, b] of Object.entries(boxes)) {
  const [cw, ch] = ck.split('x').map(Number), half = Math.max(cw / 2 - b.x0, b.x1 + 1 - cw / 2) + 3;
  const x0 = Math.max(0, Math.floor(cw / 2 - half)), x1 = Math.min(cw, Math.ceil(cw / 2 + half)), y0 = Math.max(0, b.y0 - 3), y1 = Math.min(ch, b.y1 + 4);
  box[ck] = [x0, y0, x1 - x0, y1 - y0];
}
await fsp.writeFile(path.join(o.out, 'frames.json'), JSON.stringify({ name: char, look, elev: meta.elev, scale: meta.scale, refHeight: meta.refHeight, cell: meta.cell, super: SUP, box, mirrorOf: mirror, clips }, null, 1) + '\n');
console.log(JSON.stringify({ wrote: o.out, frames: nframes, look, levels: hatch && !o['no-ramp'] ? LEVELS : null, box }));
