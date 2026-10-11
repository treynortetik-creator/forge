# Changelog

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
  and Hermes (MIT). See `lyric-forge/NOTICE.md`.
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
