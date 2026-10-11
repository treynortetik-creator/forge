# Credits and notices

lyric-forge is MIT for the original work (see `LICENSE`). It adapts or is inspired by the following.

## Adapted, with thanks

- **bitwize-music-studio / claude-ai-music-skills** (CC0 / public domain). The 13-point lyric quality checklist, the three-pass refinement schedule, the section-length, word-count and density tables, the verse-to-chorus echo rule and the Suno pronunciation rules are adapted from its `lyric-writer` skill and `craft-reference`. They are restructured and rewritten here, with the thresholds turned into things `lyric_meter.py` measures. CC0 requires no credit; it is given as a courtesy.
  https://github.com/bitwize-music-studio/claude-ai-music-skills

## Ideas only (no text copied)

- **suno-songwriting-skill** by NuNaught (Apache-2.0): the idea of a fixed Title / Lyrics / Style / Analysis output contract for Suno-ready results.
- **Hermes songwriting skill** (MIT, Teknium / Hermes Agent): the idea of respelling words phonetically for AI singers, and the style-box formula of describing the sound journey instead of naming artists.

## Data and services

- **Datamuse API** (https://www.datamuse.com/api/) is called by `scripts/rhymes.py` at run time. No key required; its usage terms apply to your use.
- **CMU Pronouncing Dictionary** via the `pronouncing` package supplies syllable and rhyme data to `scripts/lyric_meter.py`. Fetched at run time by `uv`; not bundled.
- **Demucs** (Meta / Kyutai, MIT) separates the vocals in `scripts/sung_check.py`. **whisper.cpp** (MIT) or **faster-whisper** (MIT), both built on OpenAI Whisper (MIT), transcribe them. All are fetched or installed by the user at run time; none is bundled.

## Examples

Every example lyric in this plugin is fictional and written for it. No existing song lyrics are included.

If you are a creator named above and want something changed or removed, open an issue.
