# Capturing a web app for an explainer

## Data and privacy
- Use the app's mock, demo or sample-data mode only. Confirm every name, number and record on screen is fictional.
- Put a small "Sample data · fictional names" badge on every footage frame (`footage(t0, t1)` in the timeline).
- Never capture a real customer, patient, employee or internal record, even blurred. Fake data is cheaper than a
  privacy review.

## Recording
- Playwright, Chromium headless, 1920x1080 at 30 fps, through a CDP screencast assembled with ffmpeg.
- Inject a fake macOS-style arrow cursor (SVG) with a click ripple through `addInitScript`; headless has no cursor.
- Type at 20-25 characters per second. Hold 1-1.5 s after each result appears.
- Start every take from a fresh state (new session, new documents). Earlier takes leave edits behind.

## Waits
- Time-lapse long waits down to about 3-4 s of visible progress. Log the cut points in the manifest and show a
  "Sped up" tag over that span in the edit (`sped(t0, t1)`). Make no on-screen speed claims.

## The manifest is the editor's contract
Per clip, write down: timestamps of what is on screen, the names and numbers shown, cut points, and the timestamps
of anything ugly (debug text, model self-talk, awkward copy, a mock-data notice). The editor places every zoom, ring
and patch from it.

## Ugly UI text
- Cover it with a patch in the element's own colour that tracks it frame by frame as the page scrolls:
  `track_patch.py` gives a per-frame y and background colour; hide the patch where the match error is high.
- A whole panel that comes and goes (a debug column, a side chat): time a cover from `detect_band.py`.
- Or frame it out with `focus()`. At full screen, patches show more: render that span and look.

## Footage in the edit
- `prep_media.py` re-encodes clips with a 6-frame GOP so per-frame seeks are exact.
- Crossfade layers over about 0.15 s while HOLDING the incoming clip's first frame, so a cut never shows frames
  outside the chosen range.
- Zoom in only to make a number readable, then pull back.
