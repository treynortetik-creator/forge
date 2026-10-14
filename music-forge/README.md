# music-forge

Write lyrics for AI music generators (Suno and similar), check what the generator actually sang, turn the finished song into a cut music video, and scan tracks for tempo, key and singer consistency.

*Formerly lyric-forge. Renamed and folded in at 0.2.0; the two lyric skills are unchanged.*

It follows the Forge rule: **judgment stays with the model, and anything expressed as a number gets measured instead of eyeballed.** Models miscount syllables and misjudge rhymes with total confidence, so scripts count them. The model spends its effort on what no script can see: whether a line is true, specific, and singable.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install music-forge@forge
```

Restart the session or `/clear` so the skills load. You need `uv` (https://docs.astral.sh/uv/) for the scripts; there is nothing to `pip install`. The video skill also needs `ffmpeg`/`ffprobe` and, for PNG captions and end cards, ImageMagick (`magick`), plus an `OPENROUTER_API_KEY` in your environment to animate shots. `sync_offset.py` and `chain_join.py` pull numpy (and OpenCV for `chain_join.py align`) through `uv run --with`.

## Four skills

| Skill | Use it when |
|---|---|
| **lyric-writer** | writing, revising or reviewing lyrics. Brief, draft, **measure**, critic pass against a 13-point checklist, up to three revision passes, then a Suno-ready block: Title, Style (about 1000 characters or fewer), Exclude Styles, tagged Lyrics, Performance notes, and the measured numbers |
| **sung-vs-written** | a song has been generated. Splits out the vocals, transcribes them, aligns the transcript to your written lyrics, and flags lines worth a listen |
| **music-video** | you have a finished song and want a video. Shot plan, still prompts, animation through OpenRouter video models (routed by shot type, resumable, cost-capped), sung clips synced to the vocal by their own audio, chained shots aligned at the join, camera sweeps in post, a frame-exact cut with the original song and burned captions, a review loop, and 16:9 plus vertical teasers. Hard-won rules and dated model notes from a real 3:39 video live in `skills/music-video/references/` |
| **track-check** | you want to read a track: tempo, key, loudness curve, sections and a spectrogram; or compare a singer's isolated vocals across tracks. Carries the rule that the voice score is a speech model's guess, never a verdict |

## The scripts

Lyric scripts live in `scripts/`, video scripts in `scripts/video/`, audio scripts in `scripts/audio/`. Skills call them through `${CLAUDE_PLUGIN_ROOT}`.

### `lyric_meter.py`: measure the lyric sheet

```bash
uv run --with pronouncing python scripts/lyric_meter.py song.txt --title "My Title"
uv run --with pronouncing python scripts/lyric_meter.py song.txt --json
uv run --with pronouncing python scripts/lyric_meter.py song.txt --title "My Title" --genre emo-pop-punk
uv run --with pronouncing python scripts/lyric_meter.py song.txt --max-lines verse=6,chorus=4 --words 150-250
```

Input is a text file with `[Verse 1]`, `[Chorus]` style tags. It reports:

- per line: syllable count and stress pattern (CMU dictionary through the `pronouncing` library; words it does not know fall back to a vowel-group heuristic and are marked `~`)
- per section: line count, word count, syllable range
- line-by-line syllable drift between repeated sections (verse 2 against verse 1), flagging pairs off by more than 2 (`--tolerance`)
- end-rhyme scheme letters per section, each link classed **perfect** (identical CMU rhyming part), **slant** (same final stressed vowel) or **repeat** (same end word)
- repeated end-words, in a section and song-wide
- title-in-chorus (`--title`) and verse-to-chorus echo
- a cliche and AI-tell scan from `scripts/data/cliches.txt` (edit the list; `--cliches` points at another one)
- with `--genre <name>`, a **GENRE CHECK** block (also in `--json`) from `scripts/data/genres/<name>.json`: PASS or WARN per norm, each with the measured value, the norm and a short "why" citing the guide. Norms, not laws: it never fails. For `emo-pop-punk`: total words with repeats written out, repeated-line share, chorus length and occurrences, perfect-rhyme share in the chorus, long verse lines, "you" count, title in chorus, a receipts proxy (digits and capitalised names), line-length swing, and word lists for therapy-speak, anachronism and generic angst (`emo-pop-punk-flags.txt`)

Real output on the bundled fictional fixture (`scripts/fixtures/sample.txt`, which has one deliberate syllable mismatch, one cliche and one repeated end-word):

```
REPEATED-SECTION SYLLABLE COMPARISON (line by line vs first occurrence)
  [Verse 2] vs [Verse 1]: 8>12! 8>9 10>8 11>11

