# Drawing an own script font (method, numbers, receipts)

Source of truth: the project's own-font REPORT (2026-10-21) and the ten-hands report. The glyph
tracing scripts were tied to specific scanned plates (cut boxes per letter), so they are NOT
shipped here. This file is the method so you can redo it on your own plates.

## Why not stock, why not AI

- Stock scripts (three scouted, one kept as the fallback) read "a bit generic" to the owner, and
  a stock font cannot be exclusive.
- A 2026-10-21 survey found prompt-to-font tools but none showing joined thick-and-thin pen script
  (untested by us), and the licence terms varied from clean to "the font stays on sale to others".
  One community Claude skill (photo of letters to TTF) makes no kerning, ligatures or stroke order.
- fontTools plus a drawing step is the backbone of any own-font path. The hard part is the letter
  drawings, not the font file.

## Source material

Engraved copybook alphabets in the public domain, high-resolution national-library scans. v1 took
one roundhand alphabet. The ten writer hands later used other copybook hands (italian, ladies',
engrossing, gothic) the same way. Real manuscripts found online were too small to trace (500 px
wide scans), so no real person's hand was harvested; all ten were "copybook stand-ins".

## Method (v1, about 1h15m, $0)

1. Deslant each alphabet row (slant 0.62 to 0.70).
2. Cut joined letters at the connecting hairlines in the x-height band. Keep loops and descenders whole.
3. Replace lead-ins and exits with new hairline joins at fixed heights: normal joins at 0.22 x
   height rising; after letters with top exits (b, o, r, v, w) the next letter switches to a
   high-entry form at 0.62 x height through a contextual OpenType feature.
4. Draw punctuation the plate lacks with a simulated pointed nib (`( ) ! ? -`), build `: ; " ' ...`
   and dashes from the plate's marks.
5. Trace at 4x, clean the outlines, x height 320 of 1000 units, common slant 0.66.
6. Space lowercase by the cut-to-cut widths with zero kerning; space capitals, figures and marks
   on upright outlines with 1,077 auto-kerned pairs.
7. Swap bad forms: a ball-terminal f, a closed 4, a lining 8; a w built from half a u plus a v
   (the plate's own w read as "nv").

## v2 cleanup: what was wrong, what changed

| Defect | Cause | Fix |
|---|---|---|
| Gaps inside words ("wh at") | every join was connected (676/676); advances came from plate cut positions, so some letters carried long hairline runs | space each letter BODY optically (same mean white per side, row by row through the x band, each row capped), then redraw joins to the new edges. Gap spread (sd) 0.30 to 0.23 x height |
| Baseline wobble | plate lines rise left to right: a-e ~0.12 x height low, m/n ~0.13 high | measure every letter, move it to the baseline (round letters overshoot 0.025), fit each x part to the real x height (scale clamped 0.92 to 1.10) BEFORE joins are drawn so joins stay at fixed heights |
| Capitals drifting, "N OP" | row N written larger than row A and both rows tilt | sit every capital on the baseline, fit to 1.86 x height (clamped +/-10% of its row median), kern capital pairs optically; zero ink overlaps in 1,712 pairs at 400 px/em |
| Text size weak | hairlines too thin at 24 to 36 px | second cut: x height 340 vs 300, looser lowercase (0.25 white per side), heavier hairlines (blur 1.4, threshold 0.15); weight within 8% of the stock script |
| Missing characters | v1 had 110 glyphs | 167 glyphs: accents drawn with the simulated nib and composed on joined letters with high-entry forms so they still join, a pound sign traced from a plate, `/ # % @` drawn |

Known leftovers after v2 (kept in the report, not hidden): thin z (an end-ball erased), a long
y entry hairline that shows as a thread at 32 px, descender loops touching (gj, yf), tight all-caps.

## Verdict vs the stock script it replaced (v1)

- Better at 48 px and up: a real period hand, true thick/thin, old-style figures, clean joins.
- Worse at 32 px and below: thinner hairlines, smaller x height (needed a size scale ~1.25 in v1),
  old r/s/w forms. The stock script still read faster in subtitles at small size.
- Hand JSON was larger (340 KB v1 vs 214 KB), outlines a little lumpy above ~150 px.
- v2 then closed most of the small-size gap with the Text cut.

## The ten writer hands

Ten more fonts built the same way, one per speaker, so each speaker's lines are written in their
own hand. Charset gaps as above; every hand 99.93 to 100% coverage, 0.0000 em drift, 267 to 520 KB
raw JSON (106 to 213 KB gzip). Weakest glyphs per hand are listed in the project report.

Casting rules that held:
- Cast each hand like a voice: a table of speaker, evidence of the real hand (seen or INFERRED),
  font, why. Mark inferred rows as inferred.
- Audition at game size on the game's paper colour, not at 40 px on white.
- Rejections by reviewer notes: one font's lowercase looked like capitals ("thErE"); another
  collapsed spacing ("HisLordship"); one has an r that reads as n; one regular weight too thin at
  32 px; one fell apart at 32 px though closer to the real hand; one was the most legible but
  "closer to a wedding invitation" (no pen contrast).
- Readability: a design decision was that handwriting need not be fully legible because
  narration plays as the text writes, plus a plain-font subtitle option in settings for
  accessibility. Decide this on purpose; do not discover it in QA.

## Rebuild shape (our setup, for orientation)

A venv with fontTools, numpy, scipy, scikit-image, freetype; stages: build lowercase, build
capitals/isolates, synthesise punctuation, make the font (once per cut), render a test sheet, run
the hand-JSON build, run the pair-join and overlap checks. Kept as separate scripts with
intermediates in a work folder (387 MB of work and 369 MB of venv were deletable afterwards).
