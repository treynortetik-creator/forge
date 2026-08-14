---
name: braindump-to-dossier
description: "Use when you have a raw story idea and need to turn it into a structured story dossier ready for character development and outlining. Give it a braindump and a title; it runs a generate, evaluate, critique, rewrite loop: produces 12 premises, picks the best one on logic/originality/emotional gut-punch potential, builds a complete story dossier (characters, worldbuilding, synopsis, outline plan), critiques it against storytelling best practices, then rewrites to a final polished dossier ready for the next pipeline stage."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Braindump to Dossier

**Role:** PRODUCER. Entry point for the story-forge pipeline. Your job is to turn a raw idea into a structured story dossier: a master call sheet cataloging everything the book needs before real development begins. No prose. No chapter-by-chapter outline. Generate, evaluate, and curate a premise, then build the catalog.

**System posture for all steps:** You are an expert developmental editor and story architect. This is a complex task. You are not allowed to perform at a mediocre level. Specificity beats generality every time. Emotional resonance matters as much as internal logic.

---

## Step 0: Dependency Check

Run before any generation. Do not skip.

### Required input

If no braindump is present in this conversation, stop and ask:

> "This skill needs your braindump: a raw dump of everything you know about this book. Themes, characters, images, scenes, things to avoid, comp titles, what drew you to the idea. Rough is fine. What is the book title?"

Do not proceed without a braindump and a title.

### Genre templates

This skill works best with four genre-specific templates from the Jason Hamilton Story Hacker system: a tropes guide, a plot structure template (chapter-by-chapter), a character template, and a worldbuilding template. Templates encode reader expectations for the genre. Without them, the output is weaker.

Check for templates in this order:

1. `story-forge/templates/<genre>/` directory (use Bash `ls` or Glob to check)
2. Files provided directly in this conversation

If neither source has templates, warn the user and continue:

> "Genre templates not found. Proceeding on built-in genre knowledge, which produces more generic output. To add your Story Hacker templates: save them to `story-forge/templates/<genre>/tropes.md`, `plot.md`, `characters.md`, `worldbuilding.md`. Continuing without them now."

Note template availability in the final output file header so downstream stages know how the dossier was built.

When templates are found, Read each one before proceeding.

---

## Step 1: Brainstorm 12 Premises

**Goal:** Generate 12 distinct candidate premises using the genre context and the author's braindump as inputs.

Provide all genre context first (tropes template, plot template), then the braindump, then the task instructions. Context before instructions is the correct ordering for this kind of generation.

**The 12 premises must:**
- Have original settings and premises (no default genre furniture)
- Follow the genre tropes and overall plot structure from the templates
- Adhere to the author's braindump: honor stated themes, images, characters, and anti-goals
- Be no more than one paragraph each
- Be numbered and formatted in Markdown

Run this step at high creative temperature. Prioritize variety across the 12: different entry points, different protagonist positions, different conflict angles. Convergence on the "safest" option defeats the purpose. If templates are absent, use built-in knowledge of the likely genre and note this.

---

## Step 2: Pick the Best Premise

**Goal:** Evaluate all 12 against four specific criteria. Output only the winner, verbatim. No preamble. No analysis.

**Evaluation criteria (apply in this order):**

1. **Logical soundness.** Does the premise hold together internally? Does cause and effect work, even if the world has magic or technology that breaks real-world rules? A fantasy premise can have impossible physics; it cannot have incoherent internal logic.

2. **Originality.** Which feels most distinct from typical books in this genre? Tropes are expected, but the setting and premise execution should feel fresh.

3. **Emotional gut-punch potential.** Which setup has the most room for moments that genuinely affect a reader: grief, loss, betrayal, unexpected grace, hard-won joy, catharsis? Prefer premises with built-in asymmetry and cost.

4. **Braindump alignment.** Which best honors what the author said they want this book to be? Explicit braindump elements (a specific character, an image, a theme, a thing to avoid) are the author's IP. Preserve them.

After making the selection: reproduce the text of the chosen premise verbatim. Output only that text. Nothing else.

---

## Step 3: Build the Complete Story Dossier

**Goal:** Produce a structured dossier cataloging every element the book needs before deep development begins. The dossier is a call sheet, not a bible. Brief, not fleshed out. Depth comes in the next two pipeline stages (character development, worldbuilding development).

Provide all context first (premise, templates, braindump), then the task instructions.

**Required dossier sections:**

**Characters.** A complete list of every character, including minor ones. Label each with their role: protagonist, antagonist, side character, henchman, comic relief, love interest, mentor, rival, etc. Give a brief description of who the character is and their role in the story. Keep it to 1-2 sentences per character. Do not over-develop yet; that is the job of the downstream character automation.

When referencing a named group (a guild, a crew, a unit, a family, an organization), name 3-5 individual members so the author has named characters to use when writing scenes where group members are present. Without named individuals, scenes set within the group become populated with generics.

**Worldbuilding Info.** A complete list of all locations, objects, and other worldbuilding elements this premise requires. One sentence per element describing what it is and its role in the story. Do not over-develop; that is the worldbuilding automation's job. Flag if worldbuilding scope seems at risk of bloating (more than 20-25 elements at dossier stage is a warning sign).

**Synopsis.** Reproduce the chosen premise verbatim. Do not paraphrase, improve, or compress.

