---
title: Humanizing AI Prose — Why AI Reads as AI and How to Fix It
type: concept
tags: [writing, ai-writing, anti-slop, voice, constraint-prompting, deslop, line-editing, burstiness, perplexity]
created: 2026-06-27
updated: 2026-07-08
source:
  - https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
  - https://quillbot.com/blog/ai-writing-tools/burstiness-and-perplexity/
  - https://originality.ai/blog/perplexity-and-burstiness-in-writing
  - https://medium.com/@christianaistudio/stop-telling-ai-to-write-like-a-human-do-this-instead-8db9c1a8cd34
  - https://sudowrite.com/blog/ai-writing-tips-for-fiction-authors-what-actually-works/
  - https://www.creativindie.com/how-to-humanize-chatgpt-written-content-for-better-fiction-and-to-pass-ai-detection/
  - https://arxiv.org/pdf/2604.03136 (StoryScope: Investigating Idiosyncrasies in AI Fiction, 2026)
  - https://www.helpingwritersbecomeauthors.com/impact-of-ai-on-fiction-writing/ (K.M. Weiland)
  - https://www.mcsweeneys.net/articles/the-em-dash-responds-to-the-ai-allegations (Greg Mania, McSweeney's, 2025 — em-dash satire)
  - https://www.techtimes.com/articles/319137/20260626/ai-text-detectors-flag-polished-human-writing-ai-new-studies-expose-built-paradox.htm (TechTimes, June 2026 — AI-detector false-positive paradox)
  - https://www.youtube.com/watch?v=NWGUcKXopKo + https://www.youtube.com/watch?v=Bmvg5UAb9tc (Jason Hamilton / The Nerdy Novelist)
  - https://youtu.be/MGJQnLcK-Ww "Fable 5 vs Sonnet 5 vs Mystery Model..." (Jason Hamilton / The Nerdy Novelist — live model-comparison line-edit)
status: living
---

# Humanizing AI Prose — Why AI Reads as AI and How to Fix It

AI prose is recognizable because language models optimize for **high-probability next tokens** — the statistically likely continuation given the training corpus. That optimization process produces text that is polished, correct, and deeply generic. It sounds like the average of everything it has ever read. Human writers make low-probability choices: unexpected words, mid-sentence stops, sentences that fragment where grammar says they shouldn't, rhythm that breaks the pattern right when the pattern gets comfortable. AI, left to itself, does none of that.

The result is what researchers describe as low **perplexity** (predictable word choices) and low **burstiness** (flat sentence-length variance). Both are measurable. Both are fixable. Most humanization work is fixing one or both.

---

## Part 1 — The Specific Tells

These patterns appear with high statistical frequency in AI-generated text. Flagged by the Wikipedia "Signs of AI Writing" analysis and corroborated by the StoryScope research paper (2026), which used SHAP-interpretable XGBoost classifiers to identify AI fiction fingerprints at the feature level.

### 1. Negative Parallelism ("Not X, But Y")

Constructions like "Not just a tool, but a partner" / "Not about survival — about legacy" / "It wasn't fear she felt. It was resolve." These read as rhetorical polish but are one of the most statistically over-represented AI patterns. The model was trained on argumentative and persuasive text where this form signals sophistication; it imports the pattern into narrative where it reads as mechanical.

Wikipedia flags these exact forms: *"Not just X, but also Y"*, *"Not X, but Y"*, *"X rather than Y"* as negative parallelism markers.

The `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` Desloppifier (Pass 3) targets and removes them from finished drafts.

### 2. Rule-of-Three Abuse

AI defaults to triads. Three adjectives, three examples, three clauses. The pattern appears in description ("brave, resourceful, and uncompromising"), in narration ("the smell of ash, the taste of copper, and the distant sound of bells"), and in summary transitions ("First, she needed to escape. Second, she needed to warn the others. Third, she needed to trust herself"). None of these are wrong. All of them together produce a prose texture that reads as constructed rather than felt.

