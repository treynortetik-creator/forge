---
name: typography
description: >
  Type and handwriting for a browser game: drawing an original script font, the
  "pen writes this" effect (font to skeleton strokes to writing order to a JSON hand the
  game animates, no font loaded at runtime), stroke-order preview sheets, the ink-coverage
  and HarfBuzz-drift gates, rejected hands and why, display/UI webfonts that never block
  boot, first-play byte budgets, title logos and paper title cards, and lettering rendered
  by image models. Use when a game needs handwriting, a self-writing text effect, an own
  font, a logo, or any text-heavy UI. Triggers: "pen writer", "handwriting effect",
  "make our own font", "script font", "stroke order", "font load", "title logo",
  "lettering", "text in generated images", "font blocks boot".
---

# Typography for a game

**The one-line case:** a roguelite needed text that writes itself with a pen, in a period hand
that reads at 32 px. Stock fonts looked "a bit generic", so we traced an original script font from
public-domain engravings in about 1h15m for $0 (v1), cleaned it up in a second pass (v2), and
turned every font into a JSON of pen strokes the game animates. The game never loads a font file
for the effect. Every rule below is a failure with its receipt.

> **Division of labour that held:** the model draws, spaces and judges whether it looks like a
> pen. The harness measures anything that is a number: ink coverage, layout drift against
> HarfBuzz, join counts, file size. Do not eyeball those.

Siblings: `game-forge:art-waves` (generated art, including lettering inside images),
`game-forge:game-qa-loop` (screenshots and gates), `design-forge:art-department` (HTML/deck
type, licence gate). This skill does not duplicate them.

Contents
1. Pick the route (stock font, own font, image-model lettering)
2. Build a hand: `scripts/build_hand.py`
3. Gates
4. Draw an own font (summary; depth in `references/own-script-font.md`)
5. The runtime effect (summary; depth in `references/pen-writer-runtime.md`)
6. Display/UI fonts and the boot budget
7. Logos, title cards, text rendered by image models
8. Traps
9. Licences and cost

---

## 1. Pick the route

| Need | Route | Why |
|---|---|---|
| UI body and headings | Self-hosted webfont (OFL), section 6 | no render-blocking third party |
| Text that writes itself | Any font with real stroke contrast, through `build_hand.py` | the effect needs centrelines and nib widths, which a font file does not store |
| A hand nobody else has | Trace public-domain engraving or copybook plates, rebuild joins and spacing yourself | see section 4 |
| A logo or a poster headline | Image model with the exact words in the prompt, then READ the output | section 7 |
| Print-style chapter cards | Printed type, not the pen | the owner kept cards as type and used the pen for handwriting (decision 2026-10-21) |

Prompt-to-font AI was researched on 2026-10-21 and not adopted: no tool showed a joined,
thick-and-thin pen script, and the licences were mixed (one research-only, one with the font
staying on sale to other buyers). Treat that survey as dated; re-check before relying on it.

## 2. Build a hand

`scripts/build_hand.py` (our code, generalised: no game paths, CLI args only). It turns one font
file into one JSON. Setup and a real run:

```bash
cd <skill>/scripts
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python build_hand.py --font MyScript-Regular.ttf --id myscript --name "My Script" \
  --licence OFL.txt --out-dir public/assets/fonts/pen --preview out/preview
```

Pinned deps (`requirements.txt`): fonttools, freetype-py, numpy, pillow, scikit-image, scipy,
uharfbuzz. If Pillow 13 fails to import (`_IntegralLike`, seen on some Python 3.12 to 3.14
setups, see `game-forge:local-models`), pin `pillow<13`. Smoke receipt for this copy: Pinyon Script (OFL) built to 121 glyphs, 282 strokes,
1,784 pairs, coverage min 99.96% (emdash) and mean 100.00%, drift 0.0000 em, 209 KB raw / 81 KB
gzip, about 19 s wall clock, exit 0. A forced `--min-coverage 1.0` run printed `GATE FAILED` and
exited non-zero.

What it does, per glyph:

