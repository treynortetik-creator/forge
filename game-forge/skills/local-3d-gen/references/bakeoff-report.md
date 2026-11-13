# Bake-off: local image-to-3D vs a paid cloud service (2026-10-23)

Machine: MacBook Pro M5, 32 GB, no Xcode. Everything local ran at $0. Five enemy source images
(a skeletal caster, two armoured brutes, a bloated crawler, a hammer brute as the control). Paid
reference: Tripo at about 115 credits ($1.15) per enemy. Wall times are from `/usr/bin/time -l`;
"peak" is max resident set size (GPU shared memory not separated). Some Blender renders ran
alongside, so times are slow, not fast.

## Per-run table (all exit 0)
| Enemy | Pixal3D full | TRELLIS.2 F16 | Hunyuan 2.0 full | Hunyuan turbo (fast) |
|---|---|---|---|---|
| caster | 312 s, 3.9 GB, 947k tris | 490 s, 4.3 GB, 287k | 501 s, 10.1 GB, 300k | 229 s, 9.0 GB, 30k |
| brute big | 985 s, 8.3 GB, 975k | 2586 s, 10.7 GB, 286k | 562 s, 10.1 GB, 300k | 223 s, 30k |
| brute small | 751 s, 7.5 GB, 951k | 1288 s, 7.7 GB, 275k | 555 s, 300k | 237 s, 30k |
| crawler | 586 s, 5.6 GB, 936k | 1672 s, 8.2 GB, 282k | 554 s, 300k | 241 s, 30k |
| hammer brute | 813 s, 7.0 GB, 978k | 1468 s, 8.0 GB, 280k | 602 s, 300k | 254 s, 30k |

Output sizes: Pixal3D 36-41 MB GLB, TRELLIS 11-13 MB, Hunyuan about 28 MB. All textured (PBR base
colour). Pixal3D meshes need decimation before they go in a game.

## Quality notes (judged on contact sheets, detail view plus a 124 px game-size cell at 1x and 2x)
- Pixal3D and TRELLIS.2 keep thin parts and facial/rib detail (thin staff, skull, ribs, shield planks).
- Hunyuan full is clean but softer: a skull read as a blank head, a staff topper simplified.
- At game size (a 124 px figure) all four local results and the paid reference are hard to tell apart
  in a sketch/ink render. Differences show at 2x.
- Hunyuan turbo (octree 256, 30k tris, paint 6 steps, 1k texture) saved about 55 percent of time
  (roughly 5 min per enemy) and was nearly the same at 1x, but lost fine bone and armour detail at 2x.
  The owner preferred full. Shape settings dominate; texture settings barely show in a look that
  uses albedo luminance only.
- Pixal3D and TRELLIS have no low-detail variant that was tried (quant fixed: Q8 / F16).

## Install notes (Apple Silicon, no Xcode)
- AssetFurnace v0.5.1 (Apache-2.0, github.com/Bingeljell/image-to-3dlab) bundles the backends. Its
  install.sh was read before running: no sudo, downloads only from github.com, huggingface.co and
  astral.sh, venvs inside the folder, no weights without `--yes`.
- Its Pixal3D/TRELLIS Mac routes (`scripts/bootstrap_pixal3d.py`) refuse without Xcode's `metal`
  compiler. Workaround that worked: run its own fetch and patches, then build the C++ runtime
  (`raven38/pixal3d.cpp`, which runs both Pixal3D and TRELLIS.2) with `cmake` from the PyPI wheel
  inside the venv and `-DGGML_METAL_EMBED_LIBRARY=ON`. ggml compiles its Metal shaders at run time,
  so no Xcode is needed. Build took 7 s of compile.
- Pixal3D weights: `bootstrap_pixal3d.py --weights-only --yes`, 8.4 GB (`raven38/pixal3d-sv-q8_0-v1`),
  plus a BiRefNet-lite background remover (224 MB, onnx).
- TRELLIS.2: the PyTorch Mac port (trellis-mac) needs Metal ops plus gated DINOv3 and gated RMBG, so
  it was skipped. The same C++ runtime reads the ungated `ilintar/trellis2-gguf` (F16, about 15 GB,
  DINOv3 included) at `--res 1024`.
- Stable Fast 3D: gated Stability weights, needs a login; skipped, never run.
- Disk after everything: vendor 25 GB, Hunyuan weights 17 GB, venvs about 2.3 GB.
- The wrapper's own note (AssetFurnace `pixal3d_generate.py`, not re-measured by us): the PyTorch
  Pixal3D-mac port loads about 22 GB of bf16 weights and "could not finish on a 32 GB machine at all";
  the C++ runtime runs the same model from 8 GB of Q8_0 weights in about 6 minutes.

## Rigging (SkinTokens, on the Pixal3D meshes)
- 49-74 s each, 4.8-7 GB, run directly on the 947k-tri meshes. Four bipeds rigged and passed
  AssetFurnace's `rig_check` as humanoid (25 to 40 bones). The crawler got a 52-bone rig that
  `rig_check` called not humanoid, and the retarget script refused ("expected 2 legs + 1 spine").
  The paid service also failed the crawler (its biped retarget stood it up). A hand-made squash/roll
  on the hips works for both.
- Bones come out named `bone_0..N`, not Mixamo. A post-step renames by tree role to `mixamorig:*`;
  3 to 7 bones per rig stay `bone_N` (no Neck on some, some fingers; mitten hands have no fingers).
  It is Mixamo-NAMED, not Mixamo-complete: the consumer must tolerate a missing Neck and fingers.
- Moves: Kimodo presets shipped with AssetFurnace (idle 4 s, walk 3 s, sword_swing 2.5 s, cheer 3 s
  used as a cast stand-in, hit_react 2 s, death 3 s, all 30 fps), each retargeted in about 2 s.
  No cast preset; sword_swing is an overhead two-hand swing.
- Caveats seen: the walk has root travel (not in place); rest-pose facing differs between rig and
  mesh by an arbitrary angle, so each clip needs a per-rig yaw bias (45 deg for the Hunyuan rigs, 0
  for Pixal3D); skinning is lumpy on loose cloth and armour. Acceptable at 124 px.
- GLB export is plain glTF with named actions, so a downstream Blender renderer consumed it unchanged.

## Verdict
Local Pixal3D replaced the paid service for static meshes (equal or better, MIT). Rigs: yes for
bipeds, no for the crawler. Moves: partial (generic presets only). Per enemy: $0 and 20-30 minutes
of unattended machine time vs about $1.15 and a few minutes in the cloud. The paid service stays
better for crawler-type rigs, for speed, and for a richer retarget library (chop, cast).
