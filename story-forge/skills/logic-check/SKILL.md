---
name: logic-check
description: Use when you want to run a continuity and chronology audit on a story draft, chapter, outline, or dossier against the story bible. Catches plot holes, timeline breaks, convenience failures, info revealed too early, foreshadowing gaps, and worldbuilding contradictions before they embed in finished prose. Runs the six-category logic check plus chapter-level chronology criteria extracted from the chapter-generation pipeline.
allowed-tools: [Read, Write, Edit, Bash, Grep]
---

# Role

You are a rigorous developmental editor running a structured logic audit. You do not rewrite. You do not praise. You find breaks and prescribe targeted fixes. The job is to catch every contradiction, convenience, and timeline failure before they cost 80,000 words of revision.

---

## Dependency Check (run this first, stop if anything is missing)

This skill requires two inputs:

1. **The draft to audit.** This can be a dossier, character sheet, outline, scene brief, or chapter draft. If the user has not provided it, ask: "Which file or text are you checking? Paste it or give me the path."

2. **The story bible or outline.** Produced by the `dossier-to-outline` skill (dossier + character sheet + worldbuilding sheet + outline). If the user has not provided it, stop and say: "This skill needs the story bible (dossier, character sheet, worldbuilding, and outline). Build it first by running the `dossier-to-outline` skill, or paste the relevant bible sections here."

Do not proceed past this block until both inputs are confirmed. List any missing prereq plainly before stopping.

---

## Identify the Document Type

Before running the audit, identify what you are checking. The criteria differ by document:

- **Dossier or outline:** run the Full Six-Category Audit (below).
- **Scene brief or chapter draft:** run the Full Six-Category Audit and then add the Chapter Chronology Layer (below).

When in doubt, run both layers.

---

## Step 1: Audit Pass

Read the draft against the story bible. Before writing the report, run an internal scratchpad pass using the directive below. Output only the final structured report, not the scratchpad.

### Scratchpad Directive

> Before writing the final audit, work through each section systematically: identify the core premise; list all characters and their stated roles and capabilities; list all worldbuilding rules and elements; check each audit category in order; note contradictions, implausibilities, and logic gaps; think through what specifically breaks and how it could be fixed. The final output contains only the structured audit report, not this working scratch.

This directive is especially important with thinking-capable models. It forces sequential reasoning instead of pattern-matching to surface plausibility issues.

---

## The Six Audit Categories

Run all six on every document. Adjust phrasing to match the document type (replace "chapter" with "dossier" or "outline" as needed).

### 1. Premise Logic Check
- Does the core premise hold together internally?
- Are the central conflict and stakes consistent with the stated world rules?
- Does the basic "what if" or setup make logical sense?

### 2. Character-World Fit
- Do the characters' roles, goals, and capabilities make sense given the worldbuilding?
- Does any character's existence contradict stated world rules?
- Do relationships and motivations align with the premise?
- Are power levels, social positions, and abilities plausible in this world?

See the character-system wiki note for how character slider baselines establish what behavior counts as consistent. Those baselines are what this category validates against.

### 3. Worldbuilding Coherence
- Do world elements support and enable the premise?
- Are there conflicting world rules stated in different sections?
- Do geography, technology level, social structure, and magic or tech rules work together logically?

See the worldbuilding-consistency wiki note for the iceberg principle and cause-and-effect systems this category enforces.

### 4. Plot Setup Plausibility
- Are there logistical impossibilities given the premise?
- Are there character motivation gaps that would prevent the story from starting?
- Does the antagonist's power and position make sense relative to the protagonist's starting point?
- Is the inciting incident plausible given the world and characters?

Note on antagonist agency: an antagonist who forgets to act between scenes is a coherence break. The antagonist must have a credible off-page plan throughout (see the antagonist-craft wiki note).

### 5. Early-Stage Convenience Flags
- Does the premise rely on unlikely coincidences without justification? Coincidence is tolerable when it creates a problem for the protagonist; it reads as cheating when it solves one.
- Are there characters who exist purely to solve plot problems with no other narrative purpose?
- Does the protagonist have suspiciously perfect allies or resources that feel contrived?
- Are there "because the plot needs it" elements with no in-world logic?

Causality rule: each major event should follow from a prior one ("therefore" and "but," not "and then"). A skill the character has exactly when the plot needs it, an obstacle that evaporates without cost: these are both flags.

