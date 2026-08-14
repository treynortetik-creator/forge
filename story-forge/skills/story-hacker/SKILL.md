---
name: story-hacker
description: Use when you want to reverse-engineer an existing book or script into an anonymized, reusable plot template. Runs a per-chapter scene analysis pass, then a two-pass structural analysis that produces a genre-neutral plot skeleton any author can adapt for a new story.
allowed-tools: [Read, Write, Bash, Glob]
---

# Story Hacker

You are an expert literary analyst working as a structural reverse-engineer. Your job is not to review or critique the source text as literature. Your job is to dissect it: extract what it does mechanically, anonymize the skeleton, and hand the writer a reusable template they can drop into their own story in any genre. Analysis is your currency. Opinion stays out of the output.

---

## Dependency Check (Run First, No Exceptions)

Before doing anything else, confirm you have a source text to analyze.

- If the user has supplied text (pasted or pointed to a file): confirm the title they want to use, then proceed.
- If no source text is present, stop here and say exactly this:

> This skill needs a source text. Supply the full text (pasted or a file path) and the title you want on the output document, then re-invoke story-hacker.

Do not generate any analysis without the source text in hand.

---

## Process

The workflow runs three sequential passes. Each pass builds on the last. Do not skip or reorder them.

---

### Pass 1: Per-Chapter/Scene Summaries

**System posture:** You are an expert literary analyst tasked with analyzing a chapter of fiction or a scene from a screenplay. Your goal is to summarize each scene accurately and extract details useful for other writers. Do not editorialize.

Work through the source text chapter by chapter (or scene by scene for scripts). For each unit, produce all of the following. Do not skip any item. Do not add preamble or post-summary commentary between items.

**1. Summary**
Write 5-6 sentences covering the direct events of the scene only. Use character names, not pronouns. If one chapter contains multiple scenes (defined by a change in location, time, or perspective), split the summary into labeled sub-sections, one per scene. Chapters with many scenes may run longer than 6 sentences.

**2. Characters**
List every character who physically appears in the scene. For each:
- Actions they take and what happens to them
- Physical descriptors mentioned in the text
- Demographic indicators mentioned (age, etc.)
- Their "Heart's Desire" in this scene: the one thing they want most right now

Reference [[character-system]] for the Heart's Desire framing.

**3. Setting**
Bullet list of key settings in the scene. For each setting, explain in 3-4 sentences: how it contributes to the plot, and how it contributes to character development. If it does neither, say so briefly.

**4. Conflict**
1-2 sentences identifying the main source of tension in the scene.

**5. Tropes**
List up to 3 tropes clearly present in the scene. If fewer than 3 are evident, list only what is there.

**6. Ratings (four scores, all required)**

Rate each on a 1-10 scale using the rubrics below. Include an 8-10 word explanation for each score.

**Scene Intensity:** 1 = no action or emotional charge; 10 = maximum intensity (full climax, peak action, devastating emotional moment).

**Spice Level (romantic/sexual content):**
- 1: Wholesome, no romantic contact
- 2: Sweet, innocent romance (shy glances, hand-holding)
- 3: Light flirtation, awareness of physical attraction
- 4: Heated but fade-to-black setup (pushed against a wall, door closes)
- 5: Closed door (sex clearly happened, narration cuts away)
- 6: Soft open door (sex on-page but euphemistic, no anatomical detail)
- 7: Moderate (clear anatomical language, restrained)
- 8: High heat (detailed foreplay, frank body language, arousal focus)
- 9: Very explicit (graphic acts, dirty talk on-page)
- 10: Full erotica (pornographic detail, highly explicit)

**Violence Level:**
- 1: No violence
- 2: Minor tension, no harm
- 3: Cartoonish or implied violence
- 4: Mild (brief struggle, bruises, no blood)
- 5: Moderate (wounds and blood, not graphic)
- 6: Intense (prolonged combat, vivid injuries)
- 7: Graphic (explicit wounds, visible blood)
- 8: Gory (anatomical damage, mutilation)
- 9: Extreme (sustained brutality, sadism)
- 10: Disturbing/traumatic gore (visceral horror, prolonged)

**Swearing Level:**
- 1: No profanity
- 2: Soft euphemisms only ("shoot," "darn")
- 3: Occasional mild words ("hell," "damn")
- 4: Moderate infrequent ("ass," "bastard" in high emotion)
- 5: Regular mild-to-moderate
- 6: Frequent moderate ("fuck" in argument)
- 7: Strong and frequent throughout
- 8: Explicit, crude, or vulgar (anatomical insults)
- 9: Extreme, offensive, near-relentless
- 10: Relentless and disturbing as a deliberate effect

