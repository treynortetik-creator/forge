# lyric-forge

Write lyrics for AI music generators (Suno and similar), then check what the generator actually sang.

It follows the Forge rule: **judgment stays with the model, and anything expressed as a number gets measured instead of eyeballed.** Models miscount syllables and misjudge rhymes with total confidence, so scripts count them. The model spends its effort on what no script can see: whether a line is true, specific, and singable.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install lyric-forge@forge
```

Restart the session or `/clear` so the skills load. You need `uv` (https://docs.astral.sh/uv/) for the scripts; there is nothing to `pip install`.

## Two skills

| Skill | Use it when |
|---|---|
| **lyric-writer** | writing, revising or reviewing lyrics. Brief, draft, **measure**, critic pass against a 13-point checklist, up to three revision passes, then a Suno-ready block: Title, Style (about 1000 characters or fewer), Exclude Styles, tagged Lyrics, Performance notes, and the measured numbers |
| **sung-vs-written** | a song has been generated. Splits out the vocals, transcribes them, aligns the transcript to your written lyrics, and flags lines worth a listen |

## The scripts

All live in `scripts/`. Skills call them through `${CLAUDE_PLUGIN_ROOT}`.

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

## Genre guides

`skills/lyric-writer/references/genres/` holds per-genre craft guides; the skill loads the one matching the brief. `emo-pop-punk.md` is a full guide built from a close reading of 29 songs (25 core 2001-2008 tracks plus 4 modern contrast tracks; list in `emo-pop-punk-songs-studied.md`), and its measurable norms are encoded in `scripts/data/genres/emo-pop-punk.json` for `--genre emo-pop-punk`. Without a matching guide the skill falls back to the generic tables in `references/craft.md` and says so.

## Layout

```
lyric-forge/
  .claude-plugin/plugin.json
  skills/
    lyric-writer/
      SKILL.md
      references/{craft.md, suno-notes.md, genres/emo-pop-punk*.md}
    sung-vs-written/SKILL.md
  scripts/
    lyric_meter.py  rhymes.py  sung_check.py  test_lyric_meter.py
    data/cliches.txt  data/genres/emo-pop-punk{.json,-flags.txt}  fixtures/sample.txt
```

## Credits

The checklist, refinement schedule, and section/length/density tables are adapted from **bitwize-music-studio/claude-ai-music-skills** (CC0), restructured and tied to measured thresholds. The Title/Lyrics/Style/Analysis output idea comes from NuNaught's suno-songwriting-skill (Apache-2.0) and the phonetic-respelling idea from the Hermes songwriting skill (MIT); ideas only, no text copied. Full detail: **[NOTICE.md](NOTICE.md)**.

Every example lyric here is fictional. No existing song lyrics are included.

## Licence

MIT.
