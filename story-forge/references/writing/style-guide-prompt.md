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

### The thirteen dimensions — each with its own instrument

🔴 **Do not give all thirteen the same output shape.** Each asks for something different, and the
sub-fields below are what force the model to commit instead of hedge. A sheet that says "moderately
formal-ish" is unusable downstream.

| # | Dimension | What it must produce |
|---|---|---|
| 1 | Narrative rhythm | Summary (1-2 sentences) + 3-5 rhythmic habits, each with a quoted example |
| 2 | Psychic distance | **Distance only** — close vs distant, show-vs-tell, deep POV. **Never** first-vs-third person; that is a fixed structural choice, not a style one. Give the evidence |
| 3 | Formality | **Pick one of five: very informal / informal / neutral / formal / very formal.** Not a range |
| 4 | Overall tone | **3-5 adjectives, each with a brief explanation** + **tone stability**: does it hold, or shift noticeably? |
| 5 | Emotional range | **Narrow / moderate / wide**, in 2-3 sentences, plus the common emotions with examples |
| 6 | Sentence length & rhythm | Average, and the pattern of variation |
| 7 | Paragraphing | Plus **paragraph function**: one idea per paragraph, frequent breaks for emphasis, or long blended paragraphs? |
| 8 | Reading grade level | **A specific grade. Not a range.** |
| 9 | Dialogue style | Tag habits, beat usage. Push toward "said"/"asked" plus action beats |
| 10 | Sentence openings | **Distinctive habits** — sentence-initial And/But/So — and for each, rule it **preserve / eliminate / mix in occasionally.** The verdict is the deliverable, not the observation |
| 11 | Clause structure | **Stacking vs splitting**, and subordination patterns (*because, although, even though*) |
| 12 | Punctuation habits | Inventory **commas, semicolons, colons, parentheses, ellipses, question marks, exclamation marks** — then **explicitly forbid em-dashes and name the substitutes** |
| 13 | Emphasis & cadence | The author's signature moves |

### Output shape

Markdown, one `##` section per dimension, **each following its own row in the table above** — the
sub-fields differ by dimension and that is the point. Dimension 1's Summary + Key-traits shape is not
the template for the other twelve.

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