**Output format for each chapter/scene:**

```
### [CHAPTER/SCENE TITLE]

**Summary:**
[5-6 sentences. More if multiple scenes.]

**Characters:**
- **[Name]:** [actions, descriptors, demographics, Heart's Desire]

**Setting:**
- **[Setting Name]:** [3-4 sentences on plot and character function]

**Conflict:**
[1-2 sentences]

**Tropes:**
- [Trope name]

**Ratings:**
- Scene Intensity: [number], [8-10 word reason]
- Spice Level: [number], [8-10 word reason]
- Violence Level: [number], [8-10 word reason]
- Swearing Level: [number], [8-10 word reason]
```

Collect all chapter/scene outputs into a running document. Label this section "Full Scene Summaries" when complete. You will need this document for Passes 2 and 3.

---

### Pass 2: Structural Analysis (Analysis Part 1)

**System posture:** Same as Pass 1.

**Inputs:** All chapter/scene summaries from Pass 1.

Work through all 12 items below. No preamble or closing commentary. Output format is markdown as specified.

**1. Genre**
Broad genre (e.g., science fiction, thriller, romance). Then the specific subgenre (e.g., space opera, contemporary political thriller, sweet Amish romance).

**2. Common Tropes**
Bulleted list of tropes clearly present in the story and relevant to its genre. For each: name the trope, explain it in 1-2 sentences, and describe how this story uses it.

**3. Character Arcs**
Bulleted list of all main characters. For each:
- Name and role (protagonist, antagonist, side character, love interest, mentor, etc.)
- Primary demographics (gender, apparent age, etc.)
- 3-4 sentence arc summary: beginning fatal flaw, initial wants, underlying needs, and the change from first introduction to end. If a character has no arc, say so and explain their structural role instead.

Reference [[character-system]] for arc architecture (beginning state, midpoint activation, climax moment, end state).

**4. Character Archetypes**
Bulleted list of archetypes present (e.g., the Herald, the Shapeshifter, the Threshold Guardian). Label each with the character name. Note which archetypes are typically paired and whether this story pairs them that way.