Human writers use triads selectively, when the number three has emotional or rhetorical meaning in context. AI uses them as a default fill pattern. The diagnostic: count rule-of-three constructions per page. More than one or two per 1,000 words is a flag.

### 3. Em-Dash Overuse

The em dash is not wrong — it is a real punctuation tool for sudden shifts, interruptions, and emphasis spikes (see **sentence craft and rhythm**). AI overuses it because RLHF training rewarded complex, multi-clause sentences, and the em dash became the model's preferred mechanism for packaging them. A typical AI-generated page will contain three to six em dashes; a typical human-written literary page contains zero to two.

The `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` Desloppifier (Pass 3) removes all em dashes as a target, landing at "a few" after the pass. That is the right calibration: setting the goal to "remove all" counteracts the model's bias enough to hit normal human usage.

The McSweeney's piece "The Em Dash Responds to the AI Allegations" (Greg Mania, 2025) is a useful cultural marker — the satire is funny because the overuse is real.

### 4. Sycophancy Bleed-Through

AI models trained with RLHF internalize an approval-seeking posture. In chat, this surfaces as "Great question!" and "I'd be happy to help." In narrative, it surfaces more subtly:

- Narrators who validate the reader's assumed concern before addressing it ("You might wonder why she did this. The answer is...")
- Characters who deliver conclusions in complete, satisfying, well-rounded form when a person in that situation would be confused or inarticulate
- Scenes that resolve at an emotionally comfortable level rather than staying in productive discomfort
- Dialogue that is too articulate — every character expresses exactly what they mean, no friction, no subtext

The craft fix is not prompting the AI to "stop being sycophantic." It is prompting it to model what the character would *not* say, what they would leave unsaid, where the conversation would break down.

### 5. Cadence Sameness — Low Burstiness

Even when individual sentences are well-crafted, AI output tends toward uniform sentence length and structure across a passage. The model lacks the writerly instinct to break a pattern right before it becomes comfortable. This is what **sentence craft and rhythm** calls burstiness deficit: no shocks, no dramatic shorts, no long accumulations followed by a single-word sentence.

**Burstiness** (the metric): measures variance in sentence length across a passage. High-burstiness text alternates between short bursts and long flowing sequences in response to emotional content. Low-burstiness text holds the same approximate length throughout, regardless of what is happening in the scene.

**Perplexity** (the related metric): measures how predictable the vocabulary choices are. Low perplexity = common words in expected combinations. High perplexity = unexpected word choices, lower statistical probability. Human writers naturally produce higher-perplexity text than AI, though paradoxically well-edited human prose sometimes scores low perplexity too (the detector-paradox problem documented in *TechTimes*, June 2026).

The practical fix is described in **sentence craft and rhythm** (section 6) and targeted by Pass 1 of the `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` Desloppifier.

### 6. Safe Flat Transitions

"Moreover," "Furthermore," "Additionally," "In conclusion," "It is worth noting that," "As a result." These are filler that masks weak idea-to-idea connections. They do not connect ideas — they announce that a connection is coming, then leave the reader to supply it.

Human prose creates connections through juxtaposition, sentence rhythm, and the actual logic of the content. AI creates connections by naming the relationship in a transition word. The fix: delete the transition and look at whether the two sentences actually connect. If they do, they connect without the filler. If they don't, the transition was hiding a structural problem.

### 7. Abstract Emotion Without Physical Grounding

"She felt overwhelmed." "He was overcome with grief." "A wave of something she couldn't name washed over her." These name emotional states without anchoring them in observable, sensory, or physical detail. They are technically telling-not-showing, but the AI-specific version is more mechanical: the model produces the emotional summary because it follows the scene's content logically, not because it makes a craft decision to name rather than show.

The `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` Pass 3 flags abstract emotional language for replacement with physical/sensory/observable detail. This connects directly to the deep POV material in **deep pov and psychic distance**.

