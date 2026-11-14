/* Explainer timeline engine. One paused GSAP master timeline; timeline time == narration time (seconds).
   Load order in the page: gsap.min.js, data.js (from prep_media.py), timeline.js, then your scenes.js.

   Lookups:  T(id) line start · E(id) line end · W(id, word, n) when that word is spoken (whisper word times)
   Builders: scene(id, tin, tout) · show(sel, t, vars) · hide(sel, t, vars) · stagger(sels, t, gap, vars)
             ring(sel, x, y, w, h, tin, tout)  a callout placed from a box MEASURED on the frame, never estimated
             focus(inner, vw, t, x, y, s)      zoom a 1920x1080 footage layer to source point (x, y) at scale s
             V(video, t0, clipIn, clipOut, rate)  from timeline t0 the clip plays clipIn -> clipOut (holds at ends)
             sped(t0, t1)  show the "Sped up" tag over a time-lapsed span · footage(t0, t1)  show the sample-data badge
   Contract for render_frames.mjs / ring_check.mjs: window.__ready, window.__total, window.__seek(t).
   Preview: open stage.html?play (with sound) or ?t=93 (park at a time). */
'use strict';
const L = {}; CUES.lines.forEach(l => L[l.id] = l);
const T = id => L[id].start, E = id => L[id].end;
const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
function W(id, word, n = 0) {
  const w = (window.WORDS || {})[id] || [], k = norm(word);
  for (const [txt, t] of w) if (norm(txt).startsWith(k) && n-- === 0) return t;
  console.warn('word not found', id, word); return T(id);
}
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
gsap.ticker.lagSmoothing(0);
const tl = gsap.timeline({ paused: true, defaults: { ease: 'power2.out', duration: 0.7 } });
window.tl = tl;

function scene(id, tin, tout) {
  tl.set('#' + id, { autoAlpha: 0 }, 0);
  tl.to('#' + id, { autoAlpha: 1, duration: 0.6, ease: 'power1.inOut' }, tin);
  if (tout != null) tl.to('#' + id, { autoAlpha: 0, duration: 0.6, ease: 'power1.inOut' }, tout);
}
const show = (sel, t, v = {}) => tl.to(sel, { autoAlpha: 1, y: 0, x: 0, scale: 1, duration: 0.7, ease: 'power3.out', ...v }, t);
const hide = (sel, t, v = {}) => tl.to(sel, { autoAlpha: 0, duration: 0.5, ease: 'power1.in', ...v }, t);
const stagger = (sels, t, gap, v) => sels.forEach((s, i) => show(s, t + i * gap, v));
const VIDS = [];
function V(el, t0, a, b, rate = 1) { VIDS.push({ el: typeof el === 'string' ? $(el) : el, t0, a, b, rate }); }
function focus(inner, vw, t, x, y, s, dur = 1.2, ease = 'power2.inOut') {
  const k = vw / 1920 * s, vh = vw * 9 / 16;
  let tx = vw / 2 - x * k, ty = vh / 2 - y * k;
  tx = Math.min(0, Math.max(vw - 1920 * k, tx)); ty = Math.min(0, Math.max(vh - 1080 * k, ty));
  tl.to(inner, { x: tx, y: ty, scale: k, duration: dur, ease }, t);
}
function ring(sel, x, y, w, h, t, out) {
  tl.set(sel, { left: x, top: y, width: w, height: h, scale: 1.08, autoAlpha: 0 }, 0);
  tl.to(sel, { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power3.out' }, t);
  if (out != null) tl.to(sel, { autoAlpha: 0, duration: 0.4 }, out);   // always give a ring its out time
}
const SPED = [], FOOT = [];
const sped = (a, b) => SPED.push([a, b]);
const footage = (a, b) => FOOT.push([a, b]);

/* ---------- per-frame state ---------- */
const ramp = (t, spans, e = 0.25) => spans.reduce((m, [a, b]) => Math.max(m, Math.min(1, (t - a + e) / e, (b + e - t) / e)), 0);
function overlays(t) {
  const s = $('#sped'), bdg = $('#badge');
  if (s) s.style.opacity = Math.max(0, ramp(t, SPED, 0.2)).toFixed(3);
  if (bdg) bdg.style.opacity = Math.max(0, ramp(t, FOOT, 0.4)).toFixed(3);
}
let capIdx = -2;
function captions(t) {
  const el = $('#capp'); const CAPS = window.CAPS || []; if (!el) return;
  const i = CAPS.findIndex(c => t >= c.start && t < c.end);
  if (i !== capIdx) { capIdx = i; if (i >= 0) el.innerHTML = CAPS[i].rows.map(r => r.replace(/&/g, '&amp;').replace(/</g, '&lt;')).join('<br>'); }
  if (i < 0) { el.style.opacity = 0; return; }
  const c = CAPS[i], fi = Math.min(1, (t - c.start) / 0.12), fo = Math.min(1, (c.end - t) / 0.12);
  const prev = CAPS[i - 1], next = CAPS[i + 1];   // chunks of one line butt up: fade only at line edges
  el.style.opacity = ((prev && Math.abs(prev.end - c.start) < 0.01 ? 1 : fi) * (next && Math.abs(next.start - c.end) < 0.01 ? 1 : fo)).toFixed(3);
}
function vidTarget(v, t) {
  const segs = VIDS.filter(u => u.el === v); let s = segs[0];
  for (const u of segs) if (u.t0 <= t + 1e-6 && u.t0 >= s.t0) s = u;
  return Math.min(s.b, Math.max(s.a, s.a + (t - s.t0) * s.rate));
}
function visible(el) { const s = el.closest('.scene'); return !s || parseFloat(getComputedStyle(s).opacity) > 0.001; }
async function seekVideos(t) {
  const jobs = [];
  for (const v of new Set(VIDS.map(u => u.el))) {
    if (!visible(v)) continue;
    const want = Math.min(vidTarget(v, t), (v.duration || 1e9) - 0.05) + 0.001;
    if (Math.abs(v.currentTime - want) < 0.004) continue;
    jobs.push(new Promise(res => { const done = () => { v.removeEventListener('seeked', done); res(); }; v.addEventListener('seeked', done); v.currentTime = want; setTimeout(done, 4000); }));
  }
  await Promise.all(jobs);
}
function frame(t) { tl.time(t, false); overlays(t); captions(t); const p = $('#prog'); if (p) p.style.width = (t / CUES.total * 100).toFixed(3) + '%'; }
window.__total = CUES.total;
window.__seek = async t => { frame(t); await seekVideos(t); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); return true; };
window.__ready = (async () => {
  await new Promise(r => (document.readyState === 'complete' ? r() : addEventListener('load', r, { once: true })));
  tl.to({}, { duration: 0.01 }, CUES.total - 0.01);   // pin the timeline length to the narration
  await document.fonts.ready;
  await Promise.all($$('img').map(i => i.decode().catch(() => {})));
  await Promise.all([...new Set(VIDS.map(u => u.el))].map(v => v.readyState >= 1 ? 0 : new Promise(r => { v.addEventListener('loadedmetadata', r, { once: true }); setTimeout(r, 8000); })));
  return true;
})();
const qs = new URLSearchParams(location.search);
window.__ready.then(() => {
  if (qs.has('t')) window.__seek(+qs.get('t'));
  else frame(0);
  if (qs.has('play')) {
    const a = $('#aud'); a.currentTime = 0; a.play();
    const loop = () => { frame(a.currentTime); seekVideos(a.currentTime); if (!a.paused) requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }
});
