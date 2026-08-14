---
name: short-story-outline
description: Use when you have a completed short-story dossier and need to map it onto a scene-based outline. Maps Wulf Moon's 8-Point Plot (Character/Setting/Heart's-Desire/Problem/Try/Fail/Climax/Validation) onto 5 to 8 scenes, each tagged with its structural job and a compressed yes-but/no-and try/fail beat. Specifies the opening (payload first line, enter late, promise/contract) and the ending (one of the four ending moves, planted Chekhov's gun paid, surprising-yet-inevitable). Includes a scene budget for 5,000 to 7,000 words. For dark-comedy or crime stories, adds a tonal-control and twist architecture pass. Replaces dossier-to-outline for short fiction.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Short-Story Outline

**Role:** ARCHITECT. One transform: take a short-story dossier and produce a scene-based outline. This replaces the chapter outline for short fiction. No character bible generation. No worldbuilding sheet. The dossier already holds the cast and world at short-form scale. The outline maps the 8-Point Plot onto scenes, then audits and tightens.

**System posture:** Expert short-fiction structural architect. The constraint is the form: 5,000 to 7,000 words, one arc, no subplots. Every scene must earn its word budget. Scenes that do not advance both plot and character simultaneously are waste.

---

## Dependency Check (Required First Step)

Before anything else, confirm the prerequisite exists.

**Required input:** a completed short-story dossier produced by the `short-story-dossier` skill. The dossier must include at minimum: the stated effect, the irreversible change, the protagonist's heart's desire and magic sword, the cast with moral-function slots, the POV character, and the target word band.

If the dossier is missing or incomplete, stop and say:

> "This skill needs a completed short-story dossier. Build it first by running the `short-story-dossier` skill, or supply your existing dossier file."

Do not generate anything without a valid dossier in hand.

Also confirm: working title and any author notes for this session. Ask for both if not supplied. Author notes can be blank.

---

## Step 1: Map the 8-Point Plot to Scenes

**Goal:** Translate Wulf Moon's 8-Point Plot onto 5 to 8 scenes calibrated for the target word band. Each scene gets a structural label, a plain description of what happens, a word-budget target, and its try/fail beat.

**The 8-Point Plot (from the Wulf Moon method):**
1. Character in Setting, Heart's Desire established
2. Problem: the inciting incident that threatens the heart's desire
3. Try: the protagonist acts
4. Fail: escalating; each failure costs something and raises the stakes
5. Try again: the stakes are higher; the protagonist is forced deeper in
6. Fail again (or: success at a cost that creates a worse problem)
7. Climax: the protagonist deploys the magic sword; the highest-stakes attempt
8. Validation or Denouement

Not every beat maps to a distinct scene. In short form, beats 3 and 4 may share a scene; beats 5 and 6 may share a scene. What matters is that every beat is present somewhere in the outline.

**Scene format.** For each scene, produce:

```
### Scene [N]: [Structural Label]
**Job:** [one sentence: what this scene must accomplish structurally]
**What happens:** [2 to 4 sentences, specific, using character names and concrete actions]
**Try/Fail beat:** [yes-but / no-and / "setup" for Scene 1 / "validation" for the final scene]
**Word budget:** [target word count for this scene]
**Magic sword note:** [if applicable: is the sword planted, developed, or deployed here?]
```

**Constraints:**

- Total scene word budgets must sum to the target word band. A story targeting 6,000 words cannot have seven scenes at 1,000 words each.
- No scene under 400 words (too compressed for a full try/fail beat) and no scene over 1,400 words (overextended scenes collapse short-fiction pacing).
- Scene 1 establishes character, setting, and heart's desire within the opening three paragraphs. The magic sword is planted or its absence is noted here.
- The climax scene is the only scene where the protagonist achieves a real win or a definitive loss. Every prior scene ends in yes-but or no-and only.
- Every failure costs the protagonist something meaningful and raises the stakes for the next attempt. Flat escalation (try, fail at the same pitch, try again) collapses the middle. Per the Wulf Moon method: THINGS GET WORSE.
- The magic sword deploys at the climax. If the sword as defined in the dossier cannot be the climax mechanism, note the gap here and propose a revision.

**Word-band reference:** for a 5,000 to 7,000 word story, the typical distribution is one setup scene (600 to 800 words), two to three try/fail scenes (700 to 1,000 words each), one climax scene (800 to 1,200 words), one validation scene (400 to 600 words). The exact count depends on how many try/fail cycles the premise requires. One full try/fail cycle before the climax is the minimum. Two is common. Three risks the length band.

**For dark-comedy and crime stories:** note at each scene how both the comic and the dark register operate simultaneously. Flag any scene where only one register is active. The goal is the fused register at every beat, not alternating between comic and dark scenes. Per [[dark-comedy-crime-craft]]: each scene performs both jobs at once (the Coen Rule applied to scene architecture).

---

## Step 2: Specify the Opening

**Goal:** Design the opening beat in concrete detail. The opening is a binding contract on voice, register, genre, and the promise to the reader. Get it wrong here and the draft will get it wrong.

Produce all of the following:

**Payload first line.** Write the actual opening line of the story. It must simultaneously deliver voice, the genre signal, and the story's central tension or character position. Apply the enter-late principle from [[short-story-form]]: enter mid-consequence, not mid-routine. No waking up, no weather, no mirror. Reference [[short-story-openings-and-endings]] for what a payload first line does and what it does not do.

**First-paragraph orientation.** Three to five sentences describing what the first paragraph establishes after the opening line: where and when, who this is, what pressure is already active. Per Walker Percy's coma-patient principle: orient the reader on all three axes (who, where, when) within the first paragraph, through scene and implication, not explanation.

**The opening contract.** One sentence. What does this opening promise the reader about tone, genre, and the emotional experience to come? For dark-comedy-crime: the comic register is the register the opening establishes. The darkness arrives into an already-established comic frame.

**Heart's desire placement.** Identify the exact sentence or beat in the opening where the protagonist's heart's desire becomes clear to the reader. Per the Wulf Moon method: the heart's desire appears on the first page or it is not present.

---

## Step 3: Specify the Ending

**Goal:** Design the ending before the draft stage. The opening is the contract; the ending pays it. Choose one ending move and design the closing scene around it.

**Select one ending move (from [[short-story-openings-and-endings]]):**

1. **Recollection and meditation.** The character reflects on before and after. The ending opens outward in time and implication.
2. **Suspended symbolic action.** The story ends on an unresolved gesture, an image held rather than a conclusion delivered. The reader carries the image forward.
3. **Rhyming action.** An earlier image or action returns in transformed form. The recognition is retroactive.
4. **Surprise memory.** An unexpected memory surfaces at the crisis moment, reframing the character's arc.

State the chosen move and explain in two to three sentences how it pays the opening contract.

**The last line.** Write the actual last line of the story. Per Cynthia Ozick: unrepeatable in any other position in the story. Brevity is not optional.

**The Chekhov's Gun accounting.** List every plant that must pay off by the ending, with its corresponding payoff scene. This is the structural unity check: every planted element is a promise, and the compressed form means every plant must discharge. Any plant without a payoff is a cut.

**The surprising-yet-inevitable test.** For each plant and its payoff: does the payoff recolor the scene where the plant appeared? If yes, the ending is earning its surprise. If the payoff only adds a fact without changing the meaning of what came before, it is a gimmick. Flag any payoff that fails this test and revise.

**For dark-comedy and crime stories:** add the ironic ending architecture check.

Identify the ironic ending mode:
- **Dahl mode (moral order enforced):** the deserving get theirs; the punishment rhymes with the sin; the incident-irony formula (character does X so Y inverts X) applies.
- **Coen/Highsmith mode (indifferent or absent moral order):** the guilty may walk; comeuppance is structural, not guaranteed.

Name the moral witness (from the dossier's cast) and identify their final line or beat. The moral witness legitimizes the ending's verdict. Without them, the ironic ending is a gimmick.

Run the retroreading test: after the reveal, does every earlier scene change meaning? If removing the twist leaves a coherent but duller story, the twist is not yet constitutive. Revise until it is.

---

## Step 4: Outline Critique

**Goal:** Audit the scene map, opening spec, and ending spec for structural problems. Produce an improvement plan only. Do not rewrite.

Provide the dossier, the full outline, and the critique criteria. Context before instructions.

**Critique criteria:**

- **Effect coherence.** Does every scene serve the stated single effect from the dossier? Flag any scene that pulls in a different emotional direction.
- **Escalation logic.** Does each failure cost the protagonist something meaningful and raise the stakes for the next attempt? Flat escalation is a structural failure.
- **Magic sword arc.** Is the sword planted in Scene 1 (or clearly absent and expected)? Is there at least one development beat before the climax? Does the climax deploy it?
- **Word budget realism.** Do the scene budgets sum to the target word band? Does any single scene carry more than 25% of the total word count? If yes, split it or cut it.
- **Opening contract integrity.** Does the payload first line do all its jobs? Is the heart's desire on the first page? Does the tonal register match the story's genre lane?
- **Ending accountability.** Do all plants from the Chekhov's Gun list pay off? Does the ending move pay the opening contract?
- **For dark-comedy and crime:** does every scene hold both registers simultaneously? Is the ironic ending mode identified and the moral witness positioned?

For each issue: name the scene or section, describe the problem specifically, give a concrete suggestion. Do not rewrite the outline. Produce the improvement plan only.

---

## Step 5: Outline Rewrite

**Goal:** Implement the critique plan. Apply only the flagged changes.

The word "implement" is deliberate. Do not say "rewrite the outline incorporating the suggestions." Implement the specified changes. Reproduce the entire outline with changes made.

---

## Output

Write the final scene outline to `[title-slug]-scene-outline.md` in the project working directory.

The outline file must contain: the full scene map, the opening spec (payload first line, first-paragraph orientation, opening contract, heart's desire placement), the ending spec (ending move, last line, Chekhov's Gun list, retroreading test results).

Report to the user:
- Number of scenes and total word budget
- The payload first line (confirm the contract is right)
- The chosen ending move
- Output file path
- Next step: "Run `short-story-draft` to produce the scene-by-scene draft."

**Pause for human review.** Prompt the user:

> "Scene outline is ready. Review [path] before continuing to the draft. Confirm the payload first line, the ending move, and the Chekhov's Gun list. Proceed when ready."

Wait for confirmation before advancing.

---

## Quality Rules

These apply across all generation in this skill:

- No em dashes in any output. Convert any to commas, colons, or periods.
- No negative parallelism.
- No rule-of-three padding.
- The payload first line is actual prose, not a description of what the line will do. Write the line.
- The last line is actual prose, not a description of what the line will do. Write the line.
- Scene "what happens" descriptions are specific: character names, concrete actions, no vague allusions.
- No banned words (see `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`). Feed the list as a `<prohibited_words>` constraint at every generation step.

---

## Craft References

- the Wulf Moon method: the 8-Point Plot (Step 1), the heart's desire on the first page (Step 2), the magic sword arc (Steps 1 and 3), the escalation principle (THINGS GET WORSE, the escalation engine)
- [[short-story-form]]: the compressed try/fail cycle mechanics, enter late and leave early, the scene budget constraints, the unity-of-effect governing principle
- [[short-story-openings-and-endings]]: the four ending moves (Step 3), the payload first line and opening contract (Step 2), the surprising-yet-inevitable test, the Chekhov's Gun accounting
- [[dark-comedy-crime-craft]]: the fused-register requirement, the Coen Rule for scene architecture, the two ironic ending modes (Dahl vs. Coen/Highsmith), the moral witness, the retroreading test for the crime twist
- [[information-control-and-foreshadowing]]: the Chekhov's Gun mechanism; the misdirection-vs-withholding distinction for fair-play twists
- [[chapter-hooks]]: the yes-but/no-and cycle mechanics behind the try/fail beat tagging

---

## Iteration Notes (Living Skill)

After each run, log patterns in `CHANGELOG.md` in this directory:

- Any scene where the word budget and the try/fail beat were in tension: if the beat required more space than the budget allowed, note how the conflict was resolved.
- Any magic sword that could not be planted in Scene 1 without disrupting the enter-late principle: note the structural tension and the solution.
- Any ending where the retroreading test failed on the first attempt: note what was wrong and what fixed it.
- Any dark-comedy story where a scene held only one register in the critique: note what the fusing solution was.
- Any em-dash or banned-word slip in the outline: the skill must model what the pipeline teaches.
