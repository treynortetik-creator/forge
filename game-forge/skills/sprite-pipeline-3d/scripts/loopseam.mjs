// Loop-seam check for looping animations: is the step from the last frame back to the first an ordinary step?
//   ratio = meanAbsDiff(last, first) / mean over i of meanAbsDiff(frame i, frame i+1)      (RGBA over the union alpha, cell space)
// ~1 = the loop point is as smooth as any other step; < 1.5 read as seamless in our game (we gated idle and run at < 0.8 for the packaged frames); >> 1 = a visible pop.
// (A tileable-texture edge metric does not apply to a frame loop.)
//   node loopseam.mjs <frames_dir> [clip,clip]      frames_dir holds <name>-<clip>-<dir>-<i>.png and the frames.json written by finish-frames.mjs
// Needs `npm i sharp` (not vendored). Loops from bake_sprites.py drop the duplicate end frame, so the seam step is last -> first.
import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
const [src, clipsArg] = process.argv.slice(2);
if (!src) { console.error('usage: node loopseam.mjs <frames_dir> [idle,run]'); process.exit(2); }
const fj = JSON.parse(fs.readFileSync(path.join(src, 'frames.json'), 'utf8')), char = fj.name;
const clips = (clipsArg ?? Object.keys(fj.clips).filter((c) => fj.clips[c].loop).join(',')).split(',').filter(Boolean);
const px = async (f) => (await sharp(f).ensureAlpha().raw().toBuffer());
const diff = (a, b) => { let s = 0, n = 0; for (let i = 0; i < a.length; i += 4) { if (a[i + 3] < 8 && b[i + 3] < 8) continue; for (let k = 0; k < 4; k++) s += Math.abs(a[i + k] - b[i + k]); n += 4; } return n ? s / n : 0; };
const out = {}, abs = {}; let worst = 0;
for (const clip of clips) {
  const c = fj.clips[clip]; out[clip] = {}; abs[clip] = {};
  for (const d of Object.keys(c.dirs)) {
    const fr = []; for (let i = 0; i < c.n; i++) fr.push(await px(path.join(src, `${char}-${clip}-${d}-${i}.png`)));
    const steps = []; for (let i = 0; i + 1 < fr.length; i++) steps.push(diff(fr[i], fr[i + 1]));
    const avg = steps.reduce((a, b) => a + b, 0) / steps.length, seam = diff(fr[fr.length - 1], fr[0]);
    const ratio = +(seam / Math.max(avg, 0.25)).toFixed(2); out[clip][d] = ratio; abs[clip][d] = +seam.toFixed(2); worst = Math.max(worst, ratio);
  }
}
console.log(JSON.stringify({ char, loopSeamRatio: out, seamAbsDiff_0to255: abs, worst }, null, 1));
