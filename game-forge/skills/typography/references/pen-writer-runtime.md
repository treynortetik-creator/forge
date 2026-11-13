# The pen writer: hand JSON and runtime (as built, Phaser 4.2.1)

Method-level. The effect is two files: a pure half (layout, timeline, decal planning; tested
headless with vitest) and a Phaser half (draws what the pure half returns). You can port the idea
to any renderer; the JSON is renderer-neutral.

## Hand JSON (output of `scripts/build_hand.py`)

```
v, id, name, role, upem, asc, desc, xh, cap          metrics (font units)
licence, copyright, licenceText, source              the notice and licence travel with the data
cmap    { "a": "a", ... }                            char -> glyph name
pairs   { "ab": kern | [kern, altGlyphForA|0, altGlyphForB|0] }   from HarfBuzz, every pair of the charset
glyphs  { name: { a: advance, d: "SVG path", b: [bbox],
                  s: [ [x,y,r,w, x,y,r,w, ...], ... ],   main strokes in writing order, y up
                  l: [ ... ] } }                          strokes written at the END of the word
```

- `r`: dab radius that covers the ink nearest that point. `w`: nib half width there.
- Charset: ASCII 32 to 126 plus curly quotes, dashes, ellipsis, common accents and a pound sign
  (`CHARSET` in the script; characters the font lacks are reported as `missing`).
- Sizes seen: 209 KB raw / 81 KB gzip for a stock script; 410 to 473 KB raw for the own cuts.

## Layout

Greedy word wrap at `maxW`, `\n` forces a break. Each line is set whole (so kerning and alternates
across a space hold), then aligned in the widest line. Alternates: the right-neighbour rule wins,
as OpenType calt reads ahead. Default line height 3.3 x height. `rowPitch` = ascender to descender
at the hand's own scale: a row pitch under that makes strips share ink when letters are cut apart
for effects (hands differ a lot: one hand's loops ran 6.5 x heights, another's 3.4).

## Timeline

- Per glyph the pen spends `letter * (len/mean)^0.55` ms, clamped to 0.35 to 1.9 letter-times, so
  a long letter takes longer and a dot is quick. Shares along strokes by length, shades slower
  (segment weight 0.55 + 0.9 * w/wmax). A lift costs 26 ms.
- Pauses after a char in letter-times: `,` 2.2, `;` and `:` 2.6, `.` `!` `?` 3.6, ellipsis 4,
  em dash 1.2, en dash 1 (30% of that inside a word). Word gap 0.55, line gap 2.4.
- Late strokes (i and j dots, t crosses, accents) are flushed at word end.
- Ink load: falls 1.6% a letter to a floor of 0.78; a dip every 9 to 15 letters (a short pause)
  refills it. Tinted/drier ink along a run, fullest right after a dip.
- Dab step = max(0.9 px, min radius * 0.45), so strokes are continuous at any size.
- `duration` rescales the whole timeline to fit a voice clip; `cps` (default 14) otherwise.
- A glyph with no strokes is wiped left to right over its advance (fallback look).

## Rendering (Phaser)

- Hand art drawn once per block into a canvas. A mask uncovers it by stamping the frame's new dabs
  into a DynamicTexture (reused stamp config objects, no garbage per frame). A second copy in the
  wet colour is uncovered by the same dabs and dries back to the dry ink (about half a second).
- Cost: one canvas per block, two masked images (2 filter passes a frame), about 20 to 40 stamps a
  frame at 14 letters a second. 60 fps was measured on the dev machine's GPU (Chrome, ANGLE Metal).
- Extras added for a boss-line effect: a coloured outline round every letter (legibility over a
  busy ground), a soft cream halo under the ink, and a call that returns the finished ink cut into
  one strip per glyph (for letters that sag apart). A manual-clock mode advances only on request
  so clips can be recorded frame-exact.
- `skip()` finishes in one frame; reduce motion fades the block in.

## Decals measured from real letters (instead of invented)

15 crops from 1839 to 1888 letters and penmanship books (32 letter pages: 5 blots, 2 smudges):

- Blot rate about 0.02 per 100 letters (0.1 for the messiest writer). Game default 0.05 (2 to 3x
  reality, because a short game line would otherwise never show one); 0 neat to 0.25 messy per call.
  At most one per block by default.
- Placement: 60% at a stroke end, 30% on the line between words, 10% loose near the line. The
  earlier "never in the writing band" rule was dropped. A crowded spot shrinks the drop instead of
  covering ink. Never in a letter's counter, never over a second letter.
- Shape: smooth opaque oval along the writing direction, aspect 1.2 to 2.2, radius 0.25 to 0.75 x
  height (rarely to 1.25), 0 to 1 satellite droplets, a 1 to 2 px darker rim, a rare short drip.
- Smudge: rolled per word (default 1%), the last 2 to 3 letters of one word dragged right by 0.4 to
  1.2 x height and down by -0.05 to +0.15, once that word is down.
- Dry ink is brown-grey, #4d4334 to #6a5d4b (about 4 to 5:1 on paper). The game default stays
  near-black (about 9:1) for UI-critical text.
- Paper is quiet: no fibre hairs, about 28 small dark specks per 10 cm2, faint clouding, browning
  only at edges and folds. Sparse seeded specks (about 1.5 per 100 x 100 px, 1 to 3 px across).

## Tests worth copying (vitest)

- Every mapped char has a glyph with strokes; stroke arrays are multiples of 4 numbers.
- i dots are late strokes; the loader rejects an HTML 404 page parsed as JSON and a hand with a
  missing glyph.
- Licence and copyright fields present; a reserved-name font's data never takes the reserved name.
- Layout keeps kerning and the x height asked for; wrap and centring.
- Timeline: dabs in time order; about `cps` letters a second; punctuation pauses; deterministic per
  seed; `duration` wins over `cps`.
- Decals: placement split within sampling noise, shape ranges, never over a second letter,
  seeded.
- Size: raw < 500 KB and gzip < 200 KB per own hand.

## Which hand at which size

Display cut from 44 px up, Text cut below (a `handForSize` helper). A size scale per hand
(`SIZE_SCALE`: 1.07 for the display cut, 1.0 otherwise) so a font size reads like the stock
script's. `xhForSize(hand, fontPx) = fontPx * scale * (hand.xh / hand.upem)`.
