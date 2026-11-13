---
name: sprite-pipeline-3d
description: >
  Build game characters, enemies and props as 3D models and bake them to 2D sprite sheets: headless Blender,
  fixed orthographic camera, 8 directions, an engraved/hatched "ink" look or a toon look, super-sampled
  and projected onto a fixed palette ramp, gated by measured checks (penetration, face occlusion, height and
  feet registration, loop seam), packed into atlases. Covers model source (hand-built, local or paid
  image-to-3D), rigging and clips, the idle rule, anim-only ingest, and the Blender MCP vs headless
  rules. Use for "render 3D to sprites", "8-direction sprite sheet", "Hades-style 3D to 2D", "bake a
  character to frames", "ink/engraving shader", "why do my baked sprites shimmer / slide / look murky",
  "set up Blender MCP for a game pipeline". Not for modelling a real object from photos
  (design-forge:photo-to-3d-loop).
---

# 3D to 2D sprites: build once in 3D, bake every direction, measure everything

The case: a 2D game (we used Phaser 4 + TypeScript, a top-down roguelite) needs every character and enemy
in 8 directions, with attacks that look the same from every side. Per-direction painting or per-clip video
does not scale (every attack x every direction). A rigged 3D model rendered offline does: change the model
or a move, re-run one command, get every frame. The game stays 2D; Blender never ships.

The house rule applies hard here: **anything that can be expressed as a number is measured, not eyeballed.**
Heights across directions, feet rows, palette membership, hatch coverage, loop seams and arm-through-torso
depth all have a script that exits non-zero. Judgment (does it read at 1x? is it ours?) stays with a person
or a fresh critic looking at a 1x strip.

## What is in this skill

| Piece | Where | Needs |
|---|---|---|
| The bake: camera, 8 dirs, toon or hatch look, hull outline, fit, dir-fit, line sidecar | `scripts/bake_sprites.py` | Blender 5.x |
| Free rigged test character with 4 clips (build the whole pipeline before any model exists) | `scripts/standin.py` | Blender |
| Finish: area average, line darkening, alpha floor, palette ramp snap, `frames.json` | `scripts/finish-frames.mjs` | Node + `npm i sharp` |
| Gates and stats: `penetration_check.py`, `loopseam.mjs`, `clipstat.mjs`, `chainstat.mjs`, `looknum.mjs`, `linewidth.py`, `stride.py`, `sheet.mjs`, `fitlut.mjs` | `scripts/` | see each header |
| Mesh prep: `decimate-glb.py` (carry actions over, cap texture), `untilt-glb.py` (single-view generators lean) | `scripts/` | Blender |
| Depth: camera and directions, ink look, rigging and clips, gates and packing, Blender setup | `references/*.md` | - |

Honest scope: `bake_sprites.py` is a trimmed, generalised port of a ~1,500-line renderer. The hatch look,
rest-pose stripe aiming, hull rim and contour pass are in; the game-specific parts (texture re-painting by
region masks, skin/electrode mask passes, the graphite sketch look, rig bulking) are not. The face-occlusion
gate was never generalised (method in `references/gates-and-stats.md`). Everything shipped here was run
against the `standin.py` mannequin on Blender 5.2.0 LTS; see "Smoke results" at the end for what was and was not exercised.

## Workflow

### 0. Decide the model source (link, do not redo)

| Source | Use when | Receipt |
|---|---|---|
| Hand-built in Blender (`standin.py` is the template: bone-per-part mannequin, scripted clips) | stand-in to build the pipeline; props; things AI generators botch | the stand-in has a real armature and 4 scripted clips, no downloads, no credits |
| Local image-to-3D (Pixal3D first, TRELLIS.2 backup) then local rig | cost and licence control, thin features (staff, ribs) | bake-off of 5 enemies, $0, 5-16 min each on a 32 GB laptop; see `game-forge:local-3d-gen` |
| Paid image-to-3D with auto-rig and move library (Tripo) | speed, crawler-type rigs, richer retarget library | our estimate ~200-280 credits per rigged character, **inference** from the CLI docs' example (generation 110 + texture 30), rig/retarget prices were undocumented |
| Photos of a real object | product turntables | `design-forge:photo-to-3d-loop` |

