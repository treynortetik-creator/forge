---
name: short-story-draft
description: Use when you have a completed short-story scene outline, a short-story dossier, and optionally a voice spec, and need to produce the full story prose draft (target 5,000 to 7,000 words). Drafts scene by scene using the enter-late/leave-early principle, Le Guin's crowd-and-leap compression, and the voice spec when present. Keeps the narrator's register locked throughout (critical for deadpan dark comedy). Passes the finished draft to the de-sloppifier. Replaces outline-to-chapters for short fiction.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Short-Story Draft

**Role:** WRITER. One transform: produce the full prose draft, scene by scene, anchored to the outline and the voice spec. This replaces outline-to-chapters for short fiction. There are no chapter selectors, no 13-step per-chapter pipeline, and no 20,000-word continuity context windows. Short fiction runs on a different engine: leaner setup, fewer prep steps, and Le Guin's crowd-and-leap compression principle at every level.

**System posture:** Expert short-fiction author. Compression is the primary discipline. Every sentence does something or it does not exist. Enter each scene as late as possible. Leave each scene before the aftermath settles. The narrator's register does not break.

---

## Dependency Check (Required First Step)

Before generating any prose, confirm prerequisites.

**Required artifacts:**

1. **Short-story scene outline** (producer: `short-story-outline`). Must include: the 8-Point Plot scene map with word budgets and try/fail beats, the opening spec with payload first line and heart's desire placement, and the ending spec with ending move, last line, and Chekhov's Gun list.

2. **Short-story dossier** (producer: `short-story-dossier`). Must include: stated effect, irreversible change, protagonist's heart's desire and magic sword, cast with moral-function slots, and POV character with psychic distance.

If either required artifact is missing, stop and say:

> "This skill needs [ARTIFACT]. Build it first by running the [PRODUCER SKILL] skill, or supply your existing [ARTIFACT] file."

**Optional artifact:**

3. **Voice spec** (producer: `voice`). If present, all prose anchors to its style sheet and fingerprint. If absent, the draft anchors to the genre and tone stated in the dossier. Note clearly in the output file header whether a voice spec was used or absent.

Do not generate any prose until both required artifacts are confirmed and loaded.

Also confirm: the tense (past or present; third-person close, third-person distant, or first-person). Ask if not supplied.

---

## Pre-Draft Setup

Before writing any scene, collect from the provided files and hold in working memory:

- The full scene list with word budgets and try/fail beats
- The payload first line (from the opening spec: used verbatim in Scene 1)
- The last line (from the ending spec: used verbatim in the final scene)
- The Chekhov's Gun plant list with scene assignments
- The protagonist's heart's desire (must be visible on the first page)
- The magic sword (planted in Scene 1, developed in the middle, deployed at the climax)
- The stated effect (the governing constraint for every prose decision)
- The voice spec (or genre and tone signal from the dossier if no spec is present)
- The tense
- The psychic distance (from the dossier)

Complete this checklist before writing Scene 1. Do not begin drafting until all items are loaded.

---

## Per-Scene Draft Process

Run this three-step process for each scene in order. Do not skip scenes or combine them into a single drafting pass.

---

### Scene Step A: Scene Brief

**Goal:** Build a brief for this specific scene before writing a word of prose. This is a short-fiction version of the plot scene brief from the novel pipeline, scaled down to what the compressed form requires.

Produce:

- **Scene job:** verbatim from the outline (one sentence: what this scene must accomplish structurally)
- **Beats:** 6 to 10 specific action beats, using character names and concrete actions, no vague allusions
- **Enter point:** where exactly does this scene begin? Apply enter-late: start at the latest possible moment, not at the approach to the action
- **Exit point:** where exactly does this scene end? Apply leave-early: cut before the aftermath, stop at the turn
- **Try/fail beat:** the yes-but or no-and beat that closes this scene (or "setup" for Scene 1; "validation" for the final scene)
- **Register note:** for dark-comedy and crime stories only: identify how both the comic and dark registers operate in this scene simultaneously; name the specific mechanism (deadpan narration, gap between event and character reaction, one object doing both jobs)
- **Chekhov's Gun check:** which plants or payoffs for this scene appear on the Chekhov's Gun list; confirm they are in the beats

---

### Scene Step B: Draft the Scene

Write the scene prose from the brief. Target the word budget from the outline.

**System prompt to use:** "This is a complex task and requires your full faculties. You are not allowed to be mediocre. You are an expert short-fiction author who understands compression."

