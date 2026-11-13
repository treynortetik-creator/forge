---
name: local-3d-gen
description: >
  Image-to-3D on an Apple Silicon Mac for game props and enemies, at $0: which generator to use
  (Pixal3D won a five-way bake-off, TRELLIS.2 is the backup, Hunyuan3D is out on licence, a paid
  cloud service is the last fallback), how it was installed without Xcode, run, timed and retried,
  how to prepare the input image, untilt and decimate the mesh, auto-rig bipeds, and what the
  licence table allows in a shipped game. Use when someone asks to turn concept art into a 3D
  model locally, replace a paid 3D credit spend, rig an AI-generated mesh, or pick a 3D generator.
  Triggers: "image to 3D", "local 3D generation", "Pixal3D", "TRELLIS", "Tripo alternative",
  "auto-rig", "SkinTokens", "generate a prop mesh", "3D from concept art on a Mac".
---

# Local image-to-3D on a Mac

**The one-line case:** a 2026-10-23 bake-off on a 32 GB M5 ran five enemies through four local
generators; **Pixal3D won** (MIT code and weights, thin parts survive, 5 to 16 minutes, 4 to 8 GB),
and over the next two days it produced **25 of 26 prop and centrepiece meshes on the first try** for
a roguelite, at $0 and zero paid credits. The one miss needed the backup generator.

> House thesis, applied: judgment (does this mesh read at game size?) stays with a human or a
> critic looking at a render; anything numeric (time, peak RAM, tris, pitch angle) is measured and
> logged per run, never eyeballed. Tools below log a receipt for every job.

Siblings: the next stage (mesh to sprite sheets, ink/sketch look, 8 directions) is
`game-forge:sprite-pipeline-3d`. Modelling a real object from photos is
`design-forge:photo-to-3d-loop`. Free local images/audio are `game-forge:local-models`.

## Pick a generator (measured, 5 enemies, 32 GB M5)

| | Pixal3D | TRELLIS.2 | Hunyuan3D 2.0 | Paid cloud (Tripo) |
|---|---|---|---|---|
| Role | **default** | backup | **do not ship** | last resort |
| Time per enemy | 312 to 985 s | 490 to 2586 s | 501 to 602 s (turbo 223 to 254 s) | minutes, cloud |
| Peak RAM | 3.9 to 8.3 GB | 4.3 to 10.7 GB | about 10 GB | none |
| Raw tris | about 950k | about 285k | 300k (turbo 30k) | 100k after our decimation |
| Fidelity | best: staff, skull, ribs, planks kept | about as good | softer, skull went blank | good, blobbier at 2x |
| Licence | MIT + DINOv3 | MIT + DINOv3 | **excludes EU, UK, South Korea** | per vendor terms |
| Cost | $0 | $0 | $0 | about 115 to 125 credits ($1.15 to $1.25) per rigged enemy, about 40 credits ($0.40) per prop |

Stable Fast 3D was never run (gated Stability weights, needs a login). Full tables, install notes
and quality notes: `references/bakeoff-report.md`. Licences: `references/licences.md`.

## Workflow

### 0. Install once (about 25 GB of vendor code and weights, plus venvs)
1. Clone AssetFurnace (Apache-2.0, `github.com/Bingeljell/image-to-3dlab`, v0.5.1 was used). Read
   `install.sh` first. It runs without sudo and downloads only from github.com, huggingface.co and
   astral.sh.
2. **No Xcode?** Its `scripts/bootstrap_pixal3d.py` refuses without Xcode's `metal` compiler. We ran
   its fetch and patches, then built the C++ runtime (`raven38/pixal3d.cpp`, runs both Pixal3D and
   TRELLIS.2) with `cmake` from the PyPI wheel inside the venv, `-DGGML_METAL_EMBED_LIBRARY=ON`.
   ggml compiles Metal shaders at run time; the compile took 7 s.
