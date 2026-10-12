---
name: track-check
description: "Look at and compare finished tracks without trusting guesses: scan a song for tempo, key, loudness and brightness over time, section boundaries and a spectrogram; isolate vocals with Demucs; and compare a singer's vocals across tracks for album consistency (pitch register and gross singer swaps only). Includes the Suno vocal-persona drift lesson. Use when asked what BPM or key a track is, whether two songs have the same singer, why a voice drifted between generations, or to analyse a track's structure."
allowed-tools: [Read, Write, Bash, Glob, Grep]
---

# Track Check

Two scripts that read audio for you, and one rule about what their numbers are allowed to mean.

| Script | What it measures | What it cannot tell you |
|---|---|---|
| `song_scan.py` | tempo, key (with a fit score), loudness range, brightness, percussive share, timbre-based section boundaries, a spectrogram PNG | whether the song is good; section names; a reliable tempo (half and double time are printed beside it) |
| `voice_match.py` | median sung pitch per track, speaker-embedding similarity between tracks, and a same-track control | whether two takes sound like the same singer |

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/audio/`. They need `uv` and `ffmpeg`.

## song_scan.py

```bash
uv run --with librosa --with matplotlib --with numpy python ${CLAUDE_PLUGIN_ROOT}/scripts/audio/song_scan.py song.m4a --outdir scans
uv run --with librosa --with matplotlib --with numpy python ${CLAUDE_PLUGIN_ROOT}/scripts/audio/song_scan.py a.m4a b.m4a --json
```

It decodes with ffmpeg first, because librosa (libsndfile) cannot read m4a. Read the PNG: spectrogram on top with section boundaries as cyan lines, loudness and brightness curves below.

Reading it honestly:
- **Tempo** is a beat-tracker's guess; it often lands on half or double time. Check the alternatives printed next to it against what the genre or the user asked for.
- **Key** is a template fit. A fit under about 0.6 means "unknown", say so. Relative major/minor pairs (C major / A minor) look alike to it.
- **Sections** are where timbre changes, not labels. Match them to the lyric structure yourself, with the user.
- The energy list is one number per 5 seconds: use it to find where a track builds or collapses, not to judge mixing.

Check the numbers against what was asked for: a generator told 140 BPM may deliver 129. Report the gap, with the number, and let the user decide.

## Vocal isolation

For lyrics, pitch or voice comparison, separate the vocal first; plain transcription of a full mix hallucinates (`[MUSIC PLAYING]`) and loses sung words under the band.

```bash
ffmpeg -nostdin -y -i song.m4a song.wav
uv run --with demucs --with numpy --with soundfile --with torchcodec python -m demucs --two-stems=vocals -n htdemucs -o stems song.wav
# -> stems/htdemucs/song/vocals.wav
```

`numpy` must be listed explicitly or the run fails. The first run downloads model weights and is slow on a laptop CPU. `sung_check.py` (see `sung-vs-written`) runs this step for you.

## voice_match.py: album consistency, with its limits

```bash
export TITANET_MODEL=/path/to/nemo_en_titanet_small.onnx      # fetch once, ~40 MB, see below
uv run --with sherpa-onnx --with soundfile --with librosa --with numpy \
    python ${CLAUDE_PLUGIN_ROOT}/scripts/audio/voice_match.py songA=stems/songA/vocals.wav songB=stems/songB/vocals.wav
```

Fetch the model once (the sherpa-onnx release tag is spelled `recongition`; if the URL has moved, search the sherpa-onnx releases for "speaker recognition models"):

```bash
curl -L -o nemo_en_titanet_small.onnx \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/nemo_en_titanet_small.onnx
```

The model path comes from `--model` or `$TITANET_MODEL`; nothing is hardcoded. Check the model's own licence before redistributing it; this plugin does not bundle it.

### The lesson that governs every use of this script

**TitaNet is trained on speech. It under-reads sung timbre and delivery, and human ears are ground truth.** In the case that taught this (2026-10-11), two takes of the same persona scored almost identical (0.90 against a same-song control of 0.86 to 0.87) while the user heard a "massive" difference by ear; when he A/B'd the isolated stems, he was right. So:

- Use the score for two things only: **pitch register** (median sung pitch, in semitones apart) and **gross singer swaps** (a clearly different person scores far below the same-track control).
- **Never** report a high similarity as "these takes match" or "same voice". It means "the speech model cannot tell them apart", which is a weaker claim.
- Always report the **same-song half-vs-half control** beside any cross-track score. The cross-track number means something only relative to it. The script prints it for every track.
- When a voice matters, produce isolated stems and hand them to the user for an A/B listen. Offer the number as supporting context, after the ears.

A pitch gap can come from the melody and key rather than the voice: a song written a few semitones lower sounds like a different singer even with an identical timbre. Say which you are looking at.

## Suno vocal-persona drift (dated observation, 2026-10-11)

When a Suno song used a **vocal clone or persona** at the default **25% "Audio Influence"**, the voice drifted between generations: the lead sounded like a different singer from track to track. Raising Audio Influence (to 100% in the case that found it) made the later take a closer match by the user's ears. If the new song starts copying the source track's melody or arrangement instead of just the voice, back off to roughly **70 to 80%**; lowering Variety also helps. This is one user's finding on one platform version: generator behaviour changes, so verify by ear and re-measure the pitch register after changing it. The lasting rule: for any lead that must stay consistent across an album, use a persona or clone with Audio Influence set high, and check each new track against the previous one by listening.