### 8. Vocabulary Inflation

Post-2022, a set of words surged in AI usage: *delve, tapestry, pivotal, testament, intricate, vibrant, beacon, underscore, foster, garner, resonate, groundbreaking, nuanced, multifaceted.* These words are not wrong; they are statistically overrepresented in LLM output because they appear in formal writing (which LLMs absorbed heavily) and because models reward apparent sophistication.

The complete catalog is in de-sloppifier's Pass 3 list. The fix at generation time: feed the banned list as a `<prohibited_words>` block in the prompt so the model cannot use them. The fix at editing time: Pass 3 of the desloppifier scans for them and flags for removal.

### 9. Structural Sameness — The RLHF Essay Shape

RLHF training on instruction-following tasks rewarded a specific prose shape: **state the claim → explain the claim → summarize the claim.** In fiction this appears as: describe what is happening → explain why it matters → close the passage with a paragraph that restates the key point. Readers do not name this pattern, but they feel it as condescension — the story explaining itself.

The fix is purely structural: **each sentence must introduce new information.** No restatement. No explanatory summary appended to what the scene already showed.

### 10. Character Intro Overload — The Resume Clause

AI's default move for introducing a character in motion is to cram their entire relevant backstory into a single overloaded subordinate clause riding on the entrance action, rather than trusting the reader to meet the character in real time. Flagged live in a three-model line-edit comparison (Claude Sonnet 5's draft): *"moving with a brisk forward-leaning sprint of a woman who had survived 40 regulatory inspections and intended to be back aboard the return transport before the crew finished their lukewarm protein rash."* One entrance, one clause, an entire CV of competence and cynicism stapled to it. The reviewer named it a "cadence" he sees "all the time" from these models — a specific, recognizable sentence shape, not a one-off.

