# Finishing — the parts that decide whether it looks expensive

The film is only half the work. The finishing issues in this file can undermine strong
footage, so read it before writing the page.

---

## 1. Trim the head of the film. Almost always.

Generated films very often open on a shot that does not belong to the move — a static
macro, a different framing, a beat that has not started travelling yet. It reads as a
jump-cut into the real film, and it is the first thing anyone sees.

**Look at the opening second frame by frame before you wire anything up**, and cut until
the first frame is already *inside* the movement:

```bash
# eyeball the first 2s (24fps -> f_0001..f_0048)
ffmpeg -v error -i film.mp4 -vf "select='lt(n,49)',scale=300:-1" -vsync 0 /tmp/head_%03d.jpg
# then re-extract from the frame that actually flows
ffmpeg -y -v error -ss 2.0 -i film.mp4 -vf scale=1024:-2 -q:v 6 frames/f_%04d.jpg
```

Then **update `FRAME_COUNT` to the new count** — it is the single most common way a
trimmed film breaks (the engine asks for frames that no longer exist and the canvas
blanks at the end of the scroll).

Trim any static opening or mismatched establishing frame until the first visible moment
already belongs to the continuous move.

---

## 2. Chrome over footage

A header floating over a film has to stay legible over **every** frame, and a film goes
from blinding highlights to near-black within one scroll. Cream-on-bright-comb disappears.

The fix is three cheap things together:

```css
.brand-word, nav a{ color:#fff; text-shadow:0 1px 22px rgba(0,0,0,.55); }
.brand-mark{ filter:drop-shadow(0 1px 10px rgba(0,0,0,.5)); }
.site-header::before{        /* soft scrim so chrome never sits on raw footage */
  content:""; position:absolute; inset:0 0 auto 0; height:180%; z-index:-1;
  background:linear-gradient(to bottom, rgba(8,4,2,.62), rgba(8,4,2,0));
}
```

**White, not cream** — cream reads as dirty over bright footage. Same treatment for beat
text: a soft radial scrim under each beat holds the type through the dark middle of a
film without flattening the image.

```css
.beat::before{
  content:""; position:absolute; z-index:-1; inset:-70% -24% -70% -14%;
  background:radial-gradient(60% 58% at 22% 50%, rgba(6,3,1,.72), rgba(6,3,1,.42) 45%, transparent 78%);
}
```

Check both extremes with a screenshot — the brightest frame and the darkest.

---

## 3. The page below the film is where builds go flat

The film can feel cinematic and then collapse into a stack of short, evenly-spaced text
blocks. The sections below must preserve the same confidence and visual rhythm.

Minimums for every section under the film:

- **Vertical presence.** `min-height: min(92vh, 900px)` and vertically centred content.
  Short sections read as filler no matter how good the copy is.
- **Scale contrast.** A section needs one element far larger than the rest. If every
  heading is the same size as every other heading, the page has no rhythm.
- **Arrival motion.** Rise-and-fade on intersection, staggered across children by ~90ms.
  Always behind `prefers-reduced-motion`.

```css
.section .wrap > *{ opacity:0; transform:translateY(26px);
  transition:opacity .9s var(--ease-out), transform .9s var(--ease-out); }
.section.in .wrap > *{ opacity:1; transform:none; }
.section.in .wrap > *:nth-child(2){ transition-delay:.09s; }
```
```js
const io = new IntersectionObserver((es)=>es.forEach(e=>{
  if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); }
}), { rootMargin:'0px 0px -12% 0px', threshold:.12 });
document.querySelectorAll('.section').forEach(s=>io.observe(s));
```

- **The primary CTA must be the most confident element on the page.** Not a text link.
  Give it a real treatment: resting glow, a light sweep on hover, a lift on press, and
  pull the price into the display face behind a divider so it has its own weight.

---

## 4. Real brand logos — fetch, never draw

When the brand exists, use **their** asset. Agents lose 20–30 minutes trying to hand-draw
a mark as inline SVG and the result never looks right. Budget **one** attempt, then move
on to live text set in the brand's typeface.

```bash
curl -sL -A "Mozilla/5.0" https://brand.com/ -o /tmp/b.html
grep -oiE 'https?://[^"'"'"' ]*\.(svg|png|webp)' /tmp/b.html | grep -iE 'logo|brand' | head
```

Brands usually publish a single-colour mark. If it is black and the site is dark, recolour
it rather than hunting for a white version — keep the alpha, replace the RGB:

```python
from PIL import Image
im = Image.open('logo.png').convert('RGBA'); px = im.load()
for y in range(im.size[1]):
    for x in range(im.size[0]):
        r,g,b,a = px[x,y]
        if a: px[x,y] = (255,255,255,a)
im.save('logo-white.png')
```

---

## 5. Mobile is a different film, not a narrower one

A 16:9 film letterboxed or centre-cropped on a phone throws away the subject. Generate a
**real 9:16 pass** (same journey, same grade, `aspect_ratio: "9:16"`), keep both frame sets
at the same length so the playhead maps 1:1, and swap on the breakpoint:

```js
const mq = window.matchMedia('(max-width: 768px)');
let FRAME_DIR = mq.matches ? DIR_MOBILE : DIR_DESKTOP;
mq.addEventListener('change', () => {
  FRAME_DIR = mq.matches ? DIR_MOBILE : DIR_DESKTOP;
  frames.forEach(b => b && b.close && b.close());   // decoded bitmaps belong to the old set
  frames.clear(); pending.clear();
  warmAround(current);                              // refill so the canvas never blanks
});
```

Closing the old `ImageBitmap`s matters — skipping it leaks GPU memory on every rotation.

---

## 6. Verifying without fooling yourself

- **A screenshot of a hidden or zero-size viewport is black.** Before believing a black
  capture, read `canvas.width`/`innerWidth`; if they are 0 the pane is hidden, not broken.
- **Sample the canvas, don't trust the image.** `getImageData` at the centre for three
  scroll positions: three different colours means the film is genuinely scrubbing.
- A headless run is the deterministic check — fixed viewport, no pane involved. It ships
  with this skill at `scripts/shot.js`. **One-time setup on a new machine:**

```bash
cd ~/.claude/skills/scroll-film-studio/scripts && npm install   # once, pulls puppeteer-core
```

```bash
node ~/.claude/skills/scroll-film-studio/scripts/shot.js \
     http://localhost:PORT out.png 1440 900 0.35   # url, out, w, h, scrollFraction
```

  It needs Chrome or Chromium installed (set `CHROME_PATH` if it lives somewhere unusual),
  and it prints what it actually captured — `innerWidth`, `scrollY`, the canvas backing size
  and whether the page overflows horizontally. **`canvas: none` or `innerWidth: 0` means the
  page never mounted, not that the film is black.**

- Check **both** breakpoints (e.g. 1440×900 and 390×844) every time the film or layout
  changes. Mobile is a deliverable, not a fallback.
