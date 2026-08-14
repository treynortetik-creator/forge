---
title: Anti-Slop — Preventing and Removing AI Writing Patterns
type: concept
tags: [writing, ai-writing, editing, line-editing, desloppifier, quality]
created: 2026-06-27
updated: 2026-07-19
source: YouTube — https://www.youtube.com/watch?v=NWGUcKXopKo "Follow These 7 Rules to Stop AI from Writing Low-Quality Content" + https://www.youtube.com/watch?v=Bmvg5UAb9tc "This AI Tool Makes AI Writing Sound Human (Complete Workflow)" + https://youtu.be/MGJQnLcK-Ww "Fable 5 vs Sonnet 5 vs Mystery Model..." (Jason Hamilton / The Nerdy Novelist)
status: living
---

# Anti-Slop

Default AI output is "beige, polite, frictionless, and forgettable" — robotic transitions, over-explained emotions, cliche phrases, and a dead-flat sentence rhythm. Two approaches address this: a strategic framework for preventing slop during generation, and a mechanical line-editing automation for removing it afterward.

## The 7 Rules (Strategic Framework)

**Rule 1 — You do the thinking, AI does the labor.** The soul of the story is the author's job. AI decides nothing about what the piece is about, who the readers are, what promise is being made. Open AI tools only after those decisions are made. Using AI to do your thinking atrophies you as a storyteller.

**Rule 2 — AI plus a human will always beat AI alone.** A skilled human knows what to fix, how to prompt better, and what kind of book to write in the first place. An unskilled human doesn't know what they don't know — the AI will just amplify the gap.

**Rule 3 — AI for volume, human for judgment.** Instead of trying to write one perfect hook, generate 20 curiosity-driven hooks, 20 promise-driven hooks, 20 controversy-driven hooks. Instead of one blurb, generate 10 each with different angles (emotional, logical, humorous, dark). Then scroll and pick the 2–3 best. AI gives volume; the author decides what survives. Professionals in every creative field work this way: comedians write 100 jokes to keep 10.

**Rule 4 — Never use AI's default voice.** Three tactics:
1. Feed it your real writing samples. Have the model analyze your style and return bullet points — short punchy sentences, snarky tone, concrete examples, no big fancy words — then paste those bullet points into prompts as style instructions.
2. Teach it what slop looks like: Google "signs text was written by generic AI" and build a checklist. Ask the model to scan the draft and highlight sentences matching those patterns.
3. Edit the output yourself — AI can only get you so far.

**Rule 5 — Serving the reader is king.** Two tests:
- *The $10 test*: "If a stranger charged me $10 for this book, would I feel ripped off or grateful?" Readers pay with time, which is scarcer.
- *The review mirror*: "Felt generic," "Nothing new here," "Skimmed a lot" are not personal attacks — they are market data saying value-per-page is low. Use AI to summarize criticisms and generate five ways to increase depth, specificity, or emotion in specific chapters.

**Rule 6 — Trust but verify.** AI sounds certain; that does not mean it is right. Let AI propose, you verify. Statistics: look them up. If unverifiable, cut or rephrase as a loose observation. How-to steps: ask the model to list ways the steps could fail in the real world. Story logic: ask it to find plot holes and character inconsistencies. The mindset: AI is the bold brainstormer, you are the paranoid editor. Never let AI be both idea generator and fact-checker simultaneously.

**Rule 7 — AI is leverage, not a replacement for work.** A practical workflow that treats it as leverage:
- Phase 1 (20–30 min): Thinking. Decide what this scene is about. Jot key beats. Pull from your own life. This is where the art lives.
- Phase 2 (20–30 min): Generation. Turn those bullet points into 3 different outlines, or draft a scene with one lighter and one darker version.
- Phase 3 (30–40 min): Editing. Delete the 50% that feels wrong. Rewrite the 20–30% that's close but not quite. Keep the 10–20% that is surprisingly good. Run the slop-removal pass.

## The Desloppifier Automation (3-Pass Line Edit)

An n8n automation that processes a manuscript in 1,500-word chunks. Each chunk passes through three analysis-then-rewrite pairs. The "rewrite" instruction is always: *implement only the suggested changes and do not change anything else* — never "rewrite."

### Pass 1 — Sentence and Paragraph Pacing

Targets:
- Low burstiness: sentences all running to the same length with no variation
- Panic/shock/revelation moments need short, punchy sentences
- The rest of the narrative needs healthy variation (short/medium/long rising and falling with emotional trajectory)
- Formulaic paragraph architecture (every paragraph the same shape)
- Filler and transitional language: furthermore, consequently, therefore, needless to say, worth noting, and more
- AI-pattern phrases: *is a testament to, key pivotal moment, reflects the broader, setting the stage for, deeply rooted, delve, bolstered, boasts*
- Generic claims that could apply to hundreds of subjects without modification

