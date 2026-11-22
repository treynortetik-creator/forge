# <Title>: narration v1

Target: <runtime> at the pace you agree by ear (measured as speaking words per minute; see `references/voice.md`).
Format: `## Scene N. Title`, then a `**Narration (N words):**` block of ordinary sentences (one chunk, one caption
cue per sentence), then optional bold-labelled notes such as `**On screen:**`, which the parser ignores.
Respellings go in `saymap.json` (`templates/saymap.example.json`), never in the script, so captions keep the real
spelling.

<!-- Rules: plain friendly sentences, one idea each. No real people: "someone in support", never a name.
     Every claim checked against the source (what the product really does, the exact feature name).
     Very short sentences garble in TTS: give them a few more words. Delete these comments or keep them: the
     parser strips HTML comments. -->

## Scene 1. Hook
**Narration (0 words):**
<The everyday pain, in the viewer's words.> <What it costs them.> <The product turns that into X.>

**On screen:** what the viewer sees while this is said.

## Scene 2. Meet the product
**Narration (0 words):**
<One sentence: what it is and who it is for.> <One sentence of setup the viewer needs before the demo, if any.>

**On screen:** the product, or the first sprite of the world.

## Scene 3. Show it
**Narration (0 words):**
<Do the main task on screen, one action per line, said as it happens.>

**On screen:** the main action, one thing moving at a time.

## Scene 4. Under the hood
**Narration (0 words):**
<Behind the scenes, in plain words. No overclaims: say exactly what is checked and what is not.>

**On screen:** the mechanism, shown moving.

## Scene 5. Close
**Narration (0 words):**
<The name again, inside a full sentence (a bare "Meet X." garbles).> <What the viewer can do next.>

**On screen:** the closing frame.

<!-- Per-line fallback (a named alternative, `make_video.sh`): use `templates/lines.example.json` instead, one entry per
     clip with a scene number. One take is the default: see skills/narrator-voice. -->
