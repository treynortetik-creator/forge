---
title: "Chapter Generation Pipeline (Jason Hamilton / Story Hacker)"
type: concept
tags: [writing, ai-writing, n8n, automation, chapter-generation, story-hacker]
created: 2026-06-27
updated: 2026-06-27
source: "https://www.youtube.com/watch?v=BDPfyuVuHfk (primary), https://www.youtube.com/watch?v=obVNsO5XptA (advanced version), https://www.youtube.com/watch?v=y2yam3wlTjE (simple version)"
status: living
---

# Chapter Generation Pipeline (Jason Hamilton / Story Hacker)

The backbone of Jason's n8n book-writing system. The final automation in a five-automation chain. It takes the completed `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md` output (outline + character sheet + worldbuilding sheet) and generates each chapter of the novel through a 13-step per-chapter loop. The 13 steps below run in order for every chapter.

See also: `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`, **story hacker prompts**, de-sloppifier's Pass 3 list, **ai fiction workflows**, **ai prompting for fiction**, **json super prompts**, **claude build**, **jason structure extraction**, **storyhacker pipeline architecture**

---

## Pre-Loop: Find Chapters

**What it does:** Parses the outline into a JSON array of chapter titles, establishing what the loop iterates over.

**Input:** Full outline doc + a form specifying which chapters to generate (e.g., "chapters 4 through 6" or "all").

**Prompt structure:** "You are a parser given the above book outline text return a JSON array named `chapters` containing each chapter title exactly as it appears, one element per title, including those without numbers like prologue or epilogue. Make sure the chapter numbers are also present where listed. Do not include any additional keys. Only output valid JSON." A second instruction narrows to the user's requested range.

**Also collected before the loop begins:**
- Prose style sheet (can be your own extracted style or a genre-template style)
- Full character sheet, full worldbuilding sheet, full outline
- Tense (manually specified so it stays consistent across chapters — avoids the automation deciding chapter-by-chapter whether to use first or third person)
- Last 2,000 words of existing draft (empty on chapter 1; used for continuity in all subsequent chapters)

---

## Step 1: Plot Selector

**What it does:** Extracts only the plot information for the current chapter from the full outline — verbatim.

**Input:** Full outline, current chapter name.

**Prompt logic:** "Your task is to look at the outline and extract verbatim all of the information for this chapter. Which includes the summary of the plot, the POV, the levels, and the sliders. Reproduce that text exactly as it exists in the outline. Do not include any other chapters, just the current chapter."

**Why not just pass the whole outline to later steps:** Keeps the subsequent prompts focused. Avoids "watering down" the context with irrelevant chapters. Uses cheap/fast models for this step because it's a selection task, not a reasoning task.

---

## Step 2: Character Selector

**What it does:** Extracts only the character profiles needed for this chapter. Full profile for active characters, a 1-2 sentence summary for mentioned or indirectly linked characters.

**Input:** Current chapter plot (from Step 1), full character sheet.

**Prompt logic:** "This task is all about selecting the exact characters that are actively in this chapter or mentioned. First, carefully examine the plot of the chapter and determine which characters are actively participating in the scene or chapter and which other characters might be mentioned or indirectly linked to the scene or chapter, even if not physically present. For each of the characters who are actively in the scene, reproduce the entire profile verbatim. For mentioned or indirectly linked characters, provide a one to two sentence summary only."

**Why this matters:** A large cast with full profiles overwhelms the context. Selecting only relevant characters and using cheap models for the selection keeps cost low and attention high.

---

## Step 3: Worldbuilding Selector

**What it does:** Same logic as Character Selector but for worldbuilding elements — extracts only what is relevant to this specific chapter.

**Input:** Current chapter plot, full worldbuilding sheet.

**Prompt logic:** Mirrors the character selector. Identifies which locations, objects, magic systems, groups, etc. are active in the scene and outputs only those.

---

## Step 4: Wordcount Estimator

**What it does:** Picks an appropriate target word count for the chapter, then bumps it by 25%.

**Input:** Current chapter plot, full outline (for pacing context).

**Prompt logic:** "Your task is to analyze the genre, analyze the events of the chapter, and choose an appropriate word count based on the events in the chapter, the standard for the genre, and the pacing of the scene. The word count should never go lower than 1,000 words and never higher than 5,000 words. Output just the number of words and nothing else."

