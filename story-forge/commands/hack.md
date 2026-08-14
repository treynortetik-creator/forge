---
name: hack
description: Reverse-engineer a comp title into a reusable plot structure template (use short-story-hacker for short fiction)
argument-hint: <comp-title-text-file>
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# /hack

Runs the story-hacker skill on a comp title to produce a reusable plot structure template. For short fiction, use short-story-hacker instead (it runs a different 11-section analysis built for shorter form).

**Input:** $ARGUMENTS, which should be a file path to the source text OR pasted text of the comp title you want analyzed.

**Output:** A single document containing the structural analysis (Pass 2), the anonymized plot template (Pass 3), and the full scene-by-scene summaries (Pass 1), in that order. Ready to save and adapt.

---

## Orchestration

### Step 1: Dependency check

Before anything else, confirm that $ARGUMENTS is present and points to a readable source text (or that text has been pasted inline).

- If $ARGUMENTS is a file path, Read the file now. Confirm the file loaded and note the title the user wants on the output document. If no title is given, use the filename (stripped of extension) as a default.
- If $ARGUMENTS is empty or the file is missing, stop here and tell the user:

> /hack needs a source text. Pass a file path or paste the text directly, then re-run.

Do not proceed without a source text in hand. This mirrors the dependency check inside story-hacker: that skill will halt on the same condition, so catching it here saves a wasted invocation.

---

### Step 2: Format check

Confirm whether the source text is a novel or full-length script (chapter or scene structure present), or a short story.

- Novel or script (multiple chapters or scenes, substantial length): proceed to Step 3 and run story-hacker.
- Short story (single scene or flash piece, clearly short form): stop here and tell the user:

> This looks like short fiction. Run /hack with short-story-hacker instead: that skill covers the Magic Sword, Try/Fail Cycles, Conceptual Hook, and Prose Examples that matter for short form.

This check prevents story-hacker from running a chapter-by-chapter pass on a 1,200-word piece and producing a structurally useless output.

---

### Step 3: Run story-hacker

Invoke the story-hacker skill with the source text and confirmed title.

story-hacker runs three sequential passes internally. Do not interrupt or reorder them:

1. Pass 1 (Per-Chapter/Scene Summaries): scene-by-scene breakdown with characters, setting, conflict, tropes, and four intensity ratings per scene.
2. Pass 2 (Structural Analysis): genre, tropes, character arcs and archetypes, theme, plot devices, key plot structures (inciting incident, midpoint, climax, denouement), worldbuilding, and averaged ratings across all scenes.
3. Pass 3 (Anonymized Plot Template): per-scene summaries stripped of all identifying details, names, and genre markers. Output is a genre-neutral skeleton any author can adapt.

The skill assembles all three passes into a single output document in the order: Pass 2, then Pass 3, then Pass 1.

Pass each step's output forward to the next within the skill. Do not summarize or compress between passes.

---

### Step 4: Save output

After story-hacker completes, Write the final document to:

`$ARGUMENTS/[title-kebab-case]-hacked.md`

where `[title-kebab-case]` is the comp title lowercased and hyphenated. Example: "Moby Dick" becomes `moby-dick-hacked.md`.

If the user specified a different output path in $ARGUMENTS, use that path instead.

Confirm the file path when done.

---

## Notes

- This command is the orchestration layer only. The prompts, rubrics, rating scales, and anonymization rules all live inside the story-hacker skill. Do not duplicate or override them here.
- If story-hacker stops mid-run because the source text was too large for a single pass, Read the remaining portion and continue from where it left off before assembling the final document.
- The output of this command feeds downstream skills: Pass 1 character data feeds character-system bibles; Pass 3 templates feed outline-generator and dossier-to-outline; the averaged ratings inform content-level decisions across the pipeline.
