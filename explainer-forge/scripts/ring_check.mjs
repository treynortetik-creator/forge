// Callout check: for every highlight ring, find the middle of its fully visible window, seek there, and save a crop
// around the ring as rendered (after any zoom). Read every crop: a ring a few pixels off its target reads as sloppy.
//
//   node ring_check.mjs --page build/stage.html [--selector ".ring"] [--step 0.1] [--out proof/rings]
//
// A ring counts as fully visible when its opacity times its .scene's opacity is above 0.98. Prints one line per
// ring with its visible window and screen box; "NEVER fully visible" is a defect (a ring that never lands).
// Same page contract and Playwright lookup as render_frames.mjs.
import { loadPlaywright, launch } from './pw_common.mjs';
import { mkdirSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node ring_check.mjs --page <stage.html> [--selector .ring] [--step 0.1] [--from 0] [--out proof/rings] [--width 1920 --height 1080]');
  process.exit(arg('page') ? 0 : 2);
}
const pw = loadPlaywright();
const PAGE = resolve(arg('page')), SEL = arg('selector', '.ring'), STEP = +arg('step', 0.1);
const W = +arg('width', 1920), H = +arg('height', 1080);
const OUT = resolve(arg('out', join(dirname(PAGE), 'proof', 'rings'))); mkdirSync(OUT, { recursive: true });
const b = await launch(pw);
const p = await b.newPage({ viewport: { width: W, height: H } });
await p.goto(pathToFileURL(PAGE).href); await p.evaluate(() => window.__ready);
const total = await p.evaluate(() => window.__total);
const n = await p.evaluate(sel => document.querySelectorAll(sel).length, SEL);
const vis = {};
for (let t = +arg('from', 0); t < total; t += STEP) {
  await p.evaluate(t => window.__seek(t), t);
  const ops = await p.evaluate(sel => [...document.querySelectorAll(sel)].map(r => {
    const sc = r.closest('.scene');
    return parseFloat(getComputedStyle(r).opacity) * (sc ? parseFloat(getComputedStyle(sc).opacity) : 1);
  }), SEL);
  ops.forEach((o, i) => { if (o > 0.98) (vis[i] ??= []).push(t); });
}
let never = 0;
for (let i = 0; i < n; i++) {
  const ts = vis[i]; if (!ts) { console.log('ring', i, 'NEVER fully visible'); never++; continue; }
  const t = ts[Math.floor(ts.length / 2)];
  await p.evaluate(t => window.__seek(t), t);
  const r = await p.evaluate(([sel, i]) => { const e = document.querySelectorAll(sel)[i].getBoundingClientRect(); return { x: e.x, y: e.y, w: e.width, h: e.height }; }, [SEL, i]);
  const clip = { x: Math.max(0, r.x - 70), y: Math.max(0, r.y - 50) };
  clip.width = Math.max(1, Math.min(W - clip.x, r.w + 140)); clip.height = Math.max(1, Math.min(H - clip.y, r.h + 100));
  await p.screenshot({ path: join(OUT, `ring${i}.png`), clip });
  console.log('ring', i, 't', t.toFixed(1), 'visible', ts[0].toFixed(1), '-', ts[ts.length - 1].toFixed(1), 'screen', JSON.stringify(r));
}
await b.close();
process.exit(never ? 1 : 0);
