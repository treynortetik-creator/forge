---
name: outline-generator
description: Use when you have a story dossier, character sheet, and worldbuilding sheet and need a full chapter-by-chapter advanced outline with a 6-dimension emotional audit, per-chapter sliders (Tension, Dread, Emotional Intimacy, Relationship Tension, Pacing Energy, Humor), and a logic check before handing off to the chapter-generation pipeline.
allowed-tools: [Read, Write, Edit, Glob]
---

# Outline Generator

**Role:** PRODUCER. You build the chapter-by-chapter blueprint the chapter-generation pipeline runs from.

You are an expert developmental editor who thinks structurally and emotionally at the same time. You do not pad, flatten, or vague-ify. You build a tight, honest map of the story so the author can approve it before a single draft word is written.

This skill is step 4 in the five-automation chain documented in the writing wiki (`${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md`). It depends on the dossier (step 1), character sheet (step 2), and worldbuilding sheet (step 3).

---

## Dependency Check (Run First, Before Anything Else)

Confirm all prerequisite files are present. If anything is missing, STOP completely and report it.

**Required inputs:**

1. **Story dossier** (produced by the `braindump-to-dossier` skill)
2. **Character sheet** (produced by the `dossier-to-outline` skill)
3. **Worldbuilding sheet** (also produced by the `dossier-to-outline` skill)
4. **Plot template (OPTIONAL):** a chapter-by-chapter structural template for the genre, if you have
one. Without it, work from built-in genre knowledge and say so — a template makes the beats
genre-correct, it is not required to produce an outline. Each chapter in the template specifies narrative purpose, structural beats, spice level, violence level, and swearing level.

**Optional inputs:**

- Tropes doc (list of genre tropes)
- Themes doc (thematic guidelines for the genre)
- Author notes (any specific direction from the author not captured in the dossier)

**If the dossier, character sheet or worldbuilding sheet is missing, STOP. Report plainly:**

> "This skill needs [missing item]. Build it first by running `dossier-to-outline`, or provide the
> file directly."

**A missing plot template is NOT a stop — but it IS a degradation, and you must handle it explicitly.**

🔴 The template is consumed by four of the source automation's seven agents and is the **exclusive**
source of three things. Without it, reassign each one and say so in the output:

| Supplied by the template | With no template |
|---|---|
| **Chapter count** | Derive from the dossier's scope and genre convention. **State the number and your reasoning.** |
| **Per-chapter Spice / Violence / Swearing levels** | **Ask the author to declare them once**, then apply consistently. Do not invent per chapter. |
| **Structural beats** | Fall back to built-in genre knowledge |

⚠️ **And neutralise the checks that depend on it:** skip "Plot Template Consistency" in the Step 6
logic check, and do not validate the three ratings against a document that does not exist. Silently
validating invented numbers against a missing template is worse than not checking.

List each missing item separately. Do not proceed with any steps below until all four required inputs are confirmed.

If all inputs are present, confirm it briefly and proceed.

---

## System Posture (All Steps)

Apply this framing to every step: "This is a complex task. You are not allowed to perform at a mediocre level. You are an expert developmental editor and plot assistant."

---

## Step 1: Condense Genre Tropes (Skip If No Tropes Doc)

**Purpose:** Reduce the tropes doc to a token-efficient one-sentence-per-trope reference.

**Prompt:**

```
Given the above list of tropes for this genre, condense this information to one sentence per trope:

-[Trope Name]: [1 sentence explaining the trope]
-[Next Trope Name]: [1 sentence explaining the trope]

Continue for each trope.
```

If no tropes doc was provided, skip this step and proceed to Step 2 without tropes.

---

## Step 2: Write the Initial Outline

**Inputs:** Condensed tropes (or none), themes doc (or none), plot template, dossier, character sheet, worldbuilding sheet, author notes.

**Prompt:**

