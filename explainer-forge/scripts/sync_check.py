#!/usr/bin/env python3
"""Sync check on the FINAL audio, the file the page and the MP4 actually play.

  python3 sync_check.py --audio audio/narration.m4a --cues audio/cues.json --narration narration.json
                        [--out audio/sync.json] [--words-json words.json]   (exit 1 when a scene opening is over --over)

Transcribes the final file again (a fresh whisper pass over the final file, not the build's own alignment), finds
where every chunk's first and last script word are heard, and compares those times with the cue sheet the animation is
keyed to. Reports the mean, median and worst offset and the chunks more than 150 ms off. The file's very first
chunk is left out of the mean and worst: whisper's timestamp for the first word is a known artefact.
CAVEAT: the model is the same family that timed the cues, so this cannot see a bias the model itself has (a word
start that is consistently early or late). That is why, with --audio, every SCENE-OPENING cue is also compared with the
measured speech onset (ffmpeg silencedetect, no model): scene_onsets in the output. Those are the cues animation hangs
on; trust them over the whisper offsets. A one-take voice cannot have exact cues the way stitched per-line clips do.
"""
import argparse
import json
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_lib as nl  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio", help="final narration audio (m4a or wav)")
    ap.add_argument("--cues", required=True, help="cues.json from audio_build.py")
    ap.add_argument("--narration", required=True, help="narration.json")
    ap.add_argument("--out", help="output JSON (default sync.json beside the cues)")
    ap.add_argument("--words-json", help="skip whisper: word timestamps for the final audio")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    ap.add_argument("--over", type=float, default=0.15, help="flag chunks off by more than this many seconds")
    a = ap.parse_args(argv)
    if not a.audio and not a.words_json:
        ap.error("give --audio or --words-json")
    cues = nl.load_json(a.cues)
    scenes = nl.load_json(a.narration)
    say = {c["id"]: nl.say_text(c) for s in scenes for c in s["chunks"]}
    W = nl.words_from_json(a.words_json) if a.words_json else nl.transcribe_words(a.audio, a.model)
    hyp = nl.hyp_words(W)
    ref, by_chunk = [], {}
    for c in cues["chunks"]:
        for w in nl.words(say[c["id"]]):
            by_chunk.setdefault(c["id"], []).append(len(ref))
            ref.append(w)
    sm = difflib.SequenceMatcher(None, ref, [h[0] for h in hyp], autojunk=False)
    hit = {}
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            hit[b.a + k] = (hyp[b.b + k][1], hyp[b.b + k][2])
    offs = nl.sync_offsets(cues["chunks"], by_chunk, hit)
    if not offs:
        raise SystemExit("no chunk could be matched: wrong audio for these cues?")
    res = nl.sync_summary(offs, a.over, exclude=[cues["chunks"][0]["id"]])
    res["detail"] = offs
    if a.audio:
        import dead_air
        # speech onsets = ends of silences of at least 0.12 s (same measure verify_video.sh uses)
        import re, subprocess
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.audio, "-af", "silencedetect=n=-40dB:d=0.12", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        onsets = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
        firsts, seen = [], set()
        for c in cues["chunks"]:
            if c["scene"] not in seen:
                seen.add(c["scene"])
                firsts.append((c["scene"], c["start"]))
        so = nl.onset_offsets(firsts, onsets)
        res["scene_onsets"] = so
        if so:
            res["scene_onset_worst_s"] = max(abs(o["off"]) for o in so)
            res["scene_onsets_over"] = [o["scene"] for o in so if abs(o["off"]) > a.over]
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.cues)), "sync.json")
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "detail"}, indent=1))
    print("saved", out)
    bad = res.get("scene_onsets_over", [])
    if bad:
        print("scene openings more than", a.over, "s off the measured onset:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
