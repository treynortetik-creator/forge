# Changelog

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
