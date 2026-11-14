// Proof for the INTERACTIVE HTML explainer (slides that build step by step, narration synced to cues).
//
//   node deck_proof.mjs --page explainer.html [--out proof]              every slide, desktop 1280x720 + phone 390x844
//   node deck_proof.mjs --page explainer.html --sync cues.json [--rate 1.5]   seek every cue, the deck must land on it
//
// Page contract (see references/formats.md):
//   .slide[data-steps]   one element per slide; data-steps = number of builds on that slide
//   window.__deck.go(slide, step), window.__deck.next()
//   <audio id="aud">, a sync checkbox #sync, a speed button #spd (cycles 1, 1.25, 1.5, 1.75, 2)
//   location.hash == "#<slide>.<step>" (1-based slide) while synced
// cues.json for --sync: [[slide1_start, build1, build2, ...], [slide2_start, ...], ...] in seconds.
// Slide mode reports text under 18 px and anything overflowing the #stage box; read every PNG anyway.
// Sync mode prints OK/BAD per cue and the mismatch count (must be 0, at 1x and at the --rate you ship).
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
if (process.argv.includes('--help') || !arg('page')) {
  console.log('usage: node deck_proof.mjs --page <explainer.html> [--out proof] [--sync cues.json [--rate 1]]');
  process.exit(arg('page') ? 0 : 2);
}
const pw = (() => {
  if (process.env.PLAYWRIGHT_PATH) return require(process.env.PLAYWRIGHT_PATH);
  try { return require('playwright'); } catch { return require('@playwright/test'); }
})();
const PAGE = resolve(arg('page')), URL = pathToFileURL(PAGE).href;
const OUT = resolve(arg('out', join(dirname(PAGE), 'proof'))); mkdirSync(OUT, { recursive: true });
const b = await pw.chromium.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--ignore-gpu-blocklist'] });

if (arg('sync')) {
  const cues = JSON.parse(readFileSync(resolve(arg('sync'))));
  const RATE = +arg('rate', 1);
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto(URL); await pg.waitForTimeout(2000);
  await pg.evaluate(() => { const s = document.getElementById('sync'); if (s) s.checked = true; });
  for (let i = 0; i < 6 && await pg.evaluate(() => document.getElementById('aud').playbackRate) !== RATE; i++) await pg.click('#spd');
  console.log('rate', await pg.evaluate(() => document.getElementById('aud').playbackRate));
  let bad = 0, n = 0;
  for (let si = 0; si < cues.length; si++) for (let c = 0; c < cues[si].length; c++) {
    await pg.evaluate(t => { document.getElementById('aud').currentTime = t; }, cues[si][c] + 0.05);
    await pg.waitForTimeout(500);
    const h = await pg.evaluate(() => location.hash), want = `#${si + 1}.${c}`; n++; if (h !== want) bad++;
    console.log(`${si + 1}.${c}`.padEnd(6), cues[si][c].toFixed(2).padStart(7), h === want ? 'OK ' : 'BAD', h);
  }
  console.log('cues checked', n, 'mismatches', bad, 'page errors', JSON.stringify(errs.slice(0, 5)));
  await b.close(); process.exit(bad ? 1 : 0);
}

let problems = 0;
for (const [tag, vp] of [['desk', { width: 1280, height: 720 }], ['phone', { width: 390, height: 844 }]]) {
  const pg = await b.newPage({ viewport: vp, deviceScaleFactor: tag === 'phone' ? 2 : 1 }); const errs = [];
  pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(URL); await pg.waitForTimeout(2500);
  const n = await pg.evaluate(() => document.querySelectorAll('.slide').length);
  for (let si = 0; si < n; si++) {
    const steps = await pg.evaluate(si => +document.querySelectorAll('.slide')[si].dataset.steps || 0, si);
    await pg.evaluate(si => window.__deck.go(si, 0), si); await pg.waitForTimeout(700);
    for (let k = 1; k <= steps; k++) { await pg.evaluate(() => window.__deck.next()); await pg.waitForTimeout(350); }
    await pg.waitForTimeout(2500);
    await pg.screenshot({ path: join(OUT, `${tag}-s${si + 1}.png`) });
    if (tag === 'phone') {
      const h = await pg.evaluate(si => { const s = document.querySelectorAll('.slide')[si]; return [s.scrollHeight, s.clientHeight]; }, si);
      if (h[0] > h[1] + 10) { await pg.evaluate(si => { const s = document.querySelectorAll('.slide')[si]; s.scrollTop = s.scrollHeight; }, si); await pg.waitForTimeout(400); await pg.screenshot({ path: join(OUT, `${tag}-s${si + 1}-end.png`) }); }
    }
    const small = await pg.evaluate(si => [...document.querySelectorAll('.slide')[si].querySelectorAll('*')]
      .filter(e => e.children.length === 0 && e.textContent.trim() && getComputedStyle(e).opacity !== '0' && e.offsetParent !== null)
      .filter(e => e.getBoundingClientRect().height > 0 && parseFloat(getComputedStyle(e).fontSize) * (e.getBoundingClientRect().height / (e.offsetHeight || 1)) < 18)
      .map(e => e.textContent.trim().slice(0, 24)).slice(0, 6), si);
    const over = await pg.evaluate(si => { const st = document.getElementById('stage'); if (!st) return [];
      const box = st.getBoundingClientRect(); return [...document.querySelectorAll('.slide')[si].querySelectorAll('*')]
        .filter(e => { const r = e.getBoundingClientRect(); return r.width && getComputedStyle(e).opacity !== '0' && (r.right > box.right + 1 || r.bottom > box.bottom + 1); })
        .map(e => e.className || e.tagName).slice(0, 5); }, si);
    if (small.length || over.length) problems++;
    console.log(tag, 's' + (si + 1), 'small<18px:', JSON.stringify(small), 'overflow:', JSON.stringify(over));
  }
  console.log(tag, 'errors', JSON.stringify(errs.slice(0, 8))); if (errs.length) problems++;
  await pg.close();
}
await b.close();
process.exit(problems ? 1 : 0);
