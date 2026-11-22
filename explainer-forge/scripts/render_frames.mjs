// Deterministic frame renderer: seek the paused timeline per frame, screenshot, hand the frames to ffmpeg.
// Never screen-record the HTML in real time: it drops frames.
//
//   node render_frames.mjs --page build/page.html --audio audio/narration.m4a --out out/explainer.mp4 [--workers 8]
//   node render_frames.mjs --page build/page.html --stills 12.5,40 [--dir proof]        PNG stills only
//   node render_frames.mjs --page ... --from 60 --to 70 --out preview.mp4                  a section
//   node render_frames.mjs --page ... --frames frames --out out.mp4                         RESUMABLE: frames kept on disk (stamped with the page hash, fps, size and format; a mismatch deletes the old frames)
//
// Page contract (templates/engine/engine.js and templates/timeline.js both provide it): window.__ready (Promise or
// true), window.__total (seconds), window.__seek(t). The page is opened with ?render=1 (override: --query "x=1" or
// --query "" for none) so the engine drops its player bar and draws the bare 1920x1080 stage.
// Default mode pipes PNG frames from each worker into its own ffmpeg segment, then concatenates and muxes the audio.
// --frames DIR instead writes f00000.png|jpg files (skipping any that exist, so an interrupted render resumes) and
// encodes once at the end; add --jpeg 92 for smaller JPEG frames. Both end in H.264 yuv420p crf 18 + AAC 160k, faststart.
// Playwright and Chrome: see pw_common.mjs (--playwright, $PLAYWRIGHT_PATH, --chrome-path, $CHROME_PATH, --channel, --bundled).
// On a 10-core Apple Silicon Mac, 8-10 workers rendered a 2:45 1080p30 explainer in about 6 minutes.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, rmSync, existsSync, readFileSync, readdirSync, statSync, renameSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { argOf as arg, loadPlaywright, launch } from './pw_common.mjs';

const FF = process.env.FFMPEG || 'ffmpeg';
if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node render_frames.mjs --page <page.html> [--audio narration.m4a] [--out out.mp4] [--workers 8] [--fps 30] [--width 1920 --height 1080] [--from s --to s] [--stills s1,s2 --dir proof] [--frames DIR [--jpeg 92]] [--query render=1] [--playwright DIR] [--chrome-path EXE] [--channel chrome]');
  process.exit(arg('page') ? 0 : 2);
}
const pw = loadPlaywright();
const PAGE = resolve(arg('page')), D = dirname(PAGE);
const Q = arg('query', 'render=1');
const URL = pathToFileURL(PAGE).href + (Q ? '?' + Q : '');
const FPS = +arg('fps', 30), WIDTH = +arg('width', 1920), HEIGHT = +arg('height', 1080);
const browser = await launch(pw);

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
mkdirSync(dirname(outFile), { recursive: true });
const audioArg = arg('audio');
const audio = audioArg ? ['-ss', String(from), '-t', String((f1 - f0) / FPS), '-i', resolve(audioArg)] : [];
const maps = audioArg ? ['-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k'] : ['-map', '0:v'];
const enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-g', '60', '-r', String(FPS)];
const t0 = Date.now();
let done = 0;
const run = (args) => new Promise((res, rej) => spawn(FF, args, { stdio: 'inherit' }).on('close', c => c ? rej(new Error('ffmpeg exit ' + c)) : res()));

if (arg('frames')) {
  const dir = resolve(arg('frames')); mkdirSync(dir, { recursive: true });
  const jq = arg('jpeg'); const ext = jq ? 'jpg' : 'png';
  // Resume is only safe when the folder's frames came from THIS page at THIS fps, size and format. A stamp file records
  // that; on a mismatch (page edited, other fps, other format, no stamp) the old frames are deleted, never reused.
  const stamp = { page: createHash('sha256').update(readFileSync(PAGE)).digest('hex'), query: Q, fps: FPS, width: WIDTH, height: HEIGHT, ext, jpeg: jq || null };
  const stampFile = join(dir, '.stamp.json');
  let same = false;
  try { same = JSON.stringify(JSON.parse(readFileSync(stampFile, 'utf8'))) === JSON.stringify(stamp); } catch {}
  const old = readdirSync(dir).filter(n => /^f\d+\.(png|jpg)(\.part)?$/.test(n));
  if (!same && old.length) { console.log(`frames in ${dir} are from a different page or settings: deleting ${old.length} old file(s)`); old.forEach(n => rmSync(join(dir, n))); }
  readdirSync(dir).filter(n => n.endsWith('.part')).forEach(n => rmSync(join(dir, n)));   // interrupted writes
  writeFileSync(stampFile, JSON.stringify(stamp));
  const framePath = f => join(dir, `f${String(f).padStart(5, '0')}.${ext}`);
  const have = f => { try { return statSync(framePath(f)).size > 0; } catch { return false; } };   // a zero-byte file is not a frame
  let next = f0;
  await Promise.all([...Array(N).keys()].map(async () => {
    const page = await openPage();
    await seek(page, 0);
    while (true) {
      const f = next++; if (f >= f1) break;
      if (have(f)) { done++; continue; }
      const p = framePath(f), part = p + '.part';
      await seek(page, f / FPS);
      await page.screenshot(jq ? { path: part, type: 'jpeg', quality: +jq } : { path: part, type: 'png' });
      renameSync(part, p);            // a frame exists only once it is complete
      if (++done % 300 === 0) console.log(`${done}/${f1 - f0} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
  }));
  await browser.close();
  const missing = []; for (let f = f0; f < f1; f++) if (!have(f)) missing.push(f);
  if (missing.length) { console.error(`ERROR ${missing.length} frame(s) missing or empty, first ${missing[0]}`); process.exit(1); }
  await run(['-loglevel', 'error', '-y', '-framerate', String(FPS), '-start_number', String(f0), '-i', join(dir, `f%05d.${ext}`), '-frames:v', String(f1 - f0), ...audio, ...maps, ...enc, '-movflags', '+faststart', outFile]);
  const got = +execFileSync(process.env.FFPROBE || 'ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', outFile]).toString().trim();
  if (got !== f1 - f0) { console.error(`ERROR encoded ${got} frames, expected ${f1 - f0}`); process.exit(1); }
  console.log('wrote', outFile, `${got} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s (frames kept in ${dir})`);
  process.exit(0);
}

const tmp = join(dirname(outFile), '.segs'); rmSync(tmp, { recursive: true, force: true }); mkdirSync(tmp, { recursive: true });
const per = Math.ceil((f1 - f0) / N);
async function worker(k) {
  const a = f0 + k * per, b = Math.min(f1, a + per); if (a >= b) return null;
  const page = await openPage();
  const seg = join(tmp, `seg${String(k).padStart(2, '0')}.mp4`);
  const ff = spawn(FF, ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-', ...enc, seg], { stdio: ['pipe', 'inherit', 'inherit'] });
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
await run(['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, ...audio, ...maps, '-c:v', 'copy', '-movflags', '+faststart', outFile]);
rmSync(tmp, { recursive: true, force: true });
const got = +execFileSync(process.env.FFPROBE || 'ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', outFile]).toString().trim();
if (got !== f1 - f0) { console.error(`ERROR encoded ${got} frames, expected ${f1 - f0}`); process.exit(1); }
console.log('wrote', outFile, `${f1 - f0} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