Whatever the source, the output of this step is one GLB: a mesh (decimated, see step 1), an armature, named
actions. Keep sources outside the shipped assets folder. A single-view generator's mesh may arrive tilted
by the camera pitch: `untilt-glb.py` (we measured 17.5 degrees on one prop, by PCA of the vertices).

### 1. Prep the mesh

```bash
blender -b --factory-startup -P scripts/decimate-glb.py -- full.glb game.glb 100000 2048 [extra_retarget.glb ...]
```
Triangles never reach the sprites, but a 1.4M-triangle mesh makes every frame slow. We used ~100k. The
script keeps armature, vertex groups, UVs and actions, downsizes textures, and carries the actions of extra
retarget GLBs (same skeleton) onto the first armature so one GLB holds every clip.

### 2. Stand-in first, pipeline second, model third

Run `standin.py`, bake it, run every gate on it, wire the runtime picker and fallbacks. Swapping in the real
model is then a re-render, not a rebuild. This was our written plan (the stand-in step in our pilot spec: camera,
lights, outline, manifest format, direction picker, fallbacks and tests all built with no credits spent); the
generated-model step then ran after it.

```bash
blender -b --factory-startup -P scripts/standin.py -- out/standin     # standin.glb + standin.clips.json
```

### 3. Rig and clips

Details in `references/rigging-and-clips.md`. The short version:
- Biped: auto-rig with a Mixamo-named skeleton so library moves retarget; non-biped (blob crawler, bat, hound):
  expect the auto-rigger to fail or retarget badly, and **hand-key a handful of procedural loops** instead.
- The clip spec (`*.clips.json`) is the contract between the rig and the renderer: action name, frame count,
  fps, loop flag, `hitFrames`, `segments`, optional `frameList`/`range`/per-clip `cell`, `centerBone`, `sockets`.
- Every move is a script, so a model change is one re-render.

### 4. Check the camera before anything else (gate G0)

```bash
blender -b --factory-startup -P scripts/bake_sprites.py -- --model x.glb --clips x.clips.json --out /tmp/g --gate
```
Renders a 0.5-unit cube at the origin and demands it land at (cell_w/2, 0.85 x cell_h) within 1 px.
Receipt: on a 256 cell the stand-in run printed `centre [128.0, 217.5] expected [128.0, 217.6] pass true`.
Use 0.5 not 1.0: a 1-unit cube reaches 70 px below its centre and clips the cell bottom.

### 5. Bake

```bash
blender -b --factory-startup -P scripts/bake_sprites.py -- \
  --model game.glb --clips char.clips.json --out render/char \
  --look hatch --cell 256x256 --scale 1.6 --fit-height 176 --elev 25 \
  --super 4 --samples 8 --pivot sockets --dir-fit --line-pass
```
Output: `render/char/raw/<name>-<clip>-<dir>-<i>.png` at 4x the cell, `.ln.png` line sidecars, `meta.json` with
per-frame 2D sockets, timing per clip. `--clip idle,run`, `--dirs s,e`, `--skip-existing` make iteration cheap.
Use `--look toon` for a colour look, `--look flat` to debug silhouettes and registration.
**One Blender process at a time** (`references/blender-setup.md`).

### 6. Finish

```bash
node scripts/finish-frames.mjs --render render/char --out frames/char --look hatch --line-dark 1.0 --mirror w=e,nw=ne,sw=se
```
Area-averages the super-sampled render to the cell, darkens only the defining-line pixels, floors the stray
alpha, snaps every pixel onto the palette ramp (10 levels), computes ONE crop box per cell size symmetric about
the centre column (so a flipX mirror keeps the feet on the anchor), writes `frames.json`.

