# Narrator voice: the method and the numbers

From one product-demo explainer (Nov 2026) that the owner approved on the second cut, after a slower first cut was
rejected, and from an earlier run of interactive explainers that used stock preset voices and was rejected for them.

**Default:** use the bundled narrator in `voices/default-narrator/` (a designed, fully synthetic reference, Apache-2.0
model), or audition and design your own with the steps below.

## Why this method

| Approach | What happened |
|---|---|
| Stock preset voices from the TTS model | Rejected: a strong accent the owner disliked, on every preset tried. |
| Cloning a real person's recording | Not used. Needs that person's written consent; read as "too intense" when tried on a house voice. |
| Designing each line fresh from a text description | A different person on every call: median pitch spread 4.1 semitones across 3 lines, pace 174 to 258 wpm (one voice); 162 to 310 wpm across three voices. |
| **Design once, clone every line from that one clip** | Same person on every line: pitch spread 2.7 semitones, pace 146 to 194 wpm. Approved. |

## Engine (Apple Silicon)

- `mlx-audio` 0.6.5 in a Python 3.12 venv: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python mlx-audio mlx-whisper librosa soundfile`.
- Design: `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16` makes ONE reference clip from a description.
- Clone: `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16` renders every line from that clip (ref_audio + ref_text).
- Check: `mlx-community/whisper-large-v3-turbo` for word error rate and word timestamps.
- Licence: check each model card on the day. The Qwen3-TTS mlx cards checked on the build machine said Apache-2.0.
  Quantised variants (6-bit, 8-bit) exist; they will not reproduce bf16 output bit for bit.
- Not on Apple Silicon: any TTS that can design or pick a voice once and clone it for every line works with the
  rest of the pipeline. `stitch_narration.py` only needs one WAV per line in `<clips>/<id>.wav`.

## Settings that mattered (`scripts/voice/voice_common.py`)

| Setting | Value | Why |
|---|---|---|
| seed | 42, reset before every clip | same text + same reference + same model = identical audio, so single lines can be redone |
| temperature | 0.6 (library default 0.9) | steadier, less animated |
| top_k | 50 | |
| reference clip | the designed audition, edge-trimmed, slowed to 0.75x with pitch kept | clones inherit a calmer delivery |
| pace in the prompt | "slow, relaxed" | barely changes pace. Do not fight pace in the prompt; set it in the stitch |

Voice A's description, the one picked: "A mid-range alto voice, mellow and even. Speaks American English with a
neutral General American accent, no foreign accent. Adult woman around 30. Casual and smooth, warm, low-key and
conversational, like a friendly coworker walking you through a tool. Slow, relaxed medium pace, calm and restrained
intonation with modest pitch variation. Not bubbly, not dramatic, not announcer-like, not breathy."
Measured: median pitch 234 Hz on the design sample, 209 Hz on clones; spread about 3.6 semitones.

## Speed: set it once, by ear, after the voice is picked

- Natural cloned pace varied by line (155 wpm average over 33 lines, 187 on one designed clip).
- The first cut ran at about 120 wpm overall and was called "the personification of a snail".
- The approved cut is about 1.5x the first: **about 180 wpm on the base gaps** (188 wpm of pure speech, 165 overall
  once extra footage pauses count), gaps 0.3 s head, 0.15 s between lines, 0.35 s between scenes, 2.6 s tail.
- How: `stitch_narration.py` trims every clip and applies ONE pitch-preserving `atempo` to all of them (1.213 on that
  build). Flag anything over 1.25 and listen for clipped words. A calm voice prompt keeps it calm at speed; do not
  slow the narration to sound calm.
- Use the time a faster voice frees up for more demo, not padding.

## Pronunciation: fix it in the `text` field only

Captions keep the real spelling (`caption`); only the TTS sees `text`.

| Problem | Fix |
|---|---|
| A product name said wrong | Ask the owner how it is said BEFORE rendering. Respell by syllable: `Velloq` as `Vell-ock`. Whisper normalises names, so it cannot confirm pronunciation: a person listens. |
| A respelling that makes the model hallucinate extra words | Try another respelling (hyphenated syllables were safer than a fused spelling). |
| A possessive brand name slurring ("Brand's" heard as "brand use") | Hyphenate, or rephrase so the possessive goes ("Brand built", "our own cloud"). |
| Acronyms | Spell out with spaces: `Q R`, `S S O`, `U R L`. Whisper "flags" these; that is fine. |
| A homophone heard as the wrong word ("whole" heard as "hole") | Swap in a word with no twin ("entire", "every"). |
| Very short lines ("Meet X.") garble | Give them a few more words, so the line is a full sentence with the name mid-way. |
| A word the stock voice mangles at the start of a sentence | Move it mid-sentence or rephrase. |

After any change, re-render only that line (`--only <id>`), then read its `hyp` in `check.json`.

## The full recipe, step by step (as run on the approved build)

1. **Design (once).** `Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16` (mlx-audio 0.6.5, `lang_code="english"`, 24 kHz mono)
   speaks one ~45-word audition passage three times, once per description (A mid-range alto, B lower softer alto,
   C a touch brighter; all share the same accent, age, register and "not ..." list). Seed 42 before each clip,
   temperature 0.6, top_k 50.
2. **Make the references.** Each raw design clip is edge-trimmed (librosa split at 30 dB, 0.12 s kept each end),
   then slowed to 0.75x with ffmpeg `atempo` (pitch preserved). That is `ref-<k>.wav`; the passage is `ref-<k>.txt`.
3. **Pick.** The three audition samples (trimmed, slowed toward 160 wpm, never sped up) were played to the owner,
   who picked A by ear. `report.json` (WER, median pitch, wpm) only ruled out broken takes.
4. **Clone every line.** `Qwen3-TTS-12Hz-1.7B-Base-bf16` with `ref_audio` + `ref_text` = the chosen reference,
   same seed, temperature and top_k (mlx-audio applies its own ICL repetition penalty of 1.5 internally). Lines are
   rendered at natural pace with no per-line tempo (`--no-pace`); `--check` runs whisper-large-v3-turbo, pitch and wpm.
5. **Drift check.** Three unrelated sentences, rendered both designed-per-line and cloned-from-reference; compare the
   spread of median pitch (semitones) and wpm. Cloning won (2.7 vs 4.1 semitones).
6. **Speed, once.** Stitch all lines with one pitch-preserving tempo solved for ~180 wpm on the base gaps (1.213 on
   that build), loudnorm to -16 LUFS, 48 kHz, AAC 160k.

**Re-making a reference on a new passage** (to share a voice without the words it was first designed on): clone the
approved reference speaking a neutral passage with the settings in step 4, trim it, and tempo-match it to the old
reference's measured wpm. Then confirm it is the same voice: speaker-embedding cosine against the old reference, and
the same three lines cloned from each, compared on pitch, pace and WER.

## Reproducing a voice on another machine

The description alone gives a similar but different person. To get the SAME voice you need: the reference WAV and
its transcript (`ref-<k>.wav` + `.txt`), the same clone model and precision, the settings above, and mlx-audio at the
same version. The bundled `voices/default-narrator/reference.wav` + `reference.txt` is that pair for the default voice, designed from a
text description (no real person). Keep any other reference clip out of public repos; it is the voice.
