---
title: Character System — Consistency and Depth Across a Book
type: concept
tags: [writing, ai-writing, characters, character-bible, n8n, automation]
created: 2026-06-27
updated: 2026-06-27
source: YouTube — https://www.youtube.com/watch?v=f7g9smAe-xY "Fix AI Character Consistency with THIS Exact System" + https://www.youtube.com/watch?v=YEEbZSwun_w "This AI System Writes Better Characters Than 99% Authors" (Jason Hamilton / The Nerdy Novelist)
status: living
---

# Character System

The core problem: AI models have no loyalty to your characters. Every generation is a fresh guess based on whatever you gave it. A better prompt helps a little; it doesn't hold across 300 pages. What holds is a system built once and used every time.

## The Character Bible (Character Sheet)

A character bible is a structured written document covering every dimension an AI needs to stay consistent. It is separate from the story dossier — the dossier lists characters briefly, the bible fleshes each one out.

Core fields for a major character:
- Physical description (precise and generatable — not "beautiful," but "fierce but kind, sharp features, military bearing")
- Primary role in the story (protagonist, antagonist, love interest, henchman, etc.)
- Personality profiles: MBTI, Enneagram, Clifton Strengths
- Core motivation (heart's desire driving them through the whole book)
- Background before the story begins
- A quirk that does not directly serve the plot — this is what makes the character feel like a person rather than a function
- Dialogue style and example lines in multiple emotional registers (relaxed, stressed, thoughtful, excited)
- Slider levels (see below)
- Character arc (how they begin, midpoint moment, climax moment, how they have changed by the end)

Minor characters get 2–3 sentences: background, core desire, relationship to the plot.

## The Slider Rubric

Fifteen behavioral dimensions scored from -10 to +10 with behavioral anchors at each pole. These are baselines — they shift during scenes depending on tension.

| Slider | Negative (-10) | Positive (+10) |
|--------|---------------|----------------|
| Stress/Calm | Panicky, scattered | Unflappable |
| Fear/Courage | Frozen by fear | Reckless |
| Suspicion/Trust | Paranoid | Naively trusting |
| Callous/Empathic | Cold, cruel | Absorbs others' pain |
| Impulsivity/Self-Control | Acts on first urge | Meticulously plans |
| Dominance/Submission | Overbearing | Habitually yields |
| Pessimism/Optimism | Nihilistic | Rose-colored |
| Introverted/Extroverted | Deeply withdrawn | Craves constant interaction |
| Gut/Logic | Purely instinctive | Hyper-rational |
| Detail Focused/Big Picture | Obsessively microscopic | Abstract visionary |
| Cautious/Risk Taker | Risk-averse | Reckless gambler |
| Seriousness/Humor | Grave | Constant jokester |
| Deception/Honesty | Pathological liar | Radical honesty |
| Stability/Sensitivity | Unshakeable | Extremely fragile |
| Shame/Self-Worth | Deep self-loathing | Bordering on arrogance |

The slider rubric lives inside the [[story-hacker-prompts]] as part of the Advanced Character Prompt. When scenes vary in tension, reference whether a character is at baseline, above, or below — this drives behavior without having to re-specify it each time.

## The Character Generation Automation (n8n)

Jason Hamilton's n8n automation loops through all characters in the story dossier and produces a full bible for each. The process:

**Inputs:** story dossier, genre tropes (condensed to one sentence per trope to save tokens), character template, themes template, slider rubric, author notes.

**Per-character loop (3 steps):**
1. Full character sheet generation — runs the character prompt with all context, produces the complete sheet including MBTI/Enneagram/Clifton Strengths, slider baselines, and character arc
2. Logic check — runs a second prompt checking: consistency with the dossier, alignment with genre templates, personality profile plausibility, slider level fit, motivation logic, dialogue style match, arc consistency; outputs an improvement plan
3. Implementation — takes the original sheet + the improvement plan, implements only the flagged changes, leaves everything else unchanged

**System prompt directive:** "This is a complex task. You are not allowed to perform at a mediocre level. You are an expert developmental editor and storyteller." Jason reports this phrase noticeably improves output on thinking models.

**After all characters complete:** a relationship dynamics step generates a JSON relationship map — type (rivalry, romance, ally, mentor/mentee, etc.), strength (strong/moderate/weak), direction (bidirectional or A-to-B), and evidence drawn from the character sheets and dossier. Used downstream when outlining to track how characters interact across scenes.

## Visual Continuity (for AI Video/Images)

From the f7g9smAe-xY "Continuity Ladder" — five rungs for holding character consistency when generating video clips or images:

1. **Visual Bible** — written document describing the character in precise, generatable terms (not "beautiful," but specifics like exact coloring, clothing, build, distinctive features)
2. **Reference Sheet** — one clean casting image showing multiple angles, expressions, and costume details; the model stops imagining and starts referencing
3. **Start Frame / Key Frame** — a first-frame image for each clip; reuse the character sheet images as the anchor
4. **Tool Identity Feature** — platform-specific identity lock (e.g., Higgsfield's character identity tool)
5. **Director Review** — generate one clip, check it, *then* scale; never scale bad results

The principle generalizes: for prose, the character bible is the equivalent of the visual bible. Build it once, reference it for every scene.

## Pipeline Integration

In [[chapter-generation-pipeline]], the character system feeds directly into:
- Step 2 (Character Selector) — the full bible is what the selector loads before any scene
- Step 6 (Character Scene Brief) — character emotional state and behavioral notes for *this specific scene* come from the slider rubric + arc position
- Step 12 (Style Check) — character voice consistency check compares dialogue against the dialogue style and example lines in the bible

See [[anti-slop]] for how the desloppifier's voice-check step uses the character bible to flag off-character moments during line editing.

For the motivation-layer architecture (Ghost/Wound/Lie/Weakness) that feeds the character arc field, see [[character-motivation]]. For how MBTI, Enneagram, and the 12 narrative archetypes work as a layered system, see [[archetypes]]. For ensemble cast management and the relationship map JSON structure, see [[ensemble-and-relationships]]. For the six-lever method of making each character's dialogue sound distinct on the page, see [[distinct-character-voices]]. For the drift failure mode specific to multi-session/multi-agent AI drafting, where the bible exists but nothing forces each pass to check against it, and the audit checklist that catches it, see [[character-consistency-drift-audit]].
