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

    DELETION  a citation, number, quote, cross-reference, or named entity vanished
              (entities only when EVERY occurrence is gone -- see entity_candidates)
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
# Units split by ambiguity. `in`, `s`, `m`, `h`, `k`, `M`, `g`, `x` are also ordinary
# English words, so they may only attach with NO space -- otherwise "Sales rose by 4 in
# the summer quarter" captures "4 in" as a measurement and a harmless reorder gets
# reported as a DELETED NUMBER.
UNIT_SPACED = (r"%|(?:px|pt|em|rem|vw|vh|dBFS|dB|LUFS|LKFS|kHz|Hz|kbps|Mbps|fps|ms|"
               r"min|hr|mm|cm|km|ft|kg|lb|USD|GBP|EUR|bn)\b")
UNIT_TIGHT = r"(?::\d+)|(?:x|in|s|m|h|k|K|M|g)\b"
NUMBER = re.compile(r"(?<![\w.$])[-+]?\$?\d[\d,]*(?:\.\d+)?"
                    r"(?:\s*(?:" + UNIT_SPACED + r")|(?:" + UNIT_TIGHT + r"))?")
# Quoted material — straight and curly, both directions
# The single-quote branch must not match across two possessive apostrophes. "The dog's
# bone lay beside the cat's bowl" was reported as a DELETED QUOTE -- and fiction, this
# plugin's whole domain, is saturated with possessives. Require the opening mark to
# start a word and the closing mark to end one.
QUOTE = re.compile(r"[\"“][^\"”]{12,}[\"”]"
                   r"|(?<![\w'’])[‘][^'’]{20,}[’](?![\w])"
                   r"|(?<![\w'’])'[^']{20,}'(?![\w])")
# A cross-reference the prose depends on
XREF = re.compile(r"\b(?:see|per|in|from)\s+(?:Table|Figure|Fig\.|Chapter|Section|Appendix)\s*\d+"
                  r"|\b(?:Table|Figure|Fig\.|Chapter|Section|Appendix)\s+\d+", re.I)

# Named entities. The module docstring promised these from the beginning and the code
# never checked them, so deleting an entire co-host company from a three-company event
# announcement returned "Nothing dangerous found" and exit 0. That is the single most
# expensive edit this tool exists to catch, and it was the one class it was blind to.
#
# Two shapes, both chosen to keep false positives near zero:
#   1. TWO OR MORE consecutive capitalised words -- "August Health", "Winter's Jazz Club",
#      "Chelsea Kelly", "McClurg Court". A single leading capital cannot trigger this,
#      which is what keeps ordinary sentence-initial words out.
#   2. A single token carrying an internal capital or all-caps -- "SafelyYou", "PalCare",
#      "NIC", "iPhone". These are unambiguous even standing alone.
# A bare capitalised word with neither property is NOT an entity here. "Join" and "The"
# would drown the signal, and a lone surname that vanishes usually takes its first name
# with it, which shape 1 already catches.
_CAPWORD = r"[A-Z][a-z'’\-]+"
ENTITY = re.compile(
    r"\b(?:" + _CAPWORD + r"(?:\s+(?:of|and|the|for|de|von|van))?\s+" + _CAPWORD +
    r"(?:\s+" + _CAPWORD + r")*"                       # 2+ capitalised words
    r"|[A-Za-z]+[A-Z][A-Za-z]*"                        # SafelyYou, PalCare, McClurg
    r"|[A-Z]{2,}"                                      # NIC, PPTX
    r")\b")
# Sentence-initial words are capitalised by grammar, not by being names. If a match
# starts a sentence, drop its first token before comparing: otherwise rewriting
# "Join Chelsea Kelly" to "Meet Chelsea Kelly" reads as a deleted entity.
_SENT_START = re.compile(r"(?:^|[.!?\"“'’)\]]\s+)$")
# Connectors and calendar words carry no identity on their own. "August" is exempt only
# as a bare token; "August Health" still registers through its second word.
_ENTITY_STOP = {"the", "and", "for", "of", "de", "von", "van",
                "january", "february", "march", "april", "may", "june", "july",
                "august", "september", "october", "november", "december",
                "monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday"}

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
    return _multiset(m.group(0).strip() for m in pattern.finditer(text))


def _multiset(items):
    """Counts, not a set. Set difference reports nothing when a repeated item loses one
    of its occurrences, so deleting one of two `41%` looked like no deletion at all."""
    from collections import Counter
    return Counter(items)


def norm_numbers(text):
    """Numbers with formatting normalised, so 1,000 == 1000 and 4.50 == 4.5.

    The trailing-zero strip has to run on the fractional part, not on the whole
    string. `re.sub(r"\\.0+$", ...)` collapses 4.00 but leaves 4.50 alone, so a copy
    edit that writes 4.5 for 4.50 was reported as a DELETED NUMBER — a false positive
    on exactly the kind of harmless tidying this check must stay quiet about.
    """
    out = []
    for m in NUMBER.finditer(text):
        raw = m.group(0).strip()
        core = raw.replace(",", "").replace("$", "").strip()
        mm = re.match(r"^([-+]?\d+)\.(\d+)(.*)$", core)
        if mm:
            frac = mm.group(2).rstrip("0")
            core = mm.group(1) + (f".{frac}" if frac else "") + mm.group(3)
        if re.search(r"\d", core):
            out.append(core.lower())
    return _multiset(out)


