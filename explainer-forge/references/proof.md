# Proof checklist

Run all of it before anyone else sees a cut. A script's green is a claim until you have opened the PNGs.

| Check | Command | Pass |
|---|---|---|
| Every line said right | `render_lines.py --check` | WER under 0.10 on every line, every `hyp` read, product names listened to by a person |
| Pace | `stitch_narration.py` output + `cue-table.md`, or `audio_build.py` output | about the agreed wpm (state speaking or overall); tempo about 0.8 to 1.25 |
| Runtime | `cues.json` total | inside the format's agreed length (profiles/: review explainer or demo 3:00-3:30, never over 5:00; concept video about 4:00-5:00; story film about 2:00) |
| Every scene rendered and looked at | `verify_video.sh` → `review/sheet-*.png` (1 frame / 2 s) | every sheet read: no stray ring, no double crossfade, no overflow, no blank flash, no caption over a callout |
| Callouts land | `ring_check.mjs` | no "NEVER fully visible"; every crop read; ring on its target to the pixel |
| A/V sync, per-line clips | `verify_video.sh` | under about 50 ms at the first line of the first, middle and last scene |
| A/V sync, one take | `sync_check.py` on the FINAL audio | report mean, median, worst; plan for 150 ms, read every chunk over it (`SYNC_LIMIT_MS=150` for `verify_video.sh`) |
| Take read back | `take_check.py` | every `replace`/`delete` in the middle read; an `insert` at the end is a made-up tail the build trims |
| Dead air | `dead_air.py` (also run by `proof.mjs`) | no silence over 1.2 s, in the cue sheet or in the audio |
| Text size | `proof.mjs --min-px 24` | no visible text under the floor at any proof still, measured after camera scale |
| Page errors | `proof.mjs` | 0 |
| Captions | `<name>.srt` + sheets | 2 rows max, real spellings, readable over footage |
| Sample data | sheets | the badge is on every footage frame; every name on screen is fictional |
| No real people | `name_check.py --names people.txt` on script, lines, captions, page, notes | 0 hits; every capitalised pair read |
| Facts | the source material | every claim in the script matches what the product does today |
| Interactive only | `deck_proof.mjs`, then `--sync cues.json` at 1x and the top speed | PNGs read, nothing under 18 px, 0 overflow, 0 sync mismatches |
| Size | `ls -l` | MP4 720p copy under about 35 MB for chat; HTML under about 10 MB |

Then a person watches the whole thing once at 1x with sound. They catch what no check does.
