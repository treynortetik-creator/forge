// Shared by render_frames.mjs, proof.mjs and hero.mjs: find Playwright and a Chrome, with no hard-coded paths.
//   Playwright: --playwright <module dir>, $PLAYWRIGHT_PATH, `playwright` resolved from this folder, from the current
//               folder, or from `npm root -g`, then `@playwright/test`.
//   Browser:    --chrome-path <exe>, $CHROME_PATH, a Chrome/Chromium in the usual places, else Playwright's own
//               Chromium (npx playwright install chromium). --channel chrome picks an installed Chrome by channel.
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { join } from 'node:path';

export const argOf = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 && i + 1 < process.argv.length ? process.argv[i + 1] : d; };
export const flag = k => process.argv.includes('--' + k);

export function loadPlaywright() {
  const tries = [];
  const explicit = argOf('playwright') || process.env.PLAYWRIGHT_PATH;
  if (explicit) tries.push(() => createRequire(import.meta.url)(explicit));
  tries.push(() => createRequire(import.meta.url)('playwright'));
  tries.push(() => createRequire(join(process.cwd(), 'x.js'))('playwright'));
  tries.push(() => { const root = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); return createRequire(join(root, 'x.js'))('playwright'); });
  tries.push(() => createRequire(import.meta.url)('@playwright/test'));
  for (const t of tries) { try { const m = t(); if (m && m.chromium) return m; } catch { /* next */ } }
  console.error('Playwright not found: `npm i playwright` beside the project, or --playwright <dir> / PLAYWRIGHT_PATH=<dir>');
  process.exit(2);
}

export function findChrome() {
  const c = argOf('chrome-path') || process.env.CHROME_PATH;
  if (c) return c;
  const spots = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  ];
  return spots.find(p => existsSync(p));   // undefined = Playwright's bundled Chromium
}

export async function launch(pw, extra = {}) {
  const opts = { headless: true, args: ['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--disable-gpu-vsync'], ...extra };
  if (argOf('channel')) opts.channel = argOf('channel');
  else if (!flag('bundled')) { const exe = findChrome(); if (exe) opts.executablePath = exe; }
  return pw.chromium.launch(opts);
}