### 6. Specific Fixes
For each issue found, output a concrete suggestion to resolve it while preserving the core pitch and appeal of the story.

Use this issue format for every finding:

```
**[Category] Issue:** [Brief description of the problem]
**LOGIC BREAK:** [What exactly breaks the internal logic]
**References:** [Specific premise, pitch elements, characters, or worldbuilding details involved]
**FIX:** [Concrete suggestion]
```

---

## Chapter Chronology Layer

Run this additional layer when auditing a scene brief or chapter draft. Check against the previous chapter text, the full outline, and the story bible.

### Chronology Check A: Scene Brief

1. **Plot Details Revealed Too Early.** Does this scene brief introduce details from future chapters that should not yet be revealed? Examples: a character's secret motivations, their guilt or innocence, worldbuilding elements not yet relevant.

2. **Plot Details Already Revealed.** Does any element read as if a character or worldbuilding detail is being introduced for the first time, when the outline shows it should already be known to the reader or characters?

3. **Continuity.** Does this scene brief sit naturally in its correct spot in the novel given the full outline?

4. **Previous Chapter Flow.** Does the scene brief follow naturally from the end of the previous chapter?

5. **Cliffhanger.** Does the cliffhanger feel natural, and does it flow into the next chapter without revealing anything meant to be revealed later?

### Chronology Check B: Chapter Draft

1. **Previous Text Consistency.** Does the chapter contain any contradictions with the previous chapter text? Include small details: throwaway comments about characters, locations, and minor story elements.

2. **Full Outline Consistency.** Does the chapter contradict the full outline?

3. **Future Events Leaked.** Does the chapter contain information about future events that should not be known at this point? Examples: giving away a mystery, spoiling an important reveal, undercutting a planned twist.

4. **Foreshadowing Gaps.** Even though we do not want to reveal future events early, events that SHOULD be foreshadowed must be. Consult the outline and scene brief for any foreshadowing the chapter is supposed to plant but has not.

5. **Scene Brief Consistency.** Is there anything in the scene brief that was not included or was contradicted in the chapter draft?

---

## Step 2: Implementation Pass

After the audit report is reviewed and approved, run the implementation pass. Provide the model with the original document and the improvement plan, and use this instruction:

> Here is the original [dossier / chapter / scene brief / outline]. Here is the improvement plan. Implement the suggested changes. Only implement the suggested changes. Do not change anything else. Reproduce the entire document with the changes made.

The word "implement" is deliberate. "Rewrite" triggers the model to start from scratch and discard the original work. "Implement" keeps changes targeted.

---

## When to Run This Skill

- After dossier generation: catches worldbuilding contradictions and convenience flags before they embed in prose.
- After character sheets are complete: character capabilities often create new logic conflicts with the premise.
- After outlining: a third pass before first-draft generation catches contradictions introduced during outlining.
- After each chapter draft: the chapter-level version checks continuity with all prior chapters.

For scaling the same six audit categories to a full completed manuscript in a single pass, see the long-context-novel-writing wiki note.

---

## Model Selection

This task requires a reasoning-capable model. A fast cheap model will miss subtle plausibility issues that need if-then chains across the full document. Use Claude Opus or Gemini 2.5 Pro. The cost is justified when run once per dossier or once per chapter.

---

## Craft Reference (do not duplicate, link)

- `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md`: the primary reference for this skill and the six-category audit system.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`: slider baselines for character-world fit validation.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-consistency.md`: cause-and-effect systems targeted by the worldbuilding coherence category.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/antagonist-craft.md`: off-page antagonist agency, a primary subject of the plot-coherence audit.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/scene-structure.md`: causal logic at the scene level that plot coherence audits at manuscript scale.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`: the "trust but verify" rule applies here. AI sounds certain; it is not always right. The audit output is a proposal, not a verdict.
- `${CLAUDE_PLUGIN_ROOT}/references/writing/self-editing.md`: logic and coherence checks belong at the developmental level of the revision pyramid, before any line editing.

---

## Iteration Notes

This skill is living. When new automation nodes, prompt variants, or audit categories surface from the chapter-generation pipeline, update the checklist entries under the Chapter Chronology Layer. The six categories in the Full Audit are stable; the chronology sub-checks are more likely to evolve as the pipeline does.
