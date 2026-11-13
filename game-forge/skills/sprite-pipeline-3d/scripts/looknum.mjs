// Look numbers for a render review: luminance p50/p90, HSV saturation p50 and alpha-box width/height on the opaque pixels of frames, per file.
// Review aid.   node looknum.mjs <frame.png> ...   (needs `npm i sharp`)
import sharp from 'sharp';
const q = (a, p) => { a.sort((x, y) => x - y); return a[Math.min(a.length - 1, Math.floor(p * a.length))]; };
for (const f of process.argv.slice(2)) {
  const { data, info } = await sharp(f).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const L = [], S = []; let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
  for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) { const i = (y * info.width + x) * 4; if (data[i + 3] >= 24) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    if (data[i + 3] > 200) { const r = data[i], g = data[i + 1], b = data[i + 2]; L.push(0.299 * r + 0.587 * g + 0.114 * b); const mx = Math.max(r, g, b), mn = Math.min(r, g, b); S.push(mx ? (mx - mn) / mx : 0); } }
  const w = x1 - x0 + 1, h = y1 - y0 + 1;
  console.log(JSON.stringify({ f: f.split('/').pop(), p50: Math.round(q([...L], 0.5)), p90: Math.round(q([...L], 0.9)), sat50: +q([...S], 0.5).toFixed(2), w, h, wh: +(w / h).toFixed(2) }));
}
