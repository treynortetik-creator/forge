#!/usr/bin/env node
/**
 * record-reel.mjs: record gameplay segments from a browser game with headless Chrome
 * (puppeteer-core, page.screencast at 30 fps) driven by a JSON list of segments.
 * Pair it with cut-reel.sh (ffmpeg: trim, concat, 720p, music, size check).
 *
 * Usage:
 *   node record-reel.mjs --project <dir that has node_modules/puppeteer-core> --out <dir> \
 *        --segments segments.json (--url http://localhost:5173/ | --serve "<cmd>" [--serve-cwd <dir>]) \
 *        [--serve-env KEY=VAL ...] [--chrome <path>] [--width 1920] [--height 1080] [--fps 30] \
 *        [--ready "window.__game && window.__game.ready"] [--ready-timeout 60000]
 *
 *   --url      a server you already started (dev server, preview, deployed build)
 *   --serve    a command to start a static server for you; it gets PORT=<random 4700-4899> in its env,
 *              is polled until it answers, and is killed when the script ends
 *   --ready    JS expression the page sets when the game is playable (default: window.__game && window.__game.ready)
 *   page.screencast needs ffmpeg on PATH (puppeteer's own requirement).
 *
 * segments.json: an array of
 *   { "name": "fight-1",            // output file is <out>/<name>.webm
 *     "q": "scene=run&seed=7&bot=basic&mute=1",   // query string appended to the base URL (your dev params)
 *     "pre": 1500,                  // ms to wait after "ready" before recording starts (default 1500)
 *     "dur": 12000,                 // ms to record
 *     "keys": [ { "at": 500, "down": "KeyW" }, { "at": 1200, "up": "KeyW" },
 *               { "at": 2000, "press": "Space" }, { "at": 3000, "click": [960, 540] } ] }   // "at" = ms from record start
 *
 * Keys are real puppeteer keyboard/mouse events, so they go through the game's actual input path.
 * Tip: hold a key across frames (down ... up) when the game polls input each frame; a same-frame press/release can be lost.
 */
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const argv = process.argv.slice(2);
const get = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const all = (k) => argv.flatMap((a, i) => (a === '--' + k ? [argv[i + 1]] : []));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const project = resolve(get('project', '.'));
const out = resolve(get('out', 'reel-raw'));
const segFile = get('segments');
if (!segFile) { console.error('usage: record-reel.mjs --project <dir> --out <dir> --segments <file.json> (--url <url> | --serve "<cmd>")'); process.exit(2); }
const segs = JSON.parse(readFileSync(segFile, 'utf8'));
const W = Number(get('width', '1920')), H = Number(get('height', '1080')), FPS = Number(get('fps', '30'));
const chrome = get('chrome', process.env.CHROME_PATH ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
const ready = get('ready', 'window.__game && window.__game.ready');
const readyTimeout = Number(get('ready-timeout', '60000'));

const require = createRequire(resolve(project, 'package.json'));
const puppeteer = require('puppeteer-core');
mkdirSync(out, { recursive: true });

let base = get('url');
let srv = null;
if (!base) {
  const cmd = get('serve');
  if (!cmd) { console.error('need --url or --serve'); process.exit(2); }
  const port = 4700 + Math.floor(Math.random() * 200);
  const env = { ...process.env, PORT: String(port) };
  for (const kv of all('serve-env')) { const [k, ...v] = kv.split('='); env[k] = v.join('='); }
  srv = spawn(cmd, { shell: true, cwd: resolve(get('serve-cwd', project)), env, stdio: 'ignore' });
  base = `http://localhost:${port}/`;
  let up = false;
  for (let i = 0; i < 60 && !up; i++) { await sleep(500); try { up = (await fetch(base)).ok; } catch { /* not yet */ } }
  if (!up) { srv.kill(); console.error(`server did not answer at ${base}`); process.exit(1); }
}

const browser = await puppeteer.launch({
  executablePath: chrome, headless: true,
  args: ['--no-sandbox', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--autoplay-policy=no-user-gesture-required'],
  defaultViewport: { width: W, height: H, deviceScaleFactor: 1 },
});
try {
  for (const s of segs) {
    const page = await browser.newPage();
    const logs = [];
    page.on('pageerror', (e) => logs.push(String(e)));
    await page.goto(`${base}${s.q ? '?' + s.q : ''}`, { waitUntil: 'load', timeout: 60000 });
    await page.waitForFunction(ready, { timeout: readyTimeout }).catch(() => logs.push('ready timeout'));
    await sleep(s.pre ?? 1500);
    const rec = await page.screencast({ path: `${out}/${s.name}.webm`, fps: FPS });
    const t0 = Date.now();
    for (const k of s.keys ?? []) {
      await sleep(Math.max(0, k.at - (Date.now() - t0)));
      if (k.down) await page.keyboard.down(k.down);
      if (k.up) await page.keyboard.up(k.up);
      if (k.press) await page.keyboard.press(k.press);
      if (k.click) await page.mouse.click(k.click[0], k.click[1]);
    }
    await sleep(Math.max(0, s.dur - (Date.now() - t0)));
    await rec.stop();
    console.log(s.name, 'done', logs.slice(0, 3).join(' | '));
    await page.close();
  }
} finally {
  await browser.close();
  if (srv) srv.kill();
}
