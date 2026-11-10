# proof-forge

Verify what came out of the render. Compare two exports and mark exactly where they differ, on video, stills or audio, with a threshold derived from the pair rather than guessed at.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install proof-forge@forge
```

Restart the session or `/clear` so the skill loads. Needs Python 3 and `ffmpeg`; comparing stills also needs Pillow.

## Skill

| Skill | Use it when |
|---|---|
| **render-diff** | checking whether two renders, exports, versions or deliverables are actually identical. Video gets timecoded markers and an EDL, stills get a bounding box and heat map, audio gets a phase-invert null test |

## Script

The skill calls it through `${CLAUDE_PLUGIN_ROOT}`.

```bash
python3 scripts/render_diff.py a.mov b.mov                    # video
python3 scripts/render_diff.py a.mov b.mov --edl markers.edl  # with an EDL of the differences
python3 scripts/render_diff.py a.png b.png --out diff.png     # stills
python3 scripts/render_diff.py a.wav b.wav                    # audio null test
python3 scripts/test_render_diff.py                           # tests
```

Exit 0 = same, 1 = differs, 2 = could not compare.

## License

MIT. See `LICENSE`.