**Mandatory writing constraints (all non-negotiable):**

- **Enter late.** Begin at the last possible moment. Strip the scene opening of its own explanation. The reader understands enough to follow, and no more. No transit, no waking up, no scene-setting preamble before the action starts.
- **Leave early.** End the scene before the aftermath settles. Cut at the turn (the moment of the yes-but or no-and beat), not after the reaction to it has played out.
- **Crowd and leap (Le Guin).** Dense, interconnected within what matters; bold leaps over what does not. Trust the reader to fill the gap. Do not explain transitions.
- **Register lock.** The narrator's register does not break. For deadpan dark comedy: the prose tone applies equal pitch to violence, comedy, and mundane detail. The narrator processes murder with the same affect as a scheduling conflict. Do not shift tone to signal importance. Per `${CLAUDE_PLUGIN_ROOT}/references/writing/dark-comedy-crime-craft.md` and Highsmith's equal-pitch principle: one register, applied without exception.
- **Heart's desire on the first page.** Scene 1 only: the protagonist's heart's desire is visible to the reader before the inciting event. Use the placement specified in the opening spec.
- **Payload first line.** Scene 1 only: use the payload first line from the opening spec verbatim. Do not improve it here.
- **Last line.** Final scene only: use the last line from the ending spec verbatim. Do not improve it here.
- **Voice spec anchor.** When a voice spec is present: match sentence rhythm, vocabulary tier, dialogue handling, and POV distance to the style sheet. Feed the style sheet as context before drafting each scene.
- **No em dashes.** Use commas or periods instead. No exceptions.
- **No banned words.** Feed `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md` as a `<prohibited_words>` block before drafting each scene.
- **No metaphors** unless they operate at compression level: one concrete image doing two structural jobs simultaneously.
- **Dialogue advances action.** Every dialogue beat moves plot or reveals character. No stalling, no pleasantries. Apply the Ping Pong drill: strip the exchange to spoken lines only and read them for forward momentum.
- **No repeated sentence openers.** Do not start two consecutive sentences with the same word.
- **Vary sentence and paragraph length.** Short-fiction prose requires burstiness: a healthy mix of short, medium, and long sentences rising and falling with emotional trajectory. Flat sentence-length variance is an AI tell.
- **Scene breaks:** centered `***`
- **Draft-Time Doctrine (write like the edit).** Apply the 13 rules and banned families below while drafting each scene; they exist so the draft never contains what an edit would cut.

**Draft-Time Doctrine, the 13 rules** (extracted from a 131-edit author hand-pass, 2026-07-18):

1. Never narrate the narration (no "the truest thing," no explaining why the telling matters, no restating a beat that landed).
2. One figure per beat; no cute similes; a plain verb beats a simile that outweighs its noun.
3. Stop when the image lands; no re-describing clauses, no end-of-paragraph imagery recap.
4. Name the noun; no vague "thing/something" hedges; violence gets its real verb.
5. Split at the pivot; payoffs get their own short sentence; fragments legal.
6. Diction plainer or crueler, never fancier.
7. Concrete props over abstractions; declared acts get a hand doing them; props get specs and wear.
8. Dialogue does the work; narration never duplicates what a line already carries.
9. Flourishes come from the story's established coinage, never fresh ornament.
10. An aphorism needs a concrete mechanism proved by its scene; it never grades itself; one per scene.
11. Keep the first rhetorical reversal in a paragraph, cut the third (antithesis density cap).
12. Order beats in performance chronology, the order the room experiences them.
13. No emotional summary after the emotion already landed.

**Banned families** (in addition to `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`). ⚠️ *These are one manuscript's idiom bans, kept as a worked example of the KIND of family to ban — replace them with your own book's tics:* the word "ledger" and any order/counting meta-narration (a character counting concrete real objects is exempt); emotion sitting/settling in the chest + "cold" as an emotion descriptor (physical cold exempt); "held breath" as emotional shorthand; generic "coat" as default garment (name the specific garment or cut it; plot/character garments exempt); in multi-POV work, each narrator's exclusive idiom families stay in their own scenes.

---

### Scene Step C: Scene Check

After drafting each scene, run a self-audit before advancing. Do not redraft; flag issues and implement targeted fixes only.