### 7. Gate

```bash
node scripts/clipstat.mjs frames/char char idle run attack     # alpha-box height of every clip x dir vs idle S frame 0
node scripts/loopseam.mjs frames/char idle,run                 # last->first step vs an ordinary step
blender -b --factory-startup -P scripts/penetration_check.py -- --model game.glb --seg ... --pen-mm 20   # BEFORE step 5
python3 -I scripts/linewidth.py final.png raw.ln.png 4 1.0     # line weight at game size, before/after line-dark
```
Thresholds we shipped with and the receipts: `references/gates-and-stats.md`. Look at a 1x strip and a turn
GIF too; the numbers catch drift, a person catches "it reads as a lump".

### 8. Pack and ingest

Pack frames into atlas pages (we used MaxRects, 2048 max, padding 2, extrude 1, lossless WebP; page 1 = idle
+ run for all dirs so a hero is playable after one download). Register one manifest clip per direction.
**Hook the packer into the project's anim-only ingest**: our ingest rebuilt every anim atlas on each run, so a
separate packer's output was wiped the next time anyone ran it. After merging any anim, 3D or portrait work,
run the anim-only ingest (it rewrites only `anims`/`atlases` in the manifest and the anim output folders,
nothing else). Commit sources; commit generated output only if your package owns it.

### 9. The idle rule (runtime)

A standing character shows ONE still idle frame (the middle of its loop) plus a runtime breath; never cycle
redrawn idle frames. For 3D bakes the same rig makes every idle frame, so cycling is possible, but we kept
the rule after the painted-art jitter fix: a 5 fps ping-pong between different poses had 44-73% silhouette
overlap between neighbours (the figure boiled), and holding a static pose with a breath took the max
frame-to-frame luminance step from 4-6 down to 0.7-3.

## Traps (each one cost us time)

- **Do not equalise by eye.** A slouching model is up to ~6% shorter on screen from the front than from the
  back. `--dir-fit` renders idle frame 0 in every direction and scales each about the feet to match S.
  Gate: idle frame-0 height within +-3% across directions, feet row within +-2 px.
- **Pivot on the feet, not the bounding box.** A raised sword or lance drags a bbox pivot off the body and slides
  the feet between directions. Even the 4%-lowest-vertices pivot sat a few cm off the stance centre and swung the
  feet row +-4 px as the model turned; `--pivot sockets` (midpoint of the two foot bones) fixed it.
- **Shift root-motion clips with a centre bone.** A retargeted run carries the root ~0.5 units (0.52 measured) ahead of the
  feet; `centerBone` re-centres each clip on its own mean.
- **Hatching must ride the body.** Our reviews flagged "fingerprint crawl" on the back view and a 1x run that
  read as a dark fuzzy lump (review score 5/10). The renderer fixes stripes in REST-POSE surface coordinates,
  re-aimed once per direction, so lines move with the body through a clip; check it by looking at the run GIF.
- **Fine hatch is designed to be area-averaged.** The tone hatch is finer than a screen pixel pair so a box
  average turns it into soft ink grey; structure lines are sized for 1-3 screen px so they survive. Render at 4x
  the cell (3x if a bake passes 10 minutes) and box-average. We did not measure Lanczos on it; expect ringing (inference).
- **Darken defining lines in value, never width.** After a bake read too light, the fix was a sidecar of the
  silhouette/form-edge coverage and a value pull toward ink on exactly those pixels. Thickening was an explicit
  "no" in the art direction. `linewidth.py` measures FWHM at game size so "same pencil width" is a number.
  Honest receipt on the stand-in: line contrast 0.782 -> 0.786, width 4.18 -> 4.26 px; on a model whose
  outline is already ink-black the effect is small, it matters when outlines are thin and averaged to grey.
