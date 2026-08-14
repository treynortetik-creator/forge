---
name: short-story-hacker
description: Use when structurally analyzing a short story and produce a reusable breakdown covering the magic sword, try/fail cycles, heart's-desire arc, inciting incident, conceptual hook, and verbatim prose examples. Invoke with a short story text in hand (pasted or file path).
allowed-tools: [Read, Write, Bash]
---

# Short Story Hacker

## Role

Expert literary analyst. Goal: give writers a transferable structural breakdown of any short story, covering every reusable craft mechanic. Output is a clean markdown document, ready to save or study. No preamble, no commentary outside the defined sections, no padding.

---

## Dependency Check (Run First)

This skill has one required input: the short story text.

If the user has not provided it (pasted or as a file path), stop here and ask:

> "This skill needs the short story text. Paste it here or give me a file path."

If a file path is given, Read the file before proceeding. Do not analyze until the full text is loaded.

Once the text is in hand, proceed to the Process below.

---

## Process

Run all 11 sections in order. Do not skip any section, even for very short stories. If a section genuinely does not apply (e.g., no denouement in a flash piece), state that plainly rather than inventing content.

Work only from what is on the page. Do not import assumptions from outside the text.

---

### Section 1. Summary

Write 5-6 sentences covering the direct events of the story. Use character names, not pronouns. Describe what happens, not what it means. No interpretation in this section.

---

### Section 2. Conceptual Hook

Deep analysis. Answer three questions:
- What is the primary hook? What makes this story interesting to a reader picking it up cold?
- What makes this story stand out from other stories in the same genre or premise?
- What is the central concept, and what can writers extract from it?

---

### Section 3. Characters

List every character who appears. For each character, cover all of:
- Actions taken and what happens to them during the story
- Physical descriptors given in the text
- Primary role: protagonist, antagonist, side character, love interest, mentor, etc.
- Heart's Desire: what is the deepest thing they want most?
- Heart's Desire arc: does the desire change over the course of the story? Do they get what they wanted? Do they learn their heart's desire was not truly what they needed? Or do they get it and find it was not what they expected?

The Heart's Desire is the engine behind every character decision. See [[character-system]] for how this driver connects to the full character arc and the slider dimensions that show how desire shapes behavior under pressure.

---

### Section 4. Worldbuilding / Setting

List all key setting and worldbuilding elements that the story depends on. For each:
- Describe it as the story presents it, including any exposition the text provides
- Explain specifically how it serves the plot
- Explain specifically how it serves character development

Every genre has worldbuilding elements. A contemporary story set in a hospital, a specific neighborhood, or a single room has setting that earns its place or does not. Treat all settings the same way.

---

### Section 5. Inciting Incident

Identify the inciting incident. Then answer:
- What problem does it present?
- How does it affect the protagonist externally?
- How does it affect the protagonist internally?
- Does the inciting incident rip the protagonist's Heart's Desire away from them? If so, explain how.

See [[plot-coherence]] for the craft principle here: the inciting incident should follow from cause and create a "but" or "therefore," not an "and then." Convenience inciting incidents (random, unearned) are a coherence failure, not a genre feature.

---

### Section 6. Conflict

One to two sentences only. Identify the main source of conflict and tension driving the story forward.

---

### Section 7. Magic Sword

In every short story, the protagonist should gain or already possess some ability, item, knowledge, companion, or other tool that can solve the problem presented by the inciting incident. This is not a literal sword. It is whatever power can defeat the opposing force, if the protagonist can get their hands on it or learn to wield it.

Identify what the Magic Sword is. Explain whether the protagonist already holds it or acquires it during the story, and whether they know how to use it at the start.

---

### Section 8. Try / Fail Cycles

Short stories typically contain 1-4 try/fail cycles. Each cycle follows the same pattern: the protagonist tries to solve the problem from the inciting incident, fails, and tries again. The final cycle is the climax. The climax is the only point where a real win (or definitive loss) is possible.

List each cycle as a separate bullet. Label them Try/Fail Cycle 1, Try/Fail Cycle 2, etc. For each:
- State clearly what the try was
- State clearly what the failure was

Do not blend cycles. If two attempts happen in quick succession, treat them as separate cycles if they have distinct try and fail beats.

---

### Section 9. Climax

Answer all of the following:
- What is the climax?
- What is the outcome: positive, negative, or bittersweet?
- How did the protagonist try again at the climax, and what was different this time?
- What internal or external change did the protagonist have to make in order to reach this outcome?
- What changes to characters and world result from the climax?

---

### Section 10. Denouement

What is the denouement? What loose ends are tied up? How does the closing beat demonstrate the changes that have happened to the characters or the world as a result of the story's events?

---

### Section 11. Prose Examples

Identify 5-6 passages of excellent prose. For each, reproduce it verbatim, then add one brief note on what makes it work: sentence rhythm, word precision, image specificity, dialogue compression, etc.

Before calling a passage "excellent," cross-check it against [[anti-slop]] and `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`. If a passage uses banned-word patterns (inflated vocabulary, negative parallelisms, em-dash abuse, abstract emotion without grounding), flag it as "strong but slop-adjacent" and explain why. An author's prose can be excellent in craft and still carry AI-pattern tells worth naming.

Apply the forensic lens from [[voice-matching]]: sentence length range, vocabulary tier, how description is distributed, how dialogue is tagged. A passage earns the "excellent" label when it demonstrates architectural choices, not just pleasant rhythm.

---

## Output Format

Render in markdown. Use this structure exactly:

```
## [STORY TITLE]
### By [AUTHOR NAME]

**Summary:**
[5-6 sentences]

**Conceptual Hook:**
[analysis]

**Characters:**
- **[Name]:** [description, role, Heart's Desire, arc]

**Worldbuilding / Setting:**
- **[Element]:** [description, plot function, character function]

**Inciting Incident:**
[analysis]

**Conflict:**
[1-2 sentences]

**Magic Sword:**
[analysis]

**Try / Fail Cycles:**
- **Try/Fail Cycle 1:** [try and failure]

**Climax:**
[analysis]

**Denouement:**
[analysis]

**Prose Examples:**
*"[verbatim quote]"*
[note on what makes it work]
```

If the user asks for the output as a saved file, Write it to their specified path or default to `story-forge/output/[story-title]-hacked.md`.

---

## Iteration Notes

- Source: the "Analyze Each Short Story" node of an n8n short-story analysis automation (archived at `references/writing/book-automation-workflows.md`). The source ran this analysis on each H2-delimited section of a Google Doc anthology via Gemini 3 Pro on OpenRouter. This skill treats the full story as a single input instead of batching by header.
- The 11-section structure maps directly to the prompt criteria in that source node, with prose-quality standards added from [[anti-slop]], `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`, and [[voice-matching]].
- For batch analysis of multiple stories in one session, run this skill once per story.
- For downstream use: the Characters output feeds [[character-system]] character bibles; the Magic Sword and Try/Fail Cycles feed the [[outlining-method]] five-automation chain; Prose Examples can seed a [[voice-matching]] extraction session.