Check for:
1. Did the scene enter as late as possible, or is there throat-clearing at the top?
2. Did the scene leave at the turn, or does it settle into aftermath?
3. Is the try/fail beat (yes-but or no-and) clearly present?
4. Are any Chekhov's Gun plants or payoffs for this scene present and placed correctly?
5. For dark-comedy and crime: did both registers operate simultaneously?
6. Any em dashes or banned words in this scene's prose?

If any check fails, implement the targeted fix before advancing to the next scene.

---

## Assembly and Pre-Edit Check

After all scenes are drafted and checked:

1. Assemble the full story in scene order.
2. Run a wordcount check via `wc -w [draft file]`. Report the count. If the total is under the word band by more than 15%, identify which scenes are thin. If over by more than 15%, identify which scenes ran long.
3. Read the opening and ending together. Does the last line pay the promise made by the first line? Does the ending move operate as specified? Note any mismatch.
4. Verify the Chekhov's Gun list: every plant appears at its specified scene; every payoff appears at its specified scene. Flag any gap.

---

## Output

Write the draft to `[title-slug]-draft.md` in the project working directory.

Add a one-line header noting: date generated, word count, voice spec used (yes/no), and tense.

Report to the user:
- Total word count
- Any scenes flagged for length issues
- Whether the Chekhov's Gun list is fully accounted for
- Output file path
- Next step: "Run `de-sloppifier` on the draft, then `logic-check` against the dossier and scene outline."

---

## Quality Rules

These apply across all generation in this skill:

- No em dashes in any prose or skill text. Convert any to commas or periods.
- No banned words. Feed the list as `<prohibited_words>` before every scene.
- No negative parallelism.
- No rule-of-three padding.
- Register lock is non-negotiable for dark-comedy and deadpan narration. The moment the narrator winks at the camera, the tonal effect is destroyed.
- The payload first line and last line are used verbatim from the outline spec. Do not improve them during the draft stage. If they need revision, revise the outline, then return here.
- Compression is the primary discipline. If a sentence does not do something, it does not exist.

---

## Craft References

- `${CLAUDE_PLUGIN_ROOT}/references/writing/short-story-form.md`: enter late and leave early (Scene Steps A and B), Le Guin's crowd-and-leap compression (Scene Step B), the compressed try/fail cycle mechanics, the single-sitting form constraints
- `${CLAUDE_PLUGIN_ROOT}/references/writing/short-story-openings-and-endings.md`: the payload first line and opening contract (Scene 1), the four ending moves (final scene), the Chekhov's Gun accounting (assembly check), the opening-ending loop
- the Wulf Moon method: the heart's desire on the first page (Scene 1), the magic sword deployment at the climax, the escalation engine for try/fail beats (things get worse)
- `${CLAUDE_PLUGIN_ROOT}/references/writing/dark-comedy-crime-craft.md`: the register-lock requirement, the deadpan narration mechanism, the fused-register principle (both jobs simultaneously), Highsmith's equal-pitch principle, the Puchner elision-of-reaction rule (leave the reaction out)
- `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`: the voice spec the drafting step consumes; the forensic fingerprint and 13-dimension style sheet that govern sentence rhythm and vocabulary tier
- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` and `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`: the constraint-prompting layer; the em-dash ban; the prohibited vocabulary list
- `${CLAUDE_PLUGIN_ROOT}/references/writing/dialogue-beats-vs-tags.md`: the Ping Pong dialogue drill; when action beats replace dialogue tags; the said/asked default

---

## Operating Notes

- **Do not skip the Scene Brief.** The brief takes two minutes. Skipping it produces scenes that miss their structural job or run over budget.
- **Register lock is the hardest rule to hold.** For deadpan dark comedy: model the narrator on Highsmith's equal-pitch principle. Murder and breakfast get the same prose rhythm. Do not shift tone to signal to the reader that something is important.
- **The payload first line and last line come from the outline.** Do not improve them during drafting. If they need revision, that is a signal the outline needs revision, not that the draft should improvise around it.
- **Enter late beats every other concern.** If a scene brief calls for scene-setting before the action, the brief is wrong. Revise the brief, not the constraint.

---

## Iteration Notes (Living Skill)

After each run, log patterns in `CHANGELOG.md` in this directory:

- Any scene where the enter-late principle and the word budget were in tension: note what was cut and whether the scene suffered.
- Any scene where the register broke under the pressure of dark content: note what caused the break and what restored it.
- Any Chekhov's Gun plant missed during drafting and caught only in assembly: note the plant and scene.
- Any em-dash or banned-word slips in the final prose: the skill must model what the pipeline teaches.