3. Pixal3D weights: `scripts/bootstrap_pixal3d.py --weights-only --yes` (8.4 GB, Q8_0).
4. TRELLIS.2 backup: the same runtime reads the ungated `ilintar/trellis2-gguf` (F16, about 15 GB).
5. Rigging: AssetFurnace's autorig bootstrap clones SkinTokens into `vendor/SkinTokens`, makes a
   Python 3.11 venv, downloads about 1.6 GB of weights.

### 1. Prepare the input image
- 1024x1024 PNG, flat single-colour background (we used `#BFBFBF`), three-quarter view, limbs
  apart, held props clear of the body, no glow or smoke. Ask the art source for exactly that.
- **Cut it to a real matte yourself:** `python3 -I scripts/cut_grey_bg.py in.png out-rgba.png`
  (border flood-fill of the exact background colour). 
- Never rely on an image generator's alpha channel (see Traps).

### 2. Generate (one job at a time)
```bash
./scripts/runone.sh px-urn  python3 vendor/.../scripts/pixal3d_generate.py \
    in-rgba.png runs/px-urn.glb --res 1024 --seed 1
```
- `--res` is 1024 only on the single-view weights. `--seed N` is the retry lever. `--gss` is
  structure guidance (wrapper default 10; the raw CLI default 7.5 dropped a sword blade, 13 made thin
  parts detach). `--steps` lowers sampling steps only if the build was patched for it.
- Many props in a row: `scripts/queue.sh <pixal3d_generate.py> inputs/ runs/ name1 name2 ...`
  (skips finished outputs, optional lock so a Blender bake waits its turn).
- TRELLIS.2 backup: `trellis-cli in-rgba.png out.glb --models <vendor>/pixal3d-cpp/models/trellis2-f16 --res 1024`.
- Output is textured, about 950k tris and 36 to 41 MB. It must be decimated before a game sees it.

### 3. Retry policy (what actually happened)
The decision on 2026-10-23: run locally first, **2 to 3 reruns before any paid fallback**, paid
spend only with the owner's explicit yes. In practice:
1. Rerun with a new `--seed` (and `--gss 10` to `12`, `--steps 12`).
2. If **three** Pixal3D runs lose the same feature, change generator (TRELLIS.2), do not run a
   fourth seed. Evidence: one prop lost its bone and crack in all three Pixal3D runs (seed 1; seed 2
   with gss 10; seed 5 with gss 12 and 12 steps; 1292 + 1385 + 1811 s), then TRELLIS.2 got it in
   3396 s. A repeated miss means the model misreads that image, not bad luck.
3. Only then flag the paid service to the owner with the cost. Spend on this prop set: 0 credits.

Receipts: 10 props in wave 14, 9 first try; 3 of 3 and 13 of 13 centrepieces first try. Time per
mesh 263 to 1526 s and 3.6 to 8.4 GB peak, slow whenever another builder shared the machine.