- **Colour bakes go murky on the back and sides.** Our key and fill both came from the camera half-space; fix
  was a warm back rim and a cool side rim with colour-preserving banding. A palette LUT fitted on the S view
  alone matched the front (p90 169) and left the sides at 106; fit on several directions pooled, then trim per direction.
- **Do not bake the glow.** Halos and impacts belong to the engine's filters; baked ones fight them.
- **Freestyle is too slow** (we measured ~9 min per frame and it added wrinkle noise). Hull rim + a
  camera-space normal-difference contour pass replaced it.
- **A model that fuses the weapon into the hand breaks occlusion facing away.** Weapons are separate meshes
  parented to the hand bone, baked into the frames.
- **Mirror only where mirroring is cheap.** Mirroring swaps the weapon hand mid-combo, so our spec rendered all 8
  directions for heroes and proposed 5 (E, NE, N, S, SE) + mirrored W/NW/SW for enemies as budget-neutral.
  Mirroring needs the symmetric crop box above.
- **Auto-riggers fail on crawlers.** On a low blob crawler the paid biped retarget stood it up and flung its arms;
  the local rig was made but its humanoid check failed and the retarget script refused ("expected 2 legs + 1
  spine"). A bat's avian rig (paid service) built but every retarget preset failed. Both got hand-keyed procedural loops (squash and
  roll on the hip bone; wing chains rotated about the body axis).
- **Rest-facing differs between rig and mesh by an arbitrary angle** on local-generator rigs (we needed a 45
  degree bias on one generator, 0 on another). Test one frame; `--yaw-offset`, `--facing x|y|auto`.
- **Packing is part of the pipeline.** See step 8 on the wiped atlas. Also: loops drop the duplicate end frame
  or the loop stutters.
- **A green typecheck is not a working sprite.** Run the game scene, look at the 1x fight capture beside the old art.

## Licences and cost

Read the licence of every generator before shipping; this is not legal advice and these are our readings at
the time (2026-10): Pixal3D and TRELLIS.2 (MIT) plus the DINOv3 encoder under Meta's licence (free, worldwide,
keep the licence text, no weapons or sanctioned end uses); Hunyuan3D-2 licence excludes the EU, UK and South
Korea territory for outputs, which blocks a worldwide game; Tripo free-tier outputs are retained by Tripo,
paid users "generally have all rights" (confirm in writing before shipping big); SkinTokens upstream MIT, a
Mac port had a GPL sub-crate (check before redistributing the binary); Kimodo SOMA weights NVIDIA Open Model
License ("ready for commercial use" per the card); Mixamo terms we only had as a 2022 FAQ; Cascadeur Free is
non-commercial. Cost: local generators $0 and ~20-30 min of unattended machine time per enemy; Tripo ~$1.15
per enemy in the bake-off (100k-triangle decimation, ~115 credits at $0.01).

## Smoke results (this skill, Blender 5.2.0 LTS, Node 24 + sharp)

- `standin.py` ran in <1 s and wrote a 190 KB GLB. `bake_sprites.py --gate` passed. `--look toon` and `--look hatch`
  baked 3 directions x idle + run (hatch: 48 frames + 48 line sidecars in 15 s at 256 cell, super 4, one process).
  I viewed the frames: the hatch look reads as engraved on the stand-in, toon reads as flat colour with an outline.
- `finish-frames.mjs` wrote 48 frames with 10 palette levels; `clipstat`, `loopseam`, `looknum`, `sheet`, `linewidth`
  ran. `penetration_check.py` runs and exits 1 over its limit (tested with `--pen-mm 5`).
- `stride.py` runs but the stand-in run has no planted foot, so it returned empty stance; untested on a real run cycle here.
- `chainstat.mjs` and `fitlut.mjs` were syntax-checked only. `.fbx` input, multi-mesh hatch, a rig with real
  auto-weights and a 100k-triangle mesh were not exercised.
