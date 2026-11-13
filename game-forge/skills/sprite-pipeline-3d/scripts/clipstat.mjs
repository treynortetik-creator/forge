// Mean alpha-box height and width (px, cell space, alpha >= 24) per clip and direction over a finished frame dir, relative to the idle S frame 0.
//   node clipstat.mjs <dir> <char> [clip ...]     (needs `npm i sharp`; frames are <char>-<clip>-<dir>-<i>.png; the reference is <char>-idle-s-0.png)
// Use it to catch a clip that is 8% shorter than idle in one direction (a crouching run) or a direction whose figure is a different size.
import fs from 'node:fs';
import sharp from 'sharp';
const [dir, char, ...clips] = process.argv.slice(2);
const dirs = ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se'];
const box = async (f) => { const { data, info } = await sharp(f).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1, n = 0; for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) if (data[(y * info.width + x) * 4 + 3] >= 24) { n++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } return { w: x1 - x0 + 1, h: y1 - y0 + 1, area: n }; };
const ref = (await box(`${dir}/${char}-idle-s-0.png`)).h;
const out = {};
for (const clip of clips) {
  const per = {}; let all = [];
  for (const d of dirs) { const hs = [], ws = [], as = []; for (let i = 0; ; i++) { const f = `${dir}/${char}-${clip}-${d}-${i}.png`; if (!fs.existsSync(f)) break; const b = await box(f); hs.push(b.h); ws.push(b.w); as.push(b.area); } if (hs.length) { per[d] = { h: +(hs.reduce((a, b) => a + b) / hs.length / ref).toFixed(3), w: +(ws.reduce((a, b) => a + b) / ws.length).toFixed(0), min: +(Math.min(...hs) / ref).toFixed(3), area: Math.round(as.reduce((a, b) => a + b) / as.length) }; all.push(...hs); } }
  out[clip] = { meanH: +(all.reduce((a, b) => a + b) / all.length / ref).toFixed(3), per };
}
console.log(JSON.stringify({ refH: ref, ...out }));