1. FreeType renders the glyph unhinted at a size that gives every font the same x height (140 px).
2. Zhang thinning gives a 1 px skeleton, a Euclidean distance transform gives the half width.
3. The skeleton becomes a graph. Short spurs are pruned, nearby junctions merged.
4. **Writing order**: components left to right along the ~35 degree slant; small marks above a
   lowercase letter (i and j dots, a separate t cross, accents) are deferred to the END of the
   word, as a real pen does; each component starts at its leftmost end point (the cursive entry
   stroke); at a junction the pen leaves by the STRAIGHTEST arm; a closed loop starts at its top
   and runs counter-clockwise.
5. Each stroke is smoothed, simplified (RDP), then every kept point gets `r` (the Voronoi coverage
   radius: the dab size that covers all ink nearest that point) and `w` (the nib half width).
6. HarfBuzz shapes every pair of the charset, so kerning and contextual alternates become a pair
   table and the runtime can lay out glyph by glyph and keep every cursive join.

Output schema and how the runtime uses it: `references/pen-writer-runtime.md`.

## 3. Gates

Both gates are exit codes in `build_hand.py`; wire them into CI.

| Gate | Threshold | Receipt |
|---|---|---|
| Ink coverage of the reveal dabs, worst glyph | >= 99.5% (`--min-coverage`), ~100% in practice | own font v2: min 100.00% over 146 glyphs (display cut), 99.98% (k) for the text cut; the ten writer hands 99.93 to 100% |
| Layout drift vs full HarfBuzz shaping | <= 0.01 em (`--max-drift`), 0 glyph mismatches | own font v2: 0.0000 em both cuts. Without kerning for the high-entry join forms the drift was 0.065 em |
| Join check | every lowercase pair joins (676/676) | project script, not shipped; descender loops touching (gj, yf) are the known, accepted class |
| Overlap check | zero touching pairs in capital/figure combinations | 0 of 1,712 pairs; project script, not shipped |
| JSON size | raw < 500 KB and gzip < 200 KB (own cuts); OFL hands < 260 KB raw | enforced by the game's unit tests |

**Stroke-order preview sheet** (`--preview <dir>`): one PNG per hand, a cell per glyph, green dot and
number where each stroke starts, blue to red along time, a green line for strokes deferred to the
word end, glyph name and coverage printed in the cell (red under 99.5%). Look at it before
believing the numbers: coverage can be 100% while the pen writes a letter in an order no human
would (starts at the exit, crosses a loop clockwise).

## 4. Draw an own font (summary)

Full method, numbers and the v1 to v2 diff: `references/own-script-font.md`.

- **Source shapes**: public-domain engraved alphabets (a roundhand copybook, scans from a national
  library). Letter shapes are old public-domain art; joins, spacing, kerning, accents and the font
  file are original work. No AI-generated letters.
- **Pipeline**: deslant each alphabet row, cut joined letters at the connecting hairlines, redraw
  joins at two fixed heights, trace at 4x, clean outlines, space and kern, build OTF/TTF with
  fontTools (OpenType features for the high-entry forms after letters with top exits).
- **v1 to v2** fixed three measured defects: uneven in-word gaps ("wh at", "writt en"), baseline
  wobble inherited from tilted plate rows, and drifting capitals. All three were *spacing and
  levelling*, not missing joins (676/676 pairs were already joined in v1).
- **Two cuts**: a Display cut for 44 px and up, a heavier Text cut for 24 to 36 px. Hairlines that
  look right at 96 px vanish at 32 px, so one font cannot serve both. Text cut x height 340 units
  vs 300 for Display; measured n-height 0.362 em vs Pinyon's 0.333.
- **Size scale** so any hand reads at the size you ask for: the Display cut needed its font size
  x 1.07 at body sizes (v1 needed ~1.25), the Text cut x 1.0.

## 5. The runtime effect (summary)

Full detail: `references/pen-writer-runtime.md`.

- The hand JSON is fetched on demand (lazy import of the effect, so none of it is in first play).
- Glyph outlines (SVG path in the JSON) are drawn once into a canvas. A mask uncovers that canvas
  one round dab at a time along each stroke in writing order, so letters fill in stroke by stroke.
  The font is never loaded at runtime.
