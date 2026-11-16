# Changelog

## 2026-11-16

### explainer-forge 0.1.2

- `references/lessons.md`: new section "Drawn character animation" (rules 27-44) from a 2-minute clay-style story film: shared kit and cast sheets first, props on the scale chart, screen direction in the shot list, drawn poses instead of code motion on one drawing, usage limits checked before a fan-out, prompts and assembly commands kept in the project, frame-strip proof plus a ranked review, stopping at SHIP, and recording narration in one take. Documentation only; no script changes.

## 2026-11-14

### explainer-forge 0.1.1

Bundles a default narrator voice, so a new explainer can skip voice design and audition.

- `voices/default-narrator/`: `reference.wav` (33 s, mono 24 kHz) + `reference.txt`, a 29 s `sample.m4a` at the approved 180 wpm, and a README with the model (Qwen3-TTS 1.7B Base, Apache-2.0), settings and the exact render command. The voice is designed from a text description; no real person's voice was recorded or cloned.
- `narrator-voice`, `references/voice.md`, README and `voice.example.json` now name the bundled voice as the default; audition-and-design stays as the alternative. No script changes.

### explainer-forge 0.1.0 (new)

Five skills from two real explainer runs: a set of narrated interactive explainers, and a product-demo video approved on its second cut.

- `make-an-explainer`: the ordered recipe with gates (length cap, fact-checked script, style sample first, voice spec and cost plan before spend, proof before send).
- `narrator-voice` (design three candidates, the owner picks, clone every line from one reference, whisper/pitch/pace check, TTS-only respellings, one tempo set by ear; approved pace about 180 wpm), `app-footage` (sample data with a badge, fake cursor, human-paced typing, time-lapsed waits, a manifest, tracked patches), `render-and-caption` (cue-exact stitch, word-timed captions and SRT, seek-per-frame MP4 render, one-file HTML), `explainer-proof` (2-second review sheets, ring crops, A/V sync under 50 ms, names grep, deck tests).
- Scripts are generalised from the two runs' tooling; no voice reference clips, model weights, brand assets or footage are included. Python compiles, JavaScript passes `node --check`, shell passes `bash -n`; not yet run end to end on a fresh project.

## 2026-11-12

### game-forge 0.1.0 (new)

Ten skills from building a Phaser 4 roguelite and a Phaser 3 tower-defense game with Claude Code agents.

- `build-a-game`: the end-to-end tutorial. Fourteen ordered phases from stack research to a shipped demo, each with the skill to load, a measured done-gate and the top traps, plus the agent team workflow, the trailer method and how to add a lesson.
- `game-lessons` (architecture, Phaser 4 traps, game feel, agent workflow, shipping), `game-qa-loop` (CLI, tiered bots, headless screenshots, proof ladder, perf, feedback loop, highlight reel), `sprite-pipeline-3d` (Blender bake to 8-direction sprites with gates), `local-3d-gen` (Pixal3D and TRELLIS.2 on Apple Silicon), `local-models` (the free local model menu with licences), `art-waves` (batched 2D art with `art-measure`, `palette-audit` and a taste file), `levels-and-backgrounds` (room templates, layered backgrounds, tower-defense levels), `typography` (pen-writer hands and font gates), `game-audio` (voice casting, music gates, loudness).
- Scripts are generalised from the two games' tooling; no third-party code or model weights are vendored. Smoke notes per skill are in the README: Blender, sharp and Python scripts were run on synthetic inputs, audio packers and several gates were syntax-checked only.

## 2026-10-14

### music-forge 0.3.0

Lessons from producing a 3:39 music video end to end (about 60 paid clips, three rounds of notes), folded into `music-video`.

- **Routing by shot type** (`data/model-routing.json`, checked 2026-10-14 against the live model list): sung close-ups to HeyGen Video 1 with the vocal stem, sung wides and instrumental band shots to Hailuo 3 with the full mix or an instruments-only mix, silent emotional acting to Hailuo 3 Max, action and state changes to Seedance 2.5, everything else to Seedance 1.5 Pro at 480p. New optional shot fields `framing`, `kind`, `audio_ref` and a plan-level `stems` map; `plan_check.py` validates them.
- `build_clips.py`: per-shot audio reference (song, a stem, or a file such as a TTS line for a mouthed spoken line); instrumental shots can take audio without `sing`; the sidecar records the audio window; refusal hint now points at a model override.
- New `sync_offset.py`: cross-correlates a sung clip's own soundtrack against the stem or song it was made from and writes the song time at its first frame to the sidecar. `cut.py` enters each measured clip at that offset (`--no-sync` to ignore).
- New `chain_join.py`: `last-frame`, `align` (scale/shift registration, colour match, duplicate frame dropped, 2-frame dissolve, `--dedupe` for padded frames), `check` (join frame-difference profile).
- New `post_sweep.py`: camera sweep in post (per-frame push-in plus cosine-eased pan), free and deterministic.
- `SKILL.md`: routing table, an 11-point "Hard-won rules" section, a sync/chain/sweep step, review discipline (strips, one retry per shot, note rounds, canon list, per-round budgets). Depth in new `references/` (routing, prompt rules, sync and chaining, post).
- Tests: `test_post_tools.py` (7), plus sync-offset and audio-reference cases in `test_cut.py` and routing cases in `test_plan_check.py`.

