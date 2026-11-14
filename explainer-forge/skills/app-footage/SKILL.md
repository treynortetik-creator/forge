---
name: app-footage
description: >
  Capture real web-app footage for an explainer or product demo: sample data only with a visible badge, Playwright
  headless at 1920x1080 30 fps, a fake cursor and human-paced typing, long waits time-lapsed and tagged, fresh state
  per take, and a per-clip manifest the editor works from. Covers hiding ugly UI text with a patch that tracks it
  through scrolling, and timing a cover over a panel that comes and goes. Use when asked to "record the app",
  "screen capture for the demo", "get footage of the feature", "show the real product", or to fix debug text or
  private data visible in a recording.
---

# App footage

The owner wants the real product, full screen, being used. Footage in small "browser cards" was rejected. Depth:
`${CLAUDE_PLUGIN_ROOT}/references/capture.md`.

## Checklist per flow

- [ ] App in mock/sample-data mode; every name and number on screen is fictional (read the frames, do not assume).
- [ ] Fresh state: new session, new documents. Earlier takes leave edits behind.
- [ ] Playwright Chromium headless, viewport 1920x1080, CDP screencast at 30 fps, assembled with ffmpeg.
- [ ] Fake arrow cursor + click ripple injected with `addInitScript`.
- [ ] Typing at 20-25 characters per second; hold 1-1.5 s after each result.
- [ ] Long waits time-lapsed to about 3-4 s of visible progress; cut points logged.
- [ ] Manifest row per clip: timestamps of what is on screen, names and numbers shown, cut points, and timestamps of
      anything ugly (debug text, model self-talk, awkward copy, notices).

## Fixing what should not show

```bash
# text that scrolls with the page: track it, then the stage draws a patch in the page's own colour
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/track_patch.py media/B-flow.mp4 16 930 309 1086 333 12.0 26.9 build/track/B-notice.json
# a panel that opens and closes: find when it is on screen from a 4 px strip of its splitter bar
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/detect_band.py --clips media/C-*.mp4 --x 354 --y 200 --h 700 --rgb 230,247,248 --out build/track/bands.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prep_media.py --build build --src captures/clips   # short-GOP copies + data.js
```
All coordinates are clip pixels measured on the actual frame. Patches show more at full screen: render the span and
look. Or frame the problem out with `focus()`.

## Gotchas

- A mode that renders differently in capture (oversized slides, a present mode) can be replaced by a still of the
  same screen from a clean take.
- Show the "Sped up" tag over every time-lapsed span; make no on-screen speed claims.
- Hand capture to a cheaper model; keep editing decisions with the strongest one.
