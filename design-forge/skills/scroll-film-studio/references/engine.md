# Engine recipes — how to build the page (both lanes)

Not a template. These are the load-bearing mechanics you write *into* each bespoke
build. Everything else — markup, styling, motion shape, copy — you design fresh per
brand.

---

## Scrub engine (Lane B) — canvas + frames, never `<video>`

`<video currentTime>` scrubbing stutters (seek latency). The only jank-free path:
pre-extracted JPEG frames drawn to a full-viewport `<canvas>`, driven by scroll.

**Structure:** a tall scroll driver (`~170vh per chapter`, e.g. `850vh` for 5) containing
a `position:sticky; top:0; height:100vh` stage with the canvas + overlays. Film progress:

```js
const r = filmScroll.getBoundingClientRect();
const p = Math.max(0, Math.min(1, -r.top / (r.height - innerHeight)));
```

**Lerped playhead** (this is the butter — direct mapping feels mechanical):

```js
currentFrame += (target - currentFrame) * 0.14;   // target = p * (FRAME_COUNT - 1)
```

**The anti-jank core — ImageBitmap sliding window.** `drawImage(HTMLImageElement)`
forces a *synchronous* JPEG decode on the main thread at first paint and again after
browser cache eviction — those decode spikes are the "frame-by-frame glitchy" feel.
Decode off-thread around the playhead so every draw is a pure GPU blit:

```js
const bitmaps = new Map(), decoding = new Set();
const B_AHEAD = 18, B_KEEP = 28; let bmpCenter = -999;
function ensureBitmaps(center){
  if (Math.abs(center - bmpCenter) < 3) return;
  bmpCenter = center;
  const lo = Math.max(0, center - B_AHEAD), hi = Math.min(FRAME_COUNT - 1, center + B_AHEAD);
  for (let i = lo; i <= hi; i++){
    if (bitmaps.has(i) || decoding.has(i) || !images[i]) continue;
    decoding.add(i);
    createImageBitmap(images[i]).then(b => {
      decoding.delete(i);
      if (Math.abs(i - bmpCenter) > B_KEEP){ b.close(); return; }
      bitmaps.set(i, b);
      if (i === displayed) drawFrame(i, true);      // repaint if the shown frame upgraded
    }).catch(() => decoding.delete(i));
  }
  for (const k of Array.from(bitmaps.keys()))
    if (k < center - B_KEEP || k > center + B_KEEP){ bitmaps.get(k).close(); bitmaps.delete(k); }
}
// draw: prefer bitmaps.get(idx), fall back to nearest loaded HTMLImageElement
```

Call `ensureBitmaps(Math.round(currentFrame))` every tick, **pre-warm around frame 0 at
boot**, and cap `devicePixelRatio` at **1.5** (2.0 doubles blit cost for invisible gain).

**Frame loading:** concurrency-capped pump (~10 in flight) into an array, a loader with a
real progress bar, and a `nearestFrame()` fallback (scan outward from the requested index)
so a missing frame never blanks the canvas.

**Frame payload — extract at the film's NATIVE frame rate, not a round number.**

```bash
ffmpeg -v error -y -i master.mp4 -vf "fps=24,scale=1024:-1" -q:v 6 frames/f_%04d.jpg
```

A 72-second film at 24fps is **1,728 frames**. Extracting "about 300" of it throws away 83%
of the footage and leaves the visitor scrubbing a **4-frames-per-second slideshow**. That is
visibly low-quality motion, and it is invisible in code review because the engine simply has
nothing to draw.

Illustrative adjacent-frame behavior:

| frames | fps | adjacent SSIM |
|---|---|---|
| 300 | 4.2 | **0.39 – 0.45** |
| 865 | 12 | 0.47 – 0.49 |
| **1,728** | **24** | **0.63 — the ceiling** |

Note the ceiling. Even at native rate this footage only reaches 0.63, because the camera
covers ground fast over high-frequency detail (grass, foliage, bubbles). That is fine as
*video*, where motion blur and the eye tie frames together. There is no frame count that
rescues a film whose camera moves too fast — see the storyboard rule in SKILL.md Lane B.
Frame rate fixes sampling; it does not fix distance.

