#!/usr/bin/env python3
"""Check ONE raw take against the script before anything is built from it.

  python3 take_check.py --take audio/take-raw.wav --narration narration.json [--out audio/take-raw.stt.json]
                        [--words-json words.json] [--gap 1.0]

Transcribes the take with whisper (mlx-whisper, Apple Silicon; or pass --words-json with word timestamps from any
tool), diffs the heard words against the script's SPOKEN words, and lists silences longer than --gap seconds.
Read every non-equal line: an 'insert' at the end is usually a made-up tail the audio build will trim; a 'replace' or
'delete' in the middle is a misread line, and a one-take render can only be fixed by re-rendering the take (or by
rewording the line and the spoken respelling). Exit 1 when the match ratio is under --min-ratio or any script word
was skipped or replaced (an 'insert' at the end is fine: the build trims it).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_lib as nl  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--take", help="raw take wav")
    ap.add_argument("--narration", required=True, help="narration.json")
    ap.add_argument("--out", help="where to save the transcript JSON (default <take>.stt.json)")
    ap.add_argument("--words-json", help="skip whisper: word timestamps [[word,start,end],...] or {\"words\":[...]}")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    ap.add_argument("--gap", type=float, default=1.0, help="report silences longer than this many seconds")
    ap.add_argument("--min-ratio", type=float, default=0.97, help="exit 1 when the heard words match the script less well than this, or a script word was skipped or replaced (default 0.97)")
    a = ap.parse_args(argv)
    if not a.take and not a.words_json:
        ap.error("give --take or --words-json")
    scenes = nl.load_json(a.narration)
    _, ref = nl.flatten(scenes)
    ref_words = [w for _, w in ref]
    W = nl.words_from_json(a.words_json) if a.words_json else nl.transcribe_words(a.take, a.model)
    hyp = nl.hyp_words(W)
    ratio, bad = nl.diff_script_vs_heard(ref_words, hyp)
    print("script words", len(ref_words), "heard", len(hyp), "ratio", round(ratio, 3), "take ends", round(W[-1][2], 1), "s")
    for b in bad:
        print(b)
    gaps = nl.long_gaps(W, a.gap)
    print(f"silences over {a.gap} s (end of previous word, length):", gaps)
    if a.take:
        out = a.out or os.path.splitext(a.take)[0] + ".stt.json"
        json.dump({"words": W}, open(out, "w"))
        print("saved", out)
    mid = [b for b in bad if b[0] in ("delete", "replace") and b[1]]
    if ratio < a.min_ratio or mid:
        print(f"TAKE FAILED: ratio {ratio:.3f} (min {a.min_ratio})" + (f", {len(mid)} misread or skipped passage(s) in the take" if mid else "") +
              ". Re-render the take (new --seed) or reword the line and its respelling; do not build from it.")
        sys.exit(1)
    print("take ok")


if __name__ == "__main__":
    main()