```
Using the above worldbuilding, characters, dossier, plot template, themes, and tropes, generate a simple outline for this book. Make sure to use the plot template to inform you on the kind of things that should happen in the chapters you are outlining.

The summary for each chapter should be ONLY 2-3 sentences per chapter. The goal is not to flesh out every detail, but to get a general blueprint for the story as a whole. The outline should have the same number of chapters found in the plot template.

For each chapter, mention who the viewpoint character is. For first-person genres, all chapters will have the same viewpoint character. Do not mention whether the chapter is first person, third person, or the tense. Just name the viewpoint character.

Additionally, for each chapter, include the Spice Level, Violence Level, and Swearing Level found in the plot template. These must match exactly what is in the plot template for each chapter. The 2-3 sentence description must be consistent with these ratings (if Violence Level is 1, do not describe an epic battle).

Format each chapter using this exact Markdown structure:

## [Chapter Number]:
[2-3 sentence summary of what happens in this chapter]
* **Viewpoint Character (POV):** [name only]
* **Spice Level:** [X]/10, [1 sentence about what this looks like]
* **Violence Level:** [X]/10, [1 sentence about what this looks like]
* **Swearing Level:** [X]/10, [1 sentence about what this looks like]

Continue for all chapters. Include no preamble, commentary, or anything beyond what was asked for above.
```

---

## Step 3: Emotional Check (6-Dimension Audit)

**Purpose:** Audit whether the outline has been earned emotionally, not just plotted. Stay in the emotional lane. Do not comment on plot logic, pacing for narrative momentum, or structural symmetry unless they directly cause an emotional problem.

**Prompt:**

```
Read the outline carefully, then audit it across these six dimensions:

---

1. EMOTIONAL SETUP vs. PAYOFF
For every major emotional beat (a death, a betrayal, a confession, a reunion, a sacrifice), trace backward through the outline. Ask: has the story earned this feeling? Flag any beat where the payoff arrives before the reader has had enough time, scenes, or intimacy with the people involved to actually feel it. Identify what is missing and where it should be added.

---

2. CHARACTER GRIEF AND LOSS
When a character dies, is injured, or disappears, does the narrative stop long enough for both the protagonist and the reader to grieve? Flag any death or loss treated primarily as a plot mechanism rather than an emotional event. Note if a character's absence after death feels inconsistent with how much they mattered while alive.

---

3. CLIMAX READINESS
The climax should feel like the only possible ending, the one the whole story was building toward. Evaluate whether the protagonist's climactic action emerges naturally from who they are and what they have experienced, or whether it feels like a plot convenience. Ask: if you removed every chapter before the climax, would the climax still make emotional sense? If yes, the earlier chapters are not doing enough emotional work.

---

4. RELATIONSHIP ARCS
Trace every significant relationship (friendship, rivalry, romance, mentor/student, antagonist). For each one, ask: does it change? Does it earn its final state? Flag any relationship that begins and ends in roughly the same emotional place without a clear reason why, and any relationship that makes a dramatic shift (reconciliation, betrayal, love) without sufficient scenes to support the transition.

---

5. TONAL WHIPLASH
Identify any place where the emotional register shifts too abruptly: comedy immediately after tragedy, lightness immediately before a death, resolution that arrives before the reader has processed the preceding darkness. Flag scenes that undercut emotional weight the story has been accumulating, even if they are well-written in isolation.

---

6. THE PROTAGONIST'S INTERIOR ARC
Separate from the plot arc (what happens) and the goal arc (what they are trying to solve), trace the protagonist's interior arc: what do they believe about themselves or the world at the start, and how has that changed by the end? Flag if the interior arc is absent, if it resolves too easily, or if the protagonist's final emotional state does not feel connected to what they actually went through.

---

For each flag you raise, provide:
- The specific chapter or beat where the problem occurs
- What the reader is likely to feel instead of what the story intends
- One concrete suggestion for what could be added, moved, or expanded to close the gap
```

---

## Step 4: Rewrite 1 (Implement Emotional Check)

**Purpose:** Apply the Step 3 findings to the outline. The analysis is done; this step only implements it.

**Prompt:**

```
Using the text of the original outline and the improvement plan, implement the suggestions in the improvement plan. Only implement the suggested changes and do not change anything else about the outline. Reproduce the entire outline with the same formatting as the original, but with the suggested changes made.
```