**The 25% bump:** AI reliably undershoots word count targets. A separate step multiplies the output by 1.25 before passing it downstream. The inflated number is the actual target given to the draft step.

**Rationale for variable word count:** Climax chapters often run shorter and faster (high pacing energy); establishment or emotional chapters run longer. Locking all chapters at the same word count kills natural rhythm.

---

## Step 5: Plot Scene Brief

**What it does:** Writes a detailed narrative blueprint of the chapter's plot — what happens beat by beat, from what POV, at what word count, including a cliffhanger plan.

**Input:** Selected plot (Step 1), selected characters (Step 2), selected worldbuilding (Step 3), adjusted word count (Step 4), last 2,000 words of existing draft, full outline.

**Prompt logic:** "Given the above outline, characters, worldbuilding information, your task is to flesh out a plot scene brief for this chapter." Includes:
- Chapter label (verbatim from outline, no renaming)
- Plot verbatim from the selected plot section
- POV character and tense (pulled from form input)
- Word count target (verbatim number from Step 4)
- Beats and blocking — a more detailed breakdown of what happens
- Continuity check — the plot must pick up naturally after the last chapter's final line
- Cliffhanger — includes a rubric for what makes a good versus a cheap cliffhanger

---

## Step 6: Character Scene Brief

**What it does:** Produces character-level information specifically as it applies to THIS scene — not the character's overall profile, but who they are at this exact moment.

**Input:** Full outline, selected characters (Step 2), selected plot (Step 1), last 2,000 words of existing draft, slider rubric (see **story hacker prompts**).

**Key behaviors:**
- **Removes future details.** A character sheet contains events and revelations from the whole book. If the scene is chapter 3, the brief strips out anything that happens in chapters 10+. Critical for mystery/thriller where revealing a murderer's identity in the character brief would leak it into the prose.
- **Adjusts sliders for the scene.** Characters have baseline slider levels (stress, courage, trust, etc.) but those shift per scene. If a character is normally calm but this is a combat scene, their stress slider moves. The brief establishes where each active character sits on each slider for this specific scene.
- **Scene-specific physical details.** What are they wearing right now? Have they been in a fight? Are they wet, dirty, formal? Things that differ from their baseline appearance.

---

## Step 7: Worldbuilding Scene Brief

**What it does:** Same logic as Character Scene Brief but for worldbuilding elements. Cleans the worldbuilding of any future details and frames each element as it exists in this moment of the story.

**Input:** Selected worldbuilding (Step 3), current chapter plot, full outline.

**Key behavior:** Ensures the worldbuilding brief contains no spoilers or information that the POV character could not yet know. Standardized formatting per element category (see `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md` for the category list and profile format).

---

## Step 8: Chronology Check (Scene Brief)

**What it does:** Checks the outputs of Steps 5, 6, and 7 against each other and against the full outline for chronological and logical consistency.

**Input:** All three scene briefs combined, full outline.

**Prompt logic:** Flags any inconsistencies — does the brief's timeline contradict earlier chapters? Does the character's emotional state in Step 6 conflict with where they left off in the previous chapter? Does the worldbuilding in Step 7 introduce something that should not exist yet?

**Output:** A list of flagged issues plus an improvement plan.

---

## Step 9: Scene Brief Rewrite

**What it does:** Merges the three separate scene briefs (plot, character, worldbuilding) into a single unified scene brief, incorporating the corrections flagged by the Chronology Check.

**Input:** Outputs from Steps 5, 6, 7, and 8.

**Output:** One coherent document — the full scene brief — that the First Draft step reads from. This is a cheap model task: it is implementing a plan, not inventing.

**Note:** Jason reports this review-before-draft step is one he often skips manually in the simple (non-n8n) version. In the automated pipeline, this step runs automatically and he does not review it before the First Draft runs. He finds the outline quality determines the quality of this step — a solid outline means the beat-and-blocking output from the brief is reliable.

---

## Step 10: First Draft

**What it does:** Writes the actual chapter prose.

**Input:** Prose style sheet, last 2,000 words of existing draft (for continuity), full scene brief (Step 9).

