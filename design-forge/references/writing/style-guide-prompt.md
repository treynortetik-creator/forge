---
title: Style Sheet Generator (two-stage register sampling)
type: reference
tags: [prompt, voice, style-sheet, anti-slop]
created: 2026-06-27
updated: 2026-08-14
source: Reworded from the "Style Guide Creator" n8n automation by Jason Hamilton / Story Hacker. The
  method is his; the wording below is this repository's own. See NOTICES.md.
status: living
---

# Style Sheet Generator

Turns an author's raw prose into an instruction sheet a model can write *from*. Two stages, and the
first one is the part most implementations skip.

---

## Why two stages

Handing a model 6,000 unbroken words and asking "what is this author's style" produces an average.
Averages lose the thing you actually want, because **an author's voice is most visible in how it
CHANGES between registers** — the same writer is a different instrument in a quiet descriptive passage
than in an argument or a fight.

So: **extract by register first, analyse second.**

## Stage 1 — Register sampling

For **each** writing sample (up to three, and three beats one), pull passages **verbatim** in four
registers:

| Register | What to look for | Length |
|---|---|---|
| **Calm / descriptive** | Quieter narration, description, interiority. Little dialogue, little action | ~400 words |
| **Dialogue** | A real exchange between characters | ~400 words |
| **Action / high drama** | The most kinetic or highest-stakes passage available | ~400 words |
| **Comedy** *(conditional)* | Only if the work is comic or has genuinely comic moments. **Omit entirely if not** — do not manufacture one | ~400 words |

Quote them **exactly**. Paraphrase at this stage destroys the evidence the next stage reasons over.
If a sample slot is empty, say so plainly and move on rather than inventing filler.

## Stage 2 — The style sheet

Feed the extracted passages (not the raw samples) into the analysis. The output is **instruction, not
observation** — write "do X", never "the author tends to X". A model cannot act on an observation.

**Three rules that do the work:**

1. **Base every claim ONLY on the supplied passages.** No genre assumptions, no author biography.
2. **State the pattern in general terms, then prove it with a short verbatim quote** from the samples.
   A rule without an example is unusable; an example without a rule is unactionable.
3. **Cover only the thirteen dimensions below.** Not plot, not character, not theme. Prose only.

### The thirteen dimensions

Narrative rhythm · psychic distance (close vs distant — **distance only**, never first-vs-third
person, which is a fixed structural choice not a style one) · formality · overall tone · emotional
range · average sentence length and rhythm · paragraphing · reading grade level · dialogue style ·
sentence openings · clause structure and complexity · punctuation habits · emphasis and cadence tricks
(the author's signature moves).

### Output shape

Markdown, one `##` section per dimension, each carrying a one-to-two sentence **Summary** and a
**Key traits** bullet list of three to five specific habits, each with a quoted example.

Close with a **Summarised Style Rules** checklist: **8-15 "do" rules** and **8-15 "avoid" rules**,
written as complete imperative sentences a model can follow without reading the rest of the sheet.

### Two standing constraints

- **Punctuation: forbid em-dashes explicitly and name the substitutes** (comma, period, parenthesis,
  colon). Em-dash density is among the most recognisable machine tells, and a style sheet that stays
  silent on it will faithfully reproduce whatever the samples happened to do.
- **Dialogue: push toward "said" and "asked" plus action beats**, and toward varied sentence openings.
  These are the two places a style sheet most often licenses bad habits by describing them neutrally.

---

## Where this sits

`voice` operationalises this. The sheet it produces is consumed by every drafting skill and by
`de-sloppifier` Pass 2, which checks the prose back against it.

Related: `anti-slop.md` · `de-sloppifier`'s Pass 3 list · `voice-matching.md`