### 4. Stand it upright, then decimate (both in headless Blender)
```bash
blender -b --factory-startup -P scripts/untilt_glb.py   -- runs/px-urn.glb up.glb -22 0
blender -b --factory-startup -P scripts/decimate_glb.py -- up.glb game.glb 30000 1024
```
- Single-view Pixal3D keeps the source camera's pitch, so a vertical prop **leans**. Measured by PCA
  of the vertices: 17.5 deg on one urn, about 22 on most. A TRELLIS.2 mesh of the same kind came
  out nearly upright (+6.8). Measure per prop. For slabs, biers and boxes pass yaw `auto` (turns the
  footprint's long axis onto X; they reconstruct yawed about 30 deg).
- Targets used: 30,000 tris for static props, about 100,000 for rigged characters, 1024 px albedo
  for props. Triangles never reach the final sprite, but a 1M-tri mesh makes every Blender frame slow.

### 5. Rig bipeds (optional; skip for props)
```bash
SKINTOKENS=vendor/SkinTokens CLEAN_WEIGHTS=<assetfurnace>/scripts/clean_skin_weights.py \
  ./scripts/rigone.sh name runs/px-name.glb      # about 50 to 75 s, 5 to 7 GB
```
- 4 of 4 bipeds rigged and passed the humanoid check (25 to 40 bones). The bloated crawler rigged
  but failed the check and the retarget refused; the paid service failed it too. Hand-rig non-bipeds.
- Bones come out `bone_0..N`; map to Mixamo names by tree role (3 to 7 stay `bone_N`), so the
  consumer must tolerate a missing neck and fingers.
- Moves: Kimodo presets bundled with AssetFurnace (idle, walk, sword swing, cheer, hit react,
  death; 30 fps; about 2 s per retarget). No cast or chop; for those use the paid library, Mixamo or
  Rokoko clips, or hand animation. Merge per-clip GLBs with `scripts/merge_actions.py`.
- Options, licences and what is still bad: `references/rigging-motion.md`.

### 6. Hand off to the bake
Decimated, upright GLBs go to `game-forge:sprite-pipeline-3d`. Gate every asset on a rendered
image at the real game size, looked at by a person or a fresh critic (`game-forge:art-waves`).

## Traps (each with the failure that earned it)
- **An alpha channel is not a matte** (receipts from the AssetFurnace wrapper's own notes). An image generator wrote RGBA whose alpha was opaque noise
  and the generator read it as "already cut out". A grey backdrop left in came back as two huge white
  sheets beside a fox's head. Matte it yourself, or force `--matte`.
- **Do not run two heavy jobs at once.** RAM binds first on 32 GB. Three local AI models loaded at once
  froze a 32 GB Mac (2026-11-12; language and speech models, not 3D, same lesson). A Blender bake beside a generation slows both; use one lock.
- **Check the Xcode assumption before declaring the Mac route dead.** The bootstrap said it needed
  Xcode; the runtime did not. Same for "TRELLIS needs gated weights": an ungated GGUF existed.
- **Thin parts vanish at default guidance.** Raw CLI `--gss 7.5` dropped a sword blade; the wrapper
  default is 10. Still check the render: a bone and a crack were lost on every Pixal3D seed.
- **The glTF importer leaves objects in quaternion mode.** `rotation_euler` is silently ignored
  until `rotation_mode = 'XYZ'` (baked into `untilt_glb.py`).
- **Download-time hazards.** A third-party bootstrap began cloning a repo we did not want; we killed
  it by closing its pipe and deleted the leftover. Read installers; never pass `--yes` blind.
- **Rest-pose facing differs from the mesh by an arbitrary angle.** Find a per-rig yaw bias on one
  test frame (we needed 45 deg for one generator's rigs, 0 for Pixal3D).
- **Fast modes look equal at 1x and lose detail at 2x.** If the game ships 2x assets, judge at 2x.
- **Pixal3D output is 36 to 41 MB per mesh.** Keep raw meshes out of the repo.

## Licences and cost
- Pixal3D + DINOv3 + SkinTokens + Kimodo SOMA: no territory limit, no revenue cap; keep licence
  texts with anything redistributed; DINOv3 bars weapons/military and sanctioned end uses.
- **Hunyuan3D: Territory excludes the EU, UK and South Korea. Do not ship it in a game sold
  worldwide.**
- This is a plain-English reading, not legal advice. Confirm the DINOv3 and NVIDIA texts once.
- Paid fallback costs: about 40 credits per static prop; for a rigged enemy 40 (image to model) + 25
  (rig) + 60 (three retargets) = 125 credits, about $1.25 (a 440 credit spend covered one wave of
  enemies; a hard cap was set per wave). Always get an explicit yes first.
- Not tested: multi-view Pixal3D (needs a `--back` picture and separate weights), Pixel Match
  reprojection, a cross-generator mesh+texture mix.
