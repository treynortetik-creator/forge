---
title: Voice Matching — Making AI Write in the Author's Voice
type: concept
tags: [writing, ai-writing, voice, style, claude-cowork, skills]
created: 2026-06-27
updated: 2026-06-27
source: YouTube — https://www.youtube.com/watch?v=C1snRnGbNRM "How to Make AI Write in YOUR Voice (Claude Skill Tutorial)" (Akello Harrell / The Nerdy Novelist)
status: living
---

# Voice Matching

Default AI output sounds like everyone and no one simultaneously. The model guesses "the average of everything it has ever read." A voice skill fixes that by giving the model a forensic description of how *this author's* sentences actually move.

Voice is not genre, theme, or story. It is sentence rhythm, word choices, whether the POV character thinks in full paragraphs or punchy fragments, whether you write "she said" or "she said nothing and the silence did the talking." Automatic enough that writers rarely see it until someone describes it back to them.

## The Two-Step Method

### Step 1 — Extraction

Collect 2,000–5,000 words of your own finished, edited fiction. Prose only — not blog posts, not emails. The more heavily edited the sample, the cleaner the fingerprint. Pull from different scene types (action, quiet, heavy dialogue) to capture the full range.

Paste this extraction prompt into a fresh chat, followed by the prose:

> *You are a forensic editor and writing analyst. Your job is not to evaluate quality, it is to identify pattern. Below is a body of prose from a single fiction author. Read it carefully, then produce a **voice fingerprint** for this writer. This fingerprint will be used to build a Claude skill that generates new prose in this style. Analyze the following dimensions and be specific — not vague descriptors like "lyrical" or "gritty," but architectural observations that can be turned into instructions: sentence rhythm and length, vocabulary level, dialogue handling, POV approach, naming patterns, how description is distributed.*

The output is a comprehensive report — sentence length ranges, vocabulary tier, dialogue tag patterns, POV habits, characteristic constructions. Most writers have never seen their own habits listed this plainly.

### Step 2 — Skill Creation

With the fingerprint in hand, send this follow-up in the same session:

> *Now write a voice skill file using this fingerprint. Include a short passage from the sample as the example anchor.*

Then, critically: tell Claude to formalize it rather than leave it as a document.

> *Make this into a formal skill that can be used by Claude Cowork and Claude Code. Use the skill creator.*

Without the skill-creator step, the output is just a prompt document — not an invocable skill. The resulting skill file includes: persona rules, architectural constraints specific to the author's patterns, and a prose anchor that Claude references when generating.

## Quality Check

Claude Cowork will run baseline vs. skill comparisons automatically when building the skill — three test prompts (cold open, tense two-character scene, solo action sequence) generated with and without the skill. Baseline output is noticeably more generic: longer, smoother, more institutional in tone. Skilled output preserves the author's characteristic sentence breaks and vocabulary tier.

## Key Rules

- One skill per pen name or series voice — voices built for space opera will not fit cozy mystery
- Minimum 2,000 words of sample; 3,000–5,000 is better
- Edited manuscripts outperform raw drafts as samples — the editing pass converges toward the author's actual voice
- The skill file is a living document; revise it after each project as the voice develops

## Connections

The voice skill is the foundation that all prose generation in `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` depends on — particularly the First Draft step (step 10) and the Style Check step (step 12). Without it, the model defaults to generic output regardless of how detailed the scene brief is.

The **story hacker prompts** style sheet prompt (collect 6,000 words → run through Claude → get prose style sheet) is the simplified single-session version of this same extraction method — the operational instrument is the style-sheet instrument in `voice`, the 13-dimension generator that outputs LLM writing instructions in a specific author's voice. Use the style sheet for quick projects; build a full voice skill for a series.

The de-sloppifier's Pass 3 list list works alongside the voice skill — the skill says "write like this author"; the banned list says "never use these patterns regardless."

See **claude build** for how to implement and store voice skills inside Claude Cowork.

See `${CLAUDE_PLUGIN_ROOT}/references/writing/humanizing-ai-prose.md` for the full theory of why AI defaults to generic prose — the root causes (low perplexity, low burstiness, RLHF-trained patterns) that voice matching is designed to counteract, and how voice injection integrates with constraint prompting and multi-pass deslop as the three-method humanization stack.

See **ai prompting for fiction** for the full map of prompting techniques this voice-extraction process plugs into — particularly sections 3 (Few-Shot) and 6 (Temperature/Style Steering). See **json super prompts** for how the `<prose_style_example>` and `<style_sheet>` tags that carry the voice into generation prompts are structured.