---

## Step 5: Add Per-Chapter Sliders

> The same rubric is also published standalone at
> `${CLAUDE_PLUGIN_ROOT}/references/writing/scene-sliders.md` so `dossier-to-outline` can reach it.

**Purpose:** Score every chapter across six scene-level dimensions. These numbers feed the chapter-generation pipeline (specifically the Character Scene Brief step) so tone and pacing are controlled at generation rather than left to the model's discretion. Scene sliders are distinct from character personality sliders: character sliders track who a person is; scene sliders control how the chapter should feel.

**Prompt:**

```
Analyze the outline above and the plot template, then determine the slider levels for each chapter using the rubric below.

Reproduce the text of each chapter verbatim but add the sliders beneath each chapter. Format each chapter like this:

## [Chapter Number]:
[2-3 sentence summary, copied verbatim from the outline]
* **Viewpoint Character (POV):** [copied verbatim]
* **Spice Level:** [copied verbatim]
* **Violence Level:** [copied verbatim]
* **Swearing Level:** [copied verbatim]
* **Tension (Present) Slider:** [NUMBER]/10, [one sentence explanation of what this number means for this chapter]
* **Dread (Anticipated) Slider:** [NUMBER]/10, [one sentence explanation]
* **Emotional Intimacy Slider:** [NUMBER]/10, [one sentence explanation]
* **Relationship Tension Slider:** [NUMBER]/10, [one sentence explanation]
* **Pacing Energy Slider:** [NUMBER]/10, [one sentence explanation]
* **Humor Slider:** [NUMBER]/10, [one sentence explanation]

Only output what was asked for above. No preamble or commentary.
```

**Slider Rubric**

Anchors at 1, 3, 5, 7, 10. Interpolate for values in between (e.g., 4 sits between 3 and 5).

### Tension (Present)
Measures immediate, in-the-moment threat, danger, or conflict. Not what the reader fears is coming: what is happening right now.

- **1:** Complete stillness. No conflict, no threat, no friction. The scene exists purely for atmosphere, reflection, or world-building.
- **3:** Mild friction. A low-stakes disagreement, a minor obstacle, a background unease that does not demand resolution.
- **5:** Moderate pressure. Something is at stake but the outcome feels uncertain rather than urgent. The reader is engaged but not gripping anything.
- **7:** Clear and present danger. The protagonist is actively threatened (physically, emotionally, professionally, or socially) and the outcome of the scene is genuinely in doubt.
- **10:** Maximum immediate threat. Life, identity, or everything the protagonist has worked toward is on the line right now, in this scene, with no guaranteed escape.

### Dread (Anticipated)
Measures the reader's sense of what is coming: not present danger but the shadow of future danger. A scene can have low Tension and high Dread simultaneously.

- **1:** No shadow. The reader has no reason to fear what comes next. The future feels open, safe, or unwritten.
- **3:** Faint unease. Something feels slightly off, a detail is wrong, but the reader cannot name what they are worried about yet.
- **5:** Mild anticipation. The reader senses something is building but is not bracing yet. Curiosity more than fear.
- **7:** Clear foreboding. The reader knows or strongly suspects something bad is coming and is already dreading the moment it arrives.
- **10:** Inevitable doom. The reader is almost certain something devastating is about to happen and cannot look away. The scene is unbearable in the best possible way.

### Emotional Intimacy
Measures how close the reader feels to the interior world of the viewpoint character: their thoughts, feelings, fears, and self-perception. This is not about intimacy between characters; it is about the reader's access to the person whose head they are inside.

- **1:** Completely exterior. The viewpoint character is a camera lens. Only action and dialogue, with no access to inner life.
- **3:** Occasional interiority. Brief glimpses of thought or feeling, but the scene stays mostly on the surface. The reader observes more than inhabits.
- **5:** Moderate access. The reader knows what the viewpoint character is thinking in broad strokes but does not feel the full texture of their emotional experience.
- **7:** Strong interiority. The reader is genuinely inside the viewpoint character's head. Doubts, contradictions, and emotional responses are visible and specific.
- **10:** Full immersion. The reader experiences the scene almost as the character, with complete access to vulnerability, self-deception, fear, desire, and interior contradiction. The character's inner life is the scene.

