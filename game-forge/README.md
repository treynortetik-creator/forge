# game-forge

Build a game with Claude Code agents: a deterministic sim you can test headless, 3D models baked to 2D sprite sheets, free local image-to-3D and asset models on Apple Silicon, batched art from an image model with measured gates, levels and backgrounds as data, typography and handwriting effects, voice casting before paid generation, and the lessons from shipping a Phaser roguelite and a tower-defense game.

It follows the Forge rule: **judgment stays with the model, and anything expressed as a number gets measured instead of eyeballed.** The owner and the model decide whether art, feel and text are right. Scripts say what the outline width, loop seam, loudness, frame time and palette share are. An agent's "done" is a claim until the gate has run and someone has opened the PNG.

Every rule in these skills carries the failure that earned it. The two games were not open-sourced into this plugin: the process, the generalised scripts and the numbers are here, the story, characters and art are not.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install game-forge@forge
```

Restart the session or `/clear` so the skills load. Start with `build-a-game`; it tells you which other skill to load at each phase.

## Ten skills

| Skill | Use it when |
|---|---|
| **build-a-game** | you are starting or planning a game. The end-to-end tutorial: fourteen ordered phases from stack research to a shipped demo, each with the skill to load, a measured done-gate and the top traps, plus the agent team workflow and how to add a lesson |
| **game-lessons** | you want the cross-cutting playbook: pure-sim architecture, Phaser 4 traps, game feel tables, gamepad-first input, clarity passes, the agent workflow, budgets tied to real constraints, shipping and Steam scoping, tower-defense lessons |
| **game-qa-loop** | you need to prove a browser game works without watching it: CLI, tiered bots, headless Chrome screenshots, a proof ladder, perf budgets, a one-heavy-job lock, the feedback-to-repro loop, demo video and highlight reel |
| **sprite-pipeline-3d** | characters and enemies need 8 directions: a rigged 3D model baked headless in Blender with a toon or engraved look, snapped to a palette, gated by height, feet, seam and penetration checks, packed into atlases |
| **local-3d-gen** | you want concept art turned into a mesh at $0 on an Apple Silicon Mac: Pixal3D as default, TRELLIS.2 as backup, untilt, decimate, auto-rig, and what each licence allows in a shipped game |
| **local-models** | you want to know what runs locally and what may ship: Qwen-Image, an image judge, Qwen3-TTS and Kokoro, ACE-Step music, Parakeet and whisper.cpp, with licence, RAM and speed per entry |
| **art-waves** | you produce 2D art in batches with an image model: wave brief, zip handoff, return check, cut-outs, ink redraw, `art-measure` and `palette-audit`, a taste file, labelled proofs, caps that trace to a real constraint |
| **levels-and-backgrounds** | you design rooms or levels: ASCII room templates built by script, layered backgrounds, hub scenes, seam healing, slot measuring, tower-defense paths, build pads and a wave DSL |
| **typography** | a game needs handwriting, a pen-writes-this effect, an own font, title cards or UI webfonts that never block boot: `build_hand.py` with coverage and HarfBuzz-drift gates |
| **game-audio** | you are about to spend on voice or music: casting with a measured pitch audit, directed voice, a cost plan and licence check, packing under caps, music with BPM, key, seam and LUFS gates, a Web Audio engine that respects autoplay |

From design-forge, linked rather than duplicated: `photo-to-3d-loop` (a real object from photos) and `art-department` (the visual-deliverable playbook).

## Requirements

Nothing is vendored: no third-party code, no model weights. Install what the skill you use needs.

| Skill | Needs |
|---|---|
| build-a-game | nothing; it is a checklist over the others. The trailer step uses `ffmpeg` and ImageMagick |
| game-lessons | `node` for `purity-check.mjs` and `gamepad-detect.ts` (TypeScript, run with your project's toolchain); `bash` for `heavy-lock.sh`. No API keys |
| game-qa-loop | `node`, a project with Vite and Vitest, Chrome or Chromium plus `puppeteer-core` for screenshots and screencasts, `ffmpeg` on PATH for recording and cutting. No API keys |
| sprite-pipeline-3d | Blender 5.x (smoked on 5.2.0 LTS), `node` plus `npm i sharp` for finishing and gates, Python 3 for the gate scripts |
| local-3d-gen | Apple Silicon Mac with 32 GB, about 25 GB of vendor code and weights, `cmake`, `uv`, Blender for untilt and decimation. An optional paid cloud 3D service is the last fallback; the skills do not name its key variable |
| local-models | Apple Silicon Mac with 32 GB, `uv` with Python 3.13 (3.12 for ACE-Step) and `pillow<13`, large first-run downloads (Qwen-Image weights 33 GB). Nothing needs a key |
| art-waves | Python 3 with Pillow below 13, numpy and scipy (`uv run --with` works). An image model, either through an app you drive by hand or an API; no script here calls one |
| levels-and-backgrounds | Python 3 with Pillow; `node` plus `npm i sharp` for seam and slot tools. Optional paid image model for painted layers; no script here calls one |
| typography | Python 3 venv with the pinned `requirements.txt` (fonttools, freetype-py, numpy, pillow, scikit-image, scipy, uharfbuzz) |
| game-audio | `ffmpeg`; Python with numpy, scipy and `praat-parselmouth`; `node` with `npx tsx` for the packers. Optional paid voice: `ELEVENLABS_API_KEY` (read from the environment, never printed) |

Chrome for puppeteer is only needed for the skills that screenshot or record a running game. Paid steps always come with a cap and a dry-run in their skill; over about $1, ask first.

## Layout

```
game-forge/
  .claude-plugin/plugin.json
  skills/
    build-a-game/            SKILL.md
    game-lessons/            SKILL.md  references/  scripts/
    game-qa-loop/            SKILL.md  references/  scripts/
    sprite-pipeline-3d/      SKILL.md  references/  scripts/
    local-3d-gen/            SKILL.md  references/  scripts/
    local-models/            SKILL.md  references/  scripts/
    art-waves/               SKILL.md  references/  scripts/
    levels-and-backgrounds/  SKILL.md  references/  scripts/
    typography/              SKILL.md  references/  scripts/
    game-audio/              SKILL.md  references/  scripts/
