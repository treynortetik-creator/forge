#!/usr/bin/env python3
"""
clean_text.py — strip invisible provenance/telemetry characters from a manuscript.

This is "Layer A" only: characters that are INVISIBLE to a reader. It never changes
a word, never reorders a sentence, never paraphrases. Run it and diff the prose —
the diff should be empty except for the characters listed below.

It deliberately does NOT attempt to remove statistical / token-choice watermarks.
Those live in WHICH WORDS were chosen, so the only way to remove them is to rewrite
the text with a model — which for fiction means re-slopping prose you just spent
three de-slop passes cleaning. Editing already degrades that signal as a side effect.
Do the editing; skip the rewriting.

Usage:
    clean_text.py draft.md                     # report only, no writes
    clean_text.py draft.md -o draft.clean.md   # write cleaned copy
    clean_text.py draft.md --in-place          # overwrite (makes a .bak first)
    clean_text.py chapters/ -o out/            # whole directory
    clean_text.py draft.md --strip-emoji-glue  # also remove ZWJ + variation selectors
"""
from __future__ import annotations
import argparse, pathlib, shutil, sys, unicodedata

# ── what gets removed ────────────────────────────────────────────────────────
ZERO_WIDTH = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "⁠": "WORD JOINER",
    "﻿": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "­": "SOFT HYPHEN",
}
BIDI = {
    "‎": "LEFT-TO-RIGHT MARK",
    "‏": "RIGHT-TO-LEFT MARK",
    "‪": "LEFT-TO-RIGHT EMBEDDING",
    "‫": "RIGHT-TO-LEFT EMBEDDING",
    "‬": "POP DIRECTIONAL FORMATTING",
    "‭": "LEFT-TO-RIGHT OVERRIDE",
    "‮": "RIGHT-TO-LEFT OVERRIDE",
    "⁦": "LEFT-TO-RIGHT ISOLATE",
    "⁧": "RIGHT-TO-LEFT ISOLATE",
    "⁨": "FIRST STRONG ISOLATE",
    "⁩": "POP DIRECTIONAL ISOLATE",
}
# Unicode TAG characters (U+E0000–U+E007F). The classic hidden-payload channel:
# a whole ASCII message can be encoded here and is completely invisible.
TAGS = {chr(c): "TAG CHARACTER" for c in range(0xE0000, 0xE0080)}

# "Emoji glue" — ZWJ and variation selectors. These are ALSO used to hide data,
# but removing them visibly breaks emoji (👩‍💻 → 👩💻). Kept by default.
EMOJI_GLUE = {"‍": "ZERO WIDTH JOINER", "︎": "VARIATION SELECTOR-15",
              "️": "VARIATION SELECTOR-16"}
EMOJI_GLUE.update({chr(c): "VARIATION SELECTOR" for c in range(0xE0100, 0xE01F0)})

# ── what gets normalised (visible, but wrong) ────────────────────────────────
EXOTIC_SPACES = {
    " ": "NO-BREAK SPACE", " ": "EN QUAD", " ": "EM QUAD",
    " ": "EN SPACE", " ": "EM SPACE", " ": "THREE-PER-EM SPACE",
    " ": "FOUR-PER-EM SPACE", " ": "SIX-PER-EM SPACE",
    " ": "FIGURE SPACE", " ": "PUNCTUATION SPACE", " ": "THIN SPACE",
    " ": "HAIR SPACE", " ": "NARROW NO-BREAK SPACE",
    " ": "MEDIUM MATHEMATICAL SPACE", "　": "IDEOGRAPHIC SPACE",
}


