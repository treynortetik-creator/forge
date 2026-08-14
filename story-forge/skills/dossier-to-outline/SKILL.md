---
name: dossier-to-outline
description: "Use when you have a finished story dossier and need to build the three structural production documents: a character bible, a worldbuilding sheet, and a chapter-by-chapter outline. Each document goes through a generate, critique, rewrite cycle. Run after braindump-to-dossier. Triggers on \"build my outline\", \"generate characters and worldbuilding\", \"turn the dossier into an outline\", \"dossier to outline\", or \"run dossier-to-outline\"."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Role

Producer. Takes one dossier and outputs three finished documents: character bible, worldbuilding sheet, chapter outline. Each document is generated once, critiqued against specific criteria, then rewritten with targeted changes only. No document is used downstream until its rewrite cycle is complete.

---

# Dependency Check (REQUIRED FIRST STEP)

Before anything else, confirm the prerequisite exists.

**Required input:** a story dossier produced by the `braindump-to-dossier` skill. The dossier must include at minimum: log line, synopsis, character list with roles, worldbuilding element list, and key outline moments (opening image, inciting incident, midpoint, climax, closing image).

If the dossier is missing or incomplete, STOP here and say:

> "This skill needs a completed story dossier. Build it first by running the `braindump-to-dossier` skill, or supply your existing dossier file."

Do not generate anything without a valid dossier in hand.

Also confirm: book title and any author notes the author wants applied. Ask for both if not supplied. Author notes can be blank.

---

# Process

The three documents are produced in sequence: characters first, then worldbuilding, then outline. The outline depends on both prior documents being finished.

---

## Phase 1: Character Bible

### Step 1.1, Generate

Using the dossier, produce a fleshed-out character bible covering every character needed for this book.

**For each major character, produce all of the following:**

1. Physical description (precise and generatable, not vague flattery)
2. Primary role in the story (protagonist, antagonist, love interest, henchman, etc.)
3. Personality profiles: MBTI, Enneagram, Clifton Strengths
4. Core motivation: the heart's desire driving this character most of the time
5. Background before the story begins
6. A quirk, hobby, or trait that does not fit neatly into the plot but makes the character feel like a real person
7. Dialogue style: how they talk, what they reach for, what they avoid
8. Dialogue samples in four registers: relaxed, stressed, thoughtful, excited. These samples do not have to come from this story; they exist to demonstrate vocal pattern
9. Slider baselines (see `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`): rate each of the 15 behavioral dimensions on a -10 to +10 scale with brief behavioral notes at this character's baseline. Dimensions: Stress/Calm, Fear/Courage, Suspicion/Trust, Callous/Empathic, Impulsivity/Self-Control, Dominance/Submission, Pessimism/Optimism, Introverted/Extroverted, Gut/Logic, Detail-Focused/Big-Picture, Cautious/Risk-Taker, Seriousness/Humor, Deception/Honesty, Stability/Sensitivity, Shame/Self-Worth
10. Character arc: how they begin, what pushes them into the plot, a midpoint moment, a climax moment, how they have changed by the last page

**For each minor character:** 1-2 sentences covering background, core desire, and relationship to the plot.

**Format:**

```
## [BOOK TITLE]

### [MAJOR CHARACTER NAME]
* Physical Description: ...
* Role in Story: ...
* Personality Profiles: ...
* Core Motivation: ...
* Background: ...
* Quirk: ...
* Dialogue Style: ...
* Dialogue Samples: ...
* Slider Baselines: ...
* Character Arc: ...

### Minor Characters
* [NAME]: [1-2 sentences]
```

No preamble, no commentary, nothing outside this format.

Craft note: the slider rubric is fully documented in `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`. The motivation architecture (Ghost/Wound/Lie/Weakness) lives in `${CLAUDE_PLUGIN_ROOT}/references/writing/character-motivation.md`. Every major character's heart's desire must be specific and emotional, not functional.

### Step 1.2, Critique

Read the generated character bible and produce an improvement plan. Critique against these criteria only:

