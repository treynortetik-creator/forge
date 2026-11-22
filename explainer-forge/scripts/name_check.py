#!/usr/bin/env python3
"""Name check: no real people in the script, captions, slides, notes or the final HTML. Run it before anything ships.

  python3 name_check.py [--names people.txt] FILE_OR_DIR [...] [--allow allow.txt] [--overlay DIR] [--candidates-only]

people.txt: one name per line (everyone in the source material: requesters, approvers, assignees, commenters, anyone
quoted). Each full name AND each first and last name of 3+ letters is searched, case-insensitive, whole words.
Also lists capitalised "First Last" pairs that are not in --allow (product names, fictional sample names), as
candidates for a human to read: a heuristic, never proof of absence.
--names and --allow default to names.txt and allow.txt in the private overlay folder (--overlay, then
$EXPLAINER_FORGE_OVERLAY, then ~/.config/explainer-forge/overlay; see overlay.py). With no names list at all the
script exits 2 (a check against nobody proves nothing); --candidates-only prints just the capitalised pairs and exits 0.
Every line is scanned in full; only base64 data: payloads are skipped.
Scans .md .txt .json .srt .html .js .css files. Exit 1 on any hit from people.txt, 2 on a usage or setup error.
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overlay as ov

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("paths", nargs="+"); ap.add_argument("--names"); ap.add_argument("--allow"); ap.add_argument("--overlay")
ap.add_argument("--candidates-only", action="store_true", help="no names list: only list capitalised pairs (exit 0). Without this flag a missing names list is an error")
a = ap.parse_args()
if a.overlay and not os.path.isdir(os.path.expanduser(a.overlay)):
    print(f"ERROR: --overlay {a.overlay!r} is not a folder", file=sys.stderr); sys.exit(2)
names_path = a.names or ov.find("names.txt", a.overlay)
allow_path = a.allow or ov.find("allow.txt", a.overlay)
if names_path:
    names = [l.strip() for l in open(names_path) if l.strip() and not l.startswith("#")]
    print("names list:", names_path, f"({len(names)} names)")
else:
    if not a.candidates_only:
        print("ERROR: no names list (--names FILE, or names.txt in the overlay folder). A check against nobody proves nothing: "
              "pass one, or --candidates-only to just list capitalised pairs", file=sys.stderr)
        sys.exit(2)
    names = []
    print("WARNING: no names list: only listing capitalised pairs, not checking anyone")
allow = {l.strip().lower() for l in open(allow_path)} if allow_path else set()
terms = set()
for n in names:
    terms.add(n)
    terms.update(p for p in n.split() if len(p) >= 3)
pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b", re.I) if terms else None
pair = re.compile(r"\b([A-Z][a-z]{2,} [A-Z][a-z]{2,})\b")
B64 = re.compile(r"data:[\w/+.-]*;base64,[A-Za-z0-9+/=]+")
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
        line = B64.sub("data:", line)     # drop inlined base64 payloads, then scan the WHOLE line (a cue sheet is one long line)
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