## 2026-10-13

### music-forge 0.2.1

- `lyric_meter.py`: syllable counts are now ranges when a word has more than one dictionary pronunciation (fire 1-2,
  every 2-3, hour 1-2); the flexible words are listed after the line with `≈`. Repeated-section parity flags only when even
  the closest pronunciation misses.
- New beat match: each repeated-section line pair reports the share of stressed/unstressed slots that agree (best of start-
  or end-aligned). Under `--stress-min` (default 0.6) it is flagged when the syllable counts already fit, because equal counts
  can still put the beats in different places.

## 2026-10-12

### music-forge 0.2.0

- music-forge 0.2.0: lyric-forge renamed and folded in; new music-video and track-check skills.
- `music-video`: shot plan, `plan_check.py`, still prompts, `build_clips.py` (OpenRouter video models, routing table in
  `data/model-routing.json`, resumable, `--dry-run`, `--max-usd`, opt-in `--audio-refs`), frame-exact `cut.py`, `review_frames.py`,
  `teasers.py`. `track-check`: `song_scan.py` and `voice_match.py`. `lyric-writer` and `sung-vs-written` are unchanged.
- Install name changes from `lyric-forge@forge` to `music-forge@forge`; uninstall the old one.

## 2026-10-11

### lyric-forge 0.1.0 (new)

- New plugin for writing lyrics for AI music generators. **`lyric-writer`** skill: brief, draft, measure, critic pass
  against a 13-point checklist, up to three revision passes, Suno-ready output block. **`sung-vs-written`** skill:
  separate vocals (Demucs), transcribe (whisper.cpp or faster-whisper), align to the written lyrics, flag lines
  worth a listen.
- Scripts: `lyric_meter.py` (syllables, stress, repeated-section drift, rhyme classes, title and echo checks,
  cliche scan), `rhymes.py` (Datamuse, cliche-filtered), `sung_check.py`, plus tests and a fictional fixture.
- Genre guides load from `references/genres/`; `emo-pop-punk.md` is a full guide (29 songs studied), and `lyric_meter.py --genre emo-pop-punk` runs its measurable norms as a PASS/WARN GENRE CHECK.
- Credits: adapted from bitwize-music-studio/claude-ai-music-skills (CC0); ideas from NuNaught (Apache-2.0)
  and Hermes (MIT). See `music-forge/NOTICE.md`.
- Root README and marketplace updated: four plugins became five.

## 2026-10-01

### design-forge 0.5.0

- **Removed** the `clean-export`, `de-sloppifier` and `voice` skills, and the `references/writing/` notes that
  only they used. They were duplicates of story-forge's skills, had drifted, and collided by name when both
  plugins were installed. **Prose editing now lives in story-forge only**: install it with
  `claude plugin install story-forge@forge`.
- design-forge docs that pointed at those skills (README, THIRD-PARTY-NOTICES, `doctor.sh`, `design-audit`,
  `art-department` house style, `mechanisms.md`) now point at story-forge.
- `photo-to-3d-loop`: picked up the 2026-08-19 controlled-trial results (per-part numeric feedback beats
  visual-only about 4x, tag the best iterate, IoU is a trend tracker not a gate, structural mesh checks)
  and the corrected VIGA attribution. These edits had only ever existed in a locally installed copy.

### story-forge 0.2.4

- story-forge's `clean-export`, `de-sloppifier` and `voice` are now the single canonical copies. They already
  contained every improvement from design-forge's copies (the design-forge side had only drifted behind:
  wikilink syntax that does not resolve in a plugin, the older `voice` flow without register sampling, and no
  `edit_diff.py` post-pass safety check).
- Version bump so `claude plugin update` picks up the repo state.