```

## What was and was not tested

Every skill's own smoke notes are the source for this list. "Smoked" means run once here on a small or synthetic input; none of it was run against a full game in this repo.

**Run here**
- `sprite-pipeline-3d` (Blender 5.2.0 LTS, Node 24 + sharp): the stand-in mannequin, the bake in toon and hatch looks (3 directions of idle and run, 48 frames in 15 s), the finish step, and the gates `clipstat`, `loopseam`, `looknum`, `sheet`, `linewidth`. `penetration_check.py` exits 1 over its limit. Frames were viewed.
- `typography`: `build_hand.py` on an OFL script font built to 121 glyphs with coverage min 99.96%, drift 0.0000 em, about 19 s, exit 0; a forced stricter gate printed `GATE FAILED` and exited non-zero.
- `levels-and-backgrounds`: `py_compile` on every Python file; the room draft, check (exit 1 on an unreachable or stray-floor draft), mirror and preview chain; `heal_seam.mjs` and `measure_slots.mjs --expect` (pass and fail exit codes) on synthetic images; `glow_points.py`, `td_level.py` and `wave_dsl.py` on small inputs.
- `game-qa-loop`: `node --check` and `bash -n` on its scripts; `cut-reel.sh` on synthetic clips (including the size-gate failure); `record-reel.mjs` and `perf-sample.mjs` once each against a trivial local page.
- `game-lessons`: `heavy-lock.sh` (the one shared copy; acquire, release on success and failure, usage exit 2), `purity-check.mjs` and `gamepad-detect.ts` are smoked, per the skill.
- `art-waves`: the scripts were smoke-tested with plain `python3 -I` (Pillow 12.2, numpy 2.5, scipy 1.18).

**Syntax-checked only, or not run**
- `game-audio`: `voice-f0.py` only to `py_compile` and its missing-dependency error; `loopcut.py` `--help`; `lufs-check.sh` `bash -n`; the voice packers type-strip checked, not executed. None ran against a real project.
- `sprite-pipeline-3d`: `chainstat.mjs` and `fitlut.mjs` syntax-checked only; `stride.py` ran but the stand-in has no planted foot, so a real run cycle is untested; `.fbx` input, multi-mesh hatch, real auto-weights and a 100k-triangle mesh were not exercised. The face-occlusion gate was never generalised.
- `art-waves`: the `uv run` invocation of `art-measure.py` is copied, not re-run; `ink-redraw.py` is described, not vendored.
- `local-models` and `local-3d-gen`: the numbers are measurements from the original machine (MacBook Pro M5, 32 GB) on 2026-10-22 to 23, not re-run here. ACE-Step's pinned-tempo path and its output quality are untested (never listened to). Several licence rows say "per listings" or "not recorded": read the model card before shipping. Multi-view Pixal3D was not tested; Stable Fast 3D was never run.
- `build-a-game`: the trailer step describes a capture tool and a cut script that were read, not executed.

**Time-sensitive.** Steam rules and dates were checked 2026-10-19, model and licence notes in October and November 2026. Re-verify before acting.

## Licence

MIT. Fonts, models and tools the skills point to carry their own licences; each skill's Licences section says which allow shipping.