**Prompt logic:** "Your task is to write the entire [chapter name] based on the scene brief and to cover it thoroughly from deep point of view writing the scene as if written by bestselling novelist and not rushing through the scene." Additional instructions:
- Use the tense specified in the form (from the pre-loop step)
- Note the POV character specified in the scene brief
- Hits the word count target from Step 4 (the 25%-inflated number)
- Deep POV, show-don't-tell, active voice, no adverbs, no de-sloppifier's Pass 3 list
- Dialogue carries action — no "he said/she said" tags
- Sentence rhythm: mix short punchy lines with longer ones
- Stop at the scene's conclusion — no self-added foreshadowing beyond the brief

---

## Step 11: Chronology Check 2 (Post-Draft)

**What it does:** A second chronology check, this time on the actual prose — not the brief. Looks at the last 20,000 words of the draft plus the newly written chapter.

**Why 20,000 words:** Wants a broad backward view (roughly 5-8 chapters depending on chapter length), without overloading the context. If fewer than 20,000 words exist, uses whatever exists.

**What it catches:** Repeat introductions of abilities or information already established earlier ("he discovered he had this power" written twice), timeline contradictions, continuity gaps between chapters. This is the single biggest automated quality intervention in the pipeline.

---

## Step 12: Style Check

**What it does:** Reads the chapter against the prose style sheet and makes recommendations for improvements.

**Input:** Prose style sheet, newly written chapter from Step 10.

**Output:** A list of specific suggestions — where the prose diverges from the style guide, what to change to bring it closer.

**Rationale:** The First Draft step already reads the style sheet, but the style check treats it as a separate audit pass. Jason notes this is where the biggest improvement happens over vanilla LLM output — giving the model an explicit style sheet and then having it evaluate against that sheet (rather than just "write in this style") materially improves adherence.

---

## Step 13: Rewrite

**What it does:** Incorporates the feedback from both Step 11 (Chronology Check 2) and Step 12 (Style Check) into a final version of the chapter, then appends it to the draft document.

**Input:** Original draft from Step 10, chronology check output (Step 11), style check output (Step 12).

**Prompt logic:** "Implement the suggested changes. Do not change anything else about the original chapter. Reproduce the entire chapter with the suggested changes made." The word "implement" is intentional — "rewrite" triggers the model to start from scratch rather than make targeted edits.

**Output:** The final version of the chapter, appended to the draft document. The loop then advances to the next chapter.

---

## Practical Cadence (1-Hour-Per-Day Workflow)

Do not run the full book in one pass. Running the automation 2-3 chapters at a time, then stopping to edit, produces a better draft than bulk-generating. Jason's recommended cadence (source: BDPfyuVuHfk):

1. Review and edit chapters N and N+1
2. Update the outline for chapters N+2 and N+3 (add specifics while in the flow)
3. Launch the automation for chapters N+2 and N+3
4. Stop for the day — the next day's chapters are already generating

This means the majority of active time (the editing and outline refinement) happens in parallel with the generation, and the session starts each day with chapters already waiting.

---

## Key Design Principles

- **Selectors before briefs before draft.** Never dump the full character sheet or worldbuilding doc into the draft step. Select first, then brief, then draft.
- **Two chronology checks, not one.** One on the brief (before writing), one on the prose (after writing). Different failure modes.
- **Cheap models for selection/parsing tasks.** Gemini Flash (or equivalent) handles Plot Selector, Character Selector, Worldbuilding Selector, and Wordcount Estimator. Reserve expensive models (Claude Opus, Gemini Pro) for First Draft and the Rewrites.
- **The 25% word count inflation** is a systematic correction for the model's tendency to undershoot. Build it in, don't fight it manually each time.
- **No line editing in this automation.** The pipeline intentionally omits deep line editing (anti-AI-slop passes). Jason treats that as a separate automation and/or manual pass. The **story hacker prompts** doc has the two-step improvement plan for line editing.
- **This pipeline uses rolling context by design.** The selector + 2K/20K rolling window approach was built for models under 200K tokens. With a 1M-context model, the full manuscript can be held in context — not for generation (cost/speed), but for post-draft consistency audits and developmental editing passes. See **long context novel writing** for when to switch strategies.
