# Rigging, clips and moves

## Rig sources, by character shape

| Shape | What worked | What failed |
|---|---|---|
| Biped (hero, humanoid enemy) | Paid: auto-rig with a Mixamo-named spec (rig v1.0 had 90+ presets incl. boxing, kicks, slash, cast, hit reactions). Local: SkinTokens auto-rig, 49-74 s and 4.8-7 GB on a ~950k-triangle mesh, 4 of 4 bipeds passed a humanoid rig check | local bones come out `bone_0..N`; we wrote a post-step that renames bones by tree role to `mixamorig:*`; 3-7 bones per rig stayed unnamed (no Neck on three of four; fingers on some); skinning is lumpy on loose cloth and armour, acceptable at 124 px |
| Quadruped / odd shape | paid rig v2.5 (11 presets, covers quadrupeds) and Rigify animal metarig as the fallback | local humanoid rig check refuses; Tripo's biped retarget stood a low crawler up |
| Blob crawler | hand-keyed squash-and-stretch about the hip bone plus a slow roll about the forward axis (rest, crawl 24 frames loop, lunge 24, hurt 12) | both auto-riggers |
| Bat / flyer | hand-posed wing chains: rest + flap, 24-frame loop, 32 degrees, rotate each chain about the body axis, pivot at the chain head | every retarget preset failed on the avian rig; the rig had a single chain on one side, so the two wings moved unevenly |
| Static prop | no rig; clip `frameList: [0]`; `bake_sprites.py` handles a rig-less mesh | - |

For the generators see the sibling skill `game-forge:local-3d-gen`. Rigger research (2026-10):
the best Mac rigger was a one-star community Rust/Metal port of SkinTokens with a GPL-3.0 sub-crate; official
SkinTokens/UniRig/Puppeteer needed NVIDIA CUDA. Treat the port as a build tool and ship only the rigged GLB.

## Motion sources

- Libraries are the only licence-clean, game-quality source: Mixamo (free with an account; our only terms source
  was a 2022 FAQ, read Adobe's current terms before shipping), Rokoko's free 150 moves (commercial use stated on
  their pages), the paid tool's own presets.
- Text-to-motion (HY-Motion, Kimodo) is humanoid-only; NVIDIA's Kimodo SOMA weights were licensed "ready for
  commercial use" per the model card, its SMPL-X checkpoint is research-only. Our local result: generic presets
  (idle, walk, sword swing, cheer, hit react, death) retarget in ~2 s each, but there is no cast preset and the swing
  is overhead two-handed. Weight, telegraphs and hit-stop timing come out floaty: retime for gameplay frames.
- Video-to-motion (GVHMR, WHAM, SMPL-X) and AMASS-trained weights are non-commercial. Cascadeur Free is non-commercial.
- Custom moves: author in Blender Python, one script per character. Attacks bake 3 frames per hit, so key exactly
  anticipation, contact, recovery as `{bone: euler}` dicts and set the `contact` marker. Flavour (heavy shoulders)
  as an NLA additive layer over library loops.

## The clip spec (what `bake_sprites.py` and `finish-frames.mjs` read)

```json
{ "name": "hero", "facing": "x", "centerBone": "Hips",
  "sockets": { "foot_l": {"bone":"L_Foot","ground":true}, "head": {"bone":"Head","local":[0,0,0.06]} },
  "clips": {
    "idle":   {"action":"Idle",  "n":8, "fps":8,  "loop":true},
    "run":    {"action":"Run",   "n":8, "fps":12, "loop":true},
    "attack": {"action":"Combo", "n":6, "fps":14, "loop":false, "hitFrames":[1,4], "segments":[3,3]},
    "cast":   {"action":"Cast",  "n":4, "fps":12, "loop":false, "hitFrames":[2]},
    "special":{"action":"Slam",  "n":5, "fps":12, "loop":false, "cell":[384,256]} } }
```
Frame counts we kept from the old painted rows so the runtime's segment maths and sim timing did not change:
idle 8 @8 loop, run 8 @12 loop, attack 6 @14 (segments [3,3], hits [1,4]), dash 4 @16, cast 4 @12 (hit 2),
special 5 @12 (384 cell), brace 2 @8. Enemies: idle 4-8, move 6, windup 3, strike 3, hurt 2. Our final combo
clip grew to 49 frames in a 320x288 cell (six hits, segments [4,4,4,13,11,13]); `chainstat.mjs` measures the
pose-to-pose jump inside and between those segments.

- `frameList` takes explicit source frames, or `[action, N]` pairs to cross actions. `range` limits the span.
- Loops sample `n` frames over `[f0, f1)` (duplicate end frame dropped); non-loops include both ends.
- Mark `contact` and `loop_end` in the action; the packer should drop the loop's duplicate end frame.
- `fpsK`: N/S runs read faster than diagonals on screen; we used 1.15 for N/S and 1.07 for diagonals and tuned foot slide at the turn test.
- Foot slide: `stride.py` finds the planted-foot ground speed (foot height within 0.02 units of the cycle minimum,
  position seen from the hip) and converts it to world px per cycle (speed x cycle x 64 x fit scale). Set the
  run's movement speed from it, not by feel. Caveat: the stand-in run has no planted foot, so it returned empty.

## Blender 5.x API changes that break old rigging scripts

- Actions are slotted: `Action.fcurves` is gone. Assign the action AND `arm.animation_data.action_slot = act.slots[0]`;
  to edit curves go through `act.layers[].strips[].channelbags[].fcurves`. To set interpolation, change the default
  (`preferences.edit.keyframe_new_interpolation_type = 'LINEAR'`) BEFORE inserting keys.
- The glTF importer parks actions in NLA tracks that override an assigned action: remove them first
  (`bake_sprites.py` and `penetration_check.py` both do).
- The importer leaves meshes in QUATERNION rotation mode, which ignores `rotation_euler`: set `rotation_mode = 'XYZ'` first (`untilt-glb.py` does).
- The importer adds an `Icosphere` bone-display mesh per armature; delete it or it renders as a stray ball.
- Exporting every action as a clip: one NLA track per action, `export_animation_mode='NLA_TRACKS'`.