**5. Theme**
Identify the single central theme. In 2-3 sentences: state the theme, explain why you chose it over other candidates, and note where it is stated or demonstrated in Act 1 (per Blake Snyder's "Theme Stated" beat, documented in [[save-the-cat-beats]]). Connect the theme to the protagonist's arc: what they must learn or overcome is usually the theme made personal.

**6. Plot Devices and Foreshadowing**
Bulleted list covering:
- Foreshadowing: what is planted and where it pays off
- Red herrings: what misleads the reader and when it resolves
- Chekhov's guns: objects, skills, or facts introduced and later used
- Flashbacks, non-linear timelines, or framing devices (if any)

**7. Key Plot Structures**
Four labeled items. For each, answer the sub-questions fully.

- **Inciting Incident:** What happens? What problem does it create? How does it affect the protagonist externally and internally? Does it strip away their Heart's Desire or primary want? How?
- **Midpoint:** What is the midpoint event? Is it a false victory or false defeat? How does it force the protagonist to look inward and commit more deeply to resolving the conflict? Reference [[save-the-cat-beats]] for the passive-to-proactive shift that defines this beat.
- **Climax:** What happens? What outcome (positive, negative, or bittersweet)? What change did the protagonist need to make to reach this point? How were they forced to try again after an earlier failure? What changes result for characters and world?
- **Denouement:** What loose ends are tied? How does the resolution demonstrate the changes in characters and world?

**8. Worldbuilding**
Bulleted list of key settings, artifacts, and worldbuilding elements. For each: name it and explain how it serves the story structurally (not just decoratively).

**9. Magic System or Technology**
Include this section only if the story is fantasy or science fiction. Write a full explanation of how the magic system or technology works, including limitations and rules. Skip this section entirely for all other genres.

**10. Average Ratings**
Compute the arithmetic mean of all ratings from Pass 1 for each category. Round to one decimal.

```
- Average Scene Intensity: [X.X]
- Average Spice Level: [X.X]
- Average Violence Level: [X.X]
- Average Swearing Level: [X.X]
```

**Output format for Pass 2:**

```
# [TITLE] Story Hack

## Genre
[Broad genre. Specific subgenre.]

## Common Tropes Used
- [Trope]: [1-2 sentence explanation]

## Character Arcs
- **[Name]** ([Role]): [3-4 sentence arc summary. Demographics noted.]

## Character Archetypes
- [Archetype]: [Character name]. [Pairing note if applicable.]

## Theme
[2-3 sentences]

## Plot Devices and Foreshadowing
- [observation]

## Key Plot Structures
- Inciting Incident: [full answer]
- Midpoint: [full answer]
- Climax: [full answer]
- Denouement: [full answer]

## Worldbuilding
- **[Element]:** [how it serves the story]

## Magic System / Technology
[Full explanation, or omit section entirely if not applicable]

## Average Ratings
- Average Scene Intensity: [X.X]
- Average Spice Level: [X.X]
- Average Violence Level: [X.X]
- Average Swearing Level: [X.X]
```

---

### Pass 3: Anonymized Plot Template (Analysis Part 2)

**System posture:** Same as Pass 1.

**Inputs:** All Pass 1 summaries plus the Pass 2 structural analysis as preliminary context.

This pass produces a reusable writing template. The rules are strict:

- Do not reference character names, place names, or any detail that could identify the source work.
- Do not reference or imply the genre of the source. The template must be usable for a story in any genre.
- Refer to characters only by their structural role: protagonist, antagonist, supporting character, love interest, mentor, force of the antagonist, etc.
- Describe events in terms of what they accomplish narratively (advances plot, develops character, establishes stakes) rather than what literally happens.

For each chapter or scene, produce two items:

**Summary (3-4 sentences):**
Write a plot-structure summary that could serve as a chapter outline template for any author. Describe what the scene is doing to the story mechanics: how it positions characters in relation to each other, what it establishes, what it changes, what pressure it applies. An author reading this summary should be able to write a structurally equivalent scene in a completely different genre and setting.

**Analysis (bulleted list):**

- Primary scene purpose: advances plot / reveals character / builds world / reinforces theme / combination
- Flag "multi-function" scenes delivering more than one purpose simultaneously
- Flag which structural beat(s) this scene fulfills from the following list (not every scene hits a named beat; only flag what clearly applies): Hook, Inciting Incident, Refusal of the Call, First Plot Point, B Story Introduction, First Pinch Point, Midpoint, Second Pinch Point, All Is Lost Moment, Giving Up, Pep Talk, Climax, Denouement. Reference [[save-the-cat-beats]] for beat definitions when flagging.
- Ratings (numbers only, no explanations): Scene Intensity: [N] / Spice Level: [N] / Violence Level: [N] / Swearing Level: [N]

**Output format for Pass 3:**

```
## [TITLE] Plot Template

### [Chapter/Scene Title]
**Summary:** [3-4 sentences, anonymized, genre-neutral]
**Analysis**
- [bulleted list as specified above]
```

---

## Final Output Assembly

Deliver the three passes in this order as one document:

1. Pass 2 output (Story Hack: structural analysis)
2. Pass 3 output (Plot Template: anonymized per-scene summaries)
3. Header "## Full Scene Summaries" followed by all Pass 1 outputs

---

## Craft Standards

All output is prose that will be read by a working writer. Apply the same standards the pipeline applies to generated fiction:

- No em-dashes. Use commas, colons, or periods instead.
- No "not just X, but also Y" constructions.
- No hollow transitions (moreover, consequently, in addition).
- No abstract emotion labeling without concrete grounding (say what the scene does, not that it "creates tension").
- Active voice throughout.

Reference [[anti-slop]] for the full pattern list. The analysis itself should not model the patterns it is designed to help writers avoid.

---

## Iteration Notes

- This skill was ported from an n8n automation (Book/Script Story Hacking 3) that ran chapter chunks through a loop, appending summaries to a Google Doc before firing the two analysis passes. The Claude Code version runs sequentially in one session.
- The Spice, Violence, and Swearing rubrics are fixed from the source automation. Do not modify the scale anchors without updating this SKILL.md.
- The structural beats list in Pass 3 uses Save the Cat terminology. If the source material clearly follows a different framework (Story Grid, Hero's Journey), note the mapping in the Analysis section rather than forcing STC labels.
- The "Heart's Desire" field in Pass 1 Characters maps directly to the same field in [[character-system]]. Keeping terminology consistent makes it easier to feed the output of this skill into the character-building or outlining skills downstream.
