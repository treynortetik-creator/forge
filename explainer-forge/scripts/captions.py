#!/usr/bin/env python3
"""Word-timed caption chunks plus an .srt, from cues.json and a whisper pass over each stitched clip.

  <voice venv>/bin/python captions.py --build build [--name explainer] [--row 42]

Reads <build>/cues.json and <build>/clips/<id>.wav (both from stitch_narration.py). Each line's `caption` (the real
spelling) is split into chunks of at most 2 rows of about --row characters, preferring punctuation breaks near the
middle; each chunk starts when its first word is spoken. Caption words map to whisper words by position share, so TTS
respellings never leak into captions. Whisper results are cached in <build>/whisper/<id>.json (word timing per clip,
also used by the timeline's W(id, word) helper).

Writes <build>/captions.json and <build>/<name>.srt. Needs mlx-whisper (Apple Silicon); if it is missing, chunks are
spread evenly across each line instead, and the script says so.
"""
import argparse, json, os, re

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--build", required=True); ap.add_argument("--name", default="explainer")
ap.add_argument("--row", type=int, default=42); ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
a = ap.parse_args()
B = a.build; ROW, MAXC = a.row, a.row * 2
WD = os.path.join(B, "whisper"); os.makedirs(WD, exist_ok=True)
cues = json.load(open(os.path.join(B, "cues.json")))
_warned = []


def words_of(i):
    cp = os.path.join(WD, i + ".json")
    if os.path.exists(cp):
        return json.load(open(cp))
    try:
        import mlx_whisper
    except ImportError:
        if not _warned:
            print("mlx-whisper not installed: spreading caption chunks evenly (less accurate)"); _warned.append(1)
        return []
    r = mlx_whisper.transcribe(os.path.join(B, "clips", i + ".wav"), path_or_hf_repo=a.model, word_timestamps=True,
                               language="en", condition_on_previous_text=False)
    w = [{"w": x["word"].strip(), "s": x["start"], "e": x["end"]} for s in r["segments"] for x in s.get("words", [])]
    json.dump(w, open(cp, "w")); return w


def wrap(ws):  # balanced 1-2 rows, or None
    s = " ".join(ws)
    if len(s) <= ROW:
        return [s]
    best = None
    for k in range(1, len(ws)):
        x, y = " ".join(ws[:k]), " ".join(ws[k:])
        if len(x) <= ROW + 2 and len(y) <= ROW + 2:
            sc = abs(len(x) - len(y)) + (0 if re.search(r"[,.;:?!]$", x) else 20)
            if best is None or sc < best[0]:
                best = (sc, [x, y])
    return best[1] if best else None


def split(ws):  # list of word lists, each wrappable in 2 rows
    if wrap(ws) and len(" ".join(ws)) <= MAXC:
        return [ws]
    n = len(ws); best = None
    for k in range(2, n - 1):
        x, y = ws[:k], ws[k:]
        if len(" ".join(x)) > MAXC:
            break
        sc = (0 if re.search(r"[,.;:?!]$", x[-1]) else 6) + abs(len(" ".join(x)) - len(" ".join(y))) / 12 + (8 if len(y) < 3 else 0)
        if best is None or sc < best[0]:
            best = (sc, k)
    if best is None:  # a single very long word run: hard split
        best = (0, max(1, n // 2))
    k = best[1]
    return split(ws[:k]) + split(ws[k:])


chunks, L = [], cues["lines"]
for n, c in enumerate(L):
    cw = c["caption"].split(); ww = words_of(c["id"]); idx = 0
    for p in split(cw):
        if ww:
            j = min(len(ww) - 1, round(idx / len(cw) * len(ww)))
            st = c["start"] + (ww[j]["s"] if idx else max(0.0, ww[0]["s"] - 0.08))
        else:
            st = c["start"] + idx / len(cw) * c["dur"]
        chunks.append({"line": c["id"], "start": round(st, 3), "rows": wrap(p) or [" ".join(p)]})
        idx += len(p)
    nxt = L[n + 1]["start"] if n + 1 < len(L) else cues["total"]
    end = c["end"] + 0.35
    if nxt - c["end"] < 0.6:
        end = nxt
    chunks[-1]["line_end"] = round(min(end, nxt), 3)
for k, ch in enumerate(chunks):
    ch["end"] = ch.pop("line_end") if "line_end" in ch else chunks[k + 1]["start"]
json.dump(chunks, open(os.path.join(B, "captions.json"), "w"), indent=1)


def ts(t):
    ms = round(t * 1000); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


with open(os.path.join(B, f"{a.name}.srt"), "w") as f:
    for k, ch in enumerate(chunks, 1):
        f.write(f"{k}\n{ts(ch['start'])} --> {ts(ch['end'])}\n" + "\n".join(ch["rows"]) + "\n\n")
print(len(chunks), "chunks; longest row", max(len(r) for ch in chunks for r in ch["rows"]))