### Pass 2 — Line Editing

Targets:
- Adverbs: distinguish good ones from filler; cut filler
- Dialogue tags: 95% should be "said" or "asked" — unusual tags jolt readers because they are not what readers expect; whispered occasionally acceptable
- **Decorative tag filler**: a sensory qualifier tacked onto an otherwise plain tag that adds texture but no new information or subtext — *"the pilot called back, his voice thin over the cabin comm"* instead of just "the pilot called back." Cut the qualifier unless it's doing work the reader needs (a real acoustic obstruction that matters to the scene, not scenery).
- Action beats as an alternative to dialogue tags
- Under- or over-tagging dialogue
- Passive voice
- Cliches and stock emotional idioms: *heart pounded in her chest, couldn't believe his eyes, blood ran cold, stomach dropped, butterflies in her stomach, lump in her throat*
- **Sensory atmosphere clichés** (setting/mood, not emotion): AI's stock scene-establishing smell-and-texture kit for liminal, derelict, or tech-adjacent settings — *a metallic prickle/tang of ozone, a damp earthy scent [in a setting with no earth], the stale smell of recycled air.* Same mechanism as the emotional idioms above, aimed at atmosphere instead of feeling.
- **Modifier-stacked plain nouns**: compounding a mundane adjective into an invented-feeling qualifier instead of just using the plain word — *"budget gray laminate"* instead of "gray," *"regulation-issue canvas utility bag"* instead of "canvas bag." Padding a simple noun with a qualifier that adds no information reads as AI hedging toward specificity it hasn't earned.
- Redundancies: *added bonus, end result, close proximity, past history, basic fundamentals*
- Repetitions and filler words: *just, very, really, quite, still, so, suddenly, that* — and any words the author overuses

### Pass 3 — The Desloppifier

Run last so earlier passes do not reintroduce the patterns this pass removes.

- **Negative parallelisms**: "Not just X, but also Y" / "It is not just about X, it's Y" / "Not X, not Y, just Z" — one of the most common AI patterns
- **Rule of three abuse**: formulaic triads (adjective, adjective, and adjective; noun, noun, and noun) that feel like padding
- **Em dashes**: AI overuses em dashes; the automation removes all of them as a rule (a few will still get through; that is fine — setting the target to "remove all" lands at "just a few")
- **Collaborative language**: "I would be happy to," "of course," assistant-speak that bleeds into narrative
- **Abstract language without concrete grounding**: "she felt overwhelmed," "he was overcome with grief" — flag and replace with physical/observable/sensory detail
- **Safe flat transitions**: moreover, additionally, furthermore, in addition, as a result
- **Unearned personification and metaphor**: "the silence spoke," "a weight lifted," "the walls came down" — decorative anthropomorphizing that feels automatic rather than earned. A recurring sci-fi/technical sub-flavor: machinery or bureaucratic objects given human defiance or demeanor — *"the viewport refused to cooperate with the paperwork," "the airlock's green indicator glowing with placid innocence"* — the object isn't just described, it's given an attitude it hasn't earned. A companion default: a nervous character holding a mundane object "like a shield" or "like a breastplate" as a defensive-posture simile — fine once, a tell when it's the default first-page gesture

## Connection to the Pipeline

The [[chapter-generation-pipeline]]'s Style Check step (step 11) runs a simplified version of these passes. The full desloppifier automation is for post-draft cleanup after a chapter is already written.

The de-sloppifier's Pass 3 list list is a companion artifact — feed it directly to the prose generator in the First Draft step (step 9) as the `<prohibited_words>` block so slop patterns are blocked at generation rather than requiring cleanup.

[[voice-matching]] addresses the upstream cause (AI defaulting to average prose); anti-slop addresses the downstream symptom (catching what slips through).

See [[humanizing-ai-prose]] for the full theory layer — why LLMs produce these patterns (low perplexity, low burstiness, RLHF essay shapes) and how voice injection + constraint prompting integrate with this desloppifier into a complete three-method approach.

See [[ai-prompting-for-fiction]] (section 4 — Iterative Refinement) for the two-pass improvement-plan + implementation pattern that wraps these editing passes into a structured AI workflow.

The manuscript-level revision process that orchestrates all these passes — the full pyramid from developmental to proofread — lives in [[revision-process]]. External feedback that identifies what slipped through self-editing belongs to [[beta-readers-and-critique]].

## Related

