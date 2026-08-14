---
name: dossier-to-characters
description: "Build the character bible from a story dossier, one character at a time. Extracts the roster, then runs generate, per-character logic check, and rewrite for each individual before moving to the next, then builds an ensemble relationship map across the finished cast. Use after braindump-to-dossier and before outlining. Triggers on character bible, character sheet, flesh out characters, build the cast."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Dossier to Characters

**Why this exists as its own skill.** The source automation loops **one character at a time** —
generate, check, rewrite, append, next. Doing the whole cast in a single pass is not a shortcut, it is
a different and worse operation: fifteen characters competing for attention inside one completion
cannot each carry ten fields, fifteen validated sliders and a five-part arc, and a per-character
checklist applied to a whole document degrades into a vibe check.

**Required input:** a story dossier (from `braindump-to-dossier`).
**Optional:** a character template, genre tropes, author notes.

---

## Step 0: Extract the roster

Read the dossier and produce a flat list of every character it names. **Account for all of them;
invent none.** Confirm the list before proceeding — this is the loop's control variable.

Mark each as **major** or **minor**. Minor characters get 2-3 sentences and stop.

---

## THE LOOP — run Steps 1-3 for EACH character, then append before starting the next

### Step 1: Expand one character

For a **major** character produce: name · role · physical description (precise and generatable, not
vague flattery) · background · personality profile · **heart\'s desire** (specific, not abstract —
"she wants the High Priestess to say her name with respect", not "she wants to belong") · quirk ·
dialogue samples in four registers (relaxed, stressed, thoughtful, excited) · **15 slider baselines**
scored against the anchored rubric in
`${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md` · a five-part character arc.

Two standing constraints from the source, both load-bearing:

> **"Your job is not to produce a happily ever after for each character, it is to be a brutal
> storyteller."**
> **"Do not invent major story information that is not included in the dossier."**

### Step 2: Logic-check that one character

Run this checklist against the single character just produced. **Item 5 is marked CRITICAL in the
source and is the one most often skipped** — the model emits fifteen numbers and nothing ever
validates them.