### Relationship Tension
Measures the unresolved charge between two significant characters in the scene: romantic, adversarial, or otherwise. Tracks the "will they / won't they" quality of any relationship that has not reached its final state.

- **1:** Fully resolved. The relationship has reached its resting state. No charge, no unfinished business, no question mark.
- **3:** Settled but not closed. Comfortable and functional, with only faint echoes of former tension.
- **5:** Neutral coexistence. The characters interact without significant charge. The relationship exists but is not doing active narrative work in this scene.
- **7:** Noticeable charge. Something unspoken is present between these characters. The reader is aware of what has not been said or done, even if the characters are not fully acknowledging it.
- **10:** Maximum unresolved charge. Every word and action between these characters is loaded. The reader is acutely aware of the gap between what is happening and what could happen, and feels the strain of it.

### Pacing Energy
Measures the velocity and momentum of the scene: how fast it burns, how quickly the reader moves through it, and how much forward pressure it generates. Distinct from Tension; a slow scene can be tense, and a fast scene can be low-stakes.

- **1:** Deliberately still. Ruminative, expansive, unhurried. The scene asks the reader to sit inside a moment rather than move through it. Reflection, grief, and interiority often live here.
- **3:** Measured pace. The scene moves at a walking tempo. Information lands steadily but without urgency.
- **5:** Moderate momentum. The scene has a clear direction and moves purposefully, neither rushing nor lingering.
- **7:** Elevated momentum. The scene moves quickly with short exchanges, active decisions, and forward pressure. The reader is pulled rather than led.
- **10:** Maximum velocity. The scene burns. Short sentences, rapid decisions, no pause for reflection, events overtaking each other. The reader cannot stop.

### Humor
Measures the presence and weight of humor, lightness, or comic energy in the scene. Every point on this scale is appropriate in the right context.

- **1:** Completely humorless. The scene is grave, somber, or tragic. Any attempt at lightness would be a tonal violation.
- **3:** Earnest and straight-faced. No jokes, no banter, no comic energy. The scene may be warm or human but is not playful.
- **5:** Tonally neutral. Neither comedic nor somber. Humor could arrive without jarring but is not present or expected.
- **7:** Noticeably light. Banter, wit, irony, or comic observation is present and doing real work: releasing tension, revealing character, or deepening a relationship through shared humor.
- **10:** Fully comedic. The scene operates primarily as comedy. Humor is the point, and the scene would collapse without it. May exist as pure relief, or may use comedy to carry something the story could not say any other way.

---

## Step 6: Logic Check

**System posture:** "You are performing a rigorous LOGIC CHECK on a generated novel outline. Your job is to ensure it is 100% consistent, plausible, and logical, as well as consistent with the story dossier, author notes, plot template, character sheet, and worldbuilding sheet. You are not allowed to be mediocre."

**Purpose:** Catch contradictions, logic failures, premature reveals, and slider inconsistencies before they get buried in prose. Output is an improvement plan only; do not rewrite in this step.

See `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md` for the craft theory behind what "coherent" means and why this check catches what it catches.

**Checklist:**

1. **Dossier/Characters/Worldbuilding Consistency:** Does every element align with the dossier, character sheet, and worldbuilding documents? No contradictions with story events, character roles, or worldbuilding elements?

2. **Plot Template Consistency:** Is the outline aligned with the plot template? Does it follow the template structure and still feel like a natural plot, not forced?

3. **Internal Logic and Consistency:**
   - Does the flow of events hold up under scrutiny?
   - Are there logical contradictions within the outline itself?
   - Does the plot feel forced, or does it flow naturally?

4. **Plausibility and Cause/Effect:**
   - Do the social, political, economic, or physical consequences of events make sense?
   - Does history flow logically from cause to effect, or do events happen because the plot needs them to?

5. **Thematic Resonance:**
   - Does this plot reflect or reinforce the story's central themes?
   - Could it serve as a lens through which characters explore the story's core questions?
   - Does it feel intentional, or like it was added for color without deeper purpose?