- Timeline: pen speed by glyph length (`ms = letterTime * (len/mean)^0.55`, clamped 0.35 to 1.9),
  shades slower than hairlines, a lift between strokes, longer pauses at punctuation, i dots and t
  crosses at word end, an ink dip every 9 to 15 letters. Pass `duration` to fit a voice clip.
- **Deterministic**: a seeded hash of text + seed, never `Math.random`, so a line looks the same
  every time. Real clock (cosmetic), never simulation ticks.
- **Reduce motion**: the block fades in, nothing is drawn stroke by stroke. Any input can skip.
- Speed: a pen reads as a pen at about 10 to 14 letters a second. At 20 it looks like a wipe
  (reviewer note on the first clips, 2026-10-21). The game's default is 14, the boss-line effect 12.
- Ink and paper realism comes from measured crops of real letters, not taste (see the reference).

## 6. Display/UI fonts and the boot budget

The game's UI type is a self-hosted humanist sans (body) and its small-caps sibling at weight 900
(display). What mattered was not the choice but how it loads:

1. **Self-host, never a third-party stylesheet.** The Google Fonts `<link>` was a render-blocking
   stylesheet and two extra origins. Self-hosted, six woff2 files (latin + latin-ext, 400/700/900)
   for the display face came to about 95 kB. Whole-sheet receipt: the title phase (manifests, key
   art, UI plates, glyphs, font) was 1.8 MB.
2. **`@font-face` with `font-display: swap` and `unicode-range`** so latin-ext files download only
   if a glyph needs them. Preload (`<link rel="preload" as="font" type="font/woff2" crossorigin>`)
   the latin file of each weight actually used at first paint (three here).
3. **Cap the wait at 1.5 s.** Boot code races the font loads against a timer so a slow or offline
   font never blocks boot:

```ts
const fonts = (async () => {
  try {
    const weights = ['400', '700', '900'].flatMap((w) => [
      document.fonts.load(`${w} 24px "Display SC"`), document.fonts.load(`${w} 24px "Body"`)]);
    await Promise.race([Promise.all(weights), new Promise((r) => setTimeout(r, 1500))]);
  } catch { /* offline: fall back to the system serif */ }
})();
[manifest] = await Promise.all([fetchManifest(), fonts]);   // the font loads alongside, not before
```

