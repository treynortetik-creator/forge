# Delivery formats

| Format | Use it when | Built with | Size target |
|---|---|---|---|
| **MP4 + SRT** | people will watch it: a demo, a training clip, a repost, an upload | `stage.html` + `render_frames.mjs` | 1080p H.264 crf 18; a 720p copy around 1.3 Mbps for chat apps (under about 35 MB) |
| **Interactive HTML** | people will explore it: click a station, toggle a detail, try a sample question, set the speed | a slide engine meeting the contract below + `inline_build.py` | one file, under about 10 MB |
| Both | the interactive file is the master and a reviewer wants a video | render the interactive page's autoplay path with the same frame renderer | |

## Captions
- Burned into the MP4 (a dark translucent pill, white semibold text about 40 px at 1080p, at most 2 rows of about
  42 characters), plus a separate `.srt` so players and upload sites can show them.
- Captions use the real spelling; TTS respellings never appear.
- Captions sit low and centred; move callouts, not captions, when they collide.

## Interactive explainer page contract (what `deck_proof.mjs` tests)
- One `.slide` per scene with `data-steps` = number of builds; the narration script has `data-steps + 1` lines for
  that slide (line 0 is the slide start), or sync breaks.
- `window.__deck.go(slide, step)` and `window.__deck.next()`.
- `<audio id="aud">`, a sync checkbox `#sync` (manual navigation turns it off), a speed button `#spd` that cycles
  1, 1.25, 1.5, 1.75, 2 with `preservesPitch` and scales the animation timeline to match, remembered locally.
- While synced, `location.hash` is `#<slide>.<step>`.
- Keys: arrows/click advance, P play/pause, S or < > speed, F full screen.
- Cue file: `[[slide1_start, build1, ...], ...]` in seconds; each build fires about 0.3 s before its phrase.
- Prove: every slide at 1280x720 and 390x844, then sync at 1x and at the top speed you ship: 0 mismatches.

## Sending a draft
- One file, not a link to a draft folder. Proof images labelled with what they show.
- Audio-first readers: a narrated explainer already is the audio version; do not add a second one.
