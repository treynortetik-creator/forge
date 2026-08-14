---
name: render-diff
description: "Compare two exports and mark exactly where they differ — video with timecoded markers and an EDL, stills with a bounding box and heat map, audio with a phase-invert null test. Use when checking whether two renders, exports, versions or deliverables are actually identical."
---

# Render Diff

You answer one question: **are these two files the same, and if not, where?**

You do not judge whether a change was correct. You find it and put a marker on it.

## Run it

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_diff.py a.mov b.mov
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_diff.py a.mov b.mov --edl markers.edl
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_diff.py a.png b.png --out diff.png
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_diff.py a.wav b.wav
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_diff.py a.mov b.mov --json
```

Exit 0 = same, 1 = differs, 2 = could not compare. Needs `ffmpeg`; stills need Pillow.

## The problem this solves

The task it replaces, in a practitioner's own words: drop one export over the other in
difference mode and scrub the whole thing, one clip at a time. The failure mode is that
**the difference can be one corner of the frame for one second in a two-hour sequence**,
and human eyes miss it. The commercial tool that does this properly starts in the mid five
figures.

## The hard part is the threshold, not the diff

Two exports of the same timeline are never bit-identical. A different encoder, bitrate or
colour pipeline moves every pixel a little. So an absolute PSNR threshold either flags the
entire file or nothing at all, depending on codec — and a tool that cries wolf on a routine
re-encode is one people stop running.

**The threshold is derived from the pair being compared.** Measure per-frame PSNR across
the whole comparison, take the median as that pair's own encoding-noise floor, and flag
frames that fall well below it. A uniform re-encode has a tight distribution and yields
nothing. One bad second is an outlier.

Verified both directions: CRF 18 against CRF 32, and against a completely different codec,
produce **zero** markers. A 70×70 box for one second in a 640×360 frame produces exactly
**one** marker, in the right second.

Use `--absolute DB` when you want a fixed bar instead, and `--drop DB` to change how far
below the baseline counts (default 6 dB).

## Read the output in this order

1. **Structural findings first.** Different resolution, framerate, duration or stream
   count is *the* finding. If resolution or framerate differ the tool refuses to produce
   frame markers at all, because they would be confidently wrong — a scale invents
   differences and a framerate mismatch drifts every marker after the first.
2. **The baseline and threshold.** These tell you whether the comparison was meaningful.
   A baseline around 50 dB means the files are near-identical; around 30 dB means a heavy
   re-encode, and small real differences may hide inside that noise. Say so.
3. **The markers.** Timecode in, timecode out, frame count, worst dB.

## Audio

The phase-invert null test is exact, not statistical: sum A with an inverted B and identical
audio cancels to digital silence. Anything above roughly −90 dBFS peak is a real difference;
above −60 dBFS it is audible. A 0.1% gain change shows up at −78 dBFS, so treat a small
residual as real rather than as rounding.

## What it does not do

PSNR is a whole-frame number. It tells you **where to look**, not what changed, and it
cannot distinguish an intended change from a mistake. Say that when you report. Never let
"no markers" be read as "the render is correct" — it means the two files match each other,
which is a different claim.

## Verify your fixture before you trust a null result

When testing this or anything like it, **check that your two test files actually differ**
before concluding the tool missed something. While building this, an ffmpeg filter meant to
punch a 10ms hole in a WAV silently did nothing; both files were byte-identical and the
tool's correct "nulls to silence" verdict looked exactly like a bug. The test suite now
asserts the fixture's own md5 differs before checking the verdict.

## Tests

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/test_render_diff.py
```

31 cases, fixtures generated with ffmpeg at run time. The first three assert the tool stays
**silent** on heavy re-encodes; the next four assert it **finds** one bad second. Those pull
in opposite directions, and a version that satisfies only one is useless.
