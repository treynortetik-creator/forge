#!/usr/bin/env python3
"""Script markdown -> narration.json: one chunk per sentence, caption text kept apart from the spoken respelling.

  python3 make_narration.py script.md --out narration.json [--say-map saymap.json] [--plain] [--list]

Script contract (templates/script-template.md):
    ## Scene 1. Title
    **Narration (40 words):**
    The sentences the narrator reads. One paragraph or several.

    **On screen:**
    Anything the viewer sees. Ignored here.

`show` = the sentence as written (captions, proof). `say` = what the voice reads, produced by the say map
(templates/saymap.example.json): acronyms spelled out ("AI" -> "A I"), numbers and clock times as words, names
respelled so the voice says them right. `say` appears only when it differs from `show`, so a chunk without it is read
exactly as written. Pure Python, no models.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_lib as nl  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="script markdown")
    ap.add_argument("--out", default="narration.json", help="output JSON (default narration.json)")
    ap.add_argument("--say-map", help="JSON respelling map (replace / regex / drop); none = read as written")
    ap.add_argument("--plain", action="store_true", help="no **Narration** label: the whole scene body is narration")
    ap.add_argument("--list", action="store_true", help="also print every chunk with its spoken form")
    a = ap.parse_args(argv)
    md = open(a.script, encoding="utf-8").read()
    scenes = nl.parse_script(md, plain=a.plain)
    if not scenes:
        raise SystemExit("no scenes with narration found: expected '## Scene N. Title' + '**Narration (N words):**' (or use --plain)")
    sm = nl.load_json(a.say_map) if a.say_map else None
    out = nl.build_narration(scenes, sm)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    n_words = sum(len(nl.words(c["show"])) for s in out for c in s["chunks"])
    print(f"{len(out)} scenes, {sum(len(s['chunks']) for s in out)} chunks, {n_words} words -> {a.out}")
    respelled = sum(1 for s in out for c in s["chunks"] if "say" in c)
    print(f"{respelled} chunks have a spoken respelling")
    if a.list:
        for s in out:
            for c in s["chunks"]:
                print(c["id"], "|", c.get("say", c["show"]))


if __name__ == "__main__":
    main()