6. **Jumping the Gun:**
   - Does this plot reveal details about a character or situation in early chapters that should not be revealed until later?
   - Does any foreshadowing feel forced?
   - Are any twists too obvious given what was revealed previously?

7. **Ratings and Slider Consistency:**
   - Are the spice, violence, and swearing levels consistent with the genre and what is in the plot template?
   - Are all six sliders present for every chapter: Tension (Present), Dread (Anticipated), Emotional Intimacy, Relationship Tension, Pacing Energy, Humor?
   - Are the slider values and explanations appropriate for what the 2-3 sentence summary actually describes?

**Output format:** A list of flagged issues with an improvement plan for each. Keep corrections targeted; do not ask for chapter descriptions longer than 2-3 sentences. Request corrections only, not expansions.

---

## Step 7: Rewrite 2 (Implement Logic Check): Final Outline

**Purpose:** Apply the Step 6 findings. Cheap model task. This step produces the finished outline.

**Prompt:**

```
Using the text of the original outline and the improvement plan, implement the suggestions in the improvement plan. Only implement the suggested changes and do not change anything else. Reproduce the entire outline with the same formatting as the original, but with the suggested changes made.

The formatting for each chapter should look like this:

## [Chapter Number]:
[2-3 sentence summary, with appropriate modifications if the improvement plan requires them, otherwise copied verbatim]
* **Viewpoint Character (POV):** [copied verbatim unless otherwise specified in the improvement plan]
* **Spice Level:** [copied verbatim unless otherwise specified]
* **Violence Level:** [copied verbatim unless otherwise specified]
* **Swearing Level:** [copied verbatim unless otherwise specified]
* **Tension (Present) Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
* **Dread (Anticipated) Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
* **Emotional Intimacy Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
* **Relationship Tension Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
* **Pacing Energy Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
* **Humor Slider:** [NUMBER]/10, [copied verbatim unless otherwise specified]
```

After Rewrite 2 is complete, write the final outline to a file in the project folder (e.g., `drafts/[project-name]-Outline-v1-[YYYY-MM-DD].md`) with this structure:

```
# Outline Overview

[Brief narrative summary of the full story arc: opening state, midpoint shift, climax, resolution. 3-5 sentences.]

# Full Outline

[The complete chapter-by-chapter outline from Rewrite 2]
```

---

## Human Review Note

Before running the chapter-generation pipeline, review the outline. This is the most human-intensive point in the pipeline. Things worth doing:

- Check every chapter for alignment with your vision
- Adjust slider levels where the model's read diverges from your intent
- Expand the 2-3 sentence summaries for chapters you have strong opinions about before passing them to the chapter writer
- As you generate chapters later, return to the next 2 chapters in this outline and add specifics before triggering each batch

See `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md` for the full rationale for why human review happens here rather than later in the pipeline.

---

## Craft References

Read these when working, not as reference only:

- `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md`: the five-automation chain this skill belongs to; full rationale and design decisions for each step
- `${CLAUDE_PLUGIN_ROOT}/references/writing/plot-coherence.md`: the six logic-check categories and the craft theory behind what a coherent plot actually requires
- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`: slop patterns that emerge even at the outline-summary level; apply the banned-words constraint to summary text if it reads generic
- `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`: the hard prohibited-words list; feed as a constraint block at Step 2 if outline prose is reading like AI output
- `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`: relevant if the author has an established voice that should carry through even the short 2-3 sentence summaries
- `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md`: character slider baselines feed into the Emotional Check and Logic Check; know what behavior is "in character" before flagging inconsistencies

---

## Iteration Notes (Living Skill)

After each outline session, log:

- Any emotional-check dimension that missed important beats not covered by the 6-dimension audit
- Any logic-check category that generated false positives (flagging intentional choices as errors)
- Any slider anchor description that proved ambiguous in practice
- Any step where the model resisted implementing plan changes accurately

Track changes in a `CHANGELOG.md` in this directory. Promote recurring gaps to the audit criteria above if confirmed across two or more sessions.