FLAGS (4)
  - [Chorus] end-word 'keeper' used 2x in the chorus (fine if it is the hook; a flag if it is filler)
  - [Verse 2] end-word 'thing' used 2x in one section
  - [Verse 2] line 1 (file line 16): 12 syl vs 8 in [Verse 1] (off by 4, tolerance 2) ~approx
  - cliche 'neon' in [Verse 2] line 16: 'He polishes the brass till it gleams like neon'
```

**What it does not know.** Syllables are speech counts from a dictionary, not a melody. Single-syllable function words (the, a, and) are shown unstressed because singers reduce them. Names and phonetic respellings land on the `~` heuristic, so treat those counts as plus or minus one. Slant detection is vowel-based; consonance-only rhyme and internal rhyme are not measured.

### `rhymes.py`: rhyme candidates

```bash
python3 scripts/rhymes.py window --syllables 2
python3 scripts/rhymes.py window --limit 30 --json
```

Perfect and near rhymes from the Datamuse API (no key), each with a syllable count, with anything on the cliche list filtered out and reported. It is a rhyming dictionary; Datamuse can return rare words and nothing at all for near rhymes of common words.

### `sung_check.py`: compare the sung vocals to the written lyrics

```bash
python3 scripts/sung_check.py song.m4a --lyrics lyrics.txt --model /path/to/ggml-small.en.bin
python3 scripts/sung_check.py song.m4a --lyrics lyrics.txt --vocals vocals.wav     # skip separation
python3 scripts/sung_check.py song.wav --lyrics lyrics.txt --engine faster-whisper --json
```

1. Converts to wav with ffmpeg and separates vocals with Demucs (`htdemucs`, two stems). Separation comes first because whisper on a full mix hallucinates `[MUSIC PLAYING]` and loses sung words under the band.
2. Transcribes the vocal stem with `whisper-cli` (whisper.cpp; model path from `--model` or `$WHISPER_MODEL`) if present, otherwise faster-whisper through `uv run`.
3. Aligns transcript to written words (difflib) and reports per line `ok`, `MISHEARD`, `DIFFERENT` or `DROPPED`, with `written 'X' -> heard 'Y'`, timestamps, and any audio material not in the lyrics.

**A transcript is a model's guess at sung audio.** A flag means "go listen here", not "the singer got it wrong". See `skills/sung-vs-written/SKILL.md` for the blind spots.

Requires `uv` and `ffmpeg`. First run downloads the Demucs weights.

### `test_lyric_meter.py`

```bash
uv run --with pronouncing python scripts/test_lyric_meter.py
```

## The video scripts (`scripts/video/`)

The plan scripts take the shot plan (`shot-plan.json`: title, audio, optional stems, style line, character looks, shots with id / `MM:SS.ss-MM:SS.ss` / slug / description / sing / frame, plus optional routing fields framing / kind / face / audio_ref) and default to `frames/`, `clips/`, `cuts/` beside it. Stdlib Python 3.11+ plus ffmpeg, except where noted.

| Script | Does |
|---|---|
| `plan_check.py` | gaps, overlaps, total vs audio length, missing frames, shots longer than their model's clip limit |
| `still_prompts.py` | character-sheet template and one still prompt per shot, looks not names |
| `build_clips.py` | keyframe (+ an audio reference with `--audio-refs`: song, stem or TTS file per shot's `audio_ref`) to a clip per shot via OpenRouter `/api/v1/videos`; `--dry-run` prices the plan with no key, `--max-usd` is a hard ceiling, resumable, 5 workers, per-clip sidecar JSON |
| `sync_offset.py` | cross-correlates a sung clip's own soundtrack against the stem or song it was made from: the song time at its first frame, written to the sidecar for `cut.py`. Flags clips that do not carry the audio. numpy |
| `chain_join.py` | `last-frame` to chain from, `align` (ECC scale/shift registration, colour match, duplicate frame dropped, 2-frame dissolve, optional de-judder), `check` (frame-difference profile around a join). numpy + OpenCV |
| `post_sweep.py` | a free camera move on a locked-off clip: per-frame push-in plus a cosine-eased pan; `--print-filter` gives the ffmpeg string |
| `cut.py` | frame-exact slots from the plan's times, measured sync offsets from sidecars, original song on top, SRT captions (ffmpeg subtitles filter if present, else ImageMagick PNG overlays), plus a `-small.mp4` under a size target |
| `review_frames.py` | a frame per shot for you to look at, and audio of each singing clip for a whisper check |
| `teasers.py` | N windows, each 16:9 and 9:16 blurred-fill, with fades and an optional end card |
| `data/model-routing.json` | which model for which kind of shot (sung close-up, sung wide, instrumental, emotional acting, action, default), with prices. Every rule is dated (2026-10-14) and marked as drifting |

```bash
python3 scripts/video/plan_check.py shot-plan.json
python3 scripts/video/build_clips.py shot-plan.json --dry-run
python3 scripts/video/build_clips.py shot-plan.json --max-usd 15
uv run --with numpy python scripts/video/sync_offset.py clips/14-*.mp4 --ref stems/vocals.wav --write-sidecar
python3 scripts/video/post_sweep.py clips/22-wide.mp4 clips/redo/22-wide.mp4
python3 scripts/video/cut.py shot-plan.json --out cuts/video.mp4 --captions lyrics.srt
```

**`--audio-refs` uploads song slices to a public temporary file host** (uguu.se, fallback litterbox.catbox.moe, 1 hour). It is off by default. Keyframes go inline and are never uploaded.

Tests: `uv run python scripts/video/test_plan_check.py`, `uv run python scripts/video/test_cut.py` (synthetic sine song, colour clips, a local mock of the video API; no network, no key) and `uv run --with numpy --with opencv-python-headless python scripts/video/test_post_tools.py` (synthetic stem with a known 0.4 s offset, a synthetic chained clip 2.5% larger and shifted, a sweep on a test pattern). `build_clips.py` has not been run against live OpenRouter in this form; do one cheap live shot before a big run.

## The audio scripts (`scripts/audio/`)

- `song_scan.py`: tempo (with half/double alternatives), key (with fit), loudness and brightness, sections, spectrogram. `uv run --with librosa --with matplotlib --with numpy python scripts/audio/song_scan.py song.m4a`
- `voice_match.py`: median sung pitch and a speaker-embedding similarity between isolated vocal stems, always with a same-track control. The embedding model is trained on speech: use it for pitch register and gross singer swaps, never as proof two takes match. Model path via `--model` or `$TITANET_MODEL`; fetch instructions are in the script docstring and the `track-check` skill.

## Genre guides

`skills/lyric-writer/references/genres/` holds per-genre craft guides; the skill loads the one matching the brief. `emo-pop-punk.md` is a full guide built from a close reading of 29 songs (25 core 2001-2008 tracks plus 4 modern contrast tracks; list in `emo-pop-punk-songs-studied.md`), and its measurable norms are encoded in `scripts/data/genres/emo-pop-punk.json` for `--genre emo-pop-punk`. Without a matching guide the skill falls back to the generic tables in `references/craft.md` and says so.

## Layout

```
music-forge/
  .claude-plugin/plugin.json
  skills/
    lyric-writer/       SKILL.md  references/{craft.md, suno-notes.md, genres/emo-pop-punk*.md}
    sung-vs-written/    SKILL.md
    music-video/        SKILL.md  references/{routing.md, prompt-rules.md, sync-and-chaining.md, post.md}
    track-check/        SKILL.md
  scripts/
    lyric_meter.py  rhymes.py  sung_check.py  test_lyric_meter.py
    data/cliches.txt  data/genres/emo-pop-punk{.json,-flags.txt}  fixtures/sample.txt
    video/  plan_lib.py plan_check.py still_prompts.py build_clips.py sync_offset.py chain_join.py post_sweep.py
            cut.py review_frames.py teasers.py
            test_plan_check.py test_cut.py test_post_tools.py  data/{model-routing.json,shot-plan.schema.json}  fixtures/
    audio/  song_scan.py voice_match.py
```

## Credits

The checklist, refinement schedule, and section/length/density tables are adapted from **bitwize-music-studio/claude-ai-music-skills** (CC0), restructured and tied to measured thresholds. The Title/Lyrics/Style/Analysis output idea comes from NuNaught's suno-songwriting-skill (Apache-2.0) and the phonetic-respelling idea from the Hermes songwriting skill (MIT); ideas only, no text copied. Full detail: **[NOTICE.md](NOTICE.md)**.

Every example lyric, character and shot plan here is fictional. No existing song lyrics are included.

## Licence

MIT.
