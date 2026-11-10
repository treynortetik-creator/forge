---
name: dossier-to-outline
description: "Orchestrator: turns a finished story dossier into the full novel story bible by calling dossier-to-characters, then dossier-to-worldbuilding, then outline-generator, and adds a chapter-contract pass (wants, opposition, outcome, cost) to the outline. Run after braindump-to-dossier. Triggers on \"dossier to outline\", \"run dossier-to-outline\", \"turn the dossier into an outline\", or \"build the whole story bible\"."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill]
---

# Role

Producer. Takes one dossier and gets three finished documents built: character bible, worldbuilding
sheet, chapter outline. It writes none of them itself. Each is built by its dedicated skill, which
carries the real prompts, critique criteria and rewrite loops. This layer handles order, artifact
routing, the chapter contract, and the human-review gate.

If the user asks for only one of the three documents, send them to that skill directly:
`dossier-to-characters`, `dossier-to-worldbuilding` or `outline-generator`.

---

# Dependency Check (REQUIRED FIRST STEP)

**Required input:** a story dossier produced by the `braindump-to-dossier` skill. The dossier must
include at minimum: log line, synopsis, character list with roles, worldbuilding element list, and key
outline moments (opening image, inciting incident, midpoint, climax, closing image).

If the dossier is missing or incomplete, STOP here and say:

> "This skill needs a completed story dossier. Build it first by running the `braindump-to-dossier` skill, or supply your existing dossier file."

Also confirm: book title, project directory, and any author notes. Ask for anything not supplied.
Author notes can be blank. Ask once whether the author has a plot template, tropes doc or themes doc;
they are optional inputs to `outline-generator`.

**Resume rule:** if `[project-name]-characters.md` or `[project-name]-worldbuilding.md` already exists
in the project directory, ask whether to reuse it or rebuild it before running its step.

---

# Process

Run the three skills in this order. Each one depends on the documents before it. Do not start a step
until the previous file is written and confirmed on disk.

## Step 1: Character bible

Invoke the **dossier-to-characters** skill with the dossier and author notes. It builds the bible one
character at a time with a per-character logic check, then a relationship map.

**Output:** `[project-name]-characters.md`. Confirm it exists before continuing.

## Step 2: Worldbuilding sheet

Invoke the **dossier-to-worldbuilding** skill with the dossier **and the finished character bible**
as context. It builds the sheet one element at a time and re-reads the growing sheet so later elements
stay consistent with earlier ones.

**Output:** `[project-name]-worldbuilding.md`. Confirm it exists before continuing.

## Step 3: Chapter outline

Invoke the **outline-generator** skill with the dossier, character bible, worldbuilding sheet, author
notes, and any plot template, tropes or themes doc the author supplied. It carries the 6-dimension
emotional audit, the anchored scene sliders, and the outline logic check.

When it finishes, save its final outline as `[project-name]-outline.md` in the project directory (it
may propose a `drafts/` filename; this pipeline expects the name above).

## Step 4: Chapter contract pass

`outline-generator` scores how each chapter feels. It does not record what is at stake. Add the
contract below to every chapter of `[project-name]-outline.md`, changing nothing else in the outline.

### 🔴 The chapter contract (this skill's own pass)

**The sliders measure how a chapter FEELS. They do not measure whether anything is at stake.** A
chapter can sit at Tension 9 with nothing to lose. Those are different objects, and an outline that
records only the first one produces prose that is eventful and boring — the characteristic failure of
machine-written fiction, and one no line edit can repair afterwards.

So every chapter also carries:

- **Wants:** what the viewpoint character is trying to get *in this chapter*. Concrete and actionable,
  not a state of mind. "Get Reyes to sign the release" — not "feel less guilty."
- **Opposition:** what stands in the way. Name it. A person with their own goal is strongest; weather
  and bad luck are weakest.
- **Outcome:** exactly one of **yes-but**, **no-and**, **yes**, or **no**.
- **Cost:** what the viewpoint character loses, spends, or forecloses. Time, an ally, a lie that now
  has to be maintained, an option that is gone.

**The two hard rules, backported from the short-story track where they already work:**

1. 🔴 **Only the climax may resolve `yes` or `no`.** Every other chapter ends `yes-but` or `no-and`.
   A plain `yes` before the climax releases the tension you spent chapters building.
2. 🔴 **Every `Cost` field must be non-empty, and no two consecutive chapters may cost the same thing.**
   Flat escalation — try, fail at the same pitch, try again — is what collapses a middle. If you cannot
   name the cost, the chapter has no disaster in it and should be merged with its neighbour.

**Audit the finished outline before you hand it on:** count the `yes`/`no` outcomes (should be exactly
one, at the climax), and read the Cost column top to bottom on its own. If that column reads as a
story of escalating loss, the middle will hold. If it reads as a list of minor inconveniences, the
book sags and no amount of drafting skill will save it.

**Format:**

```
#### Chapter [N]: [Title or working description]
[~100-word paragraph with specific details]

**Viewpoint:** [character name]
**Wants:** [concrete objective this chapter]
**Opposition:** [who or what blocks it, and what THEY want]
**Outcome:** [yes-but | no-and | yes | no]
**Cost:** [what is lost, spent, or foreclosed]
**Sliders:** Tension [X] | Dread [X] | Emotional Intimacy [X] | Relationship Tension [X] | Pacing Energy [X] | Humor [X]
```

---

# Output

Three files in the project directory:

- `[project-name]-characters.md` (from `dossier-to-characters`)
- `[project-name]-worldbuilding.md` (from `dossier-to-worldbuilding`)
- `[project-name]-outline.md` (from `outline-generator`, plus the chapter contract)

Flag the outline for human review before chapter generation. The outline is the most consequential
document: structural problems caught here are cheap to fix; the same problems in a finished draft are
expensive.

---

# Iteration Notes

- Slider levels in the outline are working targets; the author should adjust them before running chapter generation.
- After chapter generation begins, loop back and update the outline for the next 2-3 chapters with specifics gathered from chapters already written.
- The character bible is a living document: update slider baselines and arc position notes as the draft reveals things the bible missed.
- These three files feed the `outline-to-chapters` skill. See `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` for what it expects.
