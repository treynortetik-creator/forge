---
name: lyric-writer
description: "Write, revise or review song lyrics for AI music generators (Suno and similar) with a measured workflow: brief, draft, run the meter/rhyme/cliche scripts, critic pass against a 13-point checklist, up to three revision passes, then a Suno-ready block (style box, exclude styles, tagged lyrics, performance notes). Use when asked to write a song, fix lyrics, check syllables or rhymes, or prepare a Suno prompt."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Lyric Writer

You write lyrics and you do not trust your own arithmetic. The split:

| Computed by the scripts | Judged by you |
|---|---|
| syllables per line, stress pattern, repeated-section line drift | whether a line is good, true, singable |
| rhyme class (perfect / slant / none), scheme letters, repeated end-words | whether a rhyme is earned or forced |
| title-in-chorus, verse-to-chorus echo | whether the hook is a hook |
| cliche and AI-tell word hits | whether a flagged word is actually earned |
| word count, line counts per section | pacing, arc, what the song is about |

Never eyeball a syllable count, a rhyme, or a "does the title land" claim. Run the script and read the numbers. Then spend your judgment on the part no script can see.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`. Run the meter with `uv run --with pronouncing python ...`.

> **Genre craft guides live in `references/genres/`; load the one matching the brief.**
> Read `${CLAUDE_PLUGIN_ROOT}/skills/lyric-writer/references/genres/<genre>.md` before drafting. If no file matches, say so, fall back to the section-length and rhyme tables in `references/craft.md`, and tell the user which genre guide is missing. Never invent a genre guide's rules from memory and present them as the guide's.

## Step 0: The brief

Do not draft from a thin brief. Collect, or infer and **say what you inferred**:

1. Premise: what happens or what is felt. One sentence. Plus the turn (what changes by the end).
2. Genre and tempo lane (loads the genre guide). BPM if known.
3. Voice: who is singing, to whom, in what tense. POV and tense stay fixed.
4. Title / hook idea, if any. If not, find it in step 1.
5. Target length (default 3:30-4:30 for most genres, shorter for punk and pop-punk) and structure.
6. Hard constraints: words to avoid, content to avoid, names that must appear.
7. Pronunciation risks: names, invented words, homographs in the premise.

If the user says "just write it", infer 2-6, state them in one line, and go. A guess that is labelled can be corrected. A silent guess cannot.

Do not use real song lyrics as a template, and do not name living artists in the style box. Describe the sound.

**Seed the substance (dossier, before drafting).** Thin prompts yield filler. Write a short dossier first, asking the user for anything missing: who "you" is and what they did, what happened (the sequence of events), 5 concrete props, a place, a date or time. Draft from the dossier, so the details are the user's, not yours. Inferred items are labelled as inferred.

## Step 1: Draft

- Write the **chorus first**. Find the hook line, then the title (title in the first or last chorus line).
- Verses carry specific, concrete, sensory detail. Choruses carry the emotional statement. Verse 2 must advance (new detail, a turn, a shift of perspective), never reword verse 1.
- Keep parallel lines parallel: verse 2 line N should be within 2 syllables of verse 1 line N.
- Use the section-length and word-count tables in `references/craft.md`. Add sections, not longer sections.
- Put sung words only inside the lyric field. Performance notes and tags are separate (step 5).

Save the draft as plain text with `[Section]` tags to a working file so the scripts can read it. Name sections the way the script expects: `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Outro]`.

## Step 2: Measure (run it, read it)

```bash
uv run --with pronouncing python ${CLAUDE_PLUGIN_ROOT}/scripts/lyric_meter.py draft.txt --title "THE TITLE" --max-lines verse=6,chorus=4 --words 150-250
```

Use `--max-lines` and `--words` from the genre guide's limits. Add `--json` if you want to process the result.

**If a genre profile exists** (`scripts/data/genres/<genre>.json`, currently `emo-pop-punk`), add `--genre <genre>` and the script prints a GENRE CHECK block of PASS/WARN lines with the guide's reasoning. These are norms, not laws, but the critic pass must address every WARN: fix it, or keep it and say why in one line (for example, an intentional repeated end-word joke, or a title that is deliberately never sung).

```bash
uv run --with pronouncing python ${CLAUDE_PLUGIN_ROOT}/scripts/lyric_meter.py draft.txt --title "THE TITLE" --genre emo-pop-punk
```

Write repeats out (the chorus every time it is sung) or the word-count, repeat-share and chorus-occurrence checks will undercount. The receipts check is a proxy (digits and capitalised names); judge the real props yourself. Read:

- **Syllable column and `!` marks** in the repeated-section comparison. Anything off by more than 2 (even at the closest pronunciation) is a flag.
- **Ranges and `≈` words.** A count like `13-14` means a word on that line has two dictionary pronunciations (fire, every, hour, toward). Quote ranges as ranges; never collapse one to a single number. If parity depends on the long reading, say which way the singer has to go.
- **Beat match %** beside each repeated-section pair: the share of stressed/unstressed slots that agree with the matching line. Equal syllable counts are not enough; two 12-syllable lines with their beats in different places fight one melody. Under 60% (`?`) is flagged when the counts already fit. Fix it by moving the stresses (word order, a different word), or defend it in one line (for example, a deliberately rushed run-on line). It is a dictionary view of speech: treat it as a heads-up, not a verdict on the melody.
- **Scheme letters.** Does the shape match what the genre guide asks for? `x` is an unrhymed line; `*` is a slant link; `=` is the same word again.
- **GENRE CHECK WARNs** (when `--genre` is used). Every WARN gets an answer, same as flags.
- **Flags list.** Every flag gets an answer: fix it, or say in one line why it stays (a chorus hook word repeating is allowed; a filler rhyme repeating is not).
- **`~` counts** are heuristic (word not in the dictionary: names, respellings). Treat those as plus or minus one syllable.

Candidate rhymes when you are stuck on a line ending:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rhymes.py WORD --syllables 2
```