**Outline Plan.** Describe what the full chapter outline will need to address. Do not write the outline. Think like a developmental editor briefing a ghostwriter: name the structural beats the story requires (inciting incident, midpoint, climax, closing image), flag pacing challenges, identify character arcs to track, note worldbuilding reveals that need sequencing, and flag anything in the premise that creates an outlining difficulty. This section hands off to the `dossier-to-outline` stage.

Add other sections if the premise clearly requires them (magic system overview, faction map, timeline framework). Label additions clearly.

---

## Step 4: Dossier Critique

**Goal:** Audit the dossier for problems before the final pass. Produce an improvement plan only. Do not rewrite.

Provide all context first (premise, templates, dossier, braindump), then the critique instructions.

**Critique criteria:**

- **Logical consistency** (even in fantasy or sci-fi, internal cause and effect must hold): flag "because the plot needs it" elements with no in-world justification, motivation gaps that would prevent the story from starting, character capabilities that contradict the worldbuilding, and worldbuilding rules that contradict each other. Reference [[plot-coherence]]'s six-category audit framework for the full checklist.

- **Originality while maintaining genre tropes:** does this feel genuinely fresh, or is it a predictable execution of the most common version of the genre? Tropes are required; the specific execution of setting and character should not be generic.

- **Emotional impact potential:** are there genuine gut-punch opportunities built into the setup, or is the premise too comfortable? An emotional check at this stage is cheaper than trying to retrofit one after 80,000 words are written.

For each issue: name the category (Logic, Originality, Emotional Impact, or Character-World Fit), describe the specific problem, and give a concrete suggestion for what to change and why. Include specific examples of what you would change, not vague directions.

Do not rewrite the dossier. Produce a structured improvement plan only.

---

## Step 5: Dossier Rewrite

**Goal:** Apply the critique plan to the dossier. Implement only the flagged changes.

The word "implement" is deliberate. "Rewrite" triggers the model to start from scratch and discard the work built in Step 3. "Implement" keeps changes targeted. Use "implement" in your instructions to yourself.

Provide the original dossier, the improvement plan, and the braindump. Implement only the suggested changes. Do not improve beyond what the plan specified. Reproduce the entire dossier with the changes made.

---

## Output

Write the final dossier to `dossier-[title-slug].md` in the project working directory (or the story-forge project root if running inside the plugin).

Add a one-line header at the top of the file noting: date generated and whether genre templates were present or absent.

Report to the user:
- The chosen premise (first sentence only, so they can confirm the right one was selected)
- Count of characters and worldbuilding elements cataloged
- Output file path
- Next step: "Run `dossier-to-outline` to develop characters, worldbuilding, and the full chapter outline."

---

## Craft References

These wiki notes document the underlying craft theory. Reference them, do not duplicate them here.

- [[plot-coherence]]: the six-category logic-check framework behind Step 4's critique criteria (Premise Logic Check, Character-World Fit, Worldbuilding Coherence, Plot Setup Plausibility, Early-Stage Convenience Flags, Specific Fixes)
- [[character-system]]: the character bible structure that downstream character development builds from the dossier's character seeds; the 15-slider rubric and MBTI/Enneagram profiles begin here
- [[worldbuilding-method]]: the 12-category framework (Settings and Locations, Objects and Artifacts, Magic Systems, Groups and Races, etc.) that the worldbuilding automation expands from the dossier's one-sentence seeds
- [[outlining-method]]: the five-automation chain context; this skill is Automation 1; the Outline Plan section of Step 3 is the direct handoff to Automation 4
- [[anti-slop]] and `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`: the dossier is a planning document, not prose, but vocabulary inflation applies throughout; the banned-words list at `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md` is a hard constraint; this skill must model what the pipeline teaches (no em-dashes, no inflated vocabulary, no AI-tell transitions)
- [[voice-matching]]: not applicable at this stage; noted here so the producer stage does not prematurely lock in voice decisions that belong to a later pipeline step

---

## Operating Notes

- **Do not pad thin input.** If the braindump is sparse and templates are absent, the output will be thin. Say so. Do not inflate the dossier with generic genre content and present it as the author's custom concept.
- **The dossier is a call sheet, not a bible.** Characters get 1-2 sentences here. Worldbuilding elements get one sentence. Resist the urge to flesh things out early; that is the next two pipeline stages. Over-development at the dossier stage creates artifacts that conflict with what the deeper development steps produce.
- **Step 4 is critique, not rewrite.** If you find yourself drafting revised dossier content during the critique step, stop. Produce the improvement plan. Apply it in Step 5.
- **Step 5 uses "implement," not "rewrite."** If you catch yourself saying "rewrite the dossier incorporating the suggestions," correct it. Implement is the right verb. The distinction determines whether Step 3's work is preserved or discarded.
- **Template-less runs are degraded runs.** Mark the output file accordingly.

---

## Iteration Notes (Living Skill)

After each run, log patterns in `CHANGELOG.md` in this directory:

- Any Step 2 evaluation where multiple premises were genuinely tied on the four criteria: note whether a tiebreaker criterion would have helped, and what it would have been.
- Any Step 3 dossier section that needed heavy revision in Step 5: if this happens twice for the same section, update the Step 3 instructions.
- Any genre where the template-less fallback produced clearly insufficient output: note the genre and what was missing.
- Any critique category in Step 4 that keeps surfacing issues not covered by the current criteria: add the new category if it recurs across two or more runs.
- Any banned-word or em-dash slip in the final dossier: the skill must model what the pipeline teaches.
