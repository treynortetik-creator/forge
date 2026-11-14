# Lessons, merged

Two sources: a run of narrated interactive HTML explainers for internal decision reviews (Nov 2026) and a product-demo
MP4 built on the same kit and approved on its second cut. Each line is a rule because a real cut was rejected or a
reviewer caught it.

## What the viewer and the owner want

1. **Short.** 3:00 to 3:30 is the target for a single-topic explainer; 5:00 is the hard cap. About 7 scenes. One idea
   per sentence; merge rather than repeat. A presentation someone delivers live: under 10 minutes, three ideas.
2. **Fast, calm voice.** About 180 wpm (see voice.md). Slow narration read as "a snail"; the calm comes from the voice.
3. **No stock voices, no dramatic reads.** Presets had an accent the owner disliked; a cloned house voice was "overly
   intense". Plain, friendly sentences, not punchy one-liners.
4. **Light, warm, approachable look.** Off-white background, soft matte "clay" 3D or flat illustration, one or two
   accent colours, everyday metaphors. Dark neon "cyberpunk" vaults and glowing circuits were rejected. Approved from
   ONE sample image plus ONE rendered scene: make the style sample before building, every time a style is new.
5. **Show the real product, full screen.** Footage shrunk into fake browser cards was rejected. Edge-to-edge screen
   recordings; zoom only to make a number readable, then pull back.
6. **Pixel-exact callouts.** Rings a few pixels off read as sloppy. Place every ring from a box measured on the actual
   frame; screenshot each ring at its frame (`ring_check.mjs`).
7. **A detail pass is required.** A frame every 2 s, every sheet looked at. Found: a ring still on after its cut,
   crossfades overlapping, text overflowing a card, blank flash frames, captions over callouts.
8. **No real people.** No names, quotes or "X built Y" anywhere: narration, slides, notes, captions, footage. Use
   "someone in support". Grep before shipping (`name_check.py`).
9. **Current names and titles.** Teams rename roles; check every job title and product name with the owner.
10. **Fact-check the script against the source before recording.** A reviewer caught three overstatements in one
    draft ("checks every number" when only cited figures are checked; "download" when only PDF export existed).
11. **State facts only.** Leave out an "open questions" slide unless the audience needs it to decide.

## Build rules

12. **Timeline time is narration time.** Every animation is placed from the cue times (`T`, `E`) or the moment a word
    is spoken (`W`), never typed seconds, so a re-voiced line carries its animation with it.
13. **Cue times are sums, not guesses.** Stitch clips with fixed gaps and the cue times are exact; no alignment step.
    (Word timing from whisper alone drifted about 0.4 s on an earlier deck.)
14. **Render frame by frame, never screen-record.** Seek the paused timeline and every video per frame. Real-time
    capture drops frames.
15. **Re-encode footage with a short GOP** (6 frames, no B-frames) so every seek lands on the exact frame.
16. **One command rebuilds everything**, with a visual-only switch (`SKIP_AUDIO=1`).
17. **Vendor every library** (GSAP, three.js) so the output works offline and renders do not depend on a CDN.
18. **Image backgrounds never match the page exactly.** Sample the page colour from the images and feather each
    image's edge with a radial mask.
19. **3D labels projected onto the page** must hide when they fall into the text column and be clamped inside the
    frame, or they clip at the edge.
20. **Phone layout is its own layout.** No stage scaling on a phone: the visual in a band on top, the text reflowed
    below, short labels, tiny SVG text hidden.
21. **Give the speed control to the viewer** on interactive explainers: 1x to 2x, pitch preserved, the animation
    timeline scaled to match, remembered locally. Prove sync at 1x and at the top speed.
22. **A big inlined audio file can show 0:00 duration for a few seconds** while it decodes. It fills in on its own.

## Process rules

23. **Design and editing go to the strongest model; capture, TTS setup, file reading and fact-checks go to a cheaper
    one.**
24. **Spend plan before any paid call** (image-to-3D, image models, cloud TTS): per item, cost, retries, acceptance
    check, and a cap. On the reference run, six image-to-3D props cost $2.40 against a $3.00 cap; the product demo
    spent nothing (all graphics drawn in SVG, CSS and GSAP).
25. **Drafts go to the owner first.** The owner posts; the agent never sends to the audience.
26. **Label every proof image** you send for review with what it shows (scene, before/after).

## Time, from the two runs

| Step | Time |
|---|---|
| Voice setup + 3 candidates | about 10 min |
| 33 lines rendered | about 3 min |
| Interactive explainer, first run (incl. two style resets) | about 40 min; a repeat 25-35 min |
| App capture, first round | about 70 min (a second round of 9 flows took longer) |
| Design + edit by the strongest model | about 30-35 min per cut |
| Frame render, about 2:45 at 1080p30, 10 workers | about 6 min; full rebuild about 10 min |
