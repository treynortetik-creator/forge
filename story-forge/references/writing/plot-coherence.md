---
title: Plot Coherence — Logic Check and Chronology Auditing
type: concept
tags: [writing, ai-writing, plot, logic-check, editing, consistency]
created: 2026-06-27
updated: 2026-06-27
source: YouTube — OyH0gWzQuoE "This AI Prompt Can Actually Find and Fix Plot Holes In Your Novel" (Jason Hamilton / The Nerdy Novelist)
status: living
---

# Plot Coherence

AI is good at generating text; it is genuinely bad at remembering what it said three scenes ago. Logic breaks, convenience flags, and worldbuilding contradictions accumulate silently across a draft. The logic check prompt catches them systematically before they are buried in finished prose. But the AI workflow below only enforces a standard the craft already defines — so it is worth naming what "coherent" actually means before automating the check for it.

## Craft Foundation — What Makes a Plot Cohere

A coherent plot is one where events are connected by cause and effect, not by coincidence or authorial convenience. The reader should be able to trace a line from any late event back through the choices and consequences that produced it.

- **Causality over coincidence.** Each major event should follow from a prior one — "therefore" and "but," not "and then." Coincidence is tolerable when it creates a problem for the protagonist; it reads as cheating when it solves one.
- **Setup and payoff.** Anything that matters at the climax must be planted earlier, and anything planted with emphasis should eventually pay off. Chekhov's gun is the classic statement of the rule: a loaded rifle shown in act one must be fired by the end, or it should not be on the wall. Unpaid setups feel like loose threads; unplanted payoffs feel arbitrary.
- **Surprising yet inevitable.** A satisfying ending is one the reader did not predict in its specific form but, looking back, can see was fully prepared. Surprise comes from the particular shape; inevitability comes from the setup chain being intact. Coherence is the mechanism that lets an ending be both at once.
- **Convenience as a craft failure.** A character who has exactly the skill, ally, or resource the moment the plot needs it; an obstacle that evaporates without cost; an antagonist who forgets to act between scenes — each is a coherence break. The audit checks below ("Early-Stage Convenience Flags," "Plot Setup Plausibility") are the systematic hunt for these.

The AI logic check is a tool for enforcing these principles at scale; the principles themselves are what the writer is protecting.

## The Logic Check — Two-Step Process

All checks follow the same pattern:

**Step 1 — Audit pass.** Run the check prompt on the document. The model produces a structured improvement plan listing each issue with category, the specific logic break, the references involved, and a concrete fix.

**Step 2 — Implementation pass.** Hand the model the original document and the improvement plan:

> *Here is the original [dossier/chapter/character sheet/outline]. Here is the improvement plan. Implement the suggested changes. Only implement the suggested changes. Do not change anything else. Reproduce the entire [document] with the changes made.*

The word "implement" is deliberate — "rewrite" triggers the model to start from scratch and lose the original work. "Implement" keeps changes targeted.

## The Six Audit Checks

The logic check in the [[story-hacker-prompts]] runs these six categories. Applies to any document — dossier, character bio, chapter plan, outline. Adjust the prompt's references to match what you are auditing.

**1. Premise Logic Check**
- Does the core premise hold together internally?
- Are the central conflict and stakes consistent with the stated world rules?
- Does the basic "what if" or setup make logical sense?

**2. Character-World Fit**
- Do the characters' roles, goals, and capabilities make sense given the worldbuilding?
- Does any character's existence contradict stated world rules?
- Do relationships and motivations align with the premise?
- Are power levels, social positions, and abilities plausible in this world?

**3. Worldbuilding Coherence**
- Do world elements support and enable the premise?
- Are there conflicting world rules stated in different sections?
- Do geography, technology level, social structure, and magic/tech rules work together logically?

**4. Plot Setup Plausibility**
- Are there logistical impossibilities given the pitch?
- Are there character motivation gaps that would prevent the story from starting?
- Does the antagonist's power and position make sense relative to the protagonist's starting point?
- Is the inciting incident plausible given the world and characters?

