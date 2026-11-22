/* Explainer engine. One 1920x1080 stage, one paused GSAP timeline, and a per-frame updater list. Everything on screen
   is a pure function of the AUDIO TIME t, so live playback, a scrubber drag, a still and a frame-by-frame render all
   show the same picture. Never put wall-clock time in an animation.

   Page contract (used by scripts/render_frames.mjs, proof.mjs, hero.mjs):
     window.__ready   resolves when fonts and images are decoded
     window.__total   duration in seconds        window.__dur  same
     window.__seek(t) show time t (sync; also safe to await)
     window.__cues    the cue sheet               window.__hero(t?)  a still for a post card (see HERO_TIME)
     ?render          bare 1920x1080 stage, no player        #t=42  park at 42 s

   Globals for scene scripts
     cues     S(id) chunk start, E(id) chunk end, SC(n) scene start, SE(n) scene end, DUR
     dom      $, $$, el(parent, html, css, cls), svgAbs(parent, inner, id), mark(parent, 'ok'|'bad', x, y, size)
     sprites  sprite(parent, name, x, y, h, opts)    x = centre, y = BOTTOM edge, h = height in px, aspect from IMGAR
     motion   tl (GSAP timeline), pop, fade, swap, squash, popIn, hideAt, tagAt + tagPop, UPD.push(t => ...)
     belt     track(svgPathD) -> {L, at(len)};  belt(parent, tracks, {w, rail, bed, side, img, th, sp, speed, rollerImg, rr, rollers})
              returns a function t => move slats; call it from UPD
     token    Tok(parent, kind, scale, {bad}) with .ride(track, l0, l1, t0, dur) .hop(p0, p1, t0, dur, h) .loop(track, t0, dur, laps)
              .key(t, {o, s, bad, dot}) .posAt(t)
     camera   cam(t, dur, zoom, x, y, follow?) queues eased moves of #world; call worldOn(a, b) to show the layer
     captions capHigh(a, b) lifts the caption bar between two times; guardEdges(selectors) hides labels cut by the frame
   Scene markup: <section class="scene" id="sc1"> ... one per cue scene (id = 'sc' + n). */
'use strict';
const NS = 'http://www.w3.org/2000/svg';
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const DUR = CUES.duration;
const S = id => { const c = CUES.chunks.find(c => c.id === id); if (!c) throw new Error('no cue ' + id); return c.start; };
const E = id => { const c = CUES.chunks.find(c => c.id === id); if (!c) throw new Error('no cue ' + id); return c.end; };
const SC = n => { const s = CUES.scenes.find(s => s.n === n); if (!s) throw new Error('no scene ' + n); return s.start; };
const SE = n => { const i = CUES.scenes.findIndex(s => s.n === n); return i + 1 < CUES.scenes.length ? CUES.scenes[i + 1].start : DUR; };
if (IMGS.plaque) { document.documentElement.style.setProperty('--plaque', `url(${IMGS.plaque})`); document.documentElement.classList.add('has-plaque'); }

const tl = gsap.timeline({ paused: true });
const UPD = [];
const lerp = (a, b, u) => a + (b - a) * u, clamp01 = u => Math.max(0, Math.min(1, u));
const EASE = { io: gsap.parseEase('power1.inOut'), o: gsap.parseEase('power2.out'), i: gsap.parseEase('power2.in'), lin: u => u, io2: gsap.parseEase('power2.inOut') };

/* ---------- sprites, elements ---------- */
const SHADOWS = [];
function sprite(parent, name, x, y, h, opts = {}) {
  if (!IMGS[name]) throw new Error('no sprite ' + name);
  const w = h * (opts.ar || IMGAR[name] || 1);
  if (opts.shadow !== false) {
    const s = document.createElement('div'); s.className = 'sh'; const sw = (opts.sw || .9) * w;
    s.style.cssText = `left:${x - sw / 2}px;top:${y - 12}px;width:${sw}px;height:${Math.max(16, h * .09)}px`; parent.appendChild(s);
  }
  const im = document.createElement('img'); im.className = 'sp'; im.alt = ''; im.src = IMGS[name];
  im.style.cssText = `height:${h}px;width:${w}px;left:${x - w / 2}px;top:${y - h}px;transform-origin:50% 100%`;
  if (opts.id) im.id = opts.id;
  parent.appendChild(im);
  if (opts.shadow !== false) SHADOWS.push([im.previousSibling, im]);
  return im;
}
function el(parent, html, css, cls) { const d = document.createElement('div'); d.className = cls || 'abs'; if (css) d.style.cssText = css; d.innerHTML = html; parent.appendChild(d); return d; }
function svgAbs(parent, inner, id) {
  const s = document.createElementNS(NS, 'svg'); s.setAttribute('width', 1920); s.setAttribute('height', 1080);
  s.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none'; s.innerHTML = inner; if (id) s.id = id; parent.appendChild(s); return s;
}
const MARK = { ok: '<path d="M5 16 l7 7 l13 -16" fill="none" stroke="#5E7F4E" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
  bad: '<path d="M7 7 L23 23 M23 7 L7 23" fill="none" stroke="#C4533B" stroke-width="6" stroke-linecap="round"/>' };
