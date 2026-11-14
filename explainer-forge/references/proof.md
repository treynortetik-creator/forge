# Proof checklist

Run all of it before anyone else sees a cut. A script's green is a claim until you have opened the PNGs.

| Check | Command | Pass |
|---|---|---|
| Every line said right | `render_lines.py --check` | WER under 0.10 on every line, every `hyp` read, product names listened to by a person |
| Pace | `stitch_narration.py` output + `cue-table.md` | about the agreed wpm; tempo at or under 1.25 |
| Runtime | `cues.json` total | inside the agreed cap (default 3:00-3:30, never over 5:00) |
| Every scene rendered and looked at | `verify_video.sh` → `review/sheet-*.png` (1 frame / 2 s) | every sheet read: no stray ring, no double crossfade, no overflow, no blank flash, no caption over a callout |
| Callouts land | `ring_check.mjs` | no "NEVER fully visible"; every crop read; ring on its target to the pixel |
| A/V sync | `verify_video.sh` | under about 50 ms at the first line of the first, middle and last scene |
| Captions | `<name>.srt` + sheets | 2 rows max, real spellings, readable over footage |
| Sample data | sheets | the badge is on every footage frame; every name on screen is fictional |
| No real people | `name_check.py --names people.txt` on script, lines, captions, page, notes | 0 hits; every capitalised pair read |
| Facts | the source material | every claim in the script matches what the product does today |
| Interactive only | `deck_proof.mjs`, then `--sync cues.json` at 1x and the top speed | PNGs read, nothing under 18 px, 0 overflow, 0 sync mismatches |
| Size | `ls -l` | MP4 720p copy under about 35 MB for chat; HTML under about 10 MB |

Then a person watches the whole thing once at 1x with sound. They catch what no check does.
