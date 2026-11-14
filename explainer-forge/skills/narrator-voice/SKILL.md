---
name: narrator-voice
description: >
  Give an explainer one consistent, natural narrator voice, locally and free: design 3 candidate voices from written
  descriptions, audition them with the owner, clone the chosen one for every line so it stays the same person, check
  every line with whisper (word errors, pitch, pace), fix pronunciation in a TTS-only spelling, then set the final
  speed once, by ear, when stitching. Uses Qwen3-TTS through mlx-audio on Apple Silicon. Use when asked for "a voice",
  "narration", "voiceover", "TTS for the explainer", "the voice sounds wrong", "make it faster/slower", "fix how it
  says X", or before rendering any narrated explainer.
---

# Narrator voice

The rule: **design once, clone every line, set speed once.** A voice designed fresh per line is a different person
each time (pitch spread 4.1 semitones, 174-258 wpm across three lines); cloned from one reference it is one person
(2.7 semitones, 146-194 wpm). Stock presets and dramatic reads were rejected by the owner. Numbers and method:
`${CLAUDE_PLUGIN_ROOT}/references/voice.md`.

Scripts (in `${CLAUDE_PLUGIN_ROOT}/scripts/voice/`, run with the voice venv's python from a working folder such as
`voice/`): `design_voices.py`, `render_lines.py`, `analyze_clip.py`, `drift_test.py`, `voice_common.py` (settings).
Overrides: a `voice.json` in the working folder (`${CLAUDE_PLUGIN_ROOT}/templates/voice.example.json`).

## 0. Setup (once, about 5 min plus model download)

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python mlx-audio mlx-whisper librosa soundfile
```
Apple Silicon only. Elsewhere, use any TTS that can clone one reference for every line and write `out/<id>.wav`.

## 1. Voice spec (before any audio)

Write who the narrator is: accent chosen on purpose (default neutral General American, never a default British),
age, pitch range, texture, pace, and what to avoid ("not bubbly, not dramatic, not announcer-like, not breathy").
Three candidates that differ on ONE axis (pitch, brightness, gender) beat three random ones.

## 2. Audition: 3 candidates, the owner picks (about 10 min)

```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/design_voices.py --out .
```
Send `samples/candidate-A/B/C.m4a`, labelled, with one line each on how they differ. The owner picks by ear;
`samples/report.json` only rules out broken takes (high WER, odd pitch). Optional: `drift_test.py` proves the clone
holds steady. **If the owner has an approved reference clip already, skip to step 3 with it.**

## 3. Render every line in the chosen voice (about 3 min for 33 lines)

```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/render_lines.py ../lines.json --voice A --ref-dir ref --out out --check
```
Natural pace, no trim: speed is set in step 5. Read every `hyp` in `out/check.json`; WER over 0.10 is flagged.
Words you did not write = a hallucination: reword or re-render (`--only <id>`).

## 4. Pronunciation (the owner listens)

Ask how each product name is said BEFORE rendering. Fix only in `text` (captions keep `caption`): respell by syllable,
spell out acronyms with spaces, swap homophones, give very short lines a few more words. Whisper cannot confirm a
pronunciation: play the line to the owner.

## 5. Speed: set once, by ear

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stitch_narration.py --lines lines.json --clips voice/out --out build --target-wpm 180
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stitch_narration.py ... --tempo 1.5     # "make it 50% faster" from the first render
```
One pitch-preserving tempo for every clip. Start at 180 wpm (the approved pace, about 1.5x a first cut that was
called "a snail"), play 30 seconds to the owner, adjust. Tempo over 1.25 is flagged: listen for clipped words.

## Gotchas

- Pace words in the prompt ("slow") barely move pace. Do not iterate the prompt for speed.
- Same text + same reference + same model, precision and seed = identical audio. Changing any of them changes the
  voice: pin them in `voice.json` and keep the reference WAV with the project.
- A quantised model (6-bit, 8-bit) will not reproduce bf16 output exactly.
- Never clone a real person's recording without their written consent; never commit reference clips to a public repo.
- Very short lines garble ("That's the uh..."). Add words.
