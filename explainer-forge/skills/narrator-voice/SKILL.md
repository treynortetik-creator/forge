---
name: narrator-voice
description: >
  Give an explainer one consistent, natural narrator voice, locally and free: design 3 candidate voices from written
  descriptions, audition them with the owner, clone the chosen one for every line so it stays the same person, check
  the whole script as ONE take (per-line is the named fallback), check it with whisper (word errors, pitch, pace),
  fix pronunciation in a TTS-only spelling, then set one uniform tempo to a measured pace. Uses Qwen3-TTS through mlx-audio on Apple Silicon. Use when asked for "a voice",
  "narration", "voiceover", "TTS for the explainer", "the voice sounds wrong", "make it faster/slower", "fix how it
  says X", or before rendering any narrated explainer.
---

# Narrator voice

The rule: **design once, clone from that one clip, record the whole script in ONE take, set one tempo.** A voice
designed fresh per line is a different person each time (pitch spread 4.1 semitones, 174-258 wpm across three lines);
cloned from one reference it is one person (2.7 semitones, 146-194 wpm); and one take for the whole script also removes
the timbre shift at line and scene joins (house rule V1). Stock presets and dramatic reads were rejected. Numbers and
method: `${CLAUDE_PLUGIN_ROOT}/references/voice.md`.

Scripts (in `${CLAUDE_PLUGIN_ROOT}/scripts/voice/`, run with the voice venv's python): `one_take.py` (default route),
`design_voices.py`, `render_lines.py` (fallback), `analyze_clip.py`, `drift_test.py`, `voice_common.py` (settings).

**Bundled voices** (both synthetic, designed from a text description, no real person):

| Folder | Voice | Seed | Sample |
|---|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/voices/coworker-baritone/` | warm lower baritone, a man | 7 | 13.6 s at about 207 speaking wpm |
| `${CLAUDE_PLUGIN_ROOT}/voices/default-narrator/` | mellow mid-range alto, a woman | 42 | 29 s at about 180 wpm |

Overrides: a `voice.json` in the working folder (`${CLAUDE_PLUGIN_ROOT}/templates/voice.example.json`).

## 0. Setup (once, about 5 min plus model download)

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python mlx-audio mlx-whisper librosa soundfile
```
Apple Silicon only. Elsewhere, use any TTS that can clone one reference and read the whole script in one request.

## 1. Voice spec (before any audio)

Write who the narrator is: accent chosen on purpose (default neutral General American, never a default British),
age, pitch range, texture, pace, and what to avoid ("not bubbly, not dramatic, not announcer-like, not breathy").
Three candidates that differ on ONE axis (pitch, brightness, gender) beat three random ones.

## 2. Audition: both bundled samples plus three candidates; the owner picks by ear

Send BOTH bundled samples (a man and a woman) labelled, and, if the format has no settled voice, three designed
candidates (`design_voices.py` yields A and B women, C a man):

```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/design_voices.py --out .
```
Send `samples/candidate-A/B/C.m4a`, labelled, with one line each on how they differ. The owner picks by ear;
`samples/report.json` only rules out broken takes. If the owner already has an approved reference clip, use it. If a
bundled voice is picked, skip design: copy its `reference.wav` and `reference.txt` into the project.

## 3. Record the whole script in one take (the default)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/make_narration.py script.md --out narration.json --say-map saymap.json
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/one_take.py --narration narration.json --out audio/take-raw.wav
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/take_check.py --take audio/take-raw.wav --narration narration.json
```
`one_take.py` takes the reference clip, its exact transcript, seed, temperature and top_k as arguments (default: the
bundled `default-narrator`, seed 42; for the baritone pass `--ref-wav voices/coworker-baritone/reference.wav --ref-text-file voices/coworker-baritone/reference.txt --seed 7`).
`make_narration.py` splits the script into one chunk per sentence and keeps what the viewer reads (`show`) apart from
what the voice says (`say`, from a respelling map: `templates/saymap.example.json`). Read `take_check.py`'s diff: an
insert at the end is a made-up tail (the build trims it); a replace or delete in the middle is a misread line, and a
one-take voice can only be fixed by re-rendering the whole take (another `--seed`) or rewording the line.

## 4. Pronunciation (the owner listens)

Ask how each product name is said BEFORE rendering. Fix only in the say map (captions keep the real spelling):
respell by syllable, spell out acronyms with spaces, swap homophones, give very short sentences a few more words.
Whisper cannot confirm a pronunciation: play the take to the owner.

## 5. Pace: measured, then set once by ear

```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/audio_build.py --take audio/take-raw.wav --narration narration.json --out audio --wpm 200
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/sync_check.py --audio audio/narration.m4a --cues audio/cues.json --narration narration.json
```
`audio_build.py` MEASURES the take's speaking pace, applies ONE uniform pitch-preserving tempo to reach `--wpm`
(faster or slower; or `--tempo` by hand), cuts only between scenes, adds capped scene gaps (`--gap-base`,
`--gap-before 6=0.35`, `--max-gap 1.2`), trims the tail at the last script word, normalises to -16 LUFS and writes
`cues.json`, `captions.srt` and `check.json`. There is no pace to "start at": pick a number for the format, play 30
seconds, let the owner move it. Approved cuts measured about 180 (product demo, per-line) and about 207 (concept video,
one take) speaking wpm; neither is a rule. Say which pace a number means (speaking excludes scene gaps; overall does
not). A tempo outside about 0.8 to 1.25 gets flagged: listen for clipped or drawn-out words.

The cues are alignments of word times, not sums: `sync_check.py` measures their real error (plan for about 150 ms).

## 6. Fallback: one clip per line (V1 exception)

Use only when exact cue times matter more than continuity, or the TTS cannot read a whole script in one request. Each
line is rendered from the same reference clone; the timbre can shift at line and scene changes. Cue times are then
sums of clip lengths plus fixed gaps, exact to the sample.

```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/render_lines.py ../lines.json --voice A --ref-dir ref --out out --check
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stitch_narration.py --lines lines.json --clips voice/out --out build --target-wpm 180
```
Natural pace, no trim: one pitch-preserving tempo for every clip, set once at the stitch (`--tempo 1.5` for "make it
50% faster"). Read every `hyp` in `out/check.json`; WER over 0.10 is flagged; words you did not write are a
hallucination (`--only <id>` re-renders one line). `180` is the value that was approved for one product demo, not a
default to carry over: set `--target-wpm` for your format. `templates/lines.example.json` is the input; the bundled
narrator is used with `--voice default` after copying its reference to `ref/ref-default.wav` and `.txt`.

## Gotchas

- Pace words in the prompt ("slow") barely move pace. Do not iterate the prompt for speed.
- Same text + same reference + same model, precision and seed = identical audio. Changing any of them changes the
  voice: pin them in `voice.json` and keep the reference WAV with the project.
- A quantised model (6-bit, 8-bit) will not reproduce bf16 output exactly.
- Never clone a real person's recording without their written consent. The bundled references are synthetic and may
  ship; keep any other reference clip out of public repos.
- Very short sentences garble ("That's the uh..."). Add words.