- **Dossier fidelity:** does every character fully match the author's dossier in intent, tone, details, and spirit? Are any characters who appear in the dossier missing or misrepresented?
- **Storytelling best practices:** do the characters fit their narrative roles according to solid story craft? Is each major character distinct enough to carry their role?
- **Heart's desire:** does each major character have a clear, emotionally specific heart's desire? Could any of them be made more moving to a reader? Does the desire have a plausible origin in their background?

Do not rewrite the bible. Output an improvement plan with specific examples of what to change and why.

### Step 1.3, Rewrite

Take the original character bible and the improvement plan. Implement only the suggested changes. Do not alter anything the critique did not flag. Reproduce the entire bible with the changes applied.

No preamble, no commentary.

---

## Phase 2: Worldbuilding Sheet

Run after the character bible rewrite is complete. Use the finished character bible as context.

### Step 2.1, Generate

Using the dossier, produce a fleshed-out worldbuilding sheet covering all settings, systems, factions, and elements needed for this book.

**Organization:** group all elements into categories. Use only the categories that apply to this book. Possible categories (not all will apply):

- High-Level Worldbuilding
- Settings and Locations
- Objects and Artifacts
- Magic Systems and Technology
- Groups and Races
- Gods and Deities
- Geography and Nature
- Population and Politics
- Culture
- History and Lore
- Religion and Beliefs
- Languages

For each element: **classify it, then follow that category's full profile format** from
`${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-categories.md`. Each category has its own
document structure — Hard Rules vs Soft Rules for a magic system, The Truth Behind the Myth for a
deity, Details to Use in Prose for a culture. **3-4 generic sentences per element produces a
glossary, not a world.** Minimum 3-4 sentences per section where the format calls for prose. Write each profile to feel lived in and three-dimensional, not like a stage backdrop. Cover physical reality, emotional resonance, the people or forces connected to it, and its role in the story. See the full category-specific profile format in `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`.

**Format:**

```
## [BOOK TITLE]

### [WORLDBUILDING CATEGORY]
* [ELEMENT NAME]: [3-4 sentences, specific details]
* [ELEMENT NAME]: [3-4 sentences, specific details]

### [NEXT WORLDBUILDING CATEGORY]
* [ELEMENT NAME]: [3-4 sentences, specific details]
```

No preamble, no commentary. Only the categories and elements this story actually needs.

Craft note: every element should serve the story, not just exist for texture. The worldbuilding-scope-creep risk is real: if the dossier over-identifies elements, trim before generating so downstream context stays lean. See `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md` for the full format; see `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-consistency.md` for the iceberg principle and cause-and-effect rules.

### Step 2.2, Critique

Read the generated worldbuilding sheet and produce an improvement plan. Critique against these criteria only:

- **Dossier fidelity:** does this fully match the story dossier in intent, tone, details, and spirit?
- **Storytelling best practices:** do all worldbuilding elements actively serve the story? Is each element interesting in its own right?
- **Category integrity:** do all categories used make sense for this book? Is every element assigned to the correct category?

Do not rewrite the sheet. Output an improvement plan with specific examples.

### Step 2.3, Rewrite

Take the original worldbuilding sheet and the improvement plan. Implement only the suggested changes. Reproduce the entire sheet with the changes applied.

No preamble, no commentary.

---

## Phase 3: Chapter Outline

Run after both the character bible and worldbuilding sheet rewrites are complete. Both documents are active context for this phase.

### Step 3.1, Generate

Using the dossier, finished character bible, finished worldbuilding sheet, and genre conventions, generate a chapter-by-chapter outline for the full book.

Per chapter, produce:

- A summary of approximately 100 words in paragraph form. Use specific details, not vague allusions. Write it as if handing it to a ghostwriter to produce the first draft.
- Viewpoint character (name only)
- Scene sliders (1-10 scale) for each of: Tension, Dread, Emotional Intimacy, Relationship Tension, Pacing Energy, Humor. **Full anchor definitions: `${CLAUDE_PLUGIN_ROOT}/references/writing/scene-sliders.md`. Load it before scoring** — otherwise you are inventing six numbers per chapter against nothing.
- **The chapter contract** — four fields, described below. This is the part that decides whether the
  book is any good, and it is the part every generic outline omits.

The number of chapters should reflect the genre conventions and the scale of the story in the dossier. Follow the story structure the dossier implies (inciting incident, midpoint, climax, closing image all land at appropriate chapter positions).