Trade resolution for frames, never the other way round: **1024px at `-q:v 6` beats 1280px at
`-q:v 4`** for the same bytes, because temporal smoothness is far more visible than per-frame
sharpness on a moving image. ~1,700 frames at 1024px lands around 85–105MB.

**Scale the window with the frame rate.** A window of 18 ahead / 28 behind is ~2 seconds of
film at 300 frames but **0.75 s** at 1,728 — and a fast flick outruns it instantly. Size the
window in SECONDS of film, not frames: ~2s ahead (48 frames at 24fps), ~1.3s behind. Holding
~80 ImageBitmaps at 1024×576 is roughly 190MB, which is why this is a sliding window and not
a preload — never queue all frames up front at native rate.

**Frame loading:** concurrency-capped pump (~10–12 in flight) into an array, a loader with a
real progress bar, and a `nearestFrame()` fallback (scan outward from the requested index) so
a missing frame never blanks the canvas. Never block first paint on the whole film: prefetch a
short opening run, then stream.

**Fit, don't blindly cover.** `Math.max(cw/w, ch/h)` is right on a landscape desktop and
catastrophic on a phone: a 16:9 film in a 390×844 portrait viewport keeps only the centre
**26%** of every frame — 74% of the composition, including whatever the shot was built
around, is thrown off both sides. It also magnifies the frame ~1.5×, so every bit of camera
movement is amplified and a perfectly good scrub reads as jerky when it is merely enlarged.

Cover while the crop stays modest, letterbox once it does not. Threshold on the crop
fraction, not a breakpoint — a very wide desktop window and a tall phone are the same
problem at opposite signs:

```js
var MAX_CROP = 0.22;
function fit(bm){
  var cw=canvas.width, ch=canvas.height;
  var sCover = Math.max(cw/bm.width, ch/bm.height);
  var crop = 1 - Math.min(cw/(bm.width*sCover), ch/(bm.height*sCover));
  var s = crop > MAX_CROP ? Math.min(cw/bm.width, ch/bm.height) : sCover;
  var w = bm.width*s, h = bm.height*s;
  ctx.drawImage(bm, (cw-w)/2, (ch-h)/2, w, h);
}
```

**Cap DPR at 1.0 and match the source width instead.** A 1024px frame drawn into a
2268px-wide canvas (1512 CSS px × 1.5 DPR) is a 2.2× upscale, and it reads as *pixelated* —
which is exactly the wrong conclusion to draw, because the instinct is then to raise DPR and
make it worse. Sharpness on a scrub comes from the source matching the canvas 1:1, not from
more device pixels: extract at ~1440px and cap DPR at 1.0.

## Beat overlays (copy over the film)

> **The world brief is production notes, not source copy.**
>
> This is a reliable way to ruin a finished build. `WORLD.md` describes the film in vivid prose *because it is written for
> whoever generates the footage*. A model with no other source of imagery in the room
> can paraphrase that prose straight onto the page as beat copy and ship a shot list
> instead of brand copy.
>
> **The test:** someone who cannot see the film at all must still read every line as
> advertising for the product. If a line only makes sense next to the picture, it is
> a caption, and captions are what the picture is for.
>
> Never name the camera's position, direction, or what it is passing. No *descent*,
> *pull back*, *looking up*, *one continuous take*, no listing what is in frame. The
> beats carry what the picture cannot: the claim, the refusal, the joke.
> `scripts/copy-gate.js` fails all of these — run it, never edit it to pass.

Absolute-positioned overlays with progress envelopes, driven from the same tick:

```html
<div class="beat" data-in="0.16" data-peak="0.235" data-out="0.31"><h2>…</h2></div>
```
```js
function beatAlpha(b, p){
  if (p < b.in || p > b.out) return 0;
  if (p < b.peak) return (p - b.in) / Math.max(1e-4, b.peak - b.in);
  if (b.out > 1.5) return 1;                    // finale: data-out="2" never fades
  return 1 - (p - b.peak) / Math.max(1e-4, b.out - b.peak);
}
// alpha → style.opacity, plus a small translateY against scroll direction
```

