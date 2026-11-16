# Directing a cloud TTS narrator (ElevenLabs)

Use this when the narrator is a cloud voice instead of the local cloned voice in `voice.md`. It exists because of
lesson 44: a story narration generated as seven separate clips changed tone at every scene change. Everything marked
DOCS was read on the vendor's own pages on 2026-11-16. Models and limits change; re-check before relying on it.

## One-take recipe

1. Write the whole narration as one text and keep it under the model's limit (table below).
2. Pick the model first. The vendor's docs call Eleven v4 the current flagship and Eleven v3 the previous generation;
   the prompting rules below are written for v4 and the docs say they also apply to v3. (DOCS)
3. Audition the voice on a paragraph that uses the tags you plan to use. Tags depend on the voice: one with a narrow
   range ignores them. (DOCS, vendor blog)
4. Direct delivery inline with audio tags in square brackets, for example `[whispers]`, `[quietly]`, `[sighs]`.
   Use few. A tag colours the words after it, so put it where the change starts. (DOCS)
5. Make pauses with punctuation and layout: an ellipsis adds "pauses and weight", a line break gives a longer beat,
   and the vendor blog also lists a `[pause]` tag. SSML `<break>` tags are NOT supported on v4 or v3. (DOCS)
6. Capital letters add emphasis; ordinary punctuation sets the rhythm. (DOCS)
7. Generate the whole script in ONE request with the with-timestamps endpoint, so you get the audio and the time of
   every character back together.
8. Cut scenes from that single take: find each scene's first and last character in the text, read their times from the
   alignment, cut there, and pad with silence in the edit, never by re-generating.
9. Listen to the joins. If one line is wrong, fix the text and re-record the whole take, not one scene.

## Pauses and tags by model

| Method | Eleven v4 | Eleven v3 | Older models (v2, Flash) |
|---|---|---|---|
| Audio tags `[like this]` | Yes (DOCS) | Yes (DOCS) | Not documented |
| SSML `<break time="1.5s" />` | No (DOCS) | No (DOCS) | Documented, "up to 3 seconds"; models not named |
| Ellipsis | Yes (DOCS) | Yes (DOCS) | Works, "less consistent" (DOCS) |
| `[pause]` tag | Listed in the vendor blog | Not confirmed in docs: test it | Not documented |
| Line break for a longer beat | Vendor blog | Not confirmed: test it | Not documented |

## Limits per request (DOCS, models page)

| Model | Characters |
|---|---|
| Eleven v4 (`eleven_v4`) | 10,000 |
| Eleven v3 (`eleven_v3`) | 5,000 |
| Multilingual v2 | 10,000 |
| Flash v2.5 | 40,000 |
| Text-to-dialogue endpoint | 2,000 in total |

A 2-minute narration is about 300 words, roughly 1,800 characters: it fits in one request on every model above.

## Timestamps (DOCS, with-timestamps endpoint)

The response carries `audio_base64` and an `alignment` object with `characters`, `character_start_times_seconds` and
`character_end_times_seconds` (plus a `normalized_alignment`). The page does not say which models support it. Test on
your model with a short text before the real take.

## If you must split a long text

The API offers `previous_text`, `next_text`, `previous_request_ids` (up to 3) and a best-effort `seed`. The docs say
not every model supports them and do not say which. On our run, `eleven_v3` rejected `previous_text` and `next_text`,
which is why the scene clips drifted. Split only when the text is over the limit, split at paragraph ends, and check
the joins by ear.

## Not found in the docs on that date

Names and effects of the stability modes, a minimum prompt length, and any guidance on tone drift across a long
narration. Treat anything you read about those elsewhere as unverified.

## Spend

Paid per character. Write the cost plan first (characters, takes, a cap) and audition on one paragraph, as lesson 24
says.

## Sources

- https://elevenlabs.io/docs/best-practices/prompting
- https://elevenlabs.io/docs/overview/models
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
- https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert
- https://elevenlabs.io/blog/v3-audiotags
