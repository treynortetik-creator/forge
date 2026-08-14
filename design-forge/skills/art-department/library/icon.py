#!/usr/bin/env python3
"""Pull an icon out of the local Iconify sets. No network.

    python3 icon.py tabler:chart-bar              # SVG to stdout
    python3 icon.py tabler:chart-bar -o out.svg
    python3 icon.py tabler:chart-bar --color '#1f2937' --size 32
    python3 icon.py --search chart                 # find a name, all sets
    python3 icon.py --search chart --set healthicons
    python3 icon.py --sets                           # what's installed

Icons render with `currentColor` by default, so they inherit CSS color when
inlined. Pass --color only when the SVG must stand alone.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "icons")


def load(prefix):
    p = os.path.join(ICONS, f"{prefix}.json")
    if not os.path.exists(p):
        sys.exit(f"no set '{prefix}'. Installed: {', '.join(sets())}"
                 f"\nRun: python3 fetch.py icons")
    with open(p) as f:
        return json.load(f)


def sets():
    if not os.path.isdir(ICONS):
        return []
    return sorted(f[:-5] for f in os.listdir(ICONS) if f.endswith(".json"))


def resolve(doc, name):
    """Follow alias chains to a real icon record."""
    seen = set()
    while name in (doc.get("aliases") or {}) and name not in seen:
        seen.add(name)
        name = doc["aliases"][name]["parent"]
    return doc.get("icons", {}).get(name), name


def render(doc, name, color=None, size=None):
    rec, real = resolve(doc, name)
    if not rec:
        near = [k for k in doc.get("icons", {}) if name in k][:8]
        sys.exit(f"'{name}' not in {doc['prefix']}."
                 + (f" Close: {', '.join(near)}" if near else
                    " Try --search."))
    w = rec.get("width", doc.get("width", 16))
    h = rec.get("height", doc.get("height", 16))
    dim = f'width="{size}" height="{size}"' if size else \
          'width="1em" height="1em"'
    body = rec["body"]
    if color:
        body = body.replace("currentColor", color)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" {dim} '
            f'viewBox="0 0 {w} {h}">{body}</svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("icon", nargs="?", help="prefix:name")
    ap.add_argument("-o", "--out")
    ap.add_argument("--color", help="replace currentColor, e.g. '#1f2937'")
    ap.add_argument("--size", type=int, help="px instead of 1em")
    ap.add_argument("--search")
    ap.add_argument("--set", help="limit --search to one set")
    ap.add_argument("--sets", action="store_true")
    a = ap.parse_args()

    if a.sets:
        for s in sets():
            d = load(s)
            info = d.get("info") or {}
            lic = (info.get("license") or {}).get("spdx")
            print(f"  {s:14} {len(d.get('icons', {})):>5} icons  {lic}")
        return 0

    if a.search:
        q = a.search.lower()
        for s in ([a.set] if a.set else sets()):
            d = load(s)
            hits = [k for k in d.get("icons", {}) if q in k.lower()]
            if hits:
                print(f"\n{s} ({len(hits)}):")
                for k in sorted(hits)[:40]:
                    print(f"  {s}:{k}")
                if len(hits) > 40:
                    print(f"  … {len(hits)-40} more")
        return 0

    if not a.icon or ":" not in a.icon:
        ap.error("give an icon as prefix:name, or use --search / --sets")
    prefix, name = a.icon.split(":", 1)
    svg = render(load(prefix), name, a.color, a.size)
    if a.out:
        with open(a.out, "w") as f:
            f.write(svg + "\n")
        print(f"wrote {a.out} ({len(svg)} bytes)")
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
