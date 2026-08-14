#!/usr/bin/env python3
"""vector-check.py <storyboard.json> — audit the film's direction of travel.

Free, instant, and run BEFORE any credits are spent. It catches the failure that
no downstream gate can see: a film whose junctions are all perfect and whose
camera still wanders.

The continuity gate proves each clip is one unbroken move. It cannot prove the
moves point the same way. A film can pass every seam and every continuity check
and still read as a reel of unrelated shots, because the visitor is scrolling in
ONE direction and the camera is not.

  in-words   the camera closes on something
  out-words  the camera withdraws from it
  A clip containing both reverses on itself mid-shot.
  A clip containing neither has no instruction, and the model invents one.

Declare the film's vector in the storyboard as "vector": "...". If the sentence
does not contain a recognised direction word, add "vector_direction": "in" or
"out". One intended reversal may be declared as "reversal_at": "<clip id>".
An undeclared reversal is the bug.
"""
import json
import re
import sys

# Vertical travel counts. For a descent film "down" IS deeper, and most scroll
# films are vertical — a vocabulary that only knows in/out is blind to the most
# common vector there is. Note these match TRAVEL, not gaze: "looking straight
# up the neck" is a reorientation, and a clip that only reorients genuinely does
# not advance the journey, so being flagged as directionless is the right answer.
IN = r"\b(into|inward|deeper|closer|toward|towards|push(?:ing|es)?\s+in|" \
     r"advanc\w+|approach\w+|descend\w+|descent|down\s+into|enter\w*|" \
     r"falls?|falling|sink\w+|plunge\w*|drop(?:s|ping)?\s+(?:down|through)|" \
     r"(?:travel\w*|mov\w+|drift\w*|glide\w*)\s+down\w*|downward|straight\s+down)\b"
OUT = r"\b(outward|away|back(?:ward|s)?\s+(?:travel|motion|through)|retreat\w*|withdraw\w*|" \
      r"pull(?:ing|s)?\s+back|recede\w*|rising\s+out|exit(?:s|ing)?\b|lift\w+\s+away|" \
      r"rises?|rising|ascend\w*|climb\w+|upward|(?:travel\w*|mov\w+)\s+up\w*)\b"

# Phrases that contain a direction word but describe no camera motion at all.
# Without these the gate cries wolf on its own boilerplate — "resolve out of the
# blackness", "out of frame", "no edits" — and a gate that cries wolf gets edited
# away, which is strictly worse than not having one.
NOISE = re.compile(
    r"out\s+of\s+(frame|focus|the\s+blackness|the\s+dark\w*|view|nowhere)"
    r"|no\s+(edits?|cuts?|scene\s+changes?)"
    r"|without\s+\w+"
    r"|背景",
    re.I,
)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: vector-check.py <storyboard.json>")
    sb = json.load(open(sys.argv[1]))
    clips = sb.get("clips", [])
    if not clips:
        sys.exit("no clips in storyboard")

    vector = sb.get("vector")
    reversal = sb.get("reversal_at")
    direction = sb.get("vector_direction")
    if direction not in (None, "in", "out"):
        sys.exit('vector_direction must be "in" or "out"')

    vector_text = NOISE.sub(" ", (vector or "").lower())
    vector_in = bool(re.search(IN, vector_text))
    vector_out = bool(re.search(OUT, vector_text))
    if direction is None:
        if vector_in == vector_out:
            direction = None
        else:
            direction = "in" if vector_in else "out"

    print(f"vector-check — {len(clips)} clips")
    print(f"  declared vector: {vector or '(NONE — declare one)'}")
    print(f"  base direction: {direction or '(AMBIGUOUS — set vector_direction)'}")
    if reversal:
        print(f"  declared reversal at: {reversal}")
    print()

    # A declared reversal flips the vector for every clip from that point on.
    # Treating the turn as a single exempt clip would flag the whole second half
    # of a correctly built film.
    ids = [c.get("id", "?") for c in clips]
    turn = ids.index(reversal) if reversal in ids else None
    if reversal and turn is None:
        print(f"  ! reversal_at '{reversal}' matches no clip id\n")

    bad, mute = [], []
    for i, c in enumerate(clips):
        cid = c.get("id", "?")
        p = NOISE.sub(" ", (c.get("prompt") or "").lower())
        ins = sorted(set(m.group(0) for m in re.finditer(IN, p)))
        outs = sorted(set(m.group(0) for m in re.finditer(OUT, p)))
        base_out = direction == "out"
        expect_out = base_out if turn is None or i < turn else not base_out
        if ins and outs:
            bad.append(cid)
            print(f"  ✗ {cid:<22} REVERSES mid-clip: in={ins} out={outs}")
        elif not ins and not outs:
            mute.append(cid)
            print(f"  ✗ {cid:<22} no direction stated — the model will invent one")
        else:
            d = "out" if outs else "in"
            wrong = direction is not None and ((d == "out") != expect_out)
            mark = "✗" if wrong else "✓"
            note = ""
            if wrong:
                bad.append(cid)
                note = f"  <- expected {'out' if expect_out else 'in'}"
            print(f"  {mark} {cid:<22} {d}{note}")

    print()
    fail = False
    if not vector:
        print("FAIL no \"vector\" declared. Name the film's single direction of travel in")
        print("     one sentence before writing clips — the visitor scrolls one way, and")
        print("     the camera has to agree with them.")
        fail = True
    elif direction is None:
        print("FAIL the declared vector is ambiguous. Include a recognised direction word")
        print("     or set \"vector_direction\" to \"in\" or \"out\".")
        fail = True
    if bad:
        print(f"FAIL {len(bad)} clip(s) fight the declared vector: {', '.join(bad)}")
        print("     Either the clip reverses on itself, or it travels the wrong way for")
        print("     where it sits in the film. Split it, or commit it to one direction.")
        fail = True
    if mute:
        print(f"FAIL {len(mute)} clip(s) state no direction at all: {', '.join(mute)}")
        print("     Say how the clip CONTINUES the previous one, not what is in it.")
        fail = True

    if fail:
        print()
        print("Fix the storyboard before generating. This is the one check that is free.")
        sys.exit(1)
    print("PASS — every clip travels the declared vector")


if __name__ == "__main__":
    main()
