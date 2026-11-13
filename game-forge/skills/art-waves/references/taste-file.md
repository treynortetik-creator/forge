# The taste file: structure for an owner's recorded verdicts

A single file (`design/TASTE.md` in the roguelite) that every builder and reviewer reads before showing the owner
anything. It stood at 26 numbered verdicts plus sections after two weeks. Give the owner's words a home that
outlives the chat they were said in. This reference gives the structure only; fill it with your owner's own words.

## Header (three lines)
1. What it is for: "Every builder and reviewer checks proofs against this before showing the owner anything."
2. The honesty rule: "Only the owner's recorded words; no invented preferences." Date written.
3. Source keys: short codes for where each quote lives (a daily log with a line number, a project doc with a line
   number, a message id from the chat tool, an auto-memory note). Every entry carries one.

## Section 1: "Check every proof against these" (numbered, newest last)
Each entry: the verb, the subject, the date, the quote in quotation marks, the source key.

```
7. **HATES** [the thing]. [YYYY-MM-DD]: "[his words, typos kept]" ([source key])
8. **LOVES** / **LIKES** [the thing]. ...
9. **ALLOWS** [an exception to an earlier rule, and why]. ...
10. **WANTS** [a direction]. ...
11. **PRIORITY:** [what to do first]. ...
12. **CALLED** for [a request relayed second-hand: say so]. ...
```

Rules that kept it honest:
- Keep the verb strict. A paraphrase an agent wrote is labelled as one, and "he has not rejected it" is not recorded as
  his words ("an agent proposal he has not rejected, not his words").
- When a later message changes an entry, append "UPDATED [time] ([source])" with the new quote on the same entry,
  so the thread of a decision is readable in one place.
- Typos stay in quotes; they are evidence of the voice and of which words were his.
- Entries can carry the enforcing script: "`art-measure.py --info tone.,outline.` demotes the tone and outline checks to INFO
  for this reason".

## Section 2: Overall style
- **CURRENT (date):** one or two lines naming the style in force and the source.
- **SUPERSEDED (date):** each older style, each with the date it lost and what replaced it. Never delete these;
  they stop an agent re-proposing a dead style. Superseded guardrails (an agent's earlier safety rule overridden by
  the owner) are listed in the same way.
- Biome or area progression, if the look changes by area ("sketch lines at biome 1, firming per biome"), with
  the guardrails he accepted.
- Colour policy in one sentence ("colour is information only").

## Section 3: By class
Short bullet lists, one per class, each bullet a rule plus its date and source:
- Characters and enemies (roster rules, what may not appear in which area).
- Environment and props (contact shadow under every prop, hard alpha, render at native on-screen size).
- Lettering and UI.
- Layout (copy a reference product's layout, invent style and gameplay only).
- Feel and gameplay.
- Process.

## Section 4: Process rules that came from the owner
- Creative calls are theirs: bring two to four options plus a recommendation, build after they pick. Engineering,
  fixes and performance stay autonomous.
- Spend: the standing approval, and which new pipelines need a cost note first.
- Format of what they receive (motion as mp4, never gif, because they review on a phone).
- Look at the proof at display size before claiming a fix, side by side against their reference.
- Run the measurement script on proofs before showing them (outline width, darkness, edge softness).

## Open questions
A short list of things asked and awaiting an answer, so no builder decides them by default.

## Using it
- A builder opens the file at the start of a wave and re-reads the section for their asset class.
- A reviewer (a fresh model that did not build the proof) lists which entries the proof violates by number.
- A calibration set for `calibrate-thresholds.py` is built from the entries: frames the owner called good, frames
  they called bad. The limit then exists because of a recorded verdict, and the file names the script.
- When two entries conflict, the later dated one wins and the earlier gets a SUPERSEDED mark.
