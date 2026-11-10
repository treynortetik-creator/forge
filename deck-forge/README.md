# deck-forge

Build PowerPoint decks that survive a Google Slides import fully editable, and measure them instead of eyeballing them: type legibility at viewing distance, WCAG contrast, native charts that will flatten on import, and off-slide geometry.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install deck-forge@forge
```

Restart the session or `/clear` so the skills load. The scripts need Python 3 and `python-pptx` (`pip3 install python-pptx`).

## Skills

| Skill | Use it when |
|---|---|
| **deck-builder** | creating a `.pptx` deck. Builds every component from shape primitives (no native charts, which flatten into dead images in Google Slides) and enforces the legibility floor at build time |
| **deck-audit** | reviewing or QA-ing a PowerPoint or Google Slides deck. Measures type size at viewing distance, WCAG contrast against the real backdrop, native charts, and shapes that fall off the slide |

## Scripts

Skills call these through `${CLAUDE_PLUGIN_ROOT}`.

```bash
python3 scripts/deck_build.py --print-theme > theme.json   # the default theme, to edit
python3 scripts/deck_build.py --demo demo.pptx             # a sample deck
python3 scripts/deck_audit.py deck.pptx                    # audit; exit 1 on a hard failure
python3 scripts/deck_audit.py deck.pptx --room-depth 40 --json
python3 scripts/test_deck_audit.py                         # tests
```

Google Slides import notes live in `references/google-slides.md`.

## License

MIT. See `LICENSE`.
