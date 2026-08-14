---
name: full-book
description: "Run the full book pipeline end to end: voice (if needed), braindump-to-dossier, dossier-to-outline, outline-to-chapters."
argument-hint: <project-dir>
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Full Book Pipeline

**Orchestration command.** This command chains four skills in sequence, passing artifacts on disk between them. The individual skills hold the real prompts and craft logic. This layer handles sequencing, dependency gating, and artifact routing only.

**Chain order:** voice (if needed) → braindump-to-dossier → dossier-to-outline → outline-to-chapters

**Project directory:** `$ARGUMENTS` (where dossier, character bible, worldbuilding sheet, outline, and draft files are written). If not supplied, ask for it before proceeding.

---

## Before Starting: Establish the Project Directory

Confirm `$ARGUMENTS` is a valid path. If the directory does not exist, create it with `mkdir -p`. All output files from steps 2, 3, and 4 go here unless a skill's own rules specify otherwise. The voice spec goes to `story-forge/output/` per the voice skill's rules.

---

## Step 1: Voice Spec (Conditional)

**Purpose:** Produce the author voice spec that outline-to-chapters requires in Step 4.

**Dependency check:** Search `story-forge/output/` for any file matching `voice-*.md`. If one exists, confirm with the user which spec to use, then skip to Step 2 with that file path in hand. Do not re-run the voice skill if a valid spec already exists.

**If no voice spec is found:**

> "No voice spec found. The outline-to-chapters skill requires one. Run the voice skill now to build it, or supply the path to an existing spec."

If the user wants to run it now, invoke the **voice** skill. The voice skill will conduct its own dependency check and ask for writing samples if they are not present. Do not bypass that check. When the skill completes, note the output path (`story-forge/output/voice-[name].md`) and carry it into Step 4.

If the user wants to supply an existing spec file, read that path and carry it into Step 4.

Do not proceed past Step 1 without a resolved voice spec path.

---

## Step 2: Braindump to Dossier (Conditional)

**Purpose:** Turn a raw story idea into a structured dossier ready for character development and outlining.

**Dependency check:** Search `$ARGUMENTS` for any file matching `dossier-*.md`. If one exists, confirm with the user whether to use it or rebuild it, then proceed accordingly. If it is used as-is, carry the file path into Step 3 and skip the skill run.

**If no dossier is found:**

Invoke the **braindump-to-dossier** skill. The skill will conduct its own dependency check and ask for the braindump and book title if they are not present. Do not bypass that check.

The skill writes its output to `dossier-[title-slug].md`. When the skill completes, confirm the file was written, note the path, and carry it into Step 3.

Do not proceed to Step 3 without a resolved dossier file path.

---

## Step 3: Dossier to Outline (Conditional)

**Purpose:** Expand the dossier into three production documents: character bible, worldbuilding sheet, and chapter outline.

**Dependency check:** Search `$ARGUMENTS` for all three expected outputs from this stage. The file naming pattern is `[project-name]-characters.md`, `[project-name]-worldbuilding.md`, and `[project-name]-outline.md`. If all three exist, confirm with the user whether to use them or rebuild them.

**If any of the three files are missing:**

Invoke the **dossier-to-outline** skill, passing the dossier file from Step 2 as context. The skill will conduct its own dependency check and confirm the dossier is present and complete before generating anything. Do not bypass that check.

The skill produces three files. When it completes, confirm all three were written, note their paths, and carry all three into Step 4.

Do not proceed to Step 4 without all three file paths resolved.

**Pause for human review here.** The outline is the most consequential artifact in the pipeline. Structural problems caught in the outline are cheap to fix. The same problems in a finished draft are expensive. Prompt the user:

> "Outline, character bible, and worldbuilding sheet are ready. Review the outline at [path] before continuing to chapter generation. Proceed when ready."

Wait for confirmation before advancing to Step 4.

---

## Step 4: Outline to Chapters

**Purpose:** Generate the actual prose, one chapter at a time, running the full 13-step pipeline per chapter.

**Dependency check:** This skill requires four artifacts. Verify all four paths are in hand before invoking:

1. Chapter outline (from Step 3)
2. Character bible (from Step 3)
3. Worldbuilding sheet (from Step 3)
4. Voice spec (from Step 1)

If any are missing, stop here and report which artifact is absent and which skill produces it. Do not invoke outline-to-chapters with incomplete inputs.

**If all four are present:**

Invoke the **outline-to-chapters** skill, providing the paths to all four prerequisite files. The skill will ask which chapters to generate, what tense the book uses, and any author notes for the session. Those questions belong to the skill; answer them as they come.

The skill appends each completed chapter to the draft file. When it completes its run, report to the user: chapters generated, draft file path, and total word count if available via `wc -w`.

---

## Artifact Summary

| Stage | Produced by | File location |
|---|---|---|
| Voice spec | voice | `story-forge/output/voice-[name].md` |
| Story dossier | braindump-to-dossier | `$ARGUMENTS/dossier-[slug].md` |
| Character bible | dossier-to-outline | `$ARGUMENTS/[project]-characters.md` |
| Worldbuilding sheet | dossier-to-outline | `$ARGUMENTS/[project]-worldbuilding.md` |
| Chapter outline | dossier-to-outline | `$ARGUMENTS/[project]-outline.md` |
| Draft chapters | outline-to-chapters | `$ARGUMENTS/[project]-draft.md` (appended per chapter) |

---

## Chain Rules

- Each skill runs its own dependency check. Do not skip or soft-pedal those checks. If a skill stops and asks for input, surface that question to the user and wait.
- Steps are conditional at 2 and 3: if valid artifacts already exist on disk, the user can choose to reuse them and skip the build. Always confirm before reusing.
- Step 4 is never skipped. It is the destination.
- The human review pause at the end of Step 3 is mandatory, not optional.
- Do not chain steps without confirming the prior step's output file was actually written. Use Bash to verify the file exists and is non-empty before advancing.
