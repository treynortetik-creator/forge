#!/usr/bin/env python3
"""
edit_diff.py — classify what an edit pass actually did, and escalate the dangerous part.

WHY THIS EXISTS
---------------
August et al., PLOS ONE, February 2026: an LLM made 83 corrections to global-health
papers. **14% made the text worse**, and it silently removed 10 pieces of key
information — including in-text citations and a reference to a table. A human editor
made 21 corrections, 90% of them improvements, and **flagged seven unclear passages
instead of rewriting them**.

Neither AI tool flagged anything. That is the whole problem: a line edit that quietly
deletes a citation looks exactly like a line edit that tightened a sentence, and a
human reviewing a 90,000-word diff will not catch it.

So: diff before against after, classify every change, and escalate only the two
classes that can destroy meaning —

    DELETION  a citation, number, quote, proper noun or named entity vanished
    MEANING   a negation flipped, a hedge was removed, or a quantifier changed

Everything else (typo, style, punctuation, whitespace) is reported as a count and
otherwise left alone. The point is to make the dangerous 2% findable, not to
re-review the safe 98%.

USAGE
    python3 edit_diff.py before.md after.md
    python3 edit_diff.py before.md after.md --json
    python3 edit_diff.py before.md after.md --fail-on deletion   # exit 1 if any found

Stdlib only.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

# ── the patterns that mark something as load-bearing ─────────────────────────

# Citations: (Smith 2020) · (Smith et al., 2020) · [12] · [Smith20] · ¹² footnote marks
CITATION = re.compile(
    # (Marsh 2024) · (Marsh et al., 2024) · (Marsh & Okafor, 2024) · (Marsh and Okafor 2024b)
    r"\([A-Z][A-Za-z'’\-]+"
    r"(?:\s+et\s+al\.?|(?:\s*(?:,|and|&)\s*[A-Z][A-Za-z'’\-]+)+)?"
    r"[,\s]+\d{4}[a-z]?\)"
    r"|\[\d{1,3}(?:[,–\-]\s*\d{1,3})*\]"          # [12] · [3, 7] · [4–9]
    r"|\[[A-Z][A-Za-z]+\d{2,4}\]"                    # [Smith20]
)
# Any number carrying meaning: 14%, $2,400, 1,929 words, -23 LUFS, 4.5:1, 2026
UNIT = (r"%|:\d+|x\b|"
        r"(?:px|pt|em|rem|vw|vh|dB|dBFS|LUFS|LKFS|kHz|Hz|kbps|Mbps|fps|ms|s|min|hr|h|"
        r"mm|cm|m|km|in|ft|kg|g|lb|USD|GBP|EUR|k|K|M|bn)\b")
NUMBER = re.compile(r"(?<![\w.$])[-+]?\$?\d[\d,]*(?:\.\d+)?\s*(?:" + UNIT + r")?")
# Quoted material — straight and curly, both directions
QUOTE = re.compile(r"[\"“][^\"”]{12,}[\"”]|['‘][^'’]{20,}['’]")
# A cross-reference the prose depends on
XREF = re.compile(r"\b(?:see|per|in|from)\s+(?:Table|Figure|Fig\.|Chapter|Section|Appendix)\s*\d+"
                  r"|\b(?:Table|Figure|Fig\.|Chapter|Section|Appendix)\s+\d+", re.I)

NEGATION = re.compile(r"\b(?:not|never|no|cannot|can't|won't|doesn't|didn't|isn't|aren't|"
                      r"wasn't|weren't|shouldn't|wouldn't|couldn't|nor|neither)\b", re.I)
HEDGE = re.compile(r"\b(?:may|might|could|possibly|perhaps|appears?|seems?|suggests?|likely|"
                   r"probably|approximately|roughly|about|around|estimated|reportedly|"
                   r"allegedly|arguably|tends? to)\b", re.I)
QUANTIFIER = re.compile(r"\b(?:all|every|none|no one|nobody|always|never|most|many|some|few|"
                        r"several|majority|minority|each|any)\b", re.I)

TRIVIAL = re.compile(r"^[\s\W_]*$")


def sentences(text):
    """Split into sentences, keeping it simple and deterministic."""
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“'‘])", text)
    return [p.strip() for p in parts if p.strip()]


def extract(pattern, text):
    return set(m.group(0).strip() for m in pattern.finditer(text))


def norm_numbers(text):
    """Numbers with formatting normalised, so 1,000 == 1000 and 4.50 == 4.5.

    The trailing-zero strip has to run on the fractional part, not on the whole
    string. `re.sub(r"\\.0+$", ...)` collapses 4.00 but leaves 4.50 alone, so a copy
    edit that writes 4.5 for 4.50 was reported as a DELETED NUMBER — a false positive
    on exactly the kind of harmless tidying this check must stay quiet about.
    """
    out = set()
    for m in NUMBER.finditer(text):
        raw = m.group(0).strip()
        core = raw.replace(",", "").replace("$", "").strip()
        mm = re.match(r"^([-+]?\d+)\.(\d+)(.*)$", core)
        if mm:
            frac = mm.group(2).rstrip("0")
            core = mm.group(1) + (f".{frac}" if frac else "") + mm.group(3)
        if re.search(r"\d", core):
            out.add(core.lower())
    return out


def classify(before, after):
    """Return findings, ordered most-dangerous-first."""
    findings = []

    # ---- DELETION: load-bearing content that exists before and not after ----
    for label, pat, sev in (
        ("citation", CITATION, "DELETION"),
        ("quote", QUOTE, "DELETION"),
        ("cross-reference", XREF, "DELETION"),
    ):
        lost = extract(pat, before) - extract(pat, after)
        for item in sorted(lost):
            findings.append({
                "severity": sev, "kind": label, "detail": item,
                "why": f"a {label} present before the edit is absent after it",
            })

    lost_nums = norm_numbers(before) - norm_numbers(after)
    for item in sorted(lost_nums):
        findings.append({
            "severity": "DELETION", "kind": "number", "detail": item,
            "why": "a number present before the edit is absent after it",
        })

    # ---- MEANING: sentence-level semantic flips ----
    sb, sa = sentences(before), sentences(after)
    matcher = difflib.SequenceMatcher(None, sb, sa, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old = " ".join(sb[i1:i2])
        new = " ".join(sa[j1:j2])
        if TRIVIAL.match(old) and TRIVIAL.match(new):
            continue
        for label, pat in (("negation", NEGATION), ("hedge", HEDGE), ("quantifier", QUANTIFIER)):
            nb, na = len(pat.findall(old)), len(pat.findall(new))
            if nb != na:
                findings.append({
                    "severity": "MEANING", "kind": label,
                    "detail": f"{label} count {nb} → {na}",
                    "before": old[:180], "after": new[:180],
                    "why": f"removing or adding a {label} changes what the sentence claims",
                })
        if tag == "delete" and len(old.split()) >= 6:
            findings.append({
                "severity": "MEANING", "kind": "sentence removed",
                "detail": old[:180], "why": "a whole sentence was deleted, not rewritten",
            })

    order = {"DELETION": 0, "MEANING": 1}
    findings.sort(key=lambda f: (order[f["severity"]], f["kind"]))
    return findings


def counts(before, after):
    sb, sa = sentences(before), sentences(after)
    m = difflib.SequenceMatcher(None, sb, sa, autojunk=False)
    changed = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in m.get_opcodes() if tag != "equal")
    return {
        "sentences_before": len(sb), "sentences_after": len(sa),
        "sentences_changed": changed,
        "words_before": len(before.split()), "words_after": len(after.split()),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Classify what an edit pass did; escalate deletions and meaning changes.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-on", choices=["deletion", "meaning", "any", "none"], default="deletion",
                    help="exit 1 when findings of this severity exist (default: deletion)")
    a = ap.parse_args()

    for f in (a.before, a.after):
        if not f.exists():
            print(f"ERROR: file not found: {f}", file=sys.stderr)
            return 1

    before, after = a.before.read_text("utf-8", "replace"), a.after.read_text("utf-8", "replace")
    findings, stats = classify(before, after), counts(before, after)
    n_del = sum(1 for f in findings if f["severity"] == "DELETION")
    n_mean = sum(1 for f in findings if f["severity"] == "MEANING")

    if a.json:
        print(json.dumps({"stats": stats, "deletions": n_del, "meaning_changes": n_mean,
                          "findings": findings}, indent=2))
    else:
        print(f"\n{a.before.name} → {a.after.name}")
        print(f"  {stats['words_before']:,} → {stats['words_after']:,} words · "
              f"{stats['sentences_changed']} of {stats['sentences_before']} sentences touched")
        print(f"  🔴 {n_del} deletion(s) of load-bearing content · ⚠️  {n_mean} meaning change(s)\n")
        if not findings:
            print("  Nothing dangerous found. Style and typo changes are not reported —")
            print("  this check exists to surface the 2% that can destroy meaning.\n")
        for f in findings:
            mark = "🔴" if f["severity"] == "DELETION" else "⚠️ "
            print(f"  {mark} [{f['kind']}] {f['detail']}")
            print(f"      {f['why']}")
            if "before" in f:
                print(f"      before: {f['before']}")
                print(f"      after:  {f['after']}")
            print()

    if a.fail_on == "none":
        return 0
    if a.fail_on == "deletion":
        return 1 if n_del else 0
    if a.fail_on == "meaning":
        return 1 if n_mean else 0
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
