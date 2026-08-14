---
title: Scene sliders — the six per-chapter dimensions, with anchors
type: reference
tags: [outlining, sliders, pacing, tone]
source: the `Sliders` node of the Outline Generator automation
status: living
---

# Scene sliders

Six dimensions scored per chapter, 1-10. They control **how a chapter should feel**, and they are
consumed downstream by the Character Scene Brief step so tone and pacing are set at generation time
rather than left to the model's discretion.

**Scene sliders are not character sliders.** The 15 character sliders in `character-system.md` describe
*who a person is*. These six describe *how this chapter should land*.

> ⚠️ **`dossier-to-outline` previously demanded these six scores with no rubric anywhere in the
> plugin** — its pointer went to a wiki note that does not ship. Six numbers per chapter were being
> invented against nothing. This file is that rubric, published standalone so both outlining skills can
> reach it.

---

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

---

## A caution that is not in the source

**A slider measures intensity of feeling, not stakes.** A chapter can sit at Tension 9 with nothing
actually at risk — those are different objects. If you want the chapter to *matter*, that lives in the
chapter contract (Wants / Opposition / Outcome / Cost), not here. Score both.
