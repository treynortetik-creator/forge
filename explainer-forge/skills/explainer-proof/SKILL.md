---
name: explainer-proof
description: >
  The detail pass before anyone else sees an explainer: a frame every 2 seconds on review sheets you actually read,
  the middle frame of every scene, a crop of every highlight ring at its frame, A/V sync measured at three cues,
  runtime against the cap, a whisper check of every line, a real-names grep across script, captions and page, and for
  interactive HTML every slide at desktop and phone size plus a seek test of every cue at 1x and top speed. Use
  before sending any explainer draft, after any re-render, or when asked to "proof", "QA", "check the video", "look
  at every frame", "is it in sync", or "check for names".
---

# Explainer proof

The owner caught rings a few pixels off, a ring left on after its cut, overlapping crossfades, text overflowing a
card, blank flash frames and captions over callouts. Each was visible on a 2-second sheet nobody had read. Full
checklist with pass marks: `${CLAUDE_PLUGIN_ROOT}/references/proof.md`.

## Run

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/verify_video.sh build/explainer.mp4 build/cues.json build/proof      # sheets + sync
node ${CLAUDE_PLUGIN_ROOT}/scripts/proof.mjs --page build/page.html --out proof --cues audio/cues.json --audio audio/narration.m4a   # engine pages
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_check.py --audio audio/narration.m4a --cues audio/cues.json --narration narration.json    # one-take sync
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/dead_air.py --cues audio/cues.json --audio audio/narration.m4a                                 # silence over 1.2 s
node ${CLAUDE_PLUGIN_ROOT}/scripts/ring_check.mjs --page build/stage.html                             # ring crops
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/name_check.py --names people.txt lines.json build/ script.md      # 0 hits
node ${CLAUDE_PLUGIN_ROOT}/scripts/deck_proof.mjs --page explainer.html                                # interactive only
node ${CLAUDE_PLUGIN_ROOT}/scripts/deck_proof.mjs --page explainer.html --sync cues.json --rate 2       # 0 mismatches
```
`proof.mjs` writes one still per cue chunk (at 75 percent of the chunk), lists page errors, lists every visible text under
24 px measured AFTER camera scale, and runs the dead-air check; exit 1 on any. `verify_video.sh` honours
`SYNC_LIMIT_MS` (150 for a one-take voice) and reads either cue sheet.
Exit codes: `verify_video.sh` 1 when sync is over 50 ms; `ring_check.mjs` 1 when a ring never lands; `name_check.py`
1 on any listed name; `deck_proof.mjs` 1 on small text, overflow, page errors or a sync mismatch.

## Then look

- [ ] Every `proof/review/sheet-*.png` read, top to bottom. Note the timestamp of anything off.
- [ ] Every `proof/rings/ring*.png` read: the ring sits on its target.
- [ ] Every `proof/final/scene*-mid.png` read: the scene says what its narration says.
- [ ] `name_check.py` people list built from EVERY person in the source (requesters, approvers, commenters).
- [ ] Each capitalised pair it lists read: a product or a fictional sample name, never a real person.
- [ ] Runtime from `cues.json` inside the cap; wpm in `cue-table.md` as agreed.
- [ ] Footage frames all carry the sample-data badge.
- [ ] Watch it once, start to finish, at 1x with sound.

When sending proof images to the owner, burn a label into each (`magick in.png -gravity north -pointsize 36
-annotate +0+10 "Scene 3 ring 2" out.png`).