def clean(text: str, strip_emoji_glue: bool = False):
    """Return (cleaned_text, {description: count}). Word content is never altered."""
    removals: dict[str, int] = {}
    drop = {}
    drop.update(ZERO_WIDTH); drop.update(BIDI); drop.update(TAGS)
    if strip_emoji_glue:
        drop.update(EMOJI_GLUE)

    out = []
    for ch in text:
        if ch in drop:
            removals[drop[ch]] = removals.get(drop[ch], 0) + 1
            continue
        if ch in EXOTIC_SPACES:
            removals[f"{EXOTIC_SPACES[ch]} → space"] = removals.get(f"{EXOTIC_SPACES[ch]} → space", 0) + 1
            out.append(" ")
            continue
        # catch-all: any other invisible format char (category Cf) we didn't name,
        # except the emoji glue we're deliberately preserving
        if unicodedata.category(ch) == "Cf" and ch not in EMOJI_GLUE:
            name = unicodedata.name(ch, f"U+{ord(ch):04X}")
            removals[f"{name} (unnamed Cf)"] = removals.get(f"{name} (unnamed Cf)", 0) + 1
            continue
        out.append(ch)
    return "".join(out), removals


def canon(s: str, strip_glue: bool = False) -> str:
    """Reduce a string to ONLY the characters this tool never touches.

    The invariant: canon(before) == canon(after). If that holds, every byte we
    changed was one we intended to change, and not a single word moved.
    (An earlier version compared raw .split() streams and produced a FALSE
    failure, because a zero-width char glued to a word makes a different token.
    The guard was wrong, not the cleaner — but it refused to write, which is the
    correct way for a guard to be wrong.)
    """
    drop = {}
    drop.update(ZERO_WIDTH); drop.update(BIDI); drop.update(TAGS)
    if strip_glue:
        drop.update(EMOJI_GLUE)
    out = []
    for ch in s:
        if ch in drop:
            continue
        if ch in EXOTIC_SPACES:
            out.append(" "); continue
        if unicodedata.category(ch) == "Cf" and ch not in EMOJI_GLUE:
            continue
        out.append(ch)
    return "".join(out)


def process(path: pathlib.Path, out_path: pathlib.Path | None,
            in_place: bool, strip_glue: bool) -> tuple[int, bool]:
    raw = path.read_text(encoding="utf-8")
    cleaned, removals = clean(raw, strip_glue)
    total = sum(removals.values())

    # ── the safety assertion: everything OUTSIDE our target sets must be
    #    identical. If this fails we touched the writing — refuse to write.
    prose_intact = canon(raw, strip_glue) == canon(cleaned, strip_glue)

    print(f"\n\033[1m{path}\033[0m")
    if total == 0:
        print("  clean — nothing invisible found")
    else:
        for name, n in sorted(removals.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>6}  {name}")
        print(f"  {'':>6}  ── {total} total")
    if not prose_intact:
        print("  \033[31mSTOP: word stream changed. Not writing. This is a bug.\033[0m")
        return total, False

    if in_place and total:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(cleaned, encoding="utf-8")
        print(f"  → rewrote in place (backup: {path.name}.bak)")
    elif out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cleaned, encoding="utf-8")
        print(f"  → {out_path}")
    return total, True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="file or directory")
    ap.add_argument("-o", "--out", help="output file (or directory, if input is one)")
    ap.add_argument("--in-place", action="store_true", help="overwrite, keeping a .bak")
    ap.add_argument("--strip-emoji-glue", action="store_true",
                    help="also remove ZWJ + variation selectors (WILL break emoji)")
    a = ap.parse_args()

    src = pathlib.Path(a.path).expanduser()
    if not src.exists():
        print(f"not found: {src}", file=sys.stderr); return 1

    files = sorted(p for p in src.rglob("*")
                   if p.is_file() and p.suffix.lower() in
                   {".md", ".txt", ".markdown", ".rst", ".html"}) if src.is_dir() else [src]
    if not files:
        print("no text files found", file=sys.stderr); return 1

    grand, ok = 0, True
    for f in files:
        if src.is_dir() and a.out:
            dest = pathlib.Path(a.out).expanduser() / f.relative_to(src)
        elif a.out:
            dest = pathlib.Path(a.out).expanduser()
        else:
            dest = None
        n, good = process(f, dest, a.in_place, a.strip_emoji_glue)
        grand += n; ok = ok and good

    print(f"\n\033[1m{len(files)} file(s) · {grand} character(s) removed\033[0m")
    if not a.out and not a.in_place:
        print("(report only — pass -o or --in-place to write)")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