```
=<character_template>
[supplied]
</character_template>

<slider_rubric>
Below is a 5-point rubric for each slider, mapped to -10, -5, 0, 5, 10. You can interpolate in-between (e.g., -7 as “between -10 and -5”).

Stress / Calm
(negative = stressed, positive = calm)

-10: On the verge of breakdown; panicky, scattered, unable to think straight, body overloaded (shaking, sweating, racing thoughts).

-5: Noticeably tense; snappy, irritable, distractible, overreacts to small problems, catastrophizes internally.

0: Manageably pressured; feels strain but can stay functional, may be curt but keeps perspective.

5: Relaxed and easygoing; handles setbacks with patience, recovers quickly from annoyances.

10: Deeply serene; almost meditative, unflappable even in crises, acts as a stabilizing presence for others.

Fear / Courage
(negative = fearful, positive = courageous)

-10: Frozen by fear; avoids any perceived risk, may lie or betray values just to stay safe.

-5: Anxious and hesitant; needs reassurance, frequently backs down from conflict or danger.

0: Normally cautious; will face necessary risks after some thought, avoids needless danger.

5: Bold; steps up in challenging situations, fear is present but doesn’t dictate choices.

10: Fearless to a fault; confronts danger head-on, may seem reckless or heroic depending on context.

Suspicion / Trust
(negative = suspicious, positive = trusting)

-10: Paranoid; assumes hidden agendas everywhere, rarely believes what others say, sees threats in kindness.

-5: Wary; slow to open up, double-checks information, expects disappointment or manipulation.

0: Cautiously neutral; evaluates on a case-by-case basis, neither especially trusting nor distrustful.

5: Trusting; tends to give people the benefit of the doubt, shares information readily.

10: Naively trusting; easily persuaded or exploited, assumes everyone is fundamentally safe and honest.

Callous / Empathic
(negative = callous, positive = empathic)

-10: Cold and cruel; indifferent to suffering, may enjoy or exploit others’ pain.

-5: Blunt and unsentimental; impatient with emotional displays, prioritizes practicality over feelings.

0: Moderately considerate; recognizes others’ feelings, may not go out of their way to comfort.

5: Warm and understanding; actively tries to see others’ perspectives, offers comfort and support.

10: Deeply empathic; absorbs others’ emotions, self-sacrificing, can be overwhelmed by others’ pain.

Impulsivity / Self-Control
(negative = impulsive, positive = self-controlled)

-10: Completely impulsive; acts on first urge, chronically regretting decisions, chaotic behavior.

-5: Impetuous; often speaks or acts without thinking, but can occasionally rein it in.

0: Mixed; sometimes impulsive, sometimes measured, depends strongly on mood and stakes.

5: Deliberate; typically pauses to think, rarely makes rash decisions, good at delaying gratification.

10: Highly controlled; meticulously plans actions, may overthink or miss opportunities due to caution.

Dominance / Submission
(negative = dominant, positive = submissive)

-10: Overbearing; must lead and control, bulldozes others’ opinions, uses intimidation or pressure.

-5: Assertive and competitive; pushes for their way, dislikes being directed but can follow when necessary.

0: Balanced; can lead or follow, negotiates, comfortable sharing power.

5: Cooperative; prefers to follow a clear leader, avoids taking charge, defers in disagreements.

10: Highly submissive; habitually yields, struggles to assert needs, easily dominated or controlled.

Pessimism / Optimism
(negative = pessimistic, positive = optimistic)

-10: Nihilistic; believes things are hopeless, expects failure or betrayal, sees no point in trying.

-5: Generally pessimistic; anticipates negative outcomes, prepares for the worst, struggles to see silver linings.

0: Realist; sees pros and cons, expectations are moderate, not easily surprised either way.

5: Hopeful; expects things to work out, looks for opportunities, bounces back quickly from setbacks.

10: Rose-colored; insists things will be fine regardless of evidence, may ignore real risks or problems.

Introverted / Extroverted
(negative = introverted, positive = extroverted)

-10: Deeply withdrawn; avoids social contact whenever possible, heavily drained by interaction.

-5: Reserved; keeps to a small circle, needs recovery time after social events, dislikes big groups.

0: Ambiverted; comfortable alone or social, neither strongly drained nor energized by groups.

5: Outgoing; seeks social contact, energized by group activities, enjoys being around people.

10: Highly extroverted; craves constant interaction, uncomfortable alone for long, loves being center of attention.

Gut / Logic
(negative = gut-driven, positive = logic-driven)

-10: Purely instinctive; goes entirely by intuition, hunches, and feelings, rarely analyzes.

-5: Intuition-first; consults feelings and impressions, uses logic only to justify or tweak decisions.

0: Mixed; weighs both gut and rational analysis, shifts depending on context.

5: Analytical; seeks evidence, pros/cons, and clear reasoning before committing.

10: Hyper-rational; distrusts feelings, treats decisions as puzzles, may ignore emotional realities.

Detail Focused / Big-Picture
(negative = detail-focused, positive = big-picture)

-10: Microscopic; obsessively focused on small details, risks losing sight of goals or context.

-5: Detail-attentive; notices inconsistencies, careful with specifics, slower to act because of thoroughness.

0: Balanced; can zoom in or out as needed, not strongly biased either way.

5: Big-picture oriented; focuses on overarching goals and themes, glosses over specifics.

10: Abstract visionary; lives at the level of concepts and long-term arcs, often misses or dismisses concrete details.

Cautious / Risk Taker
(negative = cautious, positive = risk-taking)

-10: Risk-averse; avoids change, refuses gambles even with high potential reward, over-prepares.

-5: Careful; prefers safe, proven paths, takes risks only with strong justification.

0: Moderate; willing to take some risks when necessary but not thrill-seeking.

5: Adventurous; enjoys taking chances, accepts possible losses as part of life.

10: Reckless; chases risk for its own sake, ignores warnings, endangers self and others.

Seriousness / Humor
(negative = serious, positive = humorous)

-10: Grave; rarely jokes, treats most topics solemnly, uncomfortable with levity.

-5: Earnest; prefers meaningful conversations, occasional dry humor but generally straight-faced.

0: Balanced; can be playful or serious depending on context.

5: Lighthearted; frequently jokes, uses humor to connect and ease tension.

10: Constant jokester; nearly everything becomes a bit, may deflect emotions or avoid seriousness entirely.

Deception / Honesty
(negative = deceptive, positive = honest)

-10: Pathological liar; lies reflexively, even when truth is easier, manipulates narratives constantly.

-5: Habitual deceiver; lies when advantageous, omits truths freely, sees honesty as optional.

0: Socially typical; mostly honest but comfortable with white lies and strategic omissions.

5: Principled honest; strongly prefers truth, lies only under serious pressure or moral justification.

10: Radical honesty; almost never lies, blunt even when tact would help, may cause conflict through candor.

Stability / Sensitivity (Ego Fragility)
(negative = stable, positive = sensitive)

-10: Unshakeable; criticism barely registers, strong sense of self, rarely feels insulted or slighted.

-5: Thick-skinned; can handle most criticism and rejection without much emotional turbulence.

0: Typical; stung by harsh critique but recovers, can take feedback when framed well.

5: Sensitive; easily hurt by disapproval or perceived slights, ruminates on criticism.

10: Extremely fragile; small comments feel like attacks, frequent shame spikes, may lash out or withdraw dramatically.

Shame / Self-Worth
(negative = shame, positive = self-worth)

-10: Deep self-loathing; sees self as fundamentally broken or unworthy, expects rejection and failure.

-5: Insecure; frequently doubts worth, downplays successes, easily derailed by mistakes.

0: Mixed; has both strengths and insecurities, self-worth fluctuates with context.

5: Healthy self-regard; recognizes flaws but believes in personal value, recovers from setbacks without collapsing.

10: High self-worth; strongly confident, may edge into arrogance or blind spots about own flaws.
</slider_rubric>

<dossier>
[supplied]
</dossier>

<author_notes>
[supplied]
</author_notes>

## GENERATED CHARACTER PROFILE TO CHECK:
[supplied]

## YOUR CHECKLIST - Flag ANY issues for major characters (minor characters do not need the same level of information):

1. **Dossier Consistency**: Does every element (description, role, motivation, background, quirk, dialogue) align with the character's role in the Dossier? No contradictions with plot position, relationships, or story events?

2. **Author Notes Alignment**: Does the profile honor specific instructions from Author Notes (if any)

3. **Character Template Fit**: Does the profile feel appropriate for the genre and fit the description of this character's role in the Character Template (if any)

4. **Personality Profiles Plausibility**:
   - Myers-Briggs, Enneagram, Clifton Strengths: Do they make sense together? (e.g., no INTJ Enneagram 7w8 unless justified)
   - Do they support the core motivation and role?

5. **Slider Levels VALIDATION** (CRITICAL):
   - **Range**: All sliders between -10 and 10, whole numbers only?
   - **Internal Consistency**: Do slider values align with each other and profile description? (e.g., Extroverted 9 shouldn't have "prefers solitude" quirk)
   - **Rubric Match**: Does the character's description/behavior match the rubric for those slider values? Quote rubric if mismatched.
   - **Dossier Fit**: Do baselines make sense for their story role? (e.g., protagonist unlikely to have baseline Submission 9)

6. **Background & Motivation Logic**:
   - Background explains current traits/motivation without plot holes.
   - Core motivation drives believable actions in the story context.
   - Quirk is genuinely unique/interesting, not generic or contradictory. But also isn't distracting and have the potential to take away from the plot.

7. **Dialogue Style**: Matches personality profiles, sliders, and role.

8. **Character Arc**: Make sure the character arc is logical and consistent, and serves the overall story (especially for the protagonist)

8. **Major vs Minor**: Correct format used based on Dossier prominence? Major characters should have more information, while minor characters should just have 2-3 sentences.

9. **Plausibility**: No logical impossibilities.

## OUTPUT FORMAT:

Output a list of anything you might flag and create an improvement plan on how to improve the character bio. Remember that only major characters should have a lot of info. Minor characters should still only have 2-3 sentences each.
This is a complex task. You are not allowed to perform at a mediocre level. You are performing a rigorous LOGIC CHECK on a generated character profile for either a major or minor character (the major characters will have more information). Your job is to ensure it is **100% consistent, plausible, and logical**, as well as consistent with the Story Dossier, Author Notes, Character Template, etc.
```

