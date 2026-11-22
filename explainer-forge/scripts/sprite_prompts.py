#!/usr/bin/env python3
"""Assemble one image prompt per sprite: the shared style header + the item line (+ your character block).

  python3 sprite_prompts.py --items items.json --out prompts [--header prompt-header.txt] [--character character.txt]
                            [--refs-dir refs] [--only name ...]

items.json: {"items": {"parcel": "a cardboard parcel with tape and a label, three-quarter view", ...},
             "refs": {"parcel": ["parcel-example.png"]}}      (refs optional, per item, file names inside --refs-dir; a missing file is an error)
Each prompt = header + "OBJECT: <item>" + the character block (only for items listed under "characters", if given) +
the reference-attachment line. Writes prompts/<name>.txt and prompts/index.json (name -> reference files to ATTACH).
The script never calls an image model: it only makes the prompts reproducible and keeps them in the project, so a
batch can be re-run or one sprite regenerated later with the same words.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HEADER = os.path.join(os.path.dirname(HERE), "templates", "sprites", "prompt-header.txt")


def build_prompt(header, item_line, character=None, refs=None):
    parts = [header.strip(), "", "OBJECT: " + item_line.strip()]
    if character:
        parts += ["", "CHARACTER (restate every time, never rely on the reference alone):", character.strip()]
    if refs:
        parts += ["", "REFERENCE IMAGES ATTACHED: " + ", ".join(refs) + ". Match their material, palette, lighting and proportions exactly; "
                  "do not copy their pose or layout."]
    return "\n".join(parts) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--header", default=DEFAULT_HEADER)
    ap.add_argument("--character", help="text file describing your recurring character in words")
    ap.add_argument("--refs-dir", help="folder holding the reference images named under \"refs\" in items.json; each must exist, index.json gets full paths")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    spec = json.load(open(a.items))
    items = spec["items"]
    refs = spec.get("refs", {})
    chars = set(spec.get("characters", []))
    header = open(a.header, encoding="utf-8").read()
    character = open(a.character, encoding="utf-8").read() if a.character else None
    os.makedirs(a.out, exist_ok=True)
    index = {}
    for name, line in items.items():
        if a.only and name not in a.only:
            continue
        rl = refs.get(name, [])
        if rl:
            if not a.refs_dir:
                sys.exit(f"{name}: has refs {rl} but no --refs-dir was given")
            rl = [os.path.join(os.path.abspath(a.refs_dir), r) for r in rl]
            gone = [r for r in rl if not os.path.isfile(r)]
            if gone:
                sys.exit(f"{name}: reference image(s) not found: {gone}")
        txt = build_prompt(header, line, character if name in chars else None, [os.path.basename(r) for r in rl])
        with open(os.path.join(a.out, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(txt)
        index[name] = rl
        print("wrote", os.path.join(a.out, name + ".txt"), len(txt.split()), "words")
    with open(os.path.join(a.out, "index.json"), "w") as f:
        json.dump(index, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
