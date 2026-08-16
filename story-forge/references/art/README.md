# Illustration notes

Working notes for the illustrated side of a book, alongside the craft notes in `../writing/`.

**`character-anchors.md`** is the one that matters. It is the fix for character drift across
separately-generated illustrations — clothes changing colour between spreads, haircuts changing,
objects coming out malformed.

Two things in it are worth knowing before you generate anything:

1. **The cause is usually the character sheet, not the model.** A sheet controls only the attributes
   it enumerates; everything unstated is re-rolled on every call. Audited on a real 13-spread book:
   zero of eleven spreads specified a garment colour, and the mother's entry described her hair and
   face but gave her no clothing at all.
2. **Generate the whole cast in ONE image.** Characters painted in a single pass share one attention
   context, so they share brushwork and detail level. Generated separately, they arrive looking like
   they came from different books.

Written 2026-08-16 from a real diagnosis and fix, not from theory. Every provider-specific detail in
it was verified against the actual tool.