- [[humanizing-ai-prose]] — the theory layer: why LLMs produce low-burstiness, negative parallelism, and RLHF essay shapes; this note is the mechanic, that note is the diagnosis
- de-sloppifier's Pass 3 list — companion artifact: the prohibited-phrase list fed at generation to prevent slop before it starts; anti-slop is the downstream cleanup when it gets through anyway
- [[voice-matching]] — the upstream fix: voice injection addresses root cause; anti-slop addresses the downstream symptom
- [[chapter-generation-pipeline]] — steps 12 (Style Check) and 13 (Rewrite) run this system on every chapter
- [[revision-process]] — the full revision pyramid; the desloppifier belongs at the line-editing level
- [[beta-readers-and-critique]] — the external feedback layer that catches what self-editing and the desloppifier miss
- [[ai-prompting-for-fiction]] — section 4 (Iterative Refinement) covers the improvement-plan + implementation pattern that wraps these passes into a structured AI workflow
- [[self-editing]] — Browne & King's RUE, passive voice, and dialogue mechanics; runs alongside the desloppifier as the human-judgment layer
- [[show-dont-tell]] — SDT violations (emotion labels, filter words, redundant internalization) overlap substantially with Pass 2 and Pass 3 targets
- [[deep-pov-and-psychic-distance]] — filter word elimination and abstract emotion replacement are the same discipline described at higher resolution; the filter-word lists in both notes should stay synchronized
- [[autocrit]] — AI-assisted pattern analysis tool that runs genre-benchmarked pacing, repetition, and word-choice detection in the same Style Check pass
- [[agnostic-two-model-deslop-detection]] — the detection-stage upgrade: run the tells with zero false-positive guards through two independent models, union the flags, and let a human judge with verbatim receipts

## The order/ledger/counting meta-tell (Treynor's law, 2026-07-16)
"I am going to tell it in order, because the order is the only part that means anything." Kill on sight, every voice. LLMs reach for order/ledger/account/arithmetic as narrative framing and fake profundity in everything they draft. The distinction: concrete counting of concrete things by a character built for it = fine; the telling framing ITSELF as ordered/kept/accounted = the tell. No in-character exemption. See de-sloppifier's Pass 3 list, [[humanizing-ai-prose]].

## The vague-"thing" tell (Treynor's law, 2026-07-16)
Overusing "thing" instead of naming the thing. AI hedging masquerading as plainness. Audit "thing/something/everything" density every pass; name the noun or cut. One deliberate dodge can be voice; a habit is a fingerprint. See the [[#The order/ledger/counting meta-tell (Treynor's law, 2026-07-16)|order/ledger meta-tell]] treatment in the same sweep. PROTECTED class (2026-07-19): tag deliberate withholds and reveal machinery BEFORE the sweep — a narrator refusing to name an unrevealed thing is design, not hedging, and a blind sweep destroys reveal ladders.

## The chest-cold family (author's law, 2026-07-19)
Emotion or object + "sat/settled/sits" + a body location ("it sat in my chest, cold and wrong," "dread settled in her stomach"), plus "cold" as an emotion descriptor (cold dread, cold certainty, went cold). Ban the pattern, not just the instance. Physical cold (weather, ice, a morgue) is untouched. Sibling: "held breath / let the breath out" as emotional shorthand — ration to near-zero. From the 131-edit author hand-pass, 2026-07-18; see [[draft-time-doctrine]], de-sloppifier's Pass 3 list.

## The coat-class garment-generic (author's law, 2026-07-19)
"Coat" as the model's default garment on every extra. Where a garment is generic set-dressing, name a specific one (parka, mittens, scarf) or cut the garment; keep only garments doing plot or character work. Run a per-chapter "coat" census, then judge each hit — the pattern generalizes to any default-noun class the model leans on (mug, folder, sedan). See [[draft-time-doctrine]].

## The first-beat rule (author's law, 2026-07-19)
When an image lands, stop. The AI habit: unfold the image across two more re-describing clauses, then re-run the chapter's imagery in a trailing recap at the paragraph's end. Cut everything after the first landing; if the cut needs a button, use an established motif of the story, never fresh imagery. Same discipline as one-pass-per-insight (show-then-tell doubles), extended from meaning to imagery. See [[sentence-craft-and-rhythm]], [[draft-time-doctrine]].

## Aphorism discipline (author's law, 2026-07-19)
An aphorism survives only when it contains a concrete mechanism and the scene around it proves the claim. Generic-clever dies; crude-concrete lives. An aphorism must never grade itself ("the truest thing," "the realest part"). One per scene; one proved beats three asserted. Companion cap: never cut the first rhetorical reversal in a paragraph, always cut the third (antithesis density). Extends the portable-aphorism ration in [[discourse-level-ai-tells]]; see [[draft-time-doctrine]].

## Cross-voice idiom contamination (author's law, 2026-07-19)
Multi-POV books: each narrator owns exclusive idiom families, and a signature construction leaking into the other narrator's chapters is a defect even when the sentence is good. Merges and multi-agent edit waves are the main contamination vector — run a both-directions verification pass after every one. See [[distinct-character-voices]], [[draft-time-doctrine]].
