// A hero still for a post card or thumbnail, from the same page: calls window.__hero(t?) and screenshots the stage.
//   node hero.mjs --page build/page.html --out hero.png [--t 12.5] [--width 1920 --height 1080]
// Set window.HERO_TIME (and optionally HERO_SETUP, a function that enlarges labels or shows every chip) in scenes.js.
// For a taller card, make the page's HERO_SETUP grow #stage and pass --height. Playwright and Chrome: pw_common.mjs.
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { argOf as arg, loadPlaywright, launch } from './pw_common.mjs';

if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node hero.mjs --page <page.html> --out hero.png [--t seconds] [--width 1920] [--height 1080]');
  process.exit(arg('page') ? 0 : 2);
}
const W = +arg('width', 1920), H = +arg('height', 1080);
const pw = loadPlaywright();
const browser = await launch(pw);
const pg = await browser.newPage({ viewport: { width: W, height: H } });
const errs = [];
pg.on('pageerror', e => errs.push(String(e)));
await pg.goto(pathToFileURL(resolve(arg('page'))).href + '?render=1', { waitUntil: 'load' });
await pg.evaluate(() => window.__ready); await pg.evaluate(() => document.fonts.ready);
const t = arg('t');
await pg.evaluate(t => window.__hero(t === undefined ? undefined : +t), t);
await pg.waitForTimeout(300);
const out = resolve(arg('out', 'hero.png'));
await pg.screenshot({ path: out, clip: { x: 0, y: 0, width: W, height: H } });
console.log('hero', errs.length ? errs : 'ok', out);
await browser.close();
process.exit(errs.length ? 1 : 0);
