# <Title>: narration v1. Scenes = `## n Title`; one line = one clip = one cue. Target: <runtime> at ~180 wpm.

<!-- Rules: plain friendly sentences, one idea each. No real people: "someone in support", never a name.
     Every claim checked against the source (what the product really does, the exact feature name).
     Very short lines garble in TTS: give them a few more words. Spell-outs and respellings go in lines.json `text`. -->

## 1 Hook
<The everyday pain, in the viewer's words.>
<What it costs them.>
<The product turns that into X.>

## 2 Meet the product
<One sentence: what it is and who it is for.>
<One sentence of setup the viewer needs before the demo, if any.>

## 3 Show it
<Do the main task on screen, one action per line, said as it happens.>

## 4 Under the hood
<Behind the scenes, in plain words. No overclaims: say exactly what is checked and what is not.>

## 5 Close
<The name again, inside a full sentence (a bare "Meet X." garbles).>
<What the viewer can do next.>


<!-- ONE-TAKE ROUTE (scripts/make_narration.py, skill sprite-explainer): the parser reads `## Scene N. Title`, then a
     `**Narration (N words):**` block of ordinary sentences (one chunk per sentence), then optional bold-labelled
     notes such as `**On screen:**` that it ignores. Respellings go in saymap.json (templates/saymap.example.json),
     never in the script, so captions keep the real spelling:

## Scene 1. Hook
**Narration (14 words):**
A parcel arrives at the sorting room. Someone has to decide where it goes.

**On screen:** what the viewer sees while this is said.
-->
