---
name: render-and-caption
description: >
  Turn narration clips and a timeline page into a frame-exact MP4 with word-timed captions and an SRT: stitch the
  clips with one tempo and fixed gaps (exact cue times), caption from whisper word timestamps in 2-row chunks, build
  the page on a paused GSAP timeline whose time is narration time, render it frame by frame in parallel headless
  Chromium, encode H.264 with AAC, or inline everything into one interactive HTML file. Use when asked to "render the
  explainer", "make the MP4", "add captions", "burn in subtitles", "export the video", "one-file HTML", or after
  narrator-voice and before explainer-proof.
---

# Render and caption

Never screen-record the page in real time: it drops frames. Seek the paused timeline and every video per frame.

## One command

```bash
PLUGIN=${CLAUDE_PLUGIN_ROOT} VOICE_PY=voice/.venv/bin/python bash ${CLAUDE_PLUGIN_ROOT}/scripts/make_video.sh
SKIP_AUDIO=1 ... make_video.sh        # visual-only change, about 6 min on a 10-core Apple Silicon Mac
TEMPO=1.5 ... make_video.sh           # speed by ear instead of TARGET_WPM (default 180, a measured result, not a rule)
```
It runs the steps below in order. Project layout: `lines.json`, `voice/out/<id>.wav`, `captures/clips/*.mp4`,
`build/stage.html` (+ `timeline.js`, `scenes.js`, `vendor/gsap.min.js`). `gaps.json` adds pauses at footage beats.

## Two routes to the same page contract

- **Per-line clips + footage** (below): exact cue sums, word-timed 2-row captions, `templates/stage.html`.
- **One take + sprite world**: `scripts/make_onetake_video.sh` (narration, take, check, audio, sprites, build, proof,
  hero, render), the engine in `templates/engine/`, skill `sprite-explainer`. Cues come from alignment; captions are one
  splitter at 70 characters. Both routes end in `render_frames.mjs`.

`render_frames.mjs` is shared: it opens the page with `?render=1`, seeks per frame, pipes PNG to ffmpeg (or, with
`--frames DIR`, writes resumable frame files and encodes once). Playwright and Chrome are found from `--playwright` /
`$PLAYWRIGHT_PATH` and `--chrome-path` / `$CHROME_PATH` or the usual places; nothing is hard-coded.

## The steps (per-line route)

1. `stitch_narration.py` → `build/narration.m4a`, `cues.json` (exact line starts), `cue-table.md` (wpm per scene),
   `build/clips/`. Gaps: head 0.3, line 0.15, scene 0.35, tail 1.0 s (the old 2.6 s tail was dead air).
2. `captions.py` (voice venv, needs mlx-whisper) → `captions.json` + `<name>.srt`; whisper word times cached in
   `build/whisper/`, which also feed `W(id, word)`.
3. `prep_media.py` → short-GOP footage in `build/media/` and `build/data.js`.
4. The page: copy `${CLAUDE_PLUGIN_ROOT}/templates/stage.html` and `timeline.js` into `build/`, write `scenes.js`
   (`templates/scenes.example.js`). Preview: `stage.html?play`, or `?t=42`.
5. `render_frames.mjs --page build/stage.html --audio build/narration.m4a --out build/<name>.mp4 --workers 8`
   (`--stills 12.5,40` for quick checks, `--from/--to` for a section). Needs `npm i playwright` and ffmpeg.
6. `verify_video.sh` (see `explainer-proof`).

Interactive HTML instead: write the page to the contract in `${CLAUDE_PLUGIN_ROOT}/references/formats.md`, then
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/inline_build.py src.html explainer.html` (fonts, images, GLB models, audio
and vendored libraries inlined; works offline). 3D props: `blender -b --factory-startup -P
${CLAUDE_PLUGIN_ROOT}/scripts/decimate_glb.py -- in.glb out.glb 22000 1024`.

## Timeline rules

- Timeline time = narration time. Place animations with `T(id)`, `E(id)`, `W(id, word)`; never typed seconds.
- Every ring gets an out time. Every footage coordinate is measured on the frame.
- Crossfade footage over about 0.15 s holding the incoming first frame.
- Captions: dark translucent pill, about 40 px, 2 rows max, low and centred. Move callouts, not captions.
- Vendor GSAP (and three.js if used); no CDN in a render.

## Gotchas

- Roll each render worker in from 1 s before its first frame, or tweens initialise out of order (the script does).
- Videos must be seekable to the frame: always run `prep_media.py` on new footage.
- A 720p copy at about 1.3 Mbps keeps a chat-app send under about 35 MB:
  `ffmpeg -i in.mp4 -vf scale=1280:-2 -c:v libx264 -b:v 1300k -c:a aac -b:a 96k -movflags +faststart out-720p.mp4`.
