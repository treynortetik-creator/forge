// Proof pass on a built explainer page: stills at the moment each line is landing, page errors, text under a size
// floor measured AFTER the camera scale, and the dead-air check.
//
//   node proof.mjs --page build/page.html --out proof [--mode chunks|times|scene] [--times 12,40.5] [--scene 2]
//                  [--at 0.75] [--min-px 24] [--max-gap 1.2] [--cues audio/cues.json] [--audio audio/narration.m4a]
//
// chunks (default): one still per cue chunk, at --at (default 0.75) of the way through it, named <scene>-<id>.jpg.
// Reads window.__cues from the page unless --cues is given. LOOK AT EVERY STILL: stray callouts, overlapping fades,
// text cut by the frame, a caption over a label. The audit lists, per still, every visible text under --min-px on the
// 1920x1080 frame (font size x the transform scale it is drawn at). Writes proof/report.json; exit 1 on a page error,
// a small-text hit, or dead air. Playwright and Chrome: see pw_common.mjs.
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { argOf as arg, loadPlaywright, launch } from './pw_common.mjs';

if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node proof.mjs --page <page.html> --out <dir> [--mode chunks|times|scene] [--times a,b] [--scene N] [--at 0.75] [--min-px 24] [--max-gap 1.2] [--cues cues.json] [--audio narration.m4a]');
  process.exit(arg('page') ? 0 : 2);
}
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(arg('out', 'proof')); mkdirSync(OUT, { recursive: true });
const MINPX = +arg('min-px', 24), AT = +arg('at', 0.75), MAXGAP = +arg('max-gap', 1.2);
const pw = loadPlaywright();
const browser = await launch(pw);
const pg = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errs = [];
pg.on('pageerror', e => errs.push(String(e)));
pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
await pg.goto(pathToFileURL(resolve(arg('page'))).href + '?render=1', { waitUntil: 'load' });
await pg.evaluate(() => window.__ready); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(300);
const cues = arg('cues') ? JSON.parse(readFileSync(arg('cues'), 'utf8')) : await pg.evaluate(() => window.__cues);

let shots = [];
const mode = arg('mode', 'chunks');
if (mode === 'times') shots = (arg('times', '') || '').split(',').filter(Boolean).map(t => [`t${(+t).toFixed(1).padStart(6, '0')}`, +t]);
else for (const s of cues.scenes) {
  if (mode === 'scene' && String(s.n) !== String(arg('scene'))) continue;
  for (const c of cues.chunks.filter(c => c.scene === s.n)) shots.push([`s${String(s.n).padStart(2, '0')}-${c.id}`, c.start + AT * (c.end - c.start)]);
}

const audit = () => {      // visible text smaller than the floor, in drawn (post-transform) pixels
  const out = [];
  const opacityOf = e => { let o = 1; for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const cs = getComputedStyle(n); if (cs.visibility === 'hidden' || cs.display === 'none') return 0; o *= parseFloat(cs.opacity); } return o; };
  for (const e of document.querySelectorAll('#stage *')) {
    if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.right < 0 || r.left > 1920 || r.bottom < 0 || r.top > 1080) continue;
    if (opacityOf(e) < 0.05) continue;
    const fs = parseFloat(getComputedStyle(e).fontSize);
    const k = e.offsetWidth ? r.width / e.offsetWidth : 1;
    out.push([+(fs * (k > 0 ? k : 1)).toFixed(1), e.textContent.trim().slice(0, 40)]);
  }
  return out;
};
const small = {};
for (const [name, t] of shots) {
  await pg.evaluate(t => window.__seek(t), t); await pg.waitForTimeout(40);
  await pg.screenshot({ path: join(OUT, name + '.jpg'), type: 'jpeg', quality: 82, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
  for (const [px, txt] of await pg.evaluate(audit)) if (px < MINPX) (small[`${px} ${txt}`] ||= []).push(name);
}
await browser.close();

let dead = { ran: false, ok: true, output: '' };
if (arg('cues') || cues) {
  const cf = arg('cues') || join(OUT, '_cues.json'); if (!arg('cues')) writeFileSync(cf, JSON.stringify(cues));
  const args = [join(HERE, 'dead_air.py'), '--cues', cf, '--max', String(MAXGAP)]; if (arg('audio')) args.push('--audio', arg('audio'));
  const r = spawnSync('python3', args, { encoding: 'utf8' });
  dead = { ran: true, ok: r.status === 0, output: (r.stdout || '') + (r.stderr || '') };
}
const smallList = Object.entries(small).map(([k, v]) => `${k}  (${v.length} stills, first ${v[0]})`);
console.log(`stills ${shots.length} -> ${OUT}`);
console.log('page errors:', errs.length ? errs : 0);
console.log(`text under ${MINPX}px:`, smallList.length ? smallList : 0);
console.log('dead air:', dead.ran ? dead.output.trim() : 'not run');
writeFileSync(join(OUT, 'report.json'), JSON.stringify({ stills: shots.length, errors: errs, small_text: small, dead_air: dead }, null, 1));
process.exit(errs.length || smallList.length || !dead.ok ? 1 : 0);
