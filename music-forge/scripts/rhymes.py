#!/usr/bin/env python3
"""
rhymes.py - rhyme candidates from the Datamuse API, with syllable counts, minus the
cliche list. Standard library only, no API key.

    python3 rhymes.py window
    python3 rhymes.py window --syllables 2 --limit 20
    python3 rhymes.py window --json

Perfect rhymes come from rel_rhy, near rhymes from rel_nry; both ask for md=s so each
word carries its syllable count. Words (and phrases) that appear in data/cliches.txt are
dropped and reported as filtered, so the list does not hand you the thing you are trying
to stay away from.

What this does NOT do: judge whether a candidate fits your line, your meaning, or your
voice. It is a rhyming dictionary. Datamuse also returns rare words and proper nouns;
the model or the writer picks.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CLICHES = os.path.join(HERE, "data", "cliches.txt")
API = "https://api.datamuse.com/words"


def load_cliche_regex(path):
    pats = []
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                e = raw.split("#", 1)[0].strip().lower()
                if not e:
                    continue
                body = r"\s+".join(re.escape(p) for p in e.split())
                if " " not in e:
                    body += r"(?:s|es|ed|ing|d)?"
                pats.append(re.compile(r"(?<![a-z])" + body + r"(?![a-z])"))
    except OSError:
        pass
    return pats


def query(rel, word, limit):
    qs = urllib.parse.urlencode({rel: word, "md": "s", "max": limit})
    req = urllib.request.Request(f"{API}?{qs}", headers={"User-Agent": "music-forge/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        sys.exit(f"Datamuse request failed ({rel}={word}): {e}")


def main():
    ap = argparse.ArgumentParser(description="Perfect + near rhymes via Datamuse, cliches removed.")
    ap.add_argument("word")
    ap.add_argument("--limit", type=int, default=40, help="max results per list (default 40)")
    ap.add_argument("--syllables", type=int, help="only candidates with exactly this many syllables")
    ap.add_argument("--keep-cliches", action="store_true", help="do not filter the cliche list")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    word = a.word.strip().lower()
    cl = [] if a.keep_cliches else load_cliche_regex(CLICHES)
    out = {"word": word, "perfect": [], "near": [], "filtered_cliches": []}
    for key, rel in (("perfect", "rel_rhy"), ("near", "rel_nry")):
        seen = {w["word"] for w in out["perfect"]} if key == "near" else set()
        for item in query(rel, word, a.limit):
            w = item["word"]
            if w == word or w in seen:
                continue
            if any(p.search(w.lower()) for p in cl):
                out["filtered_cliches"].append(w)
                continue
            syl = item.get("numSyllables")
            if a.syllables and syl != a.syllables:
                continue
            out[key].append({"word": w, "syllables": syl, "score": item.get("score")})

    if a.json:
        print(json.dumps(out, indent=2))
        return
    for key, title in (("perfect", "PERFECT"), ("near", "NEAR")):
        print(f"{title} rhymes for '{word}' ({len(out[key])})")
        by_syl = {}
        for it in out[key]:
            by_syl.setdefault(it["syllables"] or 0, []).append(it["word"])
        for s in sorted(by_syl):
            print(f"  {s} syl: " + ", ".join(by_syl[s]))
        if not out[key]:
            print("  none" + ("  (Datamuse often returns nothing for near rhymes of common words)"
                              if key == "near" else ""))
    if out["filtered_cliches"]:
        print("filtered (on the cliche list): " + ", ".join(out["filtered_cliches"]))


if __name__ == "__main__":
    main()
