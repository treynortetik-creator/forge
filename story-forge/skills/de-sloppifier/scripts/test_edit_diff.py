#!/usr/bin/env python3
"""
test_edit_diff.py — regression tests for the semantic-damage diff.

Two properties, pulling in opposite directions, and both are required:

  1. A style-only edit must report NOTHING. A diff that fires on every tightened
     sentence is one nobody reads, which returns you to the original problem.
  2. A deleted citation must be caught even when it is buried in a rewrite that
     looks like ordinary line editing.

Case 1 is the harder one to keep true, so it comes first.

    python3 test_edit_diff.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import edit_diff as E

FAILS, RUN = [], 0


def check(name, cond, detail=""):
    global RUN
    RUN += 1
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}  {detail}")
        FAILS.append(name)


def kinds(before, after, severity=None):
    f = E.classify(before, after)
    return [x["kind"] for x in f if severity is None or x["severity"] == severity]


# ── 1. style-only edits must be SILENT ───────────────────────────────────────
print("\nfalse positives (the property that makes it readable)")

b = ("The results were quite surprising to the research team. It is important to note "
     "that the effect was observed in all three cohorts.")
a = ("The results surprised the research team. The effect appeared in all three cohorts.")
check("a tightening line edit reports nothing", E.classify(b, a) == [],
      str(E.classify(b, a)))

b2 = "The data was analysed by the team. A conclusion was reached by the authors."
a2 = "The team analysed the data. The authors reached a conclusion."
check("active-voice conversion reports nothing", E.classify(b2, a2) == [],
      str(E.classify(b2, a2)))

b3 = "He walked quietly to the door — and then he stopped."
a3 = "He tiptoed to the door, then stopped."
check("adverb and em-dash surgery reports nothing", E.classify(b3, a3) == [],
      str(E.classify(b3, a3)))

check("identical text reports nothing", E.classify(b, b) == [])


# ── 2. deletions must be CAUGHT ──────────────────────────────────────────────
print("\ndeletions")

cite_b = ("Falls declined by 41% after the intervention (Marsh et al., 2024). "
          "The mechanism remains unclear.")
cite_a = "Falls declined by 41% after the intervention. The mechanism remains unclear."
check("a deleted citation is caught", "citation" in kinds(cite_b, cite_a, "DELETION"))

for style, txt in [("numeric", "[12]"), ("range", "[4-9]"), ("alpha", "[Smith20]"),
                   ("et al", "(Okafor et al., 2019)"), ("ampersand", "(Marsh & Okafor, 2024)"),
                   ("and", "(Marsh and Okafor 2024b)"), ("single", "(Marsh 2024)"),
                   ("multi", "[3, 7]")]:
    bb = f"The effect was robust {txt}. Later work disagreed."
    aa = "The effect was robust. Later work disagreed."
    check(f"citation format: {style}", "citation" in kinds(bb, aa, "DELETION"), txt)

xr_b = "Coverage varied by site. See Table 3 for the full breakdown."
xr_a = "Coverage varied by site."
check("a deleted cross-reference is caught", "cross-reference" in kinds(xr_b, xr_a, "DELETION"))

num_b = "Adoption reached 62% by March, up from 1,240 users."
num_a = "Adoption reached 62% by March, up from a smaller base."
check("a deleted number is caught", "number" in kinds(num_b, num_a, "DELETION"))

q_b = 'The reviewer called it "a fundamental misreading of the data" in her report.'
q_a = "The reviewer criticised the analysis in her report."
check("a deleted quotation is caught", "quote" in kinds(q_b, q_a, "DELETION"))

# formatting-only number changes must NOT fire
fmt_b = "The cohort included 1,240 participants over 4.50 years."
fmt_a = "The cohort included 1240 participants over 4.5 years."
check("1,240 == 1240 and 4.50 == 4.5", "number" not in kinds(fmt_b, fmt_a, "DELETION"),
      str(kinds(fmt_b, fmt_a)))


# ── 3. meaning changes ───────────────────────────────────────────────────────
print("\nmeaning changes")

neg_b = "The treatment did not reduce mortality in the older cohort."
neg_a = "The treatment reduced mortality in the older cohort."
check("a flipped negation is caught", "negation" in kinds(neg_b, neg_a, "MEANING"))

hed_b = "The findings may suggest a link between the two variables."
hed_a = "The findings show a link between the two variables."
check("a removed hedge is caught", "hedge" in kinds(hed_b, hed_a, "MEANING"))

qnt_b = "Most participants reported some improvement."
qnt_a = "All participants reported improvement."
check("a changed quantifier is caught", "quantifier" in kinds(qnt_b, qnt_a, "MEANING"))

del_b = ("The trial ran for eighteen months. Funding came from a private foundation with "
         "ties to the manufacturer. Results were published in 2025.")
del_a = "The trial ran for eighteen months. Results were published in 2025."
check("a whole deleted sentence is caught", "sentence removed" in kinds(del_b, del_a, "MEANING"))


# ── 4. ordering, counting, exit codes ────────────────────────────────────────
print("\nreporting")

mixed_b = ("Falls fell 41% (Marsh et al., 2024). The effect may be confounded. "
           "See Table 3.")
mixed_a = "Falls fell 41%. The effect is confounded."
f = E.classify(mixed_b, mixed_a)
check("deletions are ranked above meaning changes",
      f and f[0]["severity"] == "DELETION" and any(x["severity"] == "MEANING" for x in f),
      str([(x["severity"], x["kind"]) for x in f]))
check("both a citation and a cross-reference are found",
      {"citation", "cross-reference"} <= set(x["kind"] for x in f),
      str(set(x["kind"] for x in f)))

st = E.counts(mixed_b, mixed_a)
check("word counts are reported", st["words_before"] > st["words_after"] > 0)
check("sentence counts are reported", st["sentences_before"] >= st["sentences_after"] > 0)

check("empty input does not crash", E.classify("", "") == [])
check("addition-only is not a deletion",
      not [x for x in E.classify("A short line.", "A short line. And another one here.")
           if x["severity"] == "DELETION"])

# ── named entities ────────────────────────────────────────────────────────────
# The docstring promised proper-noun/named-entity detection from day one and the code
# never implemented it, so deleting a whole co-host company from a three-company event
# announcement returned "Nothing dangerous found" and exit 0. Half of these tests are
# false-positive controls, because the first working version fired on a sentence join:
# an entity whose IDENTITY depends on its position will break on joins, splits and
# reorders, which are the three commonest line edits there are.

def _ents(b, a):
    return [x["detail"] for x in E.classify(b, a)
            if x["severity"] == "DELETION" and x["kind"] == "named entity"]

check("a deleted co-host company is caught",
      _ents("Co-hosted by SafelyYou, August Health and PalCare.",
            "Co-hosted by SafelyYou and PalCare.") == ["August Health"])
check("a deleted venue name is caught",
      _ents("Drinks at Winter's Jazz Club on the 20th.",
            "Drinks at the club on the 20th.") == ["Winter's Jazz Club"])
check("a multi-word name is reported ONCE, not once per word",
      len(_ents("Meeting at Winter's Jazz Club tonight.",
                "Meeting at the venue tonight.")) == 1)
check("a deleted CamelCase brand is caught",
      _ents("The vendor is PalCare and it works.", "The vendor works.") == ["PalCare"])

check("FP: repeated name replaced by a pronoun is NOT a deletion",
      _ents("Mara flicked ash. Mara did not look up. Mara said it anyway.",
            "Mara flicked ash. She did not look up. She said it anyway.") == [])
check("FP: rewording a sentence opener is NOT a deletion",
      _ents("Join Chelsea Kelly at the club.", "Meet Chelsea Kelly at the club.") == [])
check("FP: joining two sentences is NOT a deletion",
      _ents("Chelsea Kelly runs it. Scott Stegman signed it.",
            "Chelsea Kelly runs it and Scott Stegman signed it.") == [])
check("FP: splitting a sentence is NOT a deletion",
      _ents("Chelsea Kelly runs it and Scott Stegman signed it.",
            "Chelsea Kelly runs it. Scott Stegman signed it.") == [])
check("FP: a name moving to the front of a sentence is NOT a deletion",
      _ents("We met Scott Stegman there.", "Scott Stegman met us there.") == [])
check("FP: a bare month is not an entity",
      _ents("The show runs in August at the hall.", "The show runs later at the hall.") == [])

# ── altered vs removed ────────────────────────────────────────────────────────
# A 300-char door script came back flagged "absent" when six words inside it changed.
# Both still escalate -- silently rewording a quote is as serious as cutting it -- but
# a gate that misnames what happened is a gate people stop reading.
_q = '"' + "We are at the room limit right now, so I must hold you here a few minutes. " \
     "Give me your number and I will text you the moment I can get you in." + '"'
_q2 = _q.replace("I will text you", "I will call you")
kinds = lambda b, a: {x["kind"] for x in E.classify(b, a)}
check("a reworded quote is reported as ALTERED, not absent",
      "quote altered" in kinds("He said " + _q, "He said " + _q2))
check("an altered quote still escalates as DELETION severity",
      any(x["severity"] == "DELETION" for x in E.classify("He said " + _q, "He said " + _q2)))
check("a genuinely removed quote is still reported as removed",
      "quote" in kinds("He said " + _q, "He said nothing at all about any of it."))
check("an altered quote carries before/after so the change is visible",
      all("before" in x and "after" in x
          for x in E.classify("He said " + _q, "He said " + _q2)
          if x["kind"] == "quote altered"))

print(f"\n{RUN - len(FAILS)}/{RUN} passed")
if FAILS:
    print("FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
