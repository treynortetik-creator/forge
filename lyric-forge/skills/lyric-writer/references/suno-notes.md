# Suno and AI-singer notes: tags, style box, pronunciation

Practical notes for generators in the Suno family. Model behaviour changes between versions; treat limits and tag behaviour as "last observed", and re-check against the current generator when it matters. Nothing here is a guarantee of how a generator will sing a line.

## The three fields

| Field | What goes there | Limit (approx.) |
|---|---|---|
| Style | how it sounds | about 1000 characters on recent models; older models allow less |
| Exclude styles | what it must not sound like | short list |
| Lyrics | only what should be sung, plus section tags | keep under roughly 400 words (800+ makes the generator rush or skip) |

### Style box formula

Genre + mood + era or feel + tempo and key + vocal persona + instruments + production + dynamics arc.

| Weak | Better |
|---|---|
| "sad rock song" | "mid-tempo indie rock, wistful, late-90s feel, 112 BPM, A minor, close-mic'd male vocal with a slight crack, clean arpeggiated guitar, round bass, brushed-then-open drums, builds from sparse verse to full chorus" |

- Describe the journey, not just the genre: "sparse piano verse, full band chorus, strips back to one voice at the end".
- Build a vocal persona, not just a gender: register, texture, how it changes across the song.
- Specify BPM and key when you care.
- **No artist names or trademarks.** Describe the sound ("early-2000s pop-punk with gang vocals") instead.
- Unexpected genre pairings can work; one or two, not five.
- Put the most important descriptors first.
- Count characters before you hand it over, and state the count.

### Exclude styles

Name what would ruin it: instruments, genres, vocal types ("no autotune, no rap verses, no synth lead"). Keep it short and concrete.

## Section tags in the lyric box

Standard structure tags:

`[Intro] [Verse 1] [Pre-Chorus] [Chorus] [Post-Chorus] [Bridge] [Interlude] [Instrumental Break] [Guitar Solo] [Breakdown] [Outro] [End]`

Cues (use sparingly, typically inside or beside a section tag):

| Kind | Examples |
|---|---|
| Vocal | `[Whispered]` `[Spoken Word]` `[Belted]` `[Falsetto]` `[Raspy]` `[Gang Vocals]` `[Harmonies]` |
| Dynamics | `[Building Energy]` `[Explosive]` `[Quiet arrangement]` `[Slow Down]` |
| Atmosphere | `[Melancholic]` `[Intimate]` `[Dark Atmosphere]` |

Practice:

- A handful of cues per section at most. Tag clutter confuses more than it helps.
- Put the key cue in the section tag itself (`[Verse 1 - Whispered]`) if the generator ignores standalone cue lines.
- Instrumental tags add roughly 20-40 seconds of runtime each; budget for them.
- Do not put commentary ("sing this softly") in the lyric box as plain text; it may be sung.
- Cues work best when the style box says the same thing.

## Pronunciation

The generator reads the spelling literally. Context does not disambiguate. Fix pronunciation by changing the spelling **in the Suno lyric box only**; keep standard spelling in any distributor or streaming copy.

| Type | Standard | Write as |
|---|---|---|
| Names | an unusual surname | syllables joined by hyphens, stressed syllable in capitals when needed: "Roh-MAY-nee" |
| Acronyms | GPS | G-P-S |
| Tech terms | SQL | sequel (or S-Q-L, pick one and keep it) |
| Numbers | ninety-three | '93 or spell it |
| Homographs | live (verb vs adjective) | lyve / liv |
| Stretched vowel | sing a long note | spell the vowel long in the held syllable ("lo-o-ove") sparingly |
| Stuttered or chopped | | hyphenate: "I-I-I know" |

Rules:

1. **Homographs need an explicit decision** from the user, recorded. "The context makes it obvious" does not work; the generator picks one reading and keeps it every regeneration. Ask in one batched message with both readings listed; do not ask word by word.
2. Common homographs to catch: live, read, lead, wound, close, bass, tear, wind, row, bow, sow, minute, desert, present, record.
3. **No invented contractions.** Only standard pronoun/auxiliary contractions are safe (they'd, you'd, wouldn't). `signal'd`, `TV'd`, `network'd` get mispronounced or skipped. Write "signal would".
4. **Apply respellings everywhere** the word appears: every verse, every chorus repeat, the bridge. Missed instances are the usual failure. Search the draft for each respelled word after editing.
5. Keep a small table of respellings in the performance notes (original, respelling) so the next edit does not undo them.
6. Prefer rewriting a line to avoid a risky word over respelling it, when the line is no worse for it.
7. Phonetic respellings add syllables the dictionary cannot see; expect `~` marks from `lyric_meter.py` on those lines and treat the counts as plus or minus one.

### After generation

Generators still mishear their own lyrics and drop lines. Use the **sung-vs-written** skill on the finished track to find the lines worth a listen.
