# Licence table (from the bake-off, 2026-10-23; plain English, not legal advice)

Read the LICENSE and model card yourself before shipping. Copies of the texts were saved while
researching; keep them with anything you redistribute.

| Component | Code | Weights | Outputs (your meshes) | Commercial | Territory limits |
|---|---|---|---|---|---|
| Pixal3D (TencentARC) + pixal3d.cpp runtime (raven38) | MIT | MIT; notes TRELLIS.2 MIT, DINOv2 Apache-2.0 | no claim by licensor | yes | none |
| DINOv3 encoder inside Pixal3D and TRELLIS.2 (Meta) | n/a | DINOv3 License: free, worldwide, royalty-free; redistribution must carry the licence; no ITAR, military, weapons or sanctioned end uses; no reverse engineering; ends if you sue Meta over it | Meta disclaims output ownership claims | yes, no revenue cap | none, but US/UN/EU/UK trade controls apply |
| TRELLIS.2 (Microsoft), via ilintar GGUF | MIT | MIT (4B), plus DINOv3 above | no claim | yes | none |
| Hunyuan3D 2.0 / 2.1 (Tencent) | MIT (one MLX port); Tencent Community Licence (another port) | Tencent Hunyuan 3D Community Licence | clause 3(c): do not use, display or distribute the Works or Output outside the Territory; Output may not improve other AI models | yes inside Territory, if monthly active users < 1 million | **Territory excludes the EU, UK and South Korea; Output use there is "unlicensed"** |
| Stable Fast 3D (not run, gated) | Stability AI Community Licence | same | n/a | free under $1M annual revenue, enterprise licence above | none stated |
| SkinTokens auto-rig (VAST-AI) | MIT | MIT | rig and skin weights are yours | yes | none |
| Kimodo SOMA preset moves (NVIDIA) | Apache-2.0 | NVIDIA Open Model License, card says ready for commercial use | NVIDIA claims no ownership | yes | none stated |
| Tripo (reference) | cloud service | n/a | per Tripo terms | paid credits | n/a |

Plain read: the Pixal3D chain (Pixal3D + DINOv3 + SkinTokens + Kimodo SOMA) has no territory limit
and no revenue cap; the conditions are to keep licence texts and notices with anything
redistributed, and DINOv3's trade-control/no-weapons clause (an ordinary game is fine). Hunyuan is
the only generator with a territory carve-out and a user cap, which rules it out for a game sold
worldwide. Confirm the DINOv3 and NVIDIA text once before shipping.

Research-only traps found while surveying motion tools (see rigging-motion.md): Kimodo's SMPL-X
checkpoint (use SOMA), GVHMR/WHAM/SMPL-X video-to-motion, AMASS-trained text-to-motion weights
(secondary reading, unverified per model), Cascadeur Free (no commercial use).
