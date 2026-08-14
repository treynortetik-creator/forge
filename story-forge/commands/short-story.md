---
name: short-story
description: "Run the full short-story pipeline end to end: voice (if writing samples are provided), then short-story-dossier, then short-story-outline, then short-story-draft, then de-sloppifier, then logic-check. Produces one complete 5,000 to 7,000 word story. Triggers on \"short story pipeline\", \"write a short story\", \"run short-story\", \"full short story\"."
argument-hint: <project-dir>
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Short-Story Pipeline

**Orchestration command.** Chains six skills in sequence, passing artifacts on disk between them. The individual skills hold the craft logic and prompts. This layer handles sequencing, dependency gating, and artifact routing only.

**Chain order:** voice (conditional) → short-story-dossier → short-story-outline → short-story-draft → de-sloppifier → logic-check

**Project directory:** `$ARGUMENTS` (where all output files are written). If not supplied, ask for it before proceeding.

---

## Before Starting: Establish the Project Directory

Confirm `$ARGUMENTS` is a valid path. If the directory does not exist, create it with `mkdir -p`. All output files from steps 2 through 6 go here unless a skill's own rules specify otherwise. The voice spec is written **into the project directory** (`./voice-[name].md`) — that is where the `voice` skill puts it.

---

## Step 1: Voice Spec (Conditional)

**Purpose:** Produce the author voice spec that short-story-draft consumes. Unlike the novel pipeline, this step is optional for short fiction. A story can anchor to the genre and tone stated in the dossier when no spec is available, but the prose quality will be lower.

**Dependency check:** Search **the project directory** (`$ARGUMENTS`) for any file matching `voice-*.md`. If one exists, confirm with the user which spec to use, then skip to Step 2 with that file path in hand. Do not re-run the voice skill if a valid spec already exists.

**If no voice spec is found:**

> "No voice spec found. The short-story-draft skill can run without one, anchoring to the genre and tone in the dossier instead. A voice spec produces substantially better prose. Run the voice skill now to build one, or proceed without it. Your call."

If the user wants to build one, invoke the **voice** skill. It will conduct its own dependency check and ask for writing samples. Do not bypass that check. When it completes, note the output path and carry it into Step 4.

If the user wants to proceed without a voice spec, note "no voice spec" and carry that into Step 4.

---

## Step 2: Short-Story Dossier (Conditional)

**Purpose:** Turn a raw story idea into a compact short-story-scaled dossier.

**Dependency check:** Search `$ARGUMENTS` for any file matching `short-story-dossier-*.md`. If one exists, confirm with the user whether to use it or rebuild it. If used as-is, carry the file path into Step 3 and skip the skill run.

**If no dossier is found:**

Invoke the **short-story-dossier** skill. It will conduct its own dependency check and ask for the braindump and working title if not present. Do not bypass that check.

The skill writes its output to `short-story-dossier-[title-slug].md`. When it completes, confirm the file was written, note the path, and carry it into Step 3.

Do not proceed to Step 3 without a resolved dossier file path.

---

## Step 3: Short-Story Outline (Conditional)

**Purpose:** Map the dossier onto a scene-based outline with opening spec, ending spec, and Chekhov's Gun accounting.

**Dependency check:** Search `$ARGUMENTS` for any file matching `*-scene-outline.md`. If one exists, confirm with the user whether to use it or rebuild it. If used as-is, carry the file path into Step 4 and skip the skill run.

**If no outline is found:**

Invoke the **short-story-outline** skill, passing the dossier file from Step 2 as context. It will conduct its own dependency check.

The skill writes its output to `[title-slug]-scene-outline.md`. When it completes, confirm the file was written, note the path, and carry it into Step 4.

**Pause for human review.** The outline is the cheapest place to catch structural problems. A missed plant, a wrong ending move, or a flat escalation are all easier to fix here than in the draft. Prompt the user:

> "Scene outline is ready. Review [path] before continuing to the draft. Confirm the payload first line, the ending move, and the Chekhov's Gun list. Proceed when ready."

Wait for confirmation before advancing to Step 4.

Do not proceed to Step 4 without a resolved outline file path and the user's confirmation.

---

## Step 4: Short-Story Draft (Conditional)

**Purpose:** Generate the full story prose, scene by scene, targeting 5,000 to 7,000 words.

**Dependency check:** Verify these artifacts are in hand before invoking:

1. Scene outline (from Step 3)
2. Short-story dossier (from Step 2)
3. Voice spec path or "no voice spec" flag (from Step 1)

If a required artifact is missing, stop and report which artifact is absent and which skill produces it.

**If all required artifacts are present:**

Invoke the **short-story-draft** skill, providing the paths to all artifacts. It will ask for the tense. Surface that question to the user and wait; it belongs to the skill.

The skill writes the draft to `[title-slug]-draft.md`. When it completes, confirm the file was written and note the word count.

Do not proceed to Step 5 without a resolved draft file path.

---

## Step 5: De-Sloppifier

**Purpose:** Run the three-pass line edit (pacing, line edits, AI-pattern removal) on the full draft.

Invoke the **de-sloppifier** skill, providing the draft file from Step 4. The skill uses `${CLAUDE_PLUGIN_ROOT}/skills/de-sloppifier/scripts/chunk.py` to split the draft into approximately 1,500-word chunks, runs all three passes per chunk, and reassembles.

When the skill completes, confirm the edited file was written and note the output path. Carry it into Step 6.

Do not proceed to Step 6 without the edited draft.

---

## Step 6: Logic-Check

**Purpose:** Run the continuity and logic audit against the dossier and scene outline as the story bible.

Invoke the **logic-check** skill, providing the edited draft from Step 5 and the dossier plus scene outline as the story bible.

When it completes, report to the user: audit report path, any critical issues flagged, whether a revision pass is recommended before submission.

---

## Artifact Summary

| Stage | Produced by | File location |
|---|---|---|
| Voice spec | voice | `$ARGUMENTS/voice-[name].md` |
| Short-story dossier | short-story-dossier | `$ARGUMENTS/short-story-dossier-[slug].md` |
| Scene outline | short-story-outline | `$ARGUMENTS/[slug]-scene-outline.md` |
| Draft | short-story-draft | `$ARGUMENTS/[slug]-draft.md` |
| Edited draft | de-sloppifier | `$ARGUMENTS/[slug]-draft-deslopped.md` |
| Logic audit | logic-check | `$ARGUMENTS/[slug]-logic-audit.md` |

---

## Chain Rules

- Each skill runs its own dependency check. Do not skip or soft-pedal those checks. If a skill stops and asks for input, surface the question to the user and wait.
- Steps 2, 3, and 4 are conditional: if valid artifacts already exist on disk, the user can choose to reuse them and skip the build. Always confirm before reusing.
- Steps 5 and 6 are not skippable. They are the quality gates.
- The human review pause at the end of Step 3 is mandatory.
- Do not chain steps without confirming the prior step's output file was actually written. Use Bash to verify the file exists and is non-empty before advancing.

---

## How This Differs from the Novel Pipeline

The short-story pipeline replaces the novel's three-stage structural expansion (character bible, worldbuilding sheet, chapter outline) with two lighter stages: the short-story dossier and the scene outline. There is no 13-step per-chapter drafting engine. The draft step is scene-based and governed by compression principles (enter late, leave early, Le Guin's crowd and leap) rather than the selector-and-brief architecture the novel pipeline uses. The total output is one complete 5,000 to 7,000 word story file, not a series of chapter files appended to a draft. The voice spec is optional, not required. The editing and logic-check stages are shared with the novel pipeline, unchanged.
