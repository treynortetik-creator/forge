# Credits and notices

music-forge is MIT for the original work (see `LICENSE`). It adapts or is inspired by the following.

## Adapted, with thanks

- **bitwize-music-studio / claude-ai-music-skills** (CC0 / public domain). The 13-point lyric quality checklist, the three-pass refinement schedule, the section-length, word-count and density tables, the verse-to-chorus echo rule and the Suno pronunciation rules are adapted from its `lyric-writer` skill and `craft-reference`. They are restructured and rewritten here, with the thresholds turned into things `lyric_meter.py` measures. CC0 requires no credit; it is given as a courtesy.
  https://github.com/bitwize-music-studio/claude-ai-music-skills

## Ideas only (no text copied)

- **suno-songwriting-skill** by NuNaught (Apache-2.0): the idea of a fixed Title / Lyrics / Style / Analysis output contract for Suno-ready results.
- **Hermes songwriting skill** (MIT, Teknium / Hermes Agent): the idea of respelling words phonetically for AI singers, and the style-box formula of describing the sound journey instead of naming artists.
- **claudia-bot** by anabology (MIT, https://github.com/anabologyco-maker/claudia-bot): the budget rule of planning for about twice the seconds the cut uses, the one-change image-edit prompt for fixing stills, the note that a face refused as a first frame may pass as a reference image, and the general idea of measuring lip sync from the clip's own audio. Written here in our own words; `sync_offset.py` was written for this plugin, not ported.

## Data and services

- **Datamuse API** (https://www.datamuse.com/api/) is called by `scripts/rhymes.py` at run time. No key required; its usage terms apply to your use.
- **CMU Pronouncing Dictionary** via the `pronouncing` package supplies syllable and rhyme data to `scripts/lyric_meter.py`. Fetched at run time by `uv`; not bundled.
- **Demucs** (Meta / Kyutai, MIT) separates the vocals in `scripts/sung_check.py`. **whisper.cpp** (MIT) or **faster-whisper** (MIT), both built on OpenAI Whisper (MIT), transcribe them. All are fetched or installed by the user at run time; none is bundled.

## Services and tools used at run time (none bundled)

- **OpenRouter** (https://openrouter.ai) `/api/v1/videos`, called by `scripts/video/build_clips.py` with your own `OPENROUTER_API_KEY`. The video models behind it have their own terms and content filters.
- **uguu.se** and **litterbox.catbox.moe** are third-party temporary file hosts, used only when you pass `--audio-refs`. Slices are publicly fetchable until they expire.
- **ffmpeg** (LGPL/GPL, depending on build) and **ImageMagick** do the cutting and caption rendering.
- **librosa** (ISC) and **matplotlib** (PSF-style) power `scripts/audio/song_scan.py`. **sherpa-onnx** (Apache-2.0) runs the NVIDIA NeMo **TitaNet** speaker model in `scripts/audio/voice_match.py`; you download the model yourself and its own licence applies.

The video pipeline, routing table and audio scripts were written for this plugin from the author's own notes; no third-party repository text was copied.

## Examples

Every example lyric in this plugin is fictional and written for it. No existing song lyrics are included.

If you are a creator named above and want something changed or removed, open an issue.
