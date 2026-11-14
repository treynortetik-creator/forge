#!/usr/bin/env python3
"""Name check: no real people in the script, captions, slides, notes or the final HTML. Run it before anything ships.

  python3 name_check.py --names people.txt FILE_OR_DIR [...] [--allow allow.txt]

people.txt: one name per line (everyone in the source material: requesters, approvers, assignees, commenters, anyone
quoted). Each full name AND each first and last name of 3+ letters is searched, case-insensitive, whole words.
Also lists capitalised "First Last" pairs that are not in --allow (product names, fictional sample names), as
candidates for a human to read: a heuristic, never proof of absence.
Scans .md .txt .json .srt .html .js .css files. Exit 1 on any hit from people.txt.
"""
import argparse, os, re, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("paths", nargs="+"); ap.add_argument("--names", required=True); ap.add_argument("--allow")
a = ap.parse_args()
names = [l.strip() for l in open(a.names) if l.strip() and not l.startswith("#")]
allow = {l.strip().lower() for l in open(a.allow)} if a.allow else set()
terms = set()
for n in names:
    terms.add(n)
    terms.update(p for p in n.split() if len(p) >= 3)
pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b", re.I) if terms else None
pair = re.compile(r"\b([A-Z][a-z]{2,} [A-Z][a-z]{2,})\b")
EXT = (".md", ".txt", ".json", ".srt", ".html", ".js", ".css")
files = []
for p in a.paths:
    if os.path.isdir(p):
        for d, _, fs in os.walk(p):
            if "node_modules" in d or "/vendor" in d: continue
            files += [os.path.join(d, f) for f in fs if f.endswith(EXT)]
    else:
        files.append(p)
hits, cands = 0, {}
for f in files:
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) > 5000:
            line = line[:5000]  # skip the bulk of inlined base64
        if pat:
            for m in pat.finditer(line):
                hits += 1; print(f"HIT  {f}:{i}: {m.group(0)!r}")
        for m in pair.finditer(line):
            if m.group(1).lower() not in allow:
                cands.setdefault(m.group(1), f"{f}:{i}")
for c, where in sorted(cands.items()):
    print(f"read {c!r} (first at {where})")
print(f"{len(files)} files, {hits} name hit(s), {len(cands)} capitalised pair(s) to read")
sys.exit(1 if hits else 0)
