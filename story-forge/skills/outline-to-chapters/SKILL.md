---
name: outline-to-chapters
description: "Use when drafting one or more book chapters from a completed outline. Runs the full 13-step chapter generation pipeline per chapter: context-slicing selectors for plot, characters, and worldbuilding; wordcount estimation with 1.25x inflation; three-part scene brief construction; dual chronology checks (pre-draft and post-draft); first draft; style check; and final rewrite. Requires an outline, character bible, worldbuilding sheet, and voice spec before running. Stop and report if any prerequisite is missing."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Outline-to-Chapters

You are a pipeline conductor and expert novelist. Your job is to run the full 13-step chapter generation pipeline for each requested chapter, in order, without skipping steps or combining steps that have distinct purposes. Each step catches failure modes the next step cannot. You run the system; you do not improvise around it. No prose is generated until the scene briefs and chronology checks are complete.

---

## Dependency Check (Run This First)

Before doing anything else, check that all four prerequisite artifacts exist. If any are missing, stop immediately and report:

> "This skill needs [ARTIFACT]. Build it first by running the [PRODUCER SKILL] skill, or supply your existing [ARTIFACT]."

**Required artifacts:**

1. **Outline** (producer: `dossier-to-outline` or `outline-generator`). Chapter-level breakdown with plot summary, POV, levels, and sliders for each chapter.
2. **Character bible** (producer: `dossier-to-outline`). Full profiles for all major characters including slider baselines, MBTI/Enneagram, dialogue samples, and arc notes.
3. **Worldbuilding sheet** (producer: `dossier-to-outline`). All active locations, systems, factions, and objects organized by category.
4. **Voice spec** (producer: `voice`). Prose style sheet extracted from the author's own finished fiction: sentence rhythm, vocabulary tier, dialogue handling, POV habits, and a prose anchor passage.

If all four exist, ask the user for:
- Which chapters to generate (specific list, range, or "all")
- What tense the book is written in (first-person, third-person limited, third-person omniscient)
- Any author notes for this session (optional)

Then proceed.

---

## Pre-Loop: Parse and Load

Before iterating, collect from the provided files:
- Full prose style sheet (from the voice spec)
- Full character bible
- Full worldbuilding sheet
- Full outline
- Tense (from user input above)
- ~~Last 2,000 words of the existing draft~~ — **moved into Step 1.** See the 🔴 note below.

Extract the continuity window with the helper:

```bash
python3 skills/outline-to-chapters/scripts/chapter_context.py last-words <draft_file> --words 2000
```

Parse the outline into a list of chapter titles to iterate over. Confirm the list with the user if generating multiple chapters, then run Steps 1-13 for each chapter in order.

> 🔴 **The 2,000-word window is re-read at the START OF EVERY CHAPTER, not once here.**
> The source automation fetches it as the first action of each loop iteration, immediately after the
> previous chapter was appended to the draft. Computing it once in Pre-Loop means chapter 2 onward all
> draft against a stale predecessor — and it feeds **five** separate prompts (Steps 5, 6, 7, 8, 10), so
> the whole chapter is built on the wrong context. **It fails silently and reads as ordinary drift.**
> Note the tell: the 20,000-word window in Step 11 *is* re-fetched per chapter. The asymmetry was the bug..

---

## Per-Chapter Loop: Steps 1-13

---

### Step 1: Plot Selector

**FIRST, before anything else in this step — refresh the continuity window.** The previous chapter was
appended to the draft at the end of the last iteration, so re-read it now:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/outline-to-chapters/scripts/chapter_context.py \
  last-words <draft_file> --words 2000