Output a change list only. Do not rewrite here.

### Step 3: Rewrite that one character

Implement **only** the flagged changes. Change nothing else. Append the finished character to the
bible, then return to Step 1 for the next one.

---

## Step 4: Relationship map — after the loop drains

Re-read the **assembled** bible and produce a typed relationship map across the whole cast. This step
structurally requires a complete roster, which is why it runs last and why it cannot exist in a
single-pass version of this skill.

```
=<full_character_sheet>
[supplied]
</full_character_sheet>

<dossier>
[supplied]
</dossier>

<instructions>
Given the above list of characters, I want you to create a full relationships map for all of the character enseamble.

Critical Rules:
- ONLY use info from the sheet + dossier + logical inferences (e.g., protagonist-antagonist tension from roles/motivations/sliders). Do NOT invent new plot details.
- Base on: explicit mentions (e.g., "rival to X"), roles (protagonist vs henchman), overlapping motivations/backgrounds, slider contrasts (high dominance vs submission implies tension), story roles.
- Cover ALL characters (majors + minors). Include self-relationships if relevant (e.g., internal conflict).
- Types: friendship, romance, rivalry, family, mentor-mentee, ally, enemy, neutral/colleague, betrayal potential. Use "complex" for mixed.
- Strength: strong (deep bond), moderate, weak/one-sided.
- Direction: bidirectional (mutual) or A→B (one-way, e.g., admiration).

ALSO INCORPORATE:
- Dossier context: [INSERT DOSSIER SUMMARY HERE if available, e.g., [supplied]]
- Genre tropes: [INSERT CONDENSED TROPES HERE, e.g., [supplied]]

OUTPUT ONLY valid JSON array of relationships, e.g.:
[
  {
    "characterA": "Exact Name",
    "characterB": "Exact Name",
    "type": "rivalry",
    "strength": "strong",
    "direction": "bidirectional",
    "evidence": "1-2 sentence justification from sheet (quote sliders/roles/motivations)"
  }
]
</instructions>This is a complex task. You are not allowed to perform at a mediocre level. You are a relationship mapper for a story's character ensemble.
```

**Cover every character, majors and minors.** Infer from slider contrasts — high dominance against
high submission implies tension. **Use only what is in the sheet and dossier; do not invent new plot
details.**

---

## Output

`[project-name]-characters.md` in the project directory: the per-character profiles in roster order,
followed by a `## Relationships Dynamic` section carrying the map.

## Related

`braindump-to-dossier` (produces the input) · `dossier-to-worldbuilding` (run after this, and give it
this bible as context) · `references/writing/character-system.md` (the anchored slider rubric)