### 🔴 The chapter contract

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
### Chapter [N]: [Title or working description]
[~100-word paragraph with specific details]

**Viewpoint:** [character name]
**Wants:** [concrete objective this chapter]
**Opposition:** [who or what blocks it, and what THEY want]
**Outcome:** [yes-but | no-and | yes | no]
**Cost:** [what is lost, spent, or foreclosed]
**Sliders:** Tension [X] | Dread [X] | Emotional Intimacy [X] | Relationship Tension [X] | Pacing Energy [X] | Humor [X]
```

No preamble, no commentary.

Craft note: the outline is a blueprint for human review before chapter generation begins. Specific details now prevent drift later. See `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md` for the full system; see `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md` for the six audit categories that run next.

### Step 3.2, Critique

Read the full outline and produce an improvement plan. Critique against these criteria:

**Plot coherence (from `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md`):**
- Premise Logic: does the core premise hold together internally? Are stakes and conflicts consistent with stated world rules?
- Character-World Fit: do characters' roles, goals, and capabilities make sense in this world? Do motivations align with the premise?
- Worldbuilding Coherence: do world elements support the premise without internal contradiction?
- Plot Setup Plausibility: are there logistical impossibilities? Motivation gaps that would stop the story from starting? Is the inciting incident plausible?
- Early-Stage Convenience Flags: does any chapter rely on unlikely coincidence? Do any characters exist purely to solve a plot problem? Are there "because the plot needs it" moments with no in-world logic?

**Emotional arc:**
- Is there enough emotion across the arc? Are there genuine gut-punch moments? Or is this a sequence of events with flat affect?
- Do the slider values match what the chapter summaries actually describe?

**Structural integrity:**
- Does the outline honor the key moments in the dossier (opening image, inciting incident, midpoint, climax, closing image) at appropriate positions?
- Are character arcs from the character bible tracked correctly across chapters?

Do not rewrite the outline. Output an improvement plan with specific examples.

Scratchpad directive: before writing the final critique, systematically work through the full outline and identify all characters, world rules, and established facts. Check each audit category methodically. Note every contradiction or plausibility gap. Final output is the improvement plan only, not the scratchpad.

### Step 3.3, Rewrite

Take the original outline and the improvement plan. Implement only the suggested changes. Reproduce the entire outline with changes applied.

No preamble, no commentary.

---

# Output

Three files delivered on completion:

- `[project-name]-characters.md` (finished character bible)
- `[project-name]-worldbuilding.md` (finished worldbuilding sheet)
- `[project-name]-outline.md` (finished chapter outline with sliders)

Save all three to the project's working directory, or ask where to write them if no project directory has been established.

Flag the outline for human review before proceeding to chapter generation. The outline is the most consequential document: structural problems caught here are cheap to fix; the same problems in a finished draft are expensive.

---

# Quality Rules

These apply across all generation steps in this skill:

- No banned words (see `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`). Feed the list as a `<prohibited_words>` constraint at every generation step.
- No em dashes anywhere in the output. Convert any to commas, periods, or colons.
- No negative parallelism ("not just X, but Y").
- No rule-of-three padding (adjective, adjective, and adjective).
- Emotions must be specific and concrete, not labeled. "Her stomach dropped" is a cliche. Show the behavior, the physical signal, the thought.
- Every major character's heart's desire must be emotionally specific. "She wants to belong" is vague. "She wants the High Priestess to say her name with the same respect she uses for the Order's best students" is specific.
- Worldbuilding elements that do not serve the story are waste. Do not generate them.
- Dialogue samples must demonstrate the character's actual vocal patterns, not just vary their topic.

---

# Iteration Notes

- Slider levels in the outline are working targets; the author should adjust them before running chapter generation.
- After chapter generation begins, loop back and update the outline for the next 2-3 chapters with specifics gathered from chapters already written.
- The character bible is a living document: update slider baselines and arc position notes as the draft reveals things the bible missed.
- The worldbuilding sheet carries forward across a series; only new elements introduced in later books need to be added.
- This skill feeds directly into the `outline-to-chapters` skill (chapter generation pipeline). See `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` for what the pipeline expects from these output documents.
