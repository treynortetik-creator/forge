#!/usr/bin/env node
/**
 * perf-sample.mjs: frame-time sample of a browser game in headless Chrome (puppeteer-core).
 * Samples requestAnimationFrame deltas for N seconds and prints frame p50/p95/p99/worst, the count of frames over
 * 16.7 / 33 ms, the longest frames, the GPU renderer string and any console errors, as JSON.
 *
 * Usage:
 *   node perf-sample.mjs --project <dir with node_modules/puppeteer-core> --url "http://localhost:5173/?scene=run&bot=skilled&t=40&mute=1" \
 *        [--seconds 8] [--settle 2500] [--ready "window.__game && window.__game.ready"] [--width 1920 --height 1080] \
 *        [--chrome <path>] [--allow-third-party] [--max-p95 <ms>] [--max-over33 <n>] [--out result.json]
 *
 *   --settle   ms to wait after "ready" so shader links / font loads finish (they hide under a title card in the real game)
 *   --max-*    optional gates: exit 1 when exceeded. HEADLESS NUMBERS ARE NOT A REAL GPU: use the gates only against a
 *              baseline measured the same way on the same machine, never against a device target.
 * Third-party requests are aborted by default so a flaky network cannot decide a run (a render-blocking web font once did).
 * Run it under heavy-lock.sh, and check `uptime` first: another process's Chrome skews every number.
 */
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const a = process.argv.slice(2);
const get = (k, d) => { const i = a.indexOf('--' + k); return i >= 0 ? a[i + 1] : d; };
const url = get('url');
if (!url) { console.error('usage: perf-sample.mjs --project <dir> --url <url> [--seconds 8]'); process.exit(2); }
const seconds = Number(get('seconds', '8')), settle = Number(get('settle', '2500'));
const ready = get('ready', 'window.__game && window.__game.ready');
const require = createRequire(resolve(get('project', '.'), 'package.json'));
const puppeteer = require('puppeteer-core');
const chrome = get('chrome', process.env.CHROME_PATH ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({
  executablePath: chrome, headless: true,
  args: ['--no-sandbox', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--autoplay-policy=no-user-gesture-required'],
  defaultViewport: { width: Number(get('width', '1920')), height: Number(get('height', '1080')), deviceScaleFactor: 1 },
});
let code = 0;
try {
  const page = await browser.newPage();
  const logs = [];
  page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => logs.push(`[pageerror] ${e}`));
  if (!a.includes('--allow-third-party')) {
    const origin = new URL(url).origin;
    await page.setRequestInterception(true);
    page.on('request', (rq) => { if (rq.url().startsWith(origin) || !/^https?:/.test(rq.url())) void rq.continue(); else void rq.abort(); });
  }
  await page.goto(url, { waitUntil: 'load', timeout: 90000 });
  await page.waitForFunction(ready, { timeout: 90000 });
  await sleep(settle);
  // in-page code is a STRING: a TS runner (tsx/esbuild) injects __name() helpers into function literals and breaks page.evaluate
  const res = await page.evaluate(`(async (secs) => {
    const times = []; const long = [];
    await new Promise((done) => {
      let last = performance.now(); const t0 = last;
      function tick() {
        const now = performance.now(); const d = now - last; times.push(d); last = now;
        if (d > 33 && long.length < 20) long.push(Math.round(d));
        if (now - t0 < secs * 1000) requestAnimationFrame(tick); else done();
      }
      requestAnimationFrame(tick);
    });
    times.shift();
    const s = [...times].sort((x, y) => x - y);
    const q = (p) => Math.round(s[Math.min(s.length - 1, Math.floor(s.length * p))] * 10) / 10;
    const avg = times.reduce((x, y) => x + y, 0) / times.length;
    const c = document.querySelector('canvas'); const gl = c && (c.getContext('webgl2') || c.getContext('webgl'));
    const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
    return { frames: times.length, avgFps: Math.round(10000 / avg) / 10, p50: q(0.5), p95: q(0.95), p99: q(0.99), worst: q(1),
      over16: times.filter((x) => x > 16.7).length, over33: times.filter((x) => x > 33).length, longFramesMs: long,
      gpu: dbg && gl ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'unknown' };
  })(${seconds})`);
  res.consoleErrors = logs.filter((l) => /error/i.test(l)).slice(0, 10);
  console.log(JSON.stringify(res, null, 1));
  if (get('out')) writeFileSync(get('out'), JSON.stringify(res, null, 1));
  const mp = get('max-p95'), m33 = get('max-over33');
  if (mp !== undefined && res.p95 > Number(mp)) { console.error(`FAIL p95 ${res.p95} > ${mp}`); code = 1; }
  if (m33 !== undefined && res.over33 > Number(m33)) { console.error(`FAIL over33 ${res.over33} > ${m33}`); code = 1; }
} finally {
  await browser.close();
}
process.exit(code);