The tell is the packing, not the content: exposition and characterization that would land better distributed across several beats (a line of dialogue, an action choice, a second character's reaction) gets front-loaded into one clause because the model resolves "the reader needs to know this" immediately rather than staging it. The same instinct produces the run-on sibling: a sentence stacking a formal-sounding descriptive clause ("the confident weight of a document drafted by someone who hadn't left a desk in Geneva since the turn of the century") onto its actual point, padding a simple observation with borrowed institutional texture.

The human move: let the entrance be plain. Release the credentials and the cynicism over the scene that follows, not in the doorway.

---

## Part 2 — The Three Humanization Methods

### Method 1 — Voice Injection

The upstream fix. Instead of correcting AI prose after generation, constrain the model's output by providing a forensic description of the author's actual sentence patterns, vocabulary tier, and structural defaults before generation begins.

Full technique: `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`. The two-step method — (1) feed the model 2,000–5,000 words of your edited fiction and extract a voice fingerprint, (2) convert that fingerprint into a reusable skill — produces a constraint set that routes the model away from generic toward author-specific patterns.

Short-form version from **story hacker prompts**: collect 6,000 words of your prose, run through the style-sheet prompt, get a prose style sheet. Use for quick projects; build the full skill for a series.

The voice skill addresses the root cause. Constraint prompting and multi-pass deslop address what escapes the voice skill.

### Method 2 — Constraint Prompting

Constraint prompting specifies **what the model cannot do** rather than just what it should do. Four core constraints (from the Medium analysis of structural AI tells, 2024):

**Constraint 1 — No opener filler, no closing summary.** "Start with the first relevant sentence. End when the content ends." This breaks the RLHF-trained state/explain/summarize shape that produces self-explaining prose.

**Constraint 2 — Sentence length variation; never three sentences of similar length in a row.** This directly targets burstiness deficit. The model must actively vary rather than settle into its cadence.

**Constraint 3 — Every sentence introduces new information.** No sentence that restates, explains, or summarizes what the previous sentence already established. This eliminates the restatement loop and forces forward momentum.

**Constraint 4 — Plain vocabulary over inflated vocabulary.** Specify the vocabulary tier: "Hemingway clarity, not academic register." This reduces the probability of pulling from the high-formality / inflated-adjective layers of the training corpus.

Additional fiction-specific constraints:
- "Characters may not fully articulate what they mean. Leave subtext." (Targets sycophancy bleed-through.)
- "Vary sentence beginnings. Do not open three consecutive sentences with the same subject." (Targets structural sameness from **sentence craft and rhythm**.)
- "Use the following prohibited words list." (Feed de-sloppifier's Pass 3 list directly.)
- "No em dashes." (Targets em-dash overuse during generation rather than requiring a cleanup pass.)

From CreativIndie's fiction-specific framework: add a **scene checklist constraint** requiring motivation, opposition, conflict, tension, and a cliffhanger element — this prevents AI from completing scenes prematurely and at a comfortable emotional resolution level.

### Method 3 — Multi-Pass Deslop

The downstream fix. After generation, run the three-pass Desloppifier from `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` in sequence:

- **Pass 1** — Sentence and paragraph pacing: targets burstiness deficit, filler transitions, formulaic paragraph architecture
- **Pass 2** — Line editing: targets adverbs, weak dialogue tags, passive voice, clichés, stock emotional idioms, redundancies
- **Pass 3** — Desloppifier: targets negative parallelisms, rule-of-three abuse, em dashes, collaborative/assistant language, abstract emotion, flat transitions, unearned metaphor

**Critical rule:** Pass 3 runs last. Earlier passes can reintroduce Pass 3 patterns. The instruction at each pass is always "implement only the suggested changes" — never "rewrite."

The `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` note contains the full target list for each pass and the implementation detail.

---

## Part 3 — The Detection Caveat

The perplexity/burstiness framework has a known failure mode: polished human writing can score low on both metrics (well-edited prose uses precise, common words in expected combinations). The *TechTimes* report from June 2026 documented AI detectors flagging polished human prose as AI-generated at non-trivial rates — what researchers called the "built-in paradox" of AI detection.

This matters for humanization work: the goal is not to pass a detector. The goal is to produce prose that reads with the quality and specificity of deliberate human craft. Detector-gaming and quality-writing overlap but are not the same target.

---

## Part 4 — Pipeline Integration

In the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`:
- Voice injection and constraint prompting apply at **Step 10 (First Draft)** — before prose is generated
- Pass 1 and Pass 2 of the desloppifier apply at **Step 12 (Style Check)**
- Pass 3 (the core desloppifier) applies at **Step 13 (Rewrite)**
- The de-sloppifier's Pass 3 list list is fed as a `<prohibited_words>` block at Step 10 (generation) and re-scanned at Step 12 (Style Check)

---

## Related

- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` — The 7 strategic rules + the full 3-pass Desloppifier implementation; this note is the theory, anti-slop is the mechanic
- de-sloppifier's Pass 3 list — The prohibited vocabulary catalog; fed as a constraint at generation and scanned at Style Check
- `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md` — Voice fingerprint extraction and skill creation; the upstream fix that addresses root cause rather than symptoms
- **sentence craft and rhythm** — Burstiness as a rhythm metric; the diagnostic and structural fixes for flat cadence
- **story hacker prompts** — The quick-form style-sheet approach; the short path to voice injection
- `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` — The end-to-end pipeline this note's three methods integrate into (Steps 10, 12, 13)
- `${CLAUDE_PLUGIN_ROOT}/references/writing/self-editing.md` — Browne & King on RUE, dialogue mechanics, and the trust-the-reader posture that anti-slop methods enforce
- **deep pov and psychic distance** — Physical/sensory grounding as the fix for abstract emotional language (AI tell #7)
- `${CLAUDE_PLUGIN_ROOT}/references/writing/README.md` — The full writing system map; this note is part of the Style Check / Rewrite cluster
