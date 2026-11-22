#!/usr/bin/env python3
"""Dead-air check: any stretch of the narration with no speech longer than --max seconds.

  python3 dead_air.py --cues audio/cues.json [--audio audio/narration.m4a] [--max 1.2]

From the cue sheet: the head before the first word, every gap between two chunks, and the tail after the last word.
With --audio the file itself is scanned with ffmpeg silencedetect (-40 dB), which also catches a long gap INSIDE a
chunk that the cue sheet cannot see. A scene break may be longer than a sentence break on purpose (a held shot), so
the output says where each one is; the default 1.2 s is the cap the approved cut kept to. Exit 1 if anything is over.
"""
import argparse
import json
import re
import subprocess
import sys


def gaps_from_cues(cues, mx):
    """-> [(kind, start, length)] for every silence over mx seconds, from the cue sheet alone. Pure function."""
    ch = cues["chunks"]
    out = []
    if ch and ch[0]["start"] > mx:
        out.append(("head", 0.0, ch[0]["start"]))
    for a, b in zip(ch, ch[1:]):
        g = b["start"] - a["end"]
        if g > mx:
            out.append((f"{a['id']} -> {b['id']}" + (" (scene break)" if a["scene"] != b["scene"] else ""), a["end"], g))
    if ch and cues["duration"] - ch[-1]["end"] > mx:
        out.append(("tail", ch[-1]["end"], cues["duration"] - ch[-1]["end"]))
    return out


def silences(audio, mx, noise="-40dB"):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", f"silencedetect=n={noise}:d={mx}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    du = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r)]
    return list(zip(st, du))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cues", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--max", type=float, default=1.2)
    a = ap.parse_args(argv)
    cues = json.load(open(a.cues))
    bad = gaps_from_cues(cues, a.max)
    for k, s, g in bad:
        print(f"OVER {a.max} s  {k}: {g:.2f} s of silence from {s:.2f} s")
    if a.audio:
        for s, d in silences(a.audio, a.max):
            print(f"OVER {a.max} s  audio silence {d:.2f} s from {s:.2f} s")
            bad.append(("audio", s, d))
    longest = max((b["start"] - x["end"] for x, b in zip(cues["chunks"], cues["chunks"][1:])), default=0.0)
    print(f"longest gap between chunks {longest:.2f} s; {len(bad)} over {a.max} s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