4. **Name a fallback stack** (the game's comment says it falls back to a system serif when offline). Choosing a metrically close one to avoid reflow is advice, untested here.
5. **Cache headers**: fonts and art `max-age=900`, JSON and index.html `no-cache`. Before this,
   a return visit made 300+ conditional requests.
6. **Byte budget decides what is lazy.** The game held a first-play download budget (20 MB cap; it
   sat at 18.79 of 18.8 MB at one point, and at 15.0 MB after a packing pass) and a JS budget of
   900 KB gzip (896 used at one point). The pen effect and its 80 to 210 KB gzip hand JSONs are
   therefore on demand. Put a budget tool in CI, per phase (title, hub, biome).
7. **Do not re-set text style every frame.** Calling `setColor`/`setFontSize` on canvas text each
   frame re-renders and re-uploads the texture: about 80 uploads a second until it was changed to
   update only on change.
8. **Titles**: one weight for every screen and room title; a gilt gradient fill with an ink stroke
   and soft shadow so the type matches the logo's metal. Floating combat numbers: display face at
   900 with a 2 px dark outline.

## 7. Logos, title cards, text rendered by image models

- **Image models render lettering well now.** Put the exact words in the prompt and say "spelled
  exactly as written". Do not default to a blank plate plus pasted HTML type, which looks stuck on
  rather than lit by the scene. Treat as dated: the claim held for the GPT-image class in 2026-08.
- **Forbid invented text.** First attempt on a cover test: the model added a fabricated author
  byline. Always add "do not invent, add, or substitute any other name, byline or lettering".
- **Always look at the output.** Baked-in text cannot be edited, so a wrong word means a
  regenerate. Reading your own generation is mandatory here, not optional.
- **One image carries lettering.** The art brief told the art model "no text, no logos" for
  everything except the logo, "spell it exactly". Three logo candidates were generated in one
  wave and checked for spelling before they went to the owner; the owner picked one.
- **A rename makes baked text stale.** After the game was renamed, the logo art still said the old
  title and had to be regenerated. Keep the title text out of any image that is not the logo.
- **Human finish for the storefront.** Gamer sentiment on AI art is negative (surveys cited in the
  project's research, 2026-10-20), so the plan was a human paint-over of capsule art and logo, and
  honest disclosure. Not a typography rule, but decide it before the logo is "done".
- **OpenRouter trap**: an image-only model (declares `output_modalities: ["image"]`) 404s if you
  request `modalities: ["image","text"]`. That error is routing, not a text-rendering limit.
  Request `["image"]` for those models.
- **Paper title cards**: ask the image model for BLANK engraved paper (no text), upscale with
  Lanczos (1672x941 to 3840x2160 was used), then write the words on it with the pen effect.
  The game keeps three paper textures (wove, laid, foxed) as webp. The words stay live text, so
  they can be changed and localised.
- **Lettering over busy ground**: for text drawn over a busy floor, colour ink with a coloured
  outline plus a soft cream halo beat a paper strip; the owner chose that over the paper.
  Legibility was then carried by voiceover and subtitles, with a plain-font subtitle setting
  (off by default) for accessibility.

## 8. Traps

- **A hand that garbles a word is a defect, even if every letter passes coverage.** A key test
  word at 1280x800 read as nonsense in three of ten hands. Causes: a traced `e` with no eye read
  as `u`; `v n m u` were one tangle of the same diagonal minims; exit hairlines only 3 to 7 font
  units wide broke into dots at x height 34 px. Fixes: redraw the glyph as centreline strokes,
  and union the outline with its own centreline at a 12-unit floor so hairlines survive. Test
  the real in-game words at the real size on the real background.
- **Gaps in words are spacing, not joins.** Check join counts first (676/676 here) before
  blaming the connection strokes; the fix was optical spacing of letter bodies with joins redrawn.
- **Plate rows tilt.** Traced rows inherit the engraver's drift (letters 0.12 x height off the
  baseline, capitals 0.3 to 0.4 across a row). Measure every letter and level it to the baseline.
- **A hard-coded licence string.** The first hand builder wrote "SIL Open Font License 1.1" into
  every JSON, wrong for an own font. Make the licence name an argument (it is, here) and test it.
- **Reserved Font Name.** An OFL font with a reserved name may not name a modified version. The
  builder names the data by hand id and keeps the credit in the source line when it sees one.
- **Display cut at body size.** Hairlines vanish at 32 px and below (the report's verdict). Cut-per-size, as in section 4.
- **Missing glyphs.** The own font lacked `$ * + < = > [ \ ] ^ _ { | } ~` (listed, accepted).
  Compare your game's strings to the charset in CI, and give the runtime a fallback (it wipes a
  missing glyph left to right over its advance).
- **All-caps runs are tight** in an engraved style: fine for initials, wrong for shouting.
- **Do not trust "it loaded".** Per the CSS Font Loading spec `document.fonts.load` resolves with
  an empty list for a family that is not declared (general web knowledge, not tested here), and
  the 1.5 s race swallows timeouts silently. Confirm with a screenshot that the display face
  rendered, not the fallback.
- **Blots are rarer than you think.** The first module blotted about 0.8 per 100 letters; real
  letters measured about 0.02 (0.1 for the messiest). Defaults were reset to 0.05, with a
  per-call override from 0 (neat) to 0.25 (messy).

## 9. Licences and cost

- Stock script fonts used as fallbacks: SIL OFL 1.1 (bundling allowed; the notice AND licence
  text must travel with each copy, so the hand JSON carries `licenceText`). Apache 2.0 for one.
- Own font: proprietary to the studio, the licence name and copyright line come from `--licence`
  and `--licence-name`. Write your own studio name there; do not reuse another project's.
- Public-domain source scans: check each scan's rights statement; the shapes are free, a
  photographer's or library's terms on the image may not be.
- AI-generated letters may carry no copyright (US Copyright Office position as summarised in the
  2026-10-21 research, not re-read). Human-traced shapes with original joins avoid the question.
- Cost: v1 own font about 1h15m and $0; v2 cleanup one agent pass; ten further hands from copybook
  scans were estimated at 1 to 2 hours each. Image-model lettering is per-image API cost (see `art-waves`).
