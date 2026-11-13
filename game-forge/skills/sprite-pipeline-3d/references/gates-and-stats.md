# Gates, stats, packing and budget

A bake is only done when its gates are green. Each gate is a number with a script. The original pilot spec
defined gates G0-G8; the pass conditions below are the ones we wrote down BEFORE seeing results.

| Gate | Pass condition | Tool here |
|---|---|---|
| G0 camera | a 0.5-unit cube at the origin lands at (cell_w/2, 0.85 cell_h) within 1 px; 8-direction render of the character under 10 min and under 3 GB RAM; at least 4 GB disk free | `bake_sprites.py --gate` (the cube check only) |
| G1 model | riggable; <= 20k triangles in the spec (the generator call asked for a 20k face limit; our later game meshes were ~100k-triangle decimations of the full mesh); face and key parts read at the target height | look at a 1x strip |
| G2 look | a blind A/B at 1x in a real fight capture picks ours or calls a tie; mean colour within 28 of the reference (the importer's colour-distance formula) | `looknum.mjs`, `fitlut.mjs` |
| G3 consistent | idle frame-0 alpha height within +-3% across directions; feet row within +-2 px; mean colour distance across directions <= 28 | `clipstat.mjs` (heights), `--dir-fit`, `--pivot sockets` |
| G4 turns | circle-strafe and gamepad sweep: at most 1 direction change per 5 ticks, no pop on an attack snap, foot slide acceptable | runtime test, `stride.py` for slide |
| G5 loops | loop-seam ratio < 0.8 for idle and run, every direction | `loopseam.mjs` |
| G6 budget | the project's size check passes; file count not up | see below |
| G7 fps | the perf run within 2 fps of baseline (one headless browser at a time) | project tool |
| G8 tests | unit tests and the asset-ingest tests green | project tools |

If G2 fails on look 1, try look 3 then 4; if all fail, stop and fall back to the video route.

## Loop seam

`loopseam.mjs`: ratio = meanAbsDiff(last, first) / mean over i of meanAbsDiff(frame i, frame i+1), over the union
alpha, RGBA. ~1 means the seam is as smooth as any step; > ~1.5 is a pop. On the stand-in's hatch bake the run
loops measured 0.95-1.13 and the idle loops 1.33-1.42; treat those as noise from the fine hatch pattern, not a verdict (inference; not
investigated). The stand-in idle was authored with a duplicate end frame and the bake drops it. Measure YOUR clip against its own steps.

## Height / size stats

`clipstat.mjs <dir> <char> idle run attack`: mean alpha-box height and width (alpha >= 24) per clip x direction,
relative to idle S frame 0. Use it to catch a crouching run that is 8% shorter than idle, or a direction that
differs from the rest. On the stand-in the run sat at 0.93-0.99 of idle height (its torso leans), which is probably the authored torso lean, not an error (inference).

## Penetration gate (arm through torso)

Why: a review caught an arm passing into the body on two combo hits; the sprites looked wrong at 1x even though
the rig "worked". Constraints were NOT added to the rig (poses are authored aim targets); the gate tells you which key to move.
- Method (`penetration_check.py`): for every pose, each limb segment's vertices (>= 90% weighted to that segment) are
  tested against the body and against any segment you pair with it (other arm, own upper arm). A vertex penetrates
  when it is behind the nearest face AND a 14-ray parity vote says enclosed (>= 80% of rays); depth = nearest-face
  distance; a segment's depth = its third-deepest vertex minus the same number at the rest pose (one stray fingertip does not fail a bake).
- Threshold we used: 20 mm at an ASSUMED 1850 mm figure (the model has no real size; say the assumption in your report).
  Runs BEFORE the heavy renders and stops the bake with a hit / frame / arm / depth table. `--pen-mm 999` skips the
  verdict but still prints the table. ~2 min on the real character.
- Lesson from testing on a stand-in: any part you do not name as a segment counts as "body". The unnamed upper
  arm made the forearm's elbow overlap show as a constant 13 mm "hit" on every run frame. Name every limb part.

## Face-occlusion gate (method only; the script was not generalised)

Why: a forearm swung across the face on a right cross and a left hook.
- For every pose of each combo action and 16 camera directions in the character's own frame (the 8 compass
  directions, each level and from ~25 degrees above), project the head's skinned vertices to a 24x24 grid over the
  head box. Splat cells covered by a FOREARM or HAND (vertices >= 50% weighted to that segment) that project inside
  the box AND lie nearer the camera than the head's centre plane. Coverage = splatted cells / cells the head covers.
