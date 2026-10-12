# Lyric craft reference

Adapted from the craft-reference in bitwize-music-studio/claude-ai-music-skills (CC0), reorganised and trimmed. Numbers here are the targets that `lyric_meter.py` flags against.

## Rhyme

| Type | What it is | Example |
|---|---|---|
| Perfect | identical sound from the last stressed vowel on | night / white |
| Slant (near) | same final stressed vowel, different ending | night / mind |
| Consonance | same consonants, different vowels | blank / think |
| Assonance | same vowels, different consonants | lake / fate |
| Internal | rhyme inside a line | "the **stone** I **own**, the **bone** I've grown" |

`lyric_meter.py` classifies end-rhyme as **perfect** (identical CMU rhyming part), **slant** (same final stressed vowel only) or **none**, and marks a repeated end word as **repeat**. Consonance and internal rhyme are not measured; that part is your ear.

Scheme patterns:

| Pattern | Effect |
|---|---|
| AABB | stable, immediate resolution |
| ABAB | classic, delayed resolution |
| ABCB | lighter, less pressure (lines 2 and 4 rhyme) |
| AAAX | strong setup, surprise last line |
| AAB | blues: state, repeat, resolve |

### Quality rules for every genre

- Forced rhymes are never acceptable. Do not bend grammar, invent words or pad with filler to land one.
- No self-rhymes, no consecutive lines ending on the same word, no near-identical pairs (mind / mind, time / time).
- Meaning beats rhyme. If the perfect rhyme sounds unnatural, use a slant rhyme or restructure the line.
- Pick a scheme for a section and hold it. No random switching mid-verse. No orphan line that should rhyme and does not.
- Say the lyric aloud as plain prose. If it sounds written rather than spoken for the genre, it fails.
- Mix rhyme types. All perfect can sound like a nursery rhyme; all slant can sound lazy.

### Default scheme and strictness by genre family

There is no universal default. The genre guide in `genres/` overrides this table when it exists.

| Family | Default scheme | Strictness | Note |
|---|---|---|---|
| Hip-hop / rap | AABB | high, multisyllabic and internal rhyme | density through the bar, not only line ends |
| Pop | XAXA (conversational) | low, near rhymes preferred | if it sounds crafted, it fails |
| Rock | XAXA or ABAB | low | imagery and energy over technical rhyme |
| Punk / pop-punk | AABB (loose) | low, half-rhymes are authentic | shoutable, direct |
| Emo | ABAB or AABB | moderate, poetic near rhymes welcome | confessional, sensory |
| Metal | optional | very low | concrete imagery, riff alignment |
| Country / folk | ABCB (ballad stanza) | moderate | storytelling |
| Blues | AAB | moderate | |
| Electronic | repetition over rhyme | minimal | loop a phrase |
| R&B / soul | flexible | low | leave room for runs |
| Gospel | repetitive build | low | call and response |
| Ballad (any) | ABCB or ABAB | moderate | narrative serves the story |

## Line length

| Genre | Syllables per line | Tolerance between matching lines |
|---|---|---|
| Pop / folk / punk | 6-8 | plus or minus 2 |
| Rock / indie | 8-10 | plus or minus 2 |
| Hip-hop / rap | 10-13+ | plus or minus 3 |
| Metal / electronic | varies | flexible |

Verse 2 line N must fit the same melody as verse 1 line N. That is the line-parity check (`--tolerance`, default 2).

Syllables are speech counts from a dictionary. A singer can stretch or elide. Use the count to find the lines that are clearly off, not to enforce an exact number.

## Song length and word count

Too long (about 800+ words) makes generators rush, compress or skip lyrics. Too short gives a track under three minutes, which is fine only if intended.

| Target duration | Non-rap words | Rap words |
|---|---|---|
| 2:00-2:30 | 120-180 | 200-300 |
| 2:30-3:30 | 150-250 | 250-400 |
| 3:30-5:00 | 220-400 | 400-600 |
| 5:00-7:00 | 350-500 | 550-750 |

Add roughly 30 words' worth of runtime per instrumental break or solo (each is about 20-40 seconds). Hard ceiling before presenting: 400 words non-rap, 600 rap, unless the target is 5:00 or longer. Under 200 words: flag as probably too short.

| Genre | Typical structure | Words |
|---|---|---|
| Pop / synth-pop | 2-3 verses, pre-chorus, chorus, bridge | 250-350 |
| Rock / alt | 2-3 verses, chorus, bridge | 250-400 |
| Folk / country | 3 verses, chorus, bridge | 250-400 |
| Ballad | 2-3 verses, chorus, bridge (slower, fewer words) | 200-300 |
| Punk / pop-punk | 2 verses, chorus, bridge (short by design) | 150-250 |
| Electronic | 3 verses, pre-chorus, chorus, bridge, instrumental break | 220-300 |
| Hip-hop | 3 verses, hook, bridge | 400-600 |

To reach a longer runtime: **add sections, not longer sections**. A third verse, a pre-chorus, an instrumental break or a bridge. Do not write 10-line verses or 8-line choruses.

Defaults: chorus 4-6 lines repeated verbatim; bridge 2-4; pre-chorus 2-4; outro 2-4 and not a new verse.

## Section length limits (lines)

Generators rush or drop content from long sections. Trim before presenting. Use `--max-lines` on `lyric_meter.py`.

| Family | Verse | Chorus | Bridge | Pre-chorus |
|---|---|---|---|---|
| Hip-hop | 8 | 4-6 | 4-6 | 2-4 |
| Pop | 6-8 | 4-6 | 4 | 2-4 |
| Rock / indie | 6-8 | 4-6 | 4 | 2-4 |
| Punk / pop-punk / emo | 4-6 | 2-4 | 2-4 | 2 |
| Metal | 4-8 | 4-6 | 4 | 2-4 |
| Country / folk | 4-8 | 4-6 | 2-4 | 2-4 |
| Electronic | 4-6 | 2-4 | 2-4 | - |
| Ambient / lo-fi | 2-4 | 2-4 | 2 | - |
| R&B / soul | 6-8 | 4-6 | 4 | 2-4 |