Hero beat must be visible at scroll 0: `data-in="-0.1" data-peak="0"`. If the finale
frame is a centred product/subject, anchor the finale panel to the left so the subject
stays hero.

## Adaptive header (fixed chrome over a changing film)

Sample the drawn frame's top strip every ~180ms into a 16×4 offscreen canvas, average
luminance, toggle an `.on-light` class (threshold ≈ 138). All header colours run through
`currentColor` so one class flips everything. A **chapter readout** (label + thin progress
bar) doubles as narrative and progress UI — or theme it (e.g. a live altimeter counting
down as the film descends).

## Seam handoff (film → content, no visible line)

The assembly script samples the film's final-frame bottom-strip colour. Start the next
section's background **at exactly that hex**, and add a bottom-fade overlay on the film
stage that ramps in over the last ~8% of progress (`(p - 0.92) / 0.08`). Fade the grain +
vignette out with the same ramp. If the film ends dark and the content is light, build a
tall gradient "landing zone" that melts dark → brand-light over the first content block.

## Ambient hero layer (optional, free, sells the opening)

Themed canvas particles (snow glisten, gold pollen, embers) over the static first frame,
fading out across the first ~7% of scroll: one 32px offscreen radial-gradient sprite,
`drawImage` per particle with per-particle depth (size/speed/alpha), sin-based twinkle or
glow pulse. Never `shadowBlur` (expensive). Stop rendering entirely once alpha hits 0.
Skip under `prefers-reduced-motion`.

## The dev contract (verification hooks — implement in every build)

```js
const JUMP = new URLSearchParams(location.search).get('jump');
if (JUMP !== null) history.scrollRestoration = 'manual';   // and skip smooth-scroll init
// after everything is loaded and settled:
if (JUMP !== null){ scrollTo(0, +JUMP || 0); /* recompute progress, draw, tick once */ }
window.__ready = true;
```

`?jump=<y>` must land pre-scrolled with all scroll-driven state force-settled (for
pure-code builds: `ScrollTrigger.update()` then set each scrubbed animation's
`totalProgress` explicitly). `__ready` gates the screenshot harness. Hide any
cursor-follower until the first real `mousemove` or it photobombs captures at (0,0).

Jank meter for the console: track per-frame rAF deltas, log `max` every 2s. Judge p95/max,
never average fps — a 60fps average hides 80ms decode spikes perfectly.

---

## Pure-code film (Lane A) — the motion vocabulary

The "film" is a sequence of scroll-driven scenes. Wire Lenis into GSAP's ticker:

```js
const lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add(t => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0);
```

Vocabulary to compose from (pick what tells *this* brand's journey):
- **Char-split hero reveal** — split the wordmark into spans, stagger `yPercent:120 → 0`
  with `power4.out`.
- **Pinned scrubbed scenes** — `pin: true, scrub: true, end: '+=140%'` timelines
  (a growing/rotating form, a blend "vortex", a mask opening to full-bleed).
- **Horizontal pinned run** — translate a `width:max-content` track by
  `-(scrollWidth - innerWidth)`; give child elements their own parallax via
  `containerAnimation`. Use `invalidateOnRefresh: true`.
- **Clip-path reveals** — `inset(0 0 100% 0) → inset(0)` on scroll for editorial rows.
- **Velocity-skew** — skew a ticker/marquee by `ScrollTrigger.getVelocity()` clamped.
- **Counters** — `once: true` triggers with `snap: { textContent: 1 }`.
- **Marquee drift** — `xPercent: -50, repeat: -1` on a doubled row.

**Ordering law (silent killer):** ScrollTriggers are refreshed in *creation order*.
Create all pinned scenes **first**, ambient/background triggers **after** — otherwise
positions computed before pin spacers exist are silently wrong (effects fire thousands
of pixels early).

Performance: GPU-only properties (transform/opacity), `will-change` on the few moving
nodes, no layout-thrashing reads in tickers. Same dev contract + jank meter as Lane B.