- Measure the forearm alone, hand excluded: a fist beside the cheek is a legal guard, a forearm across the face is not.
- GATE only the face-on and front-3/4 views; report profile and back views (in profile a guard hand by the cheek is
  legal, from behind there is no face). Default limit 0.12 of the face box, forearm only.

## Hatch look checks (`hatchcheck.mjs` in the original, not shipped; the rules, for you to reimplement)

(a) off-palette: a pixel is ON the ramp within dE 9 of the Lab polyline (or an exact accent); must be 100%, per frame
set and per packed page. (b) tone bands per direction over the run frames: share of 8x8 fully-inside blocks by mean
darkness: lit < 0.12, light 0.12-0.35, mid 0.35-0.60, dark >= 0.60; every direction needs all four. (c) run-length
spread: runs of ink pixels along horizontal and vertical scanlines; 10th-90th percentile of widths spans >= 2 px, so
there are two line scales and not a mesh or a stencil. (d) 1x read checks at the sockets: a 9x9 box at the head has
>= 0.55 of paper's linear luminance with a 19x19 ring below 0.35 (face-on directions only); 7x7 boxes at each hand
have >= 30% pixels lighter than ink-3. (e) media: 1x strips of the run, run GIFs (S, E, N), a turn GIF at in-game size
on paper, and a labelled side-by-side against the previous art at 1x and 3x.

## Sheet packing and ingest

- ONE crop box per character per cell size (union of alpha boxes, padded 3 px, symmetric about the centre column);
  every frame cropped to it so atlas rects are uniform and a mirror keeps the feet on the anchor.
- Atlas: MaxRects, 2048 max, power of two, padding 2, extrude 1, lossless WebP. Page 1 = idle + run for all
  directions (the character is playable after one download); one animation never spans two pages unless past 2048 px.
- Manifest: one clip per direction, `<char>-<clip>-<dir>`, with `src: '3d'`, fps, loop, anchor [0.5, 0.85],
  cell, refHeight, atlas, `hitFrames`, per-frame sockets, and `mirrorOf` on mirrored directions. Scale 3D rows by
  `H / refHeight`, not by the painted content box.
- Hook the packer into the project's ingest. Ours rebuilt every anim atlas each run and wiped a separate packer's
  output. The "anim-only ingest" (rewrites only `anims`/`atlases` and the anim output folders) is the standard
  re-run after merging any anim, 3D or portrait work.
- Tests for 3D rows: frames resolve, `sourceSize == cell`, feet row = round(0.85 x cell_h) +-2, `mirrorOf` targets
  exist, all 8 directions covered; run unit tests with a single worker.

## Budget (inference: bytes scale with figure height squared)

| Set | Frames | Estimated size | 2048 pages |
|---|---|---|---|
| Hero 176 px, 8 dirs, 6 clips | 296 | 2.7 MiB | 3 (48 MiB GPU) |
| Enemy 124 px, 5 dirs + mirror, 17 frames/dir | 85 | 0.45 MB (about what painted rows cost) | 1 |
| Mounted boss 176 px, 8 dirs | 384 | ~7 MiB | 4-5 |

Painted rows had cost ~26 KB/frame (hero) and ~22 KB/frame (enemy). A mounted boss is the outlier: 5+mirror at
scale 1.4 with a 6-frame run (~3.5 MiB) or accept the overage. Enemies are budget-neutral ONLY if their painted
rows are deleted in the same commit. Run the budget check on every migration commit.
