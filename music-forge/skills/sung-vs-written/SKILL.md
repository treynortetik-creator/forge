---
name: sung-vs-written
description: "After a song has been generated, compare what was actually sung against the lyrics you wrote. Separates the vocals with Demucs, transcribes them with whisper, aligns the transcript to the written words, and reports per line: matched, misheard, dropped, or different, plus extra material in the audio. Use when checking a generated track for mispronounced, skipped or rewritten lyrics."
allowed-tools: [Read, Write, Bash, Glob, Grep]
---

# Sung vs Written

Generators mishear their own lyrics, skip lines, and rewrite verses. Finding that by listening to every take is slow. This skill does the first pass: it lists the lines **worth a listen**, with timestamps.

## The one rule that matters

**The transcript is a model's guess at sung audio.** A speech model hearing a vocal stem will get stretched vowels, harmonies and unusual words wrong, and it swaps near-homophones in both directions (sail / sale, "lighthouse" / "light house").

- `MISHEARD`, `DIFFERENT`, `DROPPED` mean: **go listen at that timestamp.** They are flags, not verdicts.
- `ok` does not mean the line sounded good, only that the transcript agrees with the page.
- Never tell the user "the singer got line 7 wrong" from this report alone. Say "the transcript disagrees at 0:36 (heard X, written Y); worth a listen."
- Disagreement that repeats across two different transcription engines is stronger evidence than one engine's miss. If a flag matters, run the other engine (`--engine faster-whisper`) and compare.

## Why vocals are separated first

Plain whisper on a full mix hallucinates (`[MUSIC PLAYING]`, invented lyrics), loses sung words under the band, and loops on instrumental sections. Demucs pulls the vocal stem out first; whisper then hears something close to speech.

## Run it

Needs `uv` and `ffmpeg` on PATH. For the transcription step, either `whisper-cli` (whisper.cpp) plus a ggml model, or nothing extra (falls back to faster-whisper through `uv run`, which downloads a model on first use).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sung_check.py song.m4a --lyrics lyrics.txt \
    --model /path/to/ggml-small.en.bin          # or export WHISPER_MODEL=...
```

Other forms:

```bash
# you already have a vocal stem: skip separation
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sung_check.py song.m4a --lyrics lyrics.txt --vocals vocals.wav

# faster-whisper instead of whisper.cpp
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sung_check.py song.wav --lyrics lyrics.txt --engine faster-whisper

# machine-readable, or just the trouble spots
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sung_check.py song.wav --lyrics lyrics.txt --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sung_check.py song.wav --lyrics lyrics.txt --only-problems

# keep intermediates somewhere you choose
... --work ./sung_work
```

The Demucs step it runs for you:

```bash
uv run --with demucs --with numpy --with soundfile --with torchcodec \
    python -m demucs --two-stems=vocals -n htdemucs -o OUT file.wav
```

Audio that is not wav (m4a, mp3) is converted with ffmpeg first; libsndfile cannot read m4a. First run downloads the Demucs weights and takes a few minutes; later runs on a three-minute song take about a minute on a laptop CPU.

The lyrics file is the plain text you wrote, with optional `[Section]` tags. If you used phonetic respellings for Suno ("Roh-MAY-nee"), pass the **respelled** version here: that is what the generator was asked to sing. Text in (parentheses) is treated as backing vocals and not graded.

## Reading the report

| Status | Meaning |
|---|---|
| `ok` | every written word of the line appears in order in the transcript |
| `MISHEARD` | some words differ, are missing, or extra words appear; most of the line still lines up. The report shows `written 'X' -> heard 'Y'` per difference |
| `DIFFERENT` | the transcript for this stretch is less than half similar to the line: a rewritten line, or a bad transcription. Listen |
| `DROPPED` | none of the line's words were found. Skipped by the singer, or the model missed it |
| `AUDIO MATERIAL NOT IN THE WRITTEN LYRICS` | sung words the page does not have: new lines (`ADDED`), or a section sung again (`repeat of [Chorus]`) |

Times are word-level estimates, good to a few seconds, from the transcript.

## Know the blind spots

- **Repeated sections.** If the song repeats the chorus and your file has it once, your chorus is paired with the occurrence that matches best; the other occurrences show up under AUDIO MATERIAL as repeats. A mangled early chorus can hide behind a clean later one, so read the extras too. For a thorough check, write the repeats into the lyrics file the way they were sung.
- **Respellings and names.** A deliberately respelled word will rarely be transcribed as spelled. Expect flags there and judge by ear.
- **Homophones.** Words that sound alike are interchangeable to a speech model. A flag on one is a coin flip until you listen.
- **Singing quality.** This checks words, not pitch, timing, diction quality or emotion. It cannot tell you the take is good.
- **Dense or shouted vocals, gang vocals, layered harmonies** degrade the transcript. A lot of `DIFFERENT` in those sections is the instrument, not the singer.

## What to do with the result

1. List the flagged lines with timestamps, worst first, and ask the user to listen to those spots.
2. For a line the user confirms is wrong, the fix is usually in the prompt, not the song: respell the word, shorten the line, remove a tricky cluster, or regenerate that section. Use the `lyric-writer` skill's pronunciation notes.
3. If the singer rewrote lines and the user likes the new version, update the lyrics file to match what was sung, so later checks and any lyric sheet agree with the audio.
4. Do not claim the song "matches" or "doesn't match" on a percentage alone. The word-match percentage in the summary is a size-of-the-problem number.
