# Free fixes in post (2026-10-14)

Post costs nothing and never invents a person. Reach for it before paying for a retake.

## Camera sweeps
Generate wides locked-off, then sweep in ffmpeg. The viewer's verdict on the first one: "great, nice trick"; the paid prompted sweep on the same shot barely moved.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/post_sweep.py clips/22-band-wide.mp4 clips/22-band-wide-sweep.mp4                 # push-in, left to right
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/post_sweep.py in.mp4 out.mp4 --zoom 1.0 1.3 --pan 0.5 0.5                         # straight push-in
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/post_sweep.py in.mp4 --print-filter                                               # the -vf string only
```

The filter: a per-frame `scale` (eval=frame) for the push-in, then a fixed-size `crop` whose x follows a cosine ease, `(1-cos(PI*t/D))/2`, so the move starts and ends gently. A 2K source swept to 854x480 keeps full detail at the deepest zoom. Copy each sweep's output into the plan as that shot's clip (or `--prefer-dir`).

## Crops and reframes
A non-singer mouthing along, a stray third hand, a prop that should not be there: a tight crop that leaves it out of frame fixed it three times where retakes failed. Crop, then sweep, so the crop does not feel static.

## Grades
A shot reused as a recurring POV (the same doors at four points in the song) can be regraded per use with `eq` and `colorbalance` (darker, warmer, a vignette) instead of regenerated. Check the result is still readable; one regrade came out too dark.

## Retiming
- An action that lands late: speed the clip up (`setpts=PTS/1.235`) so it lands inside the slot.
- A short good take: slow its first second or two with motion interpolation (`minterpolate`) instead of regenerating.
- An ending: slow the last shot with frame blending and fade to black, padding the audio with silence.

## Text on surfaces
Never generate text. Generate the surface blank, then:
1. Lay out the type with ImageMagick (or Pillow) at a frame where the surface is fully in view, supersampled.
2. Track the surface per frame (feature matching such as SIFT with a RANSAC homography to that reference frame, corners smoothed over time).
3. Warp the type onto each frame and overlay it with ffmpeg.
One programme insert tracked through a push-in with 3.3 px max smoothing correction this way.

## Review strips
For every clip, a strip of frames at 2 fps (`ffmpeg -vf "fps=2,scale=320:-2,tile=6xN"`) shows mid-clip failures that a single midpoint frame misses: duplicate characters, scale jumps, a hand growing, a face showing that must stay hidden.
