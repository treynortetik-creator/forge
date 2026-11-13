# Ink-redraw: a post pipeline for a set of 2D enemy strips

**Status (read first).** Built 2026-10-18 on the owner's decision to replace a procedural hatching script with an
image-model redraw of painted sheets. On 2026-10-23 the owner ruled that enemies should look like Blender-baked
sketch renders, and the taste file marks the 2D model-drawn enemy strips SUPERSEDED. I did not trace whether this
pipeline's output shipped. What survives is the method: gate a model's redraw in numbers, and lock it back into the
original silhouette. The script itself (about 1,000 lines, tied to one repo's git history and a character config)
is not vendored; this is the design so you can rebuild it for your own set.

## The problem it solves
Ask an image model to restyle one frame at a time and the character changes identity, the silhouette drifts (so
hitboxes and animation timing no longer match), tones flicker frame to frame, and fine hatching turns into periodic
"zebra" banding. The pipeline treats the painted sheet as the truth for SHAPE and the model as a source of LOOK only.

## Stages, per character
1. **Keyframe.** ONE approved keyframe: idle frame 0, image-edited with the style refs (a style prop plus a reference
   engraving). The owner approves this single image before any strip is generated.
2. **Clips as whole strips.** Each clip is redrawn as ONE strip in one edit call (painted strip + keyframe + prop
   attached), so frames are drawn together and share a hand. Strips longer than 6 frames are split into equal
   halves or thirds. A frame that fails the pose gate is retried as a strip (max 2 retries), then redrawn per frame
   with the keyframe as reference (max 2 retries).
3. **Finalize.** For each generated cell: align it to the painted cell (uniform scale plus centroid), box-downsample to
   the work scale (2.5x oversample), upsample to the sheet cell size, map tone onto the style's ink-paper ramp with a
   per-character gamma (starts at 1.2, contrast 1.6, raised until a mean-luminance audit holds on ALL the
   character's frames), then MASK to the painted alpha (1 px dilate, hard 0/255 alpha). Silhouette, hitbox and anim
   timing are therefore identical to the painted original.
4. **Blank-patch repair.** Pixels inside the painted mask that the model left as bare paper are filled from the old
   procedural pixels (same cell) and quantile tone-matched. Split strips get their second half tone-matched to the
   first so there is no brightness step.
5. **Report.** Gates in numbers, contact sheets at 1x and 3x, one GIF per clip. **Install** writes the same files the
   old tool wrote, ready for the normal ingest.
6. **Import path.** The same post pipeline accepts externally generated PNGs (same pixel size as the painted input,
   figure on flat paper or transparent), so a human-driven app can do the generation.

## The gates (config values as read)
| Gate | Rule | Value |
|---|---|---|
| Pose gate | IoU of the aligned generated figure against the painted figure | at least 0.90 to pass; below 0.85 a strip frame is redrawn per frame; marginal frames in between are kept and flagged |
| Flicker | mean absolute luminance difference of consecutive frames inside the shared mask, at screen scale, also contrast-normalised; reported as a ratio against the painted original | flag at ratio 1.5 |
| Zebra | share of 16x16 blocks (stride 8, at least 90% figure, textured) whose 4 to 12 px band energy sits on ONE spectral peak (an FFT test for periodic banding) | block 16, period 4 to 12, peak above 0.4, band share at least 0.3, flag when over 8% of blocks |
| Blank area | bare paper left inside the figure AFTER repair (flag over 0.004 of the figure); and the raw blank before repair (flag over 0.1: the old-art repair is carrying the frame) | 0.004 and 0.1 |
| Seam step | luminance step across strip-group boundaries and the loop wrap (last frame to first) | may not exceed 5.0 |
| Spend | every paid call logged to a JSON ledger; hard stop at a cap | 15.0 USD; the ledger at the time read about 5.56 USD |

The zebra detector was calibrated with its own sub-command (`calibrate-zebra`) against painted and
procedurally engraved sheets before use; do the same for any periodicity detector.

## What to keep for your own pipeline
- A single approved keyframe before any strip; the owner signs one image, not forty.
- Whole-strip redraws first, per-frame fallback second, both gated by IoU.
- Re-impose the original alpha mask after the model draws: shape is never the model's decision.
- Numeric gates for flicker and banding, and a cap on paid calls with a ledger.
- Calibrate every gate on examples the owner has already judged (see `measure-and-audit.md`).
