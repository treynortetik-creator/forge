#!/usr/bin/env node
/**
 * shot.js — deterministic headless screenshot of a scroll-film page.
 *
 *   node shot.js <url> <out.png> [width] [height] [scrollFraction|scrollPx]
 *
 *   node shot.js http://localhost:8080 top.png                 # top of page
 *   node shot.js http://localhost:8080 mid.png 1440 900 0.35   # 35% down
 *   node shot.js http://localhost:8080 m.png   390  844 0.5    # mobile breakpoint
 *
 * A value <= 1 is treated as a fraction of the scrollable height; anything
 * larger is treated as an absolute pixel offset.
 *
 * Why this exists: a screenshot taken through an IDE preview pane is black
 * whenever the pane is hidden or zero-size, which reads as "the film is
 * broken" when it is fine. This runs in a fixed offscreen viewport instead,
 * so a black frame here means a black frame, full stop.
 *
 * Requires Chrome/Chromium on the machine. Run `npm install` in this folder
 * once (see package.json) to get puppeteer-core.
 */
const fs = require('node:fs');
const path = require('node:path');

let puppeteer;
try {
  puppeteer = require('puppeteer-core');
} catch {
  console.error(
    'shot.js: puppeteer-core is not installed.\n' +
    `  cd "${__dirname}" && npm install\n`
  );
  process.exit(2);
}

/** Chrome ships in different places per OS; find one rather than hardcoding. */
function findChrome() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) {
    return process.env.CHROME_PATH;
  }
  const candidates = {
    darwin: [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    ],
    linux: [
      '/usr/bin/google-chrome',
      '/usr/bin/google-chrome-stable',
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
      '/snap/bin/chromium',
    ],
    win32: [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ],
  }[process.platform] || [];

  const found = candidates.find((p) => fs.existsSync(p));
  if (!found) {
    console.error(
      'shot.js: no Chrome/Chromium found.\n' +
      '  Install Chrome, or set CHROME_PATH to the executable.\n' +
      `  Looked in:\n${candidates.map((c) => '    ' + c).join('\n')}\n`
    );
    process.exit(2);
  }
  return found;
}

(async () => {
  const [url, out, w, h, pos] = process.argv.slice(2);
  if (!url || !out) {
    console.error('usage: node shot.js <url> <out.png> [width] [height] [scrollFraction|scrollPx]');
    process.exit(1);
  }

  const width = Number(w) || 1440;
  const height = Number(h) || 900;

  const browser = await puppeteer.launch({
    executablePath: findChrome(),
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 2 });
    // NOT networkidle0: this page is a continuous image pump — a 601-frame film keeps a
    // sliding decode window in flight, so the network may never go idle and goto() would
    // throw a navigation timeout without ever taking a shot.
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

    // The engine sets window.__ready once the first frame is painted. That, not the
    // network, is the real readiness signal.
    const sawReady = await page
      .waitForFunction('window.__ready === true', { timeout: 15000 })
      .then(() => true)
      .catch(() => false);
    await new Promise((r) => setTimeout(r, sawReady ? 900 : 2500));

    let requested = null;
    if (pos !== undefined) {
      const v = Number(pos);
      if (Number.isNaN(v)) {
        console.error(`shot.js: scroll position "${pos}" is not a number`);
        process.exit(1);
      }
      requested = await page.evaluate((val) => {
        const doc = document.documentElement;
        // documentElement is the scroller in these builds; body under-reports when
        // html carries the height.
        const height = Math.max(doc.scrollHeight, document.body.scrollHeight);
        const max = Math.max(0, height - window.innerHeight);
        const target = val <= 1 ? Math.round(max * val) : Math.round(val);
        // Lenis owns scroll when present and fights a bare scrollTo, so drive it
        // through Lenis if the page exposes it.
        if (window.lenis && typeof window.lenis.scrollTo === 'function') {
          window.lenis.scrollTo(target, { immediate: true });
        }
        window.scrollTo(0, target);
        return target;
      }, v);
      // let the lerped playhead settle onto the target frame
      await new Promise((r) => setTimeout(r, 1800));
    }

    fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
    await page.screenshot({ path: out });

    // Report what was actually captured — a hidden viewport reports 0 here,
    // which is how you tell "pane was hidden" from "the film is black".
    const info = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      const doc = document.documentElement;
      return {
        innerWidth: window.innerWidth,
        scrollY: Math.round(window.scrollY),
        docHeight: Math.max(doc.scrollHeight, document.body.scrollHeight),
        canvas: c ? `${c.width}x${c.height}` : 'none',
        overflowX: doc.scrollWidth > window.innerWidth,
      };
    });
    const result = { out, ready: sawReady, ...info };

    // A requested scroll that did not land is the difference between "the film isn't
    // scrubbing" and "the screenshot was taken at the top". Say which, loudly.
    if (requested !== null && Math.abs(info.scrollY - requested) > 4) {
      result.scrollMismatch = { requested, achieved: info.scrollY };
      console.error(
        `shot.js WARNING: asked for scrollY=${requested}, page settled at ${info.scrollY}. ` +
        `The capture is NOT at the position you requested — do not read it as a film fault.`
      );
    }
    if (info.canvas === 'none' || info.innerWidth === 0) {
      console.error('shot.js WARNING: no canvas / zero-width viewport — the page did not mount. A black capture here means nothing.');
    }
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error('shot.js failed:', e.message);
  process.exit(1);
});
