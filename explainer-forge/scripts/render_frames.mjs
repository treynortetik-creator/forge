// Deterministic frame renderer: seek the paused timeline (and every <video>) per frame, screenshot, pipe to ffmpeg.
// Never screen-record the HTML in real time: it drops frames.
//
//   node render_frames.mjs --page build/stage.html --audio build/narration.m4a --out build/explainer.mp4 [--workers 8]
//   node render_frames.mjs --page build/stage.html --stills 12.5,40 [--dir proof]      PNG stills only
//   node render_frames.mjs --page ... --from 60 --to 70 --out preview.mp4               a section
//
// Page contract (templates/timeline.js provides it): window.__ready (Promise), window.__total (seconds),
// window.__seek(t) (async; sets every visual to time t and resolves when every video has seeked).
// Needs Playwright (`npm i playwright` beside the project, or PLAYWRIGHT_PATH=<module path>) and ffmpeg on PATH.
// Output: H.264 yuv420p crf 18 + AAC 160k, faststart. On a 10-core Apple Silicon Mac, 8-10 workers rendered
// about 2:45 at 1080p30 in about 6 minutes.
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const FF = process.env.FFMPEG || 'ffmpeg';
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node render_frames.mjs --page <stage.html> [--audio narration.m4a] [--out out.mp4] [--workers 8] [--fps 30] [--width 1920 --height 1080] [--from s --to s] [--stills s1,s2 --dir proof] [--channel chrome]');
  process.exit(arg('page') ? 0 : 2);
}
const pw = (() => {
  if (process.env.PLAYWRIGHT_PATH) return require(process.env.PLAYWRIGHT_PATH);
  try { return require('playwright'); } catch { return require('@playwright/test'); }
})();
const { chromium } = pw;
const PAGE = resolve(arg('page')), D = dirname(PAGE), URL = pathToFileURL(PAGE).href;
const FPS = +arg('fps', 30), WIDTH = +arg('width', 1920), HEIGHT = +arg('height', 1080);
const launch = { headless: true, args: ['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--disable-gpu-vsync'] };
if (arg('channel')) launch.channel = arg('channel');
const browser = await chromium.launch(launch);

async function openPage() {
  const ctx = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  page.on('console', m => { if (m.type() === 'warning' || m.type() === 'error') console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(URL, { waitUntil: 'load' });
  await page.evaluate(() => window.__ready);
  return page;
}
const seek = (page, t) => page.evaluate(t => window.__seek(t), t);

if (arg('stills')) {
  const out = resolve(arg('dir', join(D, 'proof'))); mkdirSync(out, { recursive: true });
  const page = await openPage();
  for (const s of arg('stills').split(',').map(Number)) {
    await seek(page, 0); await seek(page, s);
    await page.screenshot({ path: join(out, `t-${s.toFixed(2)}.png`) });
    console.log('still', s);
  }
  await browser.close(); process.exit(0);
}

const total = await (await openPage()).evaluate(() => window.__total);
const from = +arg('from', 0), to = Math.min(+arg('to', total), total);
const N = +arg('workers', 8), f0 = Math.round(from * FPS), f1 = Math.ceil(to * FPS);
const outFile = resolve(arg('out', join(D, 'explainer.mp4')));
const tmp = join(dirname(outFile), '.segs'); rmSync(tmp, { recursive: true, force: true }); mkdirSync(tmp, { recursive: true });
const per = Math.ceil((f1 - f0) / N), t0 = Date.now();
let done = 0;
async function worker(k) {
  const a = f0 + k * per, b = Math.min(f1, a + per); if (a >= b) return null;
  const page = await openPage();
  const seg = join(tmp, `seg${String(k).padStart(2, '0')}.mp4`);
  const ff = spawn(FF, ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-g', '60', '-r', String(FPS), seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  await seek(page, 0);
  await seek(page, Math.max(0, a / FPS - 1)); // roll in from 1 s before, so tweens initialise in order
  for (let f = a; f < b; f++) {
    await seek(page, f / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (++done % 300 === 0) console.log(`${done}/${f1 - f0} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  return seg;
}
const segs = (await Promise.all([...Array(N).keys()].map(worker))).filter(Boolean);
await browser.close();
const list = join(tmp, 'list.txt'); writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
const audioArg = arg('audio');
const audio = audioArg ? ['-ss', String(from), '-t', String((f1 - f0) / FPS), '-i', resolve(audioArg)] : [];
const maps = audioArg ? ['-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k'] : ['-map', '0:v'];
await new Promise((res, rej) => spawn(FF, ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, ...audio,
  ...maps, '-c:v', 'copy', '-movflags', '+faststart', outFile], { stdio: 'inherit' })
  .on('close', c => c ? rej(new Error('mux exit ' + c)) : res()));
rmSync(tmp, { recursive: true, force: true });
console.log('wrote', outFile, `${f1 - f0} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