## Density and pacing

| BPM | Max lines per verse | Topics per verse | Feel |
|---|---|---|---|
| under 80 | 4 | 1-2 | slow, heavy |
| 80-94 | 4-6 | 1-2 | laid back |
| 94-110 | 6 | 2-3 | driving |
| 110-140 | 6-8 | 2-3 | standard rock/pop |
| 140+ | 4 | 1 | fast: short verses, energy over density |

Default to 4 lines per verse unless genre and tempo justify more. At most 1-2 topics per 4-line verse. Prefer two short verses to one dense one.

Red flags: an 8-line verse under 100 BPM; a verse that reads like a list of names or facts; "laid back" in the brief but wall-to-wall syllables; more than 3 proper nouns introduced in one verse; every verse dense with no breathing room.

Fix by adding a verse rather than compressing; give each topic a full couplet to land; re-read at the target tempo.

## Prosody

Match stressed syllables to strong beats.

- Stressed syllables land on downbeats (1 and 3 in 4/4).
- Multi-syllable words keep natural stress: HAP-py, not hap-PY.
- Higher melodic notes pair with emphasised words.
- Stable feelings (resolution) pair with settled rhymes; unstable feelings (longing, doubt) with slant rhymes and unresolved endings. Flip it deliberately when it serves the song.
- Test: speak the line. If the emphasis feels wrong, rewrite.

The stress column from `lyric_meter.py` is the dictionary's view of the spoken line (`/` stressed, `.` unstressed). Single-syllable function words (the, a, and, to) are shown unstressed because singers reduce them. It tells you where the words want the beat; it cannot tell you where the melody puts it.

## Show, don't tell

- **Action:** what would someone do feeling this? "She set his plate and never sat" over "I'm lonely".
- **Imagery:** nouns that can be seen or touched. "Coffee gone cold on the counter."
- **Senses:** sight, sound, smell, touch, taste, body, motion. One sense per line is thin.
- Verses carry the specific detail. Choruses carry the emotional statement. A plain statement can be the point if the song has earned it.

## Verse vs chorus contrast

| | Verse | Chorus |
|---|---|---|
| Lyric | observational, narrative | emotional, universal |
| Energy | building | peak |
| Detail | specific, sensory | abstract, said plainly |

### No verse-to-chorus echo

A verse must not repeat a key phrase, image, or rhyme word from the chorus it feeds, or the chorus loses its punch. Compare the last two lines of each verse (and the bridge) with the first two lines of the next chorus. Flag exact phrases, shared rhyme words, a restated hook, and shared signature imagery. The script checks shared words and shared end words; you judge restated hooks and imagery.

Fix by writing a verse line that creates tension or expectation with different imagery. Verse says "spark", chorus says "start". Complementary, not redundant.

## Hook and title

- Title in the first or last line of the chorus.
- Repeat the title near the start and end of the song.
- Give the title the rhythmic accent and the melodic peak.

## POV and tense

Pick one and hold it. First person is most intimate, second draws the listener in, third gives storyteller distance. Present tense is immediate, past tense is reflective. Do not switch within a section without a reason you could state.

## Pitfalls checklist (quick)

- Forced emphasis; inverted word order to rhyme (Yoda-speak)
- Predictable rhymes (moon / June, fire / desire)
- Pronoun or tense drift
- Too specific (alienating names and places) or too vague (abstractions with no image)
- Twin verses: verse 2 is verse 1 reworded. Verse 2 must advance the story, deepen the feeling or shift the view
- No hook; hook given away early
- Section too long; orphan lines; scheme wrong for the genre
- Filler phrases padding lines
- Inconsistent syllables inside a verse
- Verse-chorus echo
- Invented contractions and unhandled pronunciation (see `suno-notes.md`)

## Refinement pass reference

### Pass 1: Tighten

| Pattern | Before | After |
|---|---|---|
| Filler | "He stood up and spoke the words" | "He said" |
| Redundant modifier | "completely destroyed" | "destroyed" |
| Passive | "The door was opened by her" | "She opened the door" |
| Throat-clearing | "Well, I think that maybe I should" | "I should" |
| Double-saying | "alone and by myself" | "alone" |

### Pass 2: Strengthen

| Pattern | Before | After |
|---|---|---|
| Generic image | "the city at night" | "the bus stop sign buzzing over wet gravel" |
| Abstract emotion | "I felt so lost" | "couldn't find my keys, my name, my street" |
| Cliche | "cold as ice" | "cold as a landlord's smile" |
| Single sense | "the room was dark" | "dark, just the hum of pipes and mildew air" |
| Weak verb | "went across the room" | "cut across the room" |
| Vague quantity | "a lot of people came" | "thirty faces in a room for ten" |

### Pass 3: Flow and ear

| Pattern | Before | After |
|---|---|---|
| Consonant pile-up | "sixth street's strict structures" | "sixth street's sharp edges" |
| Stacked vowels | "she oughta allow our hour" | "she gave us the hour" |
| Transition bump | verse 1 reflective, verse 2 aggressive, no bridge | add a pre-chorus or a transitional line |
| No breath point | 12-syllable line, no pause | split at a caesura |
| Choppy rhythm | "Stop. Go. Wait. No. Run." | "Stop and go, wait, no, run" |
| Syllable mismatch | verse 1 line 8 syllables, verse 2 line 13 | match within plus or minus 2 |