```

Returns empty on chapter 1 (the draft file does not exist yet), which is the correct state. **Do not
carry a window forward from a previous chapter.**


**Purpose:** Extract only this chapter's plot information from the full outline, verbatim. Keeps later steps focused; avoids diluting context with irrelevant chapters. Use a cheap/fast model for this step.

**Prompt:**

> You are a parser. Given the outline document, extract verbatim all of the information for [CHAPTER NAME], which includes the summary of the plot, the POV, the levels, and the sliders. Reproduce that text exactly as it exists in the outline. Do not include any other chapters, just [CHAPTER NAME]. Do not include any preamble, commentary, or anything other than what is asked for.

**Output:** Verbatim plot text for the current chapter only.

---

### Step 2: Character Selector

**Purpose:** Extract only the character profiles needed for this chapter. Full profile for active participants; 1-2 sentence summary for mentioned or indirectly linked characters. Keeps context lean for later expensive steps. Use a cheap/fast model.

**Prompt:**

> This task is all about selecting the exact characters that are actively in [CHAPTER NAME], or mentioned. The current chapter is [CHAPTER NAME]. You have the plot of this chapter so you know what is happening.
>
> Follow these steps:
>
> 1. Carefully examine the plot of [CHAPTER NAME] and determine which characters are actively participating in the scene, and which other characters might be mentioned or indirectly linked, even if not physically present.
> 2. For each active character, reproduce their entire profile verbatim from the character bible, including the same markdown formatting.
> 3. For mentioned or indirectly linked characters, provide only a 1-2 sentence summary based on their profile in the character bible.
>
> Format output as:
>
> ## Active Characters In This Chapter
>
> ### [CHARACTER NAME]
>
> [full verbatim profile]
>
> ### Mentioned or Indirectly Linked Characters For This Chapter
>
> * **[Name]**: [1-2 sentence summary]
>
> Do not include any preamble, commentary, or anything other than what is asked for.

---

### Step 3: Worldbuilding Selector

**Purpose:** Same logic as Step 2, but for worldbuilding elements. Active elements get the full verbatim section; mentioned elements get a 1-2 sentence summary. Use a cheap/fast model.

**Prompt:**

> This task is all about selecting the exact worldbuilding elements that are actively in [CHAPTER NAME], or mentioned. The current chapter is [CHAPTER NAME]. You have the plot of this chapter so you know what is happening.
>
> Follow these steps:
>
> 1. Carefully examine the plot of [CHAPTER NAME] and determine which worldbuilding elements are actively in the scene, and which might be mentioned or indirectly linked.
> 2. For each active element, reproduce the entire section verbatim from the worldbuilding sheet, including the same markdown formatting.
> 3. For mentioned or indirectly linked elements, provide only a 1-2 sentence summary.
>
> Format output as:
>
> ## Active Worldbuilding Elements In This Chapter
>
> ### [ELEMENT NAME]
>
> [full verbatim section]
>
> ### Mentioned or Indirectly Linked Worldbuilding Elements For This Chapter
>
> * **[Name]**: [1-2 sentence summary]
>
> Do not include any preamble, commentary, or anything other than what is asked for.

---

### Step 4: Wordcount Estimator

**Purpose:** Pick a chapter-specific word count target, then apply a mandatory 1.25x inflation to correct for the model's consistent tendency to undershoot. Climax chapters run shorter and faster; establishment chapters run longer. Variable word count preserves rhythm.

**Step 4a prompt:**

> Your task is to pick how many words [CHAPTER NAME] should be.
>
> 1. Analyze the genre of this story.
> 2. Analyze the events of the chapter.
> 3. Choose an appropriate word count based on the events in the chapter, the genre standards, and the pacing of the scene. The word count must not go below 1,000 or above 5,000.
> 4. Output only the number. No other text. Example: 2500
>
> Do not include any preamble, commentary, or anything other than the exact number.

**Step 4b prompt (apply immediately after 4a):**

> Take the number [STEP 4a OUTPUT] and multiply it by 1.25. If the result exceeds 6,000, cap it at 6,000.
>
> Output only the final number. No other text.

Alternatively, get a fast heuristic via the helper and adjust manually:

```bash
python3 skills/outline-to-chapters/scripts/chapter_context.py estimate --scene-type action
```

---

### Step 5: Plot Scene Brief

**Purpose:** Write a detailed narrative blueprint for the chapter: what happens beat by beat, from what POV, at what word count, ending on a planned cliffhanger. This is the primary document the First Draft reads from.

**System prompt:** "This is a complex task and requires your full faculties. You are not allowed to be mediocre for this task. You are an expert plotter, character expert, and developmental writer of bestselling books."

**Prompt:**

> Given the following: the current chapter plot, the full outline (for context on how this chapter fits with all others), the selected characters and worldbuilding for this chapter, the adjusted word count from Step 4b, and the last 2,000 words of the existing draft, flesh out a "plot scene brief" for [CHAPTER NAME]. Make sure the chapter is clearly labelled with the word(s) "[CHAPTER NAME]". Do not name the chapter anything besides this.
>
> Include each of these sections:
>
> **Plot Verbatim:** Reproduce the current chapter plot text exactly as it appears, including the bulleted list of levels and sliders.
>
> **POV and Tense:** Pull the viewpoint character from the current chapter plot. The tense is: [TENSE FROM USER].
>
> **Word Count:** Include this number from Step 4b verbatim. Only the number. **If the scene's
> material does not fill it, cut the target rather than padding** — a word count met by elaboration is
> exactly how the over-described middle happens.
>
> **Scene contract (write this BEFORE the beats):** copy `Wants`, `Opposition`, `Outcome` and `Cost`
> from the chapter's outline row. Then add, for **every** character present who speaks or acts:
> what they want in this scene, and **the one thing they will not say out loud**. Two characters who
> want the same thing and say everything they mean produce the flat, agreeable, on-the-nose dialogue
> that reads as machine-written. The unsaid thing is what subtext is made of.
>
> **Beats and Blocking:** Draft 12-18 scene beats covering the important details of the scene. **Beats focus exclusively on plot — what happens.** 🔴 **Do not establish sensory detail here.** That is the drafting step's job; a beat list that carries atmosphere is doing two jobs badly and inflates the count.
>
> ⚠️ **Do not exceed 18 beats.** At 20-25 beats for a 2,500-word chapter you are writing roughly one
> beat per 100 words, which mechanically forbids a **sequel beat** — the reaction, thought and decision
> that has to follow a disaster before the next scene can start. Relentless, evenly-paced eventfulness
> with no room to react is the single most recognisable texture of AI-drafted fiction. Leave the room. For each beat, also establish blocking: describe how characters, objects, and elements are positioned in space, how they move, and what physical actions they are performing relative to each other and their surroundings. Label both the beat and the blocking for each bullet point.
>
> **Previous Chapter:** Confirm the plot for this scene picks up appropriately after the end of the previous chapter text. Disregard if this is the first chapter and there is no previous chapter text.
>
> **Chapter ending:** Every chapter ends on a TURN — the situation is materially different from how it began. A cliffhanger is one kind of turn, not the only kind; a decision, a reversal, a revelation or a cost paid all qualify. **Vary the type**, because the list of cheap tells below includes "every chapter ending the same way." A turn that feels earned, not forced. It must not venture into territory that will not be covered until future chapters.
>
> Effective cliffhanger types:
> - Reversal: a plan succeeds but creates a worse problem, or fails in an unexpected way
> - New threat enters: introduce a danger just as the current problem seemed manageable
> - Revelation recontextualizes: a piece of information changes how the reader understands everything that came before
> - A choice is made: end the chapter the moment a character commits to an irreversible action, before we see the result
> - Emotional gut-punch: a betrayal, loss, or confession lands; let it sit without resolving the reader's feelings
>
> Craft rules for cliffhangers: cut the scene earlier than feels natural, stop before the aftermath; use a short punchy final sentence; vary intensity, not every chapter needs a bomb; plant the setup 2-3 scenes earlier so the payoff feels earned; end on the character's reaction to news rather than the news itself.
>
> Cliffhangers that read as cheap: fake-out deaths or dangers resolved immediately at the start of the next chapter; withholding information the POV character already knows just to create mystery; every chapter ending the same way; cliffhangers with no connection to the chapter's emotional arc.

---

### Step 6: Character Scene Brief

**Purpose:** Produce character-specific state for THIS scene only. No future details, these are stripped against the full outline. Sliders are adjusted per-scene, not just baseline. This step prevents character bible spoilers from leaking into the prose.

**System prompt:** Same as Step 5.

**Prompt:**

> Given the full outline, the selected character profiles, the plot scene brief from Step 5, the last 2,000 words of the existing draft, and the 15-slider rubric, flesh out a "character scene brief" for [CHAPTER NAME].
>
> For each active character:
> - Reproduce their profile with small modifications for this specific scene
> - Remove any parts that reference future events (consult the full outline to determine this)
> - Update physical appearance to reflect their state at this moment: clothing, posture, visible wear, not their baseline appearance from the profile
> - List all 15 character sliders. For each slider, include: their baseline number; the number for this specific scene on a scale from -10 to +10 (interpolate within the rubric); and one sentence explaining what the shift implies for this specific scene
>
> The 15 sliders: Stress/Calm, Fear/Courage, Suspicion/Trust, Callous/Empathic, Impulsivity/Self-Control, Dominance/Submission, Pessimism/Optimism, Introverted/Extroverted, Gut/Logic, Detail Focused/Big Picture, Cautious/Risk Taker, Seriousness/Humor, Deception/Honesty, Stability/Sensitivity, Shame/Self-Worth.
>
> For mentioned or associated characters: 1-2 sentence snapshot only, no future details.
>
> Format output as:
>
> ## [CHAPTER NAME] Characters
>
> ### [ACTIVE CHARACTER NAME]
>
> [modified profile with slider list]
>
> ### Mentioned or Indirectly Linked Characters For This Chapter
>
> * **[Name]**: [1-2 sentence snapshot]
>
> Do not include any preamble, commentary, or anything other than what is asked for.

The full 5-point anchor rubric lives in `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`. **Load it into context before running this step** — the interpolation instruction below is meaningless without it.

---

### Step 7: Worldbuilding Scene Brief

**Purpose:** Same logic as Step 6 but for worldbuilding. Each element is cleaned of spoilers and framed as a snapshot: time-of-day, weather, and tone-relevant details for locations.

**System prompt:** Same as Step 5.

**Prompt:**

> Given the plot scene brief from Step 5, the full outline, the selected worldbuilding elements, and the last 2,000 words of the existing draft, flesh out a "worldbuilding scene brief" for [CHAPTER NAME].
>
> For each active worldbuilding element:
> - Reproduce the section verbatim with modifications: remove any parts that reference future events (consult the full outline to determine this)
> - For settings and locations: reflect the current time of day, weather, and other details relevant to the tone of this scene
> - Confirm each element contains all information needed to write this chapter
> - Do not include any reference to events that have not yet occurred in the story
>
> For mentioned or indirectly linked elements: 1-2 sentence summary only, no future details.
>
> Format output as:
>
> ## Active Worldbuilding Elements In This Chapter
>
> ### [ELEMENT NAME]
>
> [modified section]
>
> ### Mentioned or Indirectly Linked Worldbuilding Elements For This Chapter
>
> * **[Name]**: [1-2 sentence summary]
>
> Do not include any preamble, commentary, or anything other than what is asked for.

---

### Step 8: Chronology Check (Scene Brief)

**Purpose:** Catch inconsistencies in the three scene briefs before prose generation. Fixing a brief is orders of magnitude cheaper than fixing a draft.

**System prompt:** Same as Step 5.

**Prompt:**

> You have the previous chapter text (if any), the full outline, the combined scene brief (plot + character + worldbuilding from Steps 5, 6, 7) **and — critically — the raw Character Selector and Worldbuilding Selector outputs from Steps 2 and 3.**

> 🔴 **Include the raw selector outputs.** Without them this check can only compare the brief against the outline. With them it can catch a brief that *mangled a source profile* — which is the failure it exists to find. Category 1 (plot details revealed too early, secret motivations) is unanswerable without the profiles. Run a "chronology check" to confirm the scene brief is chronologically consistent with the full outline and with what has already been written.
>
> Flag any issues in these categories:
>
> 1. **Plot Details Revealed Too Early:** Does the brief introduce details from future chapters that should not yet be revealed? This includes character secret motivations, worldbuilding elements not relevant at this stage, or hints at mystery or major reveals.
>
> 2. **Plot Details Already Revealed:** Does the brief treat anything as a fresh introduction when the full outline makes clear it should already be known to the reader or characters?
>
> 3. **Continuity:** Does this scene brief fit naturally in its correct position in the novel, given the full outline?
>
> 4. **Previous Chapter Text:** Does the scene brief flow naturally from where the previous chapter ended?
>
> 5. **Cliffhanger:** Does the cliffhanger feel natural? Does it flow into the next chapter (see full outline) without revealing anything reserved for a later reveal?
>
> List all flagged issues and a recommended fix for each. Do not rewrite the brief. Produce the improvement plan only.

---

### Step 9: Scene Brief Rewrite

**Purpose:** Merge the three separate scene briefs into one unified document and implement the chronology fixes from Step 8. The unified scene brief is what the First Draft reads.

**Prompt:**

> Using the text of the original scene brief (the plot, character, and worldbuilding sections from Steps 5, 6, and 7 combined) and the improvement plan from the chronology check, implement the suggestions in the improvement plan. Only implement the suggested changes. Do not change anything else. Reproduce the entire scene brief with the changes made.

The word "implement" is deliberate. "Rewrite" triggers the model to start from scratch and loses the original work. Keep changes targeted.

---

### Step 10: First Draft

**Purpose:** Write the actual chapter prose. The most expensive step. Reads from the unified scene brief and the voice spec.

**System prompt:** "This is a complex task and requires your full faculties. You are not allowed to be mediocre for this task. You are an expert author who writes bestselling books."

**Prompt:**

> Given the prose style sheet, the last 2,000 words of the existing draft (for continuity), and the scene brief, write the entire [CHAPTER NAME] based on the scene brief. Cover it thoroughly from deep point of view, writing the scene as if written by a bestselling novelist, not rushing through the scene. Use the prose style samples to know what the prose style should be. Pay close attention to show-don't-tell and deep point of view to fully flesh out the scene without skipping important details. The reader should feel fully immersed in the scene, seeing events through the lens of the viewpoint character rather than being told what happened.
>
> Tense: [TENSE FROM USER]. Note the POV character in the scene brief above.

**Mandatory writing constraints (all non-negotiable):**

- Style: match the prose style of the voice spec
- Word count: target approximately [STEP 4b WORD COUNT] words
- Continuity: pick up directly after the previous chapter text, no repeated moments, no overlap
- No em-dashes. Use commas or ... instead
- Do not start multiple sentences in a row with the same word
- Do not use any word from the prohibited words list (see `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`, pass the list as a `<prohibited_words>` block)
- Convey events and story through dialogue where possible; dialogue must always continue the action, never stall or add unnecessary fluff; vary descriptions to avoid repetition
- No metaphors in the prose
- Never conclude the scene on your own, follow the beat instructions exactly; never deviate from the brief; never write beyond what the brief specifies
- Vary paragraph length
- Vary sentence length, mix short and long; never run too many of either in a row; use mixed cadence
- Scene breaks: `***`
- Chapter title: H1 heading using numerals, not spelled-out numbers

See `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` for why each constraint exists. The three-method humanization stack is: voice injection (voice spec feeds Step 10), constraint prompting (the rules above), and multi-pass deslop (the the `de-sloppifier` skill skill, run separately after all chapters are drafted).

**Draft-Time Doctrine (write like the edit).** Include this block in the Step 10 prompt context. Extracted from a 131-edit author hand-pass (2026-07-18); it encodes what a line edit would otherwise cut, so the draft never contains it:

1. Never narrate the narration (no "the truest thing," no explaining why the telling matters, no restating a beat that landed).
2. One figure per beat; no cute similes; replacements shorter and meaner.
3. Stop when the image lands; no re-describing clauses, no end-of-paragraph imagery recap.
4. Name the noun; no vague "thing/something" hedges; violence gets its real verb.
5. Split at the pivot; payoffs get their own short sentence; fragments legal.
6. Diction plainer or crueler, never fancier.
7. Concrete props over abstractions; declared acts get a hand doing them; props get specs and wear.
8. Dialogue does the work; narration never duplicates what a line already carries.
9. Flourishes come from the story's established coinage, never fresh ornament.
10. An aphorism needs a concrete mechanism proved by its scene; it never grades itself; one per scene.
11. Keep the first rhetorical reversal in a paragraph, cut the third (antithesis density cap).
12. Order beats in performance chronology, the order the room experiences them.
13. No emotional summary after the emotion already landed.

Banned families (in addition to `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`): the word "ledger" and any order/counting meta-narration (a character counting concrete real objects is exempt); emotion sitting/settling in the chest + "cold" as an emotion descriptor (physical cold exempt); "held breath" as emotional shorthand; generic "coat" as default garment (name the specific garment or cut it; plot/character garments exempt); in multi-POV books, each narrator's exclusive idiom families stay in their own chapters.

---

### Step 11: Chronology Check 2 (Post-Draft)

**Purpose:** Check the actual prose against the last 20,000 words of the existing draft and the full outline. The post-draft check catches different failure modes than the pre-draft check: the draft can introduce contradictions even when the brief was clean.

Extract the context window:

```bash
python3 skills/outline-to-chapters/scripts/chapter_context.py last-words <draft_file> --words 20000
```

**System prompt:** Same as Step 5.

**Prompt:**

> You have the last 20,000 words of the existing draft, the full outline, the scene brief, and the newly written chapter. Look at the chapter and run a "chronology check" to confirm it is consistent with previous chapters and with the full outline.
>
> Check these five categories:
>
> 1. **Previous Text Consistency:** Does the chapter contain any contradictions with the previous text? Look for small details, throwaway comments from or about characters, locations, and other story elements.
>
> 2. **Full Outline Consistency:** Does the chapter contain any contradictions with the full outline?
>
> 3. **Future Events:** Does the chapter contain information about future events that should not yet be known? Does it give away information about a mystery or other important reveals?
>
> 4. **Foreshadowing:** Even though we do not want to reveal future information, are there events that SHOULD be foreshadowed in this chapter, per the full outline and scene brief, that are missing from the prose?
>
> 5. **Scene Brief Consistency:** Is there any information from the scene brief that was not included or was contradicted in the chapter?
>
> List all issues and create a recommended fix for each. Do not rewrite the chapter. Produce the improvement plan only.

---

### Step 12: Style Check

**Purpose:** Compare the draft against the prose style sheet and flag any divergence in voice or technique.

**System prompt:** Same as Step 5.

**Prompt:**

> You have the prose style sheet and the newly written chapter. Your job is to run a "style guide check" to confirm that this chapter is written in a similar style to the style samples and adheres to the style guide recommendations.
>
> Do not recommend CHANGING the chosen tense or viewpoint character — those are fixed by the outline. **Do flag VIOLATIONS of them:** head-hopping into a non-POV character's interiority, tense drift, and filter-word POV leakage ("she saw that", "he felt that") are defects, not style choices, and this is the only per-chapter pass positioned to catch them.
>
> List all style issues and create a recommended fix for each. Do not rewrite the chapter. Produce the improvement plan only.

---

### Step 13: Rewrite (Final)

**Purpose:** Implement feedback from both Step 11 (Chronology Check 2) and Step 12 (Style Check) into the final chapter version. Then append to the draft.

**Prompt:**

> Using the text of the original chapter, the chronology improvement plan from Step 11, and the style improvement plan from Step 12, implement the suggestions in both improvement plans. Only implement the suggested changes. Do not change anything else about the original chapter. Reproduce the entire chapter with the suggested changes made.
>
> The chapter should begin with the chapter header written as an H1 heading using numerals: "# [CHAPTER NAME]"

Save the final chapter. Append it to the draft file. Advance to the next chapter if generating multiple.

---

## Helper Script

`scripts/chapter_context.py`, pure stdlib. Two modes.

**`last-words`:** Extract the last N words from a draft file. Splits on whitespace; never cuts mid-word. Used in the pre-loop (2K window) and Step 11 (20K window). Prints to stdout.

```bash
python3 skills/outline-to-chapters/scripts/chapter_context.py last-words draft.md --words 2000
python3 skills/outline-to-chapters/scripts/chapter_context.py last-words draft.md --words 20000
```

**`estimate`:** Suggest a word count target for a chapter given scene type, with the 1.25x inflation already applied. Use this as a quick heuristic and override with the LLM's output if they differ significantly.

```bash
python3 skills/outline-to-chapters/scripts/chapter_context.py estimate --scene-type action
# scene types: action, quiet, establishment, climax, dialogue
python3 skills/outline-to-chapters/scripts/chapter_context.py --help
```

---

## Wiki References

This skill implements the pipeline documented in the writing wiki. Read these notes before modifying any step:

- `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`, the authoritative 13-step reference, design principles, and practical cadence
- `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`, the full 15-slider rubric with 5-point anchors; the character bible structure fed into Steps 2 and 6
- `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md`, the six logic-check categories that inform Steps 8 and 11; the two-step audit-then-implement pattern
- `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`, the voice extraction method that produces the voice spec prerequisite; why generic prose happens
- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`, the constraint rationale for Step 10; the three-method humanization stack
- `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`, the prohibited-words list used as `<prohibited_words>` block in Step 10
- `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`, the category structure and profile format of the worldbuilding sheet used in Steps 3 and 7

---

## Iteration Notes

- The 1.25x inflation in Step 4 is a systematic correction for model undershooting. Do not remove it without testing on real output.
- The word "implement" in Steps 9 and 13 is critical. "Rewrite" instructs the model to start from scratch. "Implement" keeps changes targeted.
- Steps 1-3 are selection tasks, use cheaper, faster models. Steps 5-7, 10, 11, 13 require full-capability models.
- Recommended cadence: generate 2-3 chapters, stop and edit those chapters, update the outline for the next set, then generate. Bulk-generating the whole book in one pass produces a worse draft.
- The the `de-sloppifier` skill skill is a separate pass intended for post-draft cleanup. This pipeline intentionally omits deep line editing.
- On first run, test one chapter end-to-end before committing to a full book run.