def entity_candidates(text):
    """Capitalised TOKENS that are load-bearing names, mapped to the phrase they came from.

    Tokens, not phrases, and presence checked against the whole after-text -- because
    both alternatives are position-dependent and edits move words across sentence
    boundaries constantly. Keying on the phrase meant joining two sentences rewrote
    "Stegman" into "Scott Stegman", and the old key vanishing read as a deleted name on
    an edit that deleted nothing. Any rule that changes an entity's identity based on
    where it sits will fire on sentence joins, splits and reorders, which are the three
    most common line edits there are.

    A token qualifies when it belongs to a run of 2+ capitalised words, or carries an
    internal capital / is all-caps. Tokens that OPEN a sentence are excluded, since they
    are capitalised by grammar: that is what keeps "Join" out when "Join Chelsea Kelly"
    becomes "Meet Chelsea Kelly".
    """
    out = {}
    for m in ENTITY.finditer(text):
        phrase = m.group(0).strip()
        opens = bool(_SENT_START.search(text[:m.start()]))
        for i, tok in enumerate(phrase.split()):
            if i == 0 and opens and not (re.search(r"[a-z][A-Z]", tok) or tok.isupper()):
                continue                      # capitalised only because it starts a sentence
            if len(tok) < 3 or tok.lower() in _ENTITY_STOP:
                continue
            out.setdefault(tok, phrase)
    return out


def capitalised_tokens(text):
    """Every capitalised token anywhere in the text, regardless of role."""
    return {m.group(0) for m in re.finditer(r"\b[A-Z][\w'’\-]*", text)}


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
        for item, n in sorted(lost.items()):
            findings.append({
                "severity": sev, "kind": label, "detail": item,
                "why": (f"a {label} present before the edit is absent after it"
                        + (f" ({n} occurrences lost)" if n > 1 else "")),
            })

    # Entities use a HARDER bar than numbers: only a drop to ZERO counts. Losing one of
    # five "Mara"s is the de-sloppifier doing its job -- Pass 2 explicitly tells it to
    # swap a repeated character name for a pronoun -- and fiction is this plugin's home
    # turf, so a per-occurrence rule would make the DEFAULT gate unusable exactly where
    # it is used most. Losing the LAST "August Health" from a three-co-host announcement
    # is the catastrophe. Numbers keep the per-occurrence rule because a repeated figure
    # is a restated fact, not a restated name.
    cand, still_there = entity_candidates(before), capitalised_tokens(after)
    lost_by_phrase = {}                  # one finding per NAME, not per word of the name
    for tok in sorted(k for k in cand if k not in still_there):
        lost_by_phrase.setdefault(cand[tok], []).append(tok)
    for phrase, toks in sorted(lost_by_phrase.items()):
        findings.append({
            "severity": "DELETION", "kind": "named entity", "detail": phrase,
            "why": ("this name appears nowhere after the edit"
                    if len(toks) > 1 or toks[0] == phrase else
                    f"the name {toks[0]!r} appears nowhere after the edit"),
        })

    lost_nums = norm_numbers(before) - norm_numbers(after)
    for item, n in sorted(lost_nums.items()):
        findings.append({
            "severity": "DELETION", "kind": "number", "detail": item,
            "why": (f"a number present before the edit is absent after it"
                    + (f" ({n} occurrences lost)" if n > 1 else "")),
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
            # Compare the MULTISET of matched words, not the count. Counting alone is
            # blind to any equal-count substitution, which is every meaning inversion
            # that matters: "Most sites complied" -> "All sites complied" both match
            # exactly one quantifier, so the count check returned NOTHING on the very
            # example the skill advertises by name. Same hole for "most" -> "few" and
            # for swapping one negation or hedge for another.
            fb = sorted(m.lower() for m in pat.findall(old))
            fa = sorted(m.lower() for m in pat.findall(new))
            if fb != fa:
                gone, added = sorted(set(fb) - set(fa)), sorted(set(fa) - set(fb))
                if gone or added or len(fb) != len(fa):
                    bits = []
                    if gone:
                        bits.append("removed " + ", ".join(repr(x) for x in gone))
                    if added:
                        bits.append("added " + ", ".join(repr(x) for x in added))
                    if not bits:
                        bits.append(f"count {len(fb)} → {len(fa)}")
                    findings.append({
                        "severity": "MEANING", "kind": label,
                        "detail": f"{label}: " + "; ".join(bits),
                        "before": old[:180], "after": new[:180],
                        "why": f"changing a {label} changes what the sentence claims",
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
