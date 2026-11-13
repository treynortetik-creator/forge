#!/usr/bin/env node
// measure_slots.mjs: find the centres of N coloured marks (cushions, seals, sockets, candle holders) on a generated prop and print
// them as FRACTIONS of the image, so game code can place icons/overlays on the prop at any display scale.
// Needs: npm i sharp.   node measure_slots.mjs <image.png> [--rgb R,G,B] [--tol 60] [--min-area 800] [--expect N] [--json]
//   --rgb       the mark colour to look for (default 200,40,40, a red wax seal). Distance is Euclidean in RGB; alpha must be > 200.
//   --tol       max RGB distance (default 60)
//   --min-area  drop connected blobs smaller than this many px (default 800; raise it if specks appear)
//   --expect N  exit 1 unless exactly N blobs were found (the "count them, don't trust the model" gate)
// Output: one line per blob, top to bottom: area, cx, cy (fractions 0..1), width px, height px.
// Why this exists: an image model asked for "exactly seven seals" drew six twice; counting by script caught it, and the same script
// gave the placement table (SEAL_POINTS) with no eyeballing. The original tool hard-coded a red rule; this one takes any colour.
import sharp from 'sharp';
const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf(n); if (i < 0) return d; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const bool = (n) => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
const rgb = flag('--rgb', '200,40,40').split(',').map(Number), tol = +flag('--tol', 60), minArea = +flag('--min-area', 800), expect = flag('--expect', null), asJson = bool('--json');
const f = argv[0];
if (!f || rgb.length !== 3 || rgb.some(Number.isNaN)) { console.error('usage: node measure_slots.mjs <image.png> [--rgb R,G,B] [--tol 60] [--min-area 800] [--expect N] [--json]'); process.exit(2); }
const { data, info } = await sharp(f).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
const W = info.width, H = info.height, m = new Uint8Array(W * H);
for (let i = 0; i < W * H; i++) {
  const a = data[i * 4 + 3]; if (a <= 200) continue;
  const d = Math.hypot(data[i * 4] - rgb[0], data[i * 4 + 1] - rgb[1], data[i * 4 + 2] - rgb[2]);
  if (d <= tol) m[i] = 1;
}
const seen = new Uint8Array(W * H), blobs = [];
for (let s = 0; s < W * H; s++) if (m[s] && !seen[s]) {
  const st = [s]; seen[s] = 1; let n = 0, sx = 0, sy = 0, x0 = W, x1 = 0, y0 = H, y1 = 0;
  while (st.length) {
    const p = st.pop(), x = p % W, y = (p / W) | 0; n++; sx += x; sy += y; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    for (const q of [p - 1, p + 1, p - W, p + W]) if (q >= 0 && q < W * H && m[q] && !seen[q] && !((q === p - 1 && x === 0) || (q === p + 1 && x === W - 1))) { seen[q] = 1; st.push(q); }
  }
  if (n >= minArea) blobs.push({ area: n, cx: +(sx / n / W).toFixed(3), cy: +(sy / n / H).toFixed(3), w: x1 - x0 + 1, h: y1 - y0 + 1 });
}
blobs.sort((a, b) => a.cy - b.cy);
if (asJson) console.log(JSON.stringify({ width: W, height: H, blobs }, null, 1));
else { console.log(`${W}x${H}, ${blobs.length} blobs`); for (const b of blobs) console.log(b.area, b.cx.toFixed(3), b.cy.toFixed(3), b.w, b.h); }
if (expect !== null && blobs.length !== +expect) { console.error(`expected ${expect}, found ${blobs.length}`); process.exit(1); }