function mark(parent, kind, x, y, size) {
  return el(parent, `<svg width="${size}" height="${size}" viewBox="0 0 30 30"><g filter="url(#clay)">${MARK[kind]}</g></svg>`, `left:${x - size / 2}px;top:${y - size / 2}px;opacity:0`);
}

/* ---------- paths, belt, tokens ---------- */
const tmpSvg = document.createElementNS(NS, 'svg'); tmpSvg.setAttribute('width', 0); tmpSvg.setAttribute('height', 0); tmpSvg.style.position = 'absolute'; document.body.appendChild(tmpSvg);
function track(d) {   // a polyline sampled every ~2 px from an SVG path: at(len) -> [x, y, angle]
  const p = document.createElementNS(NS, 'path'); p.setAttribute('d', d); tmpSvg.appendChild(p);
  const L = p.getTotalLength(), n = Math.max(2, Math.ceil(L / 2)), X = new Float32Array(n + 1), Y = new Float32Array(n + 1);
  for (let i = 0; i <= n; i++) { const q = p.getPointAtLength(i * L / n); X[i] = q.x; Y[i] = q.y; }
  const at = len => { const f = Math.max(0, Math.min(n, len / L * n)), i = Math.min(n - 1, Math.floor(f)), u = f - i;
    return [X[i] + (X[i + 1] - X[i]) * u, Y[i] + (Y[i + 1] - Y[i]) * u, Math.atan2(Y[i + 1] - Y[i], X[i + 1] - X[i])]; };
  return { L, at, d };
}
function belt(parent, tracks, o) {
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', 1920); svg.setAttribute('height', 1080); svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
  const W = o.w, path = (d, st, sw, extra = '') => `<path d="${d}" fill="none" stroke="${st}" stroke-width="${sw}" stroke-linecap="round" ${extra}/>`;
  let g = '';
  tracks.forEach(t => { g += path(t.d, '#3b2a1a', W, `stroke-opacity=".22" filter="url(#soft)" transform="translate(0,${W * .3})"`) + path(t.d, o.side || o.rail, W, `transform="translate(0,${W * .17})"`); });
  g += '<g filter="url(#clay)">'; tracks.forEach(t => { g += path(t.d, o.rail, W) + path(t.d, o.bed, W * .74); }); g += '</g>';
  svg.innerHTML = g; parent.appendChild(svg);
  const box = document.createElement('div'); box.style.cssText = 'position:absolute;left:0;top:0'; parent.appendChild(box);
  const slats = [];
  if (o.img && IMGS[o.img]) tracks.forEach(t => { const n = Math.floor(t.L / (o.sp || 40)); for (let i = 0; i < n; i++) {
    const im = document.createElement('img'); im.src = IMGS[o.img]; im.alt = ''; im.className = 'sp';
    im.style.cssText = `width:${W * .78}px;height:${o.th || 12}px;left:${-W * .39}px;top:${-(o.th || 12) / 2}px`; box.appendChild(im); slats.push([im, t, i * t.L / n]); } });
  const rollers = [], rr = o.rr || 13;
  if (o.rollerImg && IMGS[o.rollerImg]) (o.rollers || []).forEach(([x0, x1, y]) => { for (let x = x0; x <= x1; x += 64) {
    const im = document.createElement('img'); im.src = IMGS[o.rollerImg]; im.alt = ''; im.className = 'sp';
    im.style.cssText = `width:${2 * rr}px;height:${2 * rr}px;left:${x - rr}px;top:${y - rr}px`; box.appendChild(im); rollers.push(im); } });
  return t => {       // call from UPD: slats ride their track at o.speed px/s, rollers turn with them
    const off = t * (o.speed || 46);
    for (const [im, tr, base] of slats) { const len = (base + off) % tr.L; const [x, y, a] = tr.at(len); im.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) rotate(${(a + Math.PI / 2).toFixed(3)}rad)`; }
    const rot = off / rr; for (const im of rollers) im.style.transform = `rotate(${rot.toFixed(3)}rad)`;
  };
}
function Tok(parent, kind = 'token', scale = 1, opts = {}) {   // the thing that travels: segments of motion + keyed state
  const d = document.createElement('div'); d.className = 'tok';
  const badImg = opts.bad && IMGS[opts.bad] ? `<img class="b" src="${IMGS[opts.bad]}" alt="" style="opacity:0">` : '<img class="b" alt="" style="opacity:0">';
  d.innerHTML = `<div class="tsh"></div><img class="g" src="${IMGS[kind]}" alt="">${badImg}<div class="dot"></div>`;
  parent.appendChild(d);
  const T = { el: d, segs: [], keys: [], s: scale };
  T.go = (t0, dur, f, ease = EASE.io) => { T.segs.push({ t0, dur, f, ease }); return T; };
  T.ride = (tr, l0, l1, t0, dur, ease) => T.go(t0, dur, u => tr.at(lerp(l0, l1, u)), ease);
  T.hop = (p0, p1, t0, dur, h = 120) => T.go(t0, dur, u => [lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - h * 4 * u * (1 - u)], EASE.lin);
  T.loop = (tr, t0, dur, laps) => T.go(t0, dur, u => tr.at((u * laps % 1) * tr.L), EASE.lin);
  T.key = (t, k) => { T.keys.push([t, k]); T.keys.sort((a, b) => a[0] - b[0]); return T; };   // k: {o opacity, s scale, bad 0..1, dot 0..1}
  T.posAt = t => {
    let pos = null, best = -1;
    for (const sg of T.segs) { if (t >= sg.t0 && sg.t0 >= best) { best = sg.t0; pos = sg.f(sg.ease(clamp01((t - sg.t0) / sg.dur))); } }
    if (!pos && T.segs.length) { const f = T.segs.reduce((a, b) => a.t0 <= b.t0 ? a : b); pos = f.f(0); }
    return pos;
  };
  T.update = t => {
    const pos = T.posAt(t);
    const hasO = T.keys.some(([, k]) => 'o' in k);
    const st = { o: hasO ? 0 : 1, s: T.s, bad: 0, dot: 0 };
    for (const [kt, k] of T.keys) if (t >= kt) Object.assign(st, k);
    if (!hasO && T.segs.length && t < Math.min(...T.segs.map(g => g.t0))) st.o = 0;
    T.pos = pos;
    if (!pos) return;
    d.style.transform = `translate(${pos[0].toFixed(1)}px,${pos[1].toFixed(1)}px) scale(${st.s})`;
    d.style.opacity = st.o; d.children[1].style.opacity = 1 - st.bad; d.children[2].style.opacity = st.bad; d.children[3].style.opacity = st.dot;
  };
  UPD.push(T.update); return T;
}

/* ---------- motion helpers (all place a tween on the master timeline at time `at`) ---------- */
const pop = (sel, at, extra = {}) => tl.fromTo(sel, { opacity: 0, scale: .6 }, Object.assign({ opacity: 1, scale: 1, duration: .45, ease: 'back.out(2)', immediateRender: false }, extra), at);
const fade = (sel, at, o = 1, dur = .4) => tl.to(sel, { opacity: o, duration: dur, ease: 'power2.out' }, at);
const swap = (a, b, at) => { fade(a, at - .05, 0, .25); fade(b, at + .15); };
const squash = (elx, at) => tl.to(elx, { scaleY: .92, scaleX: 1.05, duration: .09, ease: 'power2.out' }, at).to(elx, { scaleY: 1, scaleX: 1, duration: .5, ease: 'elastic.out(1,.45)' }, at + .09);
function tagAt(parent, cls, text, x, y) { return el(parent, text, `left:${x}px;top:${y}px;translate:-50% 0`, 'tag ' + cls); }
const tagPop = (t, at, off) => { tl.fromTo(t, { opacity: 0, scale: .4, y: 14 }, { opacity: 1, scale: 1, y: 0, duration: .32, ease: 'back.out(2.2)', immediateRender: false }, at); if (off) tl.to(t, { opacity: 0, duration: .25 }, off); };
const popIn = (e, at, dy = 30) => {
  tl.fromTo(e, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: .5, ease: 'back.out(1.6)', immediateRender: true }, at);
  if (e.previousSibling && e.previousSibling.className === 'sh') tl.fromTo(e.previousSibling, { opacity: 0 }, { opacity: .2, duration: .4, immediateRender: true }, at);
};
const hideAt = (e, at) => { tl.to(e, { opacity: 0, duration: .3 }, at); if (e.previousSibling && e.previousSibling.className === 'sh') tl.to(e.previousSibling, { opacity: 0, duration: .3 }, at); };
const show = (id, at) => popIn(typeof id === 'string' ? $(id) : id, at, 24);
const hide = (id, at) => hideAt(typeof id === 'string' ? $(id) : id, at);

/* ---------- scenes: every scene crossfades into the next, no blank frame between them ---------- */
const SCENE_EL = n => '#sc' + n;
if (!window.EF_NO_AUTOFADE) CUES.scenes.forEach((s, i) => {
  const nx = CUES.scenes[i + 1];
  tl.to(SCENE_EL(s.n), { autoAlpha: 1, duration: i ? .35 : .01 }, s.start - (i ? .15 : 0));
  if (nx) tl.to(SCENE_EL(s.n), { autoAlpha: 0, duration: .3 }, nx.start - .1);
});
const worldOn = (a, b) => tl.to('#world', { autoAlpha: 1, duration: .4 }, a - .15).to('#world', { autoAlpha: 0, duration: .3 }, b - .1);

/* ---------- camera: a queue of eased moves of #world ---------- */
const CAM = [];
const cam = (t, dur, z, x, y, follow = null) => CAM.push({ t, dur, z, x, y, follow });   // z zoom, (x, y) look-at point in world px; follow = a Tok
function camState(k, t) { const p = k.follow && k.follow.posAt(t); if (p) return { z: k.z, x: lerp(k.x, p[0], .75), y: lerp(k.y, p[1] - 60, .75) }; return { z: k.z, x: k.x, y: k.y }; }
UPD.push(t => {
  if (!CAM.length || !$('#world')) return;
  let i = -1; for (let j = 0; j < CAM.length; j++) if (t >= CAM[j].t) i = j;
  let s;
  if (i < 0) s = camState(CAM[0], t);
  else { const k = CAM[i], b = camState(k, t); if (i === 0) s = b; else { const a = camState(CAM[i - 1], t), u = EASE.io2(clamp01((t - k.t) / k.dur)); s = { z: lerp(a.z, b.z, u), x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u) }; } }
  const hw = 960 / s.z, hh = 540 / s.z;
  const x = Math.max(hw, Math.min(1920 - hw, s.x)), y = Math.max(hh - 200, Math.min(1080 - hh + 60, s.y));   // keep the frame inside the world
  $('#world').style.transform = `translate(${(960 - x * s.z).toFixed(1)}px,${(540 - y * s.z).toFixed(1)}px) scale(${s.z.toFixed(4)})`;
});

/* ---------- captions with safe areas, edge guard ---------- */
const CAPHI = [];
const capHigh = (a, b) => CAPHI.push([a, b]);      // lift the caption bar clear of low art between a and b
function guardEdges(sels, margin = 4) {            // a label cut off by the frame edge in a close-up is hidden, never shown half-clipped
  UPD.push(() => {
    if (window.__heroMode) { sels().forEach(e => e.style.visibility = 'visible'); return; }
    const sr = $('#stage').getBoundingClientRect(), k = sr.width / 1920;
    for (const e of sels()) {
      e.style.visibility = 'visible'; const r = e.getBoundingClientRect(); if (!r.width) continue;
      const out = (r.left - sr.left) / k < margin || (r.right - sr.left) / k > 1920 - margin || (r.top - sr.top) / k < margin || (r.bottom - sr.top) / k > 1080 - margin;
      if (out) e.style.visibility = 'hidden';
    }
  });
}
const capEl = () => $('#capT');
let lastCap = null, lastHi = null;
const stepVal = (arr, t) => { let v = arr[0]; for (const a of arr) if (t >= a[0]) v = a; return v; };   // for stepped text: [[t0, value], ...]

/* ---------- render: everything is a function of audio time ---------- */
const POST = [];                                      // per-frame hooks for scene scripts: EF.post(t => ...)
function render(t) {
  tl.time(Math.min(t, DUR));
  for (const f of UPD) f(t);
  for (const f of POST) f(t);
  for (const [sh, im] of SHADOWS) { const o = (+im.style.opacity || (im.style.opacity === '' ? 1 : 0)); sh.style.opacity = (.2 * o).toFixed(3); }
  let c = ''; for (const k of CUES.captions) { if (t >= k.start - .05 && t < k.end + .2) c = k.text; }
  if (c !== lastCap) { capEl().textContent = c; lastCap = c; }
  const hi = CAPHI.some(([a, b]) => t >= a && t < b); if (hi !== lastHi) { $('#cap').classList.toggle('hi', hi); lastHi = hi; }
}

/* ---------- player ---------- */
const EF = {
  post: f => POST.push(f),
  start() {
    $$('#stage [style]').forEach(e => { if (e.style.translate && e.style.translate.startsWith('-50%')) { e.style.translate = ''; gsap.set(e, { xPercent: -50 }); } });   // tags centred on x
    tl.set({}, {}, DUR);                              // pin the timeline length to the narration
    const qs = new URLSearchParams(location.search);
    const renderMode = qs.has('render');
    if (renderMode) { document.body.classList.add('render'); window.__frozen = true; }
    window.__seek = t => { render(t); return true; };
    window.__dur = window.__total = DUR; window.__cues = CUES;
    window.__hero = (t) => {                          // a still for a post card: park at HERO_TIME, hide player and captions
      window.__frozen = true; window.__heroMode = true; document.body.classList.add('render');
      $('#cap').style.display = 'none'; render(t != null ? t : (window.HERO_TIME != null ? window.HERO_TIME : DUR * .9));
      if (window.HERO_SETUP) window.HERO_SETUP();
      return true;
    };
    const au = $('#au'), pos = $('#pos'), pp = $('#pp');
    pos.max = DUR;
    CUES.scenes.forEach(s => { const i = document.createElement('i'); i.style.left = (s.start / DUR * 100) + '%'; i.title = s.title; $('#ticks').appendChild(i); });
    const fmt = x => Math.floor(x / 60) + ':' + String(Math.floor(x % 60)).padStart(2, '0');
    const RATES = [1, 1.25, 1.5, 0.75];
    const store = { get: k => { try { return localStorage.getItem(EF_KEY + k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(EF_KEY + k, v); } catch (e) {} } };
    let rate = +store.get('rate') || 1;
    const setRate = r => { rate = r; au.playbackRate = r; au.preservesPitch = true; $('#spd').innerHTML = r + '&times;'; store.set('rate', r); };
    setRate(RATES.includes(rate) ? rate : 1);
    let cap = store.get('cc') !== '0';
    const setCap = v => { cap = v; document.body.classList.toggle('nocap', !v); $('#cc').style.opacity = v ? 1 : .5; store.set('cc', v ? '1' : '0'); };
    setCap(cap);
    const play = () => { $('#big').style.display = 'none'; au.play(); };
    const toggle = () => au.paused ? play() : au.pause();
    $('#big').onclick = play; $('#big').onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); play(); } };
    pp.onclick = toggle;
    $('#spd').onclick = () => setRate(RATES[(RATES.indexOf(rate) + 1) % RATES.length]);
    $('#cc').onclick = () => setCap(!cap);
    pos.oninput = () => { au.currentTime = +pos.value; $('#big').style.display = 'none'; };
    au.onplay = () => pp.textContent = 'Pause'; au.onpause = () => pp.textContent = 'Play'; au.onended = () => { pp.textContent = 'Replay'; };
    document.addEventListener('keydown', e => {
      if (e.target.tagName === 'INPUT' && e.key !== ' ') return;
      if (e.key === ' ') { e.preventDefault(); toggle(); }
      else if (e.key === 'ArrowRight') au.currentTime = Math.min(DUR, au.currentTime + 5);
      else if (e.key === 'ArrowLeft') au.currentTime = Math.max(0, au.currentTime - 5);
      else if (e.key === 'c' || e.key === 'C') setCap(!cap);
    });
    function fit() {
      if (document.body.classList.contains('render')) return;
      const w = innerWidth, h = innerHeight - 64, k = Math.min(w / 1920, h / 1080);
      $('#stage').style.transform = `translate(${(w - 1920 * k) / 2}px, ${(h - 1080 * k) / 2}px) scale(${k})`;
    }
    addEventListener('resize', fit); fit();
    const hashT = parseFloat((location.hash.match(/t=([\d.]+)/) || [])[1]);
    if (!isNaN(hashT)) { au.currentTime = hashT; render(hashT); $('#big').style.display = 'none'; } else render(0);
    (function loop() {
      if (!window.__frozen) {
        const t = au.currentTime; render(t);
        if (document.activeElement !== pos) pos.value = t;
        $('#time').textContent = fmt(t) + ' / ' + fmt(DUR);
      }
      requestAnimationFrame(loop);
    })();
    window.__ready = (async () => {
      await new Promise(r => (document.readyState === 'complete' ? r() : addEventListener('load', r, { once: true })));
      await document.fonts.ready;
      await Promise.all($$('img').map(i => i.decode().catch(() => {})));
      return true;
    })();
  },
};
