# Measuring art: art-measure, calibration, palette audit

## What each art-measure metric means (sprites)
Sprites are cropped to the alpha box and resampled (Lanczos, premultiplied, no colour fringe) so that
sqrt(opaque pixels) = 70 before any metric (the median of the original calibration set), so export size does not
change a verdict. Rescales outside 0.35 to 3.0 add a note: edge metrics are unreliable there, export nearer the shipped size.

| Metric | Meaning |
|---|---|
| tone.L_median, L_p10, L_p90 | luminance (0.299R + 0.587G + 0.114B) percentiles over pixels with alpha at least 128. p10 low means crushed blacks; median low means muddy |
| tone.near_black_pct | share of opaque pixels with L under 40 |
| tone.sat_mean | mean HSV saturation |
| tone.moss_pct | share with hue 50 to 110 degrees, saturation over 0.28, value over 0.15 (an olive-green mould detector; adapt or drop for your art) |
| outline.coverage_pct | share of alpha-boundary pixels that have near-black ink (L under 55) on them |
| outline.width_px | area of boundary-connected dark ink within 8 px of the edge, divided by inked boundary pixels |
| outline.ink_weight_px | width times coverage: black ink pixels per boundary pixel. The one that carries "the outline is too thick" |
| outline.contour_L_mean | mean luminance of the 2 px ring inside the edge |
| feather.ramp_px | partial-alpha pixels within 14 px of full transparency divided by boundary length. A hard edge is about 1 to 3 px, a faded edge 10 or more |
| shadow | a soft darker partial-alpha blob in the bottom 25% of the box at least 35% of its width. Reported, never judged |
| hatch.hatch_pct, largest_area_pct | pixels inside long, parallel, thin strokes: structure-tensor coherence over 0.72, gradient sign alternating across strokes (balance under 0.5), edge density over 0.4 in a sigma-6 window |

Screens: HUD rectangles are masked on game-shaped frames (aspect 1.3 to 1.9), letterbox rows are excluded, and the
frame is cut into 64 px tiles; per tile hatch, thin black ink (near-black strokes up to about 5 px thick on a pale
ground) and moss; a heatmap PNG goes to the output folder, never beside the input. Darkness is judged on sprites only:
a screenshot legitimately contains black pits and letterboxes.

## The calibration rule (`scripts/calibrate-thresholds.py`)
Per metric: `g` = worst value over the GOOD set; `b` = 10th percentile of the pooled BAD values, over the BAD sets
that metric is about. If `g` and `b` do not separate by at least 10% of the larger value, the metric is INFO. Else
`warn = g + 0.5(b - g)` and `fail = g + 0.75(b - g)`, mirrored for metrics where smaller is worse. `--ref` tolerance
per metric = the p5 to p95 spread of the GOOD set (warn beyond 1x, fail beyond 2x).

Numbers from the shipped example (`scripts/art-measure.thresholds.example.json`, 64 good idle+move frames of a
baked enemy, bad frames from a painted-redraw set and two painted floor-effect sets; one art style, for the format only):

| metric | dir | good worst | bad p10 | warn | fail |
|---|---|---|---|---|---|
| tone.near_black_pct | max | 14.31 | 24.288 | 19.299 | 21.794 |
| tone.L_p10 | min | 27.0 | 21.0 | 24.0 | 22.5 |
| tone.L_median | min | 106.3 | 55.06 | 80.68 | 67.87 |
| outline.ink_weight_px | max | 1.66 | 2.406 | 2.033 | 2.22 |
| outline.coverage_pct | max | 71.7 | 96.13 | 83.915 | 90.022 |
| feather.ramp_px | max | 5.41 | 10.601 | 8.005 | 9.303 |

Metrics that did not separate stayed INFO (outline.width_px alone, feather.partial_ring_pct). Sprite hatch had no bad
example, so it is warn-only at the worst good value. On screens, the thin-ink metrics are warn-only because black
lettering and dark wall ornament both read as thin black ink.

## Limits, stated by the tool's author and worth repeating
- One enemy look calibrated the outline and tone limits; thresholds are a ruler for that look, not a law. Add labelled
  samples and re-run.
- No independent hold-out: the other-poses check uses the same model, render and directions as the fit.
- A role can demote metrics to INFO (the player character was allowed to be darker so the player can track it;
  the owner's outline verdicts were about enemies only): `art-measure.py --info tone.,outline.`.
- Hatch needs strokes of at least about 2 px at a 4 to 12 px pitch; very fine, very coarse or curved hatching reads
  low.
- Run with Pillow below 13 (it broke the tool when written), through `uv run --with "pillow<13" --with numpy --with scipy`
  or an environment that has them. zsh does not word-split a string variable; wrap the command in a shell function.

## Screen thresholds
Same rule with screens as the sets. Receipt numbers (example): hatch largest-area 0.55% worst good against 3.67% bad
p10 gave warn 2.11 and fail 2.89; tile share 1.0% against 7.5% gave warn 4.25 and fail 5.875. A "good" screen set that
is partly "neutral, nobody complained" is weaker than owner-labelled good, and the calibration note said so.

## Palette audit (`scripts/palette-audit.py`)
- Convert to Lab. Off palette = chroma over 12, NOT within delta-E 9 of the ramp POLYLINE (not just the 5 token
  points: anti-aliased pixels between tokens would all be false positives), NOT within hue_tol 14 degrees and at least
  0.6x the chroma of an allowed colour.
- That last clause means a soft halo that fades through mid chroma IS flagged. Fade glows by alpha down to near the
  ramp, or keep them saturated and tight; never wide low-alpha coloured washes.
- `warm_pct` (orange/amber hue band 30 to 68 degrees, chroma over 12, off the ramp) is its own budget, 0.5%.
- ADD blending a colour over pale paper shifts its hue toward yellow: shoot it and run the audit, do not assume.
- Mask rects (`<shot>.mask.json`) exclude areas with their own rules, such as portrait boxes. Heatmap: the shot dimmed,
  off-palette pixels in red. A squint image (6 px blur, greyscale) per combat shot is a cheap silhouette test.
- The original also scoped a number to "what this work package owns" (walkable floor only, HUD and sprites masked).
  That is project machinery; use mask rects instead.

## Gates are not yours to move
Raising a budget, loosening a threshold, skipping a test or deleting a failing assertion to get green is forbidden
for a builder. Report the failure with the numbers. Only the owner moves a gate.