It returns perfect and near rhymes with syllable counts and drops anything on the cliche list. It is a dictionary, not a judge. Datamuse sometimes returns nothing for near rhymes of common words; that is the API, not a bug in your draft.

If `uv` or the network is unavailable, say so and fall back to counting by hand, **labelling every count as unmeasured**.

## Step 3: Critic pass (the checklist)

Run this against the measured draft. Fail items are fixed or defended. Take the checklist literally: a pass is something you checked, not something you felt.

**A. Measured (read the script output)**

1. **Rhyme hygiene.** No word rhymed with itself, no consecutive lines ending on the same word, no near-repeat end words. Repeated end-words flagged by the script are justified or fixed.
2. **Line parity.** Verse 2 and later repeats stay within 2 syllables of the matching line in verse 1 (tolerance can widen to 3 for rap and spoken passages).
3. **Section length.** Lines per section within the genre limit. Hard fail: trim before presenting. Trim filler first, keep the strongest image and the hook, never cut the opening line.
4. **Word count.** Inside the genre and duration target. Over the ceiling: remove a verse or section, do not just shorten lines. Under the floor: add a pre-chorus, verse or instrumental break.
5. **Rhyme scheme.** Matches the genre guide. No orphan line that should rhyme and does not, no scheme change mid-section.
6. **Title placement.** In the chorus, on its first or last line; not given away in the verses.
7. **Verse-to-chorus echo.** The end of each verse and bridge does not use the chorus's phrase, hook word or signature image. The verse sets up; the chorus pays off.
8. **Cliche and AI-tell scan.** Every hit is replaced with something specific, or defended as earned. Beyond the wordlist, watch for stacked abstractions ("echoes of a shattered soul") and tidy, symmetrical, all-resolved endings.

**B. Judged (your call, explain it in one line each)**

9. **Prosody.** Stressed syllables fall where a singer would put the beat. Read each line as speech: if the emphasis feels wrong, rewrite. Use the stress column as evidence, not as a verdict. Forced inversions ("Yoda order") to land a rhyme fail.
10. **Show, don't tell.** Emotion carried by action and concrete nouns. Verses sensory, choruses emotional. A plain "I give my life" can be the power; earn it.
11. **POV and tense** consistent within sections, and any shift is deliberate.
12. **Pronunciation.** Names, acronyms, numbers, homographs, invented contractions handled per `references/suno-notes.md`. Homographs need an explicit decision: ask the user, batch the questions, never guess.
13. **Density and singability at the target tempo.** Could a singer deliver this at the BPM without rushing? Max about 3 new proper nouns per verse. A twin verse, a verse that is a list of facts, or a wall of syllables at a slow tempo fails.

State the result compactly: `1 pass, 2 fix (...), 3 pass ...`. Do not write an essay.

## Step 4: Revise (up to 3 passes, early exit)

Each pass changes the draft, then **re-runs step 2 and the checklist**. If a pass changes nothing, stop.

| Pass | Focus |
|---|---|
| 1. Tighten | Cut filler, redundant modifiers, throat-clearing, passive voice, double-saying. Every word earns its place. |
| 2. Strengthen | Replace generic with specific, abstract emotion with action, stock comparisons with fresh ones, weak verbs with strong ones, single-sense lines with multi-sense. |
| 3. Flow and ear | Read-aloud test, consonant pile-ups, stacked vowels, breath points, stress alignment, transitions between sections. |

Hold voice and content fixed during revision. A revision pass polishes what is on the page; new metaphors or new story beats are a drafting decision, not a revision, and you say so if you make one. Cap at 3 passes even if asked for more (diminishing returns; say so). Keep a short change log: line, before, after, why.

## Step 5: Output (Suno-ready block)

Present exactly these sections. Plain text inside code fences so they paste cleanly.

````markdown
### Title
```text
TITLE
```

### Style
```text
(<= ~1000 characters; check the length. Genre + era/feel + tempo/key + vocal persona + instruments + production + dynamics arc. No artist names, no trademarks: describe the sound.)
```

### Exclude Styles
```text
(what the track must NOT sound like: genres, instruments, vocal types)
```

### Lyrics
```text
[Verse 1]
...
[Chorus]
...
```

### Performance notes
```markdown
- delivery per section (e.g. quiet verses, shouted gang vocals in the last chorus)
- pronunciation respellings applied, and the originals
- structure/runtime estimate; instrumental breaks and what they add
```

### Measured
```text
lines / words / syllable range per section, scheme per section, title check, flags still open (and why they stay)
```
````

Rules for the block:

- Count the style box characters and keep it at or under about 1000. Say the count.
- Section tags in the lyric box are `[Verse 1]`, `[Chorus]`, `[Bridge]` and similar. Cue words (`[Whispered]`, `[Gang Vocals]`) go inside or next to a section tag and stay sparse; see `references/suno-notes.md`. Do not paste performance directions as sung lines.
- Apply phonetic respellings **in the Suno lyric box only**. If the user also wants streaming/distributor lyrics, give them separately with the standard spelling.
- Lyrics sent to Suno contain only what should be sung. No commentary in the lyric box.
- Offer to save the block to a file. Do not write it unless asked.

## After generation

When the user has a generated track, offer the **sung-vs-written** skill: it separates the vocals, transcribes them, and compares against the lyrics you wrote, so mishearings and dropped lines get flagged for a listen instead of discovered by accident.

## Not in scope

- Copying or closely paraphrasing existing copyrighted lyrics. Write original lines. Fictional or generic examples only.
- Claiming a song "sounds good". You cannot hear it. You can measure it and judge the page.
