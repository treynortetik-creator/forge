# Model routing by shot type (checked 2026-10-14)

Everything here is an OBSERVATION from real paid runs, mostly one 3:39 music video made on 2026-10-14 (about 60 generated clips, 50-odd shots, roughly $35 all-in including tests and three rounds of fixes). Video models change weekly. Before a big run, re-read `GET https://openrouter.ai/api/v1/videos/models` (free, no key; prices are in `pricing_skus`) and do one cheap paid probe. When this page and the live API disagree, the API wins: update `scripts/video/data/model-routing.json`.

## The routing table

| Shot type | Model | Input | Price (2026-10-14) | Why |
|---|---|---|---|---|
| Sung close-up or medium | **HeyGen Video 1**, 480p | keyframe + **vocal-stem** slice, both as `input_references` | listed $0.07/s at 480p with a reference; billed $0.035/s | audio match 0.82-0.99 on eight close-ups; Hailuo-level staging for well under half the price |
| Sung band wide, hero performance | **Hailuo 3**, 2K only | keyframe + **full-mix** slice | $0.13/s + $0.04 per reference image | faces hold at width; the full mix makes hands and drums move to the music |
| Band shot in an instrumental | **Hailuo 3** | keyframe + **instruments-only** stem mix, "nobody sings, all mouths stay closed" | as above | nobody mouths words, heads and hands still move to the beat |
| Silent emotional acting (fear, grief, a scream, a tear) | **Hailuo 3 Max**, 480p | first frame only | $0.05/s | beat Seedance 1.5 Pro head-to-head on the same frame; took faces Seedance 2.5 refused |
| Physical action, state changes, no-face physics | **Seedance 2.5**, 480p | first frame (or text only) | $0.08-0.10/s | the only one that got "candles snuffed row by row", "doors blow open", a one-handed yank right |
| Cheap silent shots and simple inserts | **Seedance 1.5 Pro**, 480p | first frame (or text only) | about $0.012/s ($0.049 per 4 s) | took every photoreal face in the video; fine for simple motion |

Shot fields that drive this: `sing`, `framing` (close / medium / wide), `kind` (performance / acting / action / insert / establishing), `audio_ref`. A shot's own `model` beats every rule.

## Render SD for phone-first social

480p (854x480) is enough when most viewers watch on a phone, and it roughly halves or quarters the per-second price on every model that offers it. Hailuo 3 is 2K only: use that headroom for a post-production sweep (below) and downscale.

## Model notes

- **HeyGen Video 1.** Rejects `frame_images` (first_frame) together with references: send image and audio both as `input_references`. It passes the reference audio through into its soundtrack (so `sync_offset.py` can measure it) and its video starts at pts ~0.083 s. It invents props near the mouth: a microphone the keyframe never had, a black leather glove on the mic hand. Say "no microphone and no mic stand anywhere in frame, hands out of frame, mouth fully visible" unless the mic is in the keyframe.
- **Hailuo 3.** Copies the keyframe faithfully, flaws included: a human hand drawn on a werewolf stayed human for the whole clip, a gripped mic stand stayed gripped. Non-singers in a wide mouthed along in about half the takes even with "mouth closed" per character; a crop in post was the reliable fix. Prompted camera sweeps barely moved.
- **Hailuo 3 Max.** Pads its frames with a repeated frame about every 4th (visible judder): `chain_join.py align --dedupe` drops them and re-interpolates. One take jumped to a close-up mid-clip (say "one continuous wide shot"); one changed a character's hair colour.
- **Seedance 2.5.** Refused photoreal faces as `InputImageSensitiveContentDetected.PrivacyInformation` ("may contain real person"), creatures with photoreal faces included, per image, at no charge. Audio only works when the keyframe is in `input_references`; a pinned `first_frame` silently drops the audio.
- **Seedance 1.5 Pro.** Weak at physics: "the candles go out" grew a giant candle; "boots walk the aisle" became giant stomping boots. Re-route those to Seedance 2.5.
- **HeyGen Avatar IV.** Exact audio passthrough (match 1.00) but a static talking head that reframes tight. Rejected for performance shots.

## Long multi-scene clips (Wan 3.0, Seedance 2.5, up to 30 s)

Asked for several scenes in one request ("cut to ... at 4.2 s"), Wan 3.0 landed its cuts within 0.05 s of the targets and Seedance 2.5 within 0.4 s. That looks like a shortcut and mostly is not:

- Only the first frame is pinned, so **identity drifts after scene 1**: a costume changed, a hidden face showed, a main character vanished from scene 6 of a 24 s request.
- **Bodies and scale go wrong**: a character grew to giant size by the last scene; a covered body was uncovered.
- Rule: at most one scene set per request (all scenes in the same location with the same characters as the keyframe), about 13 s max, or plain single shots. Character-free scenes (a staircase, lightning, a macro insert) chain more safely.
- **Grok Imagine 1.5 Lite morphs** between scenes instead of hard-cutting (max frame difference 8/255): no use for cut sequences. Seedance 2.0 Mini missed a cut by 0.6 s.

Rank long-clip tests by the whole image, not by cut timing: the take with perfect cuts was rejected on sight for a scale jump the timing metric could not see.

## When a shot is refused

A refusal is free. Do not edit the image to sneak it past a filter; give the shot a `model` override (Hailuo 3 Max for silent acting, Hailuo 3 for sung) and re-run with `--only`. Another project reports that a face refused as a first frame sometimes passes as a reference image (`input_references`); untested here.

## Spend

- Check the provider key's own limit before a big batch: an OpenRouter key's monthly cap halted a fix round mid-run with 403 "Key limit exceeded" while the account still had credit. `GET https://openrouter.ai/api/v1/key` shows limit, usage and remaining.
- Set a cap per round (`--max-usd`), not one for the project. Rounds on 2026-10-14: tests $7.29, production $8.62 (retries $2.30 of it), fixes $1.79 / $6.22 / $5.32.
- Budget roughly 2x the seconds the final cut uses: first takes, one retry each, and note rounds (another project measured 1.9x and 2.0x).