**5. Early-Stage Convenience Flags**
- Does the premise rely on unlikely coincidences without justification?
- Are there characters who exist purely to solve plot problems with no other narrative purpose?
- Does the protagonist have suspiciously perfect allies or resources that feel contrived?
- Are there "because the plot needs it" elements with no in-world logic?

**6. Specific Fixes**
- For each major issue: concrete suggestion to resolve the problem while preserving the core pitch and appeal of the story

Issue format:
```
**[Category] Issue:** [Brief description of the problem]
**LOGIC BREAK:** [What exactly breaks the internal logic]
**References:** [Specific premise/pitch elements, characters, or worldbuilding details involved]
**FIX:** [Concrete suggestion]
```

## Scratchpad Directive

When running the audit, add this to the prompt to activate structured reasoning:

> *Before writing your final audit, use a scratchpad to systematically work through each section: first identify the core premise and main pitch; list all characters and their stated roles/capabilities; list all worldbuilding rules and elements; check each audit category systematically; note contradictions, implausibilities, or logic gaps; think through what specifically breaks and how it could be fixed. Your final output should contain only the six-section audit report, not the scratchpad.*

This is especially valuable with thinking models because it forces sequential reasoning rather than pattern-matching to surface plausibility issues.

## Model Selection

This task requires a reasoning-capable model. A fast cheap model will miss subtle plausibility issues that require following a chain of if-then logic across the entire document. Recommended: Claude Opus 4.6 or Gemini 2.5 Pro. The cost is acceptable when you are running it once per dossier or once per chapter.

## When to Run It

Early (dossier stage): catches worldbuilding contradictions and convenience flags before they are embedded in 80,000 words of prose.

After characters are developed: run the check again once character sheets are complete — character capabilities and motivations often create new logic conflicts with the premise.

After outlining: a third pass before first draft generation catches any new contradictions introduced during the outlining process.

After draft chapters: the chapter-level version checks continuity with previous chapters — character behavior consistency, timeline coherence, whether facts established in earlier scenes still hold.

## Pipeline Integration

The [[chapter-generation-pipeline]] has two explicit chronology checks (step 8 after the scene briefs are generated, and step 11 after the first draft). The logic check prompt is the implementation of those steps. Run the full six-category version on the dossier pre-pipeline; run a lighter continuity-focused version on each scene brief to confirm it does not contradict what has already been written.

See [[character-system]] for how character sliders and arc information flow into the character-world fit check — slider baselines establish what behavior is consistent for a character, which the logic check then validates against scenes.

This note is the primary reference for the chronology check steps in [[chapter-generation-pipeline]].

For scaling these same audit categories to a full completed manuscript in a single pass, see [[long-context-novel-writing]].

## Related

- [[story-hacker-prompts]] — the raw prompt library containing the six-category logic check prompt (already in body)
- [[character-system]] — character slider baselines that the character-world fit check validates against (already in body)
- [[chapter-generation-pipeline]] — chronology check steps 8 and 11 run this system per chapter (already in body)
- [[long-context-novel-writing]] — scaling the same six audit categories to a full manuscript in one pass (already in body)
- [[self-editing]] — the developmental revision pass where logic and coherence are assessed first in the revision pyramid
- [[revision-process]] — the full revision pyramid; plot-coherence checks belong at the developmental level before any line editing
- [[outlining-method]] — the third pre-draft logic check pass: catching contradictions before prose generation begins
- [[worldbuilding-consistency]] — the iceberg principle and cause-and-effect systems that worldbuilding coherence checks enforce; primary target of the Worldbuilding Coherence audit category
- [[antagonist-craft]] — the antagonist's off-page plan (agency between scenes) is a primary subject of the plot-coherence audit
- [[scene-structure]] — causal logic at the scene level (stimulus→response, disaster→sequel) is the micro foundation that plot-coherence audits at manuscript scale
