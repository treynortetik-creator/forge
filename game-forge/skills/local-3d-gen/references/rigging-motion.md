# Rigging and motion options for local game characters (researched 2026-10-23)

Web research, not hands-on, except where marked "ran it". "UNVERIFIED" = not confirmed on a
primary page. Every upstream fact dates from Feb-Oct 2026 and may have moved. Re-check before use.

## What we ran
- SkinTokens (VAST-AI, MIT) through AssetFurnace's bootstrap: `demo.py --input in.glb --output rig.glb --use_transfer`, then a skin-weight clean-up. Python 3.11 venv with torch from PyPI, weights about 1.6 GB (VAST-AI/SkinTokens) plus Qwen3-0.6B config and tokenizer. See `scripts/rigone.sh`. Ran on MPS; no CUDA needed on this route.
- Kimodo preset moves (NVIDIA, SOMA skeleton) retargeted onto the SkinTokens rig by a bone-tree-shape matcher (spine, a chest that forks into neck and two arms, hands with five fingers or none), never by `bone_N` number. Hips travel is scaled by the ratio of hip heights so short characters do not moonwalk. `scripts/merge_actions.py` merges one-clip-per-GLB files into one GLB. The retargeter itself is AssetFurnace's (upstream, Apache-2.0); we edited a copy and do not vendor it.

## Picks from the research (not all run)
| Need | Pick | Note |
|---|---|---|
| Biped rig | SkinTokens (ran it); Mixamo web autorigger as fallback | Mixamo: T-pose humanoids only; FAQ is 2022-era (no royalties, games OK, cannot redistribute raw character/animation files as a product); no 2026 terms page found |
| Odd-shape rig (blob crawler, hound, bat) | Blender hand-rig (Rigify animal metarig or a simple armature + automatic weights) driven through a Blender MCP | SkinTokens non-humanoid classes exist in a one-star community Rust/Metal port (GPL-3.0 sub-crate, untested by us); learned riggers on odd topology are unproven |
| Moves, humanoid | Mixamo library, Rokoko free motion library (150 moves, free for commercial use per two pages) retargeted in Blender; Kimodo presets for fill-ins | Rokoko Create (Apr 2026): 5 free exports a month, commercial terms not stated (UNVERIFIED) |
| Moves, non-humanoid | Keyframe 4 to 8 short loops by script (sine/IK-style crawl, wing flap, quad gait), tuned by eye | No local text-to-motion handles non-humanoids (HY-Motion's card lists them unsupported) |

## Tool notes
- UniRig, Puppeteer, MagicArticulate: need NVIDIA CUDA; no Mac route. SkinTokens' official repo also needs CUDA 12.1 + flash-attn; the Mac route is a port.
- HY-Motion 1.0 (Tencent): community licence excludes EU/UK/South Korea, 1M MAU cap; needs about 24-26 GB VRAM, tight and untested on 32 GB unified memory.
- Kimodo official: NVIDIA only; a Kimodo.cpp port runs Vulkan/CPU (about 34 s CPU for 3 s, Metal not mentioned). The preset moves bundled with AssetFurnace worked with no extra setup.
- Cascadeur: free tier no commercial use; Indie only under $100k revenue/funding.
- Blender automation: ahujasid/blender-mcp (MIT); majidmanzarpour/blender-game-skills (MIT, gated phases: rig weight check, named clips, export reimport) is a useful pattern.

## Still bad at (expect manual work)
Blob crawlers, bat wings and any non-standard topology; loose cloth, hair, tails, wings (auto-skinning shears); heavy-weight attack telegraphs and hit-stop timing (generic and floaty; retime to your gameplay frames); Mixamo clips on odd proportions (foot sliding, clipping).

## Hand-rig for the crawler that auto-rig could not do
A Blender script built the armature from the mesh's own proportions, with IK hands and feet (so a planted limb is world-fixed by construction), automatic weights, then a script pass (distance weights for vertices the solver dropped, 4-bone limit, two smoothing passes, protected cores so a belly and arms cannot tear off). Exported glTF with forced sampling so IK is baked into deform bones, controls omitted. We read its header, not its output frames, for this skill: treat it as a pattern, not a measured result.
