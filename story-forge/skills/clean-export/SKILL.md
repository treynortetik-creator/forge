---
name: clean-export
description: Final export step for any manuscript. Strips invisible provenance characters (zero-width, bidi, Unicode TAG payloads, exotic spaces) without touching a single word. Run it on anything before it leaves the machine. Use when the user asks to clean, export, or finalize a draft, or mentions watermarks / invisible characters / AI provenance marks.
---

# clean-export

**The last thing that touches a manuscript before it leaves.** It removes characters a reader
cannot see and never alters the writing.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py draft.md                    # report only
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py draft.md -o draft.clean.md  # write a copy
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py chapters/ -o out/           # whole directory
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py draft.md --in-place         # overwrite (+ .bak)
```

Stdlib only, no dependencies. Report mode is the default — it writes nothing unless you pass
`-o` or `--in-place`.

## What it removes

| Class | Examples | Why |
|---|---|---|
| **Zero-width** | ZWSP, ZWNJ, word joiner, BOM, soft hyphen | invisible, and the cheapest place to hide a signal |
| **Bidi controls** | LRM, RLM, RLO, isolates | invisible; RLO can also disguise text direction |
| **Unicode TAG chars** | `U+E0000–E007F` | ⚠️ **an entire ASCII message can be encoded here, fully invisible** |
| **Exotic spaces** | NBSP, thin, hair, narrow-NBSP, ideographic | visible-ish, and a well-known machine-text tell → normalised to a plain space |
| **Any other `Cf`** | anything invisible we didn't name | catch-all, reported by its Unicode name |

**Preserved by default: ZWJ and variation selectors.** They are also a hiding place, but removing
them visibly breaks emoji (👩‍💻 → 👩💻). Pass `--strip-emoji-glue` if you want them gone and the
document has no emoji.

## 🔒 The guarantee, and how it is enforced

The script computes `canon()` — the text reduced to only characters it never touches — for the input
and the output, and **refuses to write if they differ.** So a bug cannot silently edit prose; the
worst case is it declines to run.

> ⚠️ That guard has already earned itself. During development an earlier version of the *check*
> was wrong (it compared whitespace-split tokens, and a zero-width character glued to a word makes a
> different token). It produced a false failure and **refused to write.** The guard was wrong and it
> still failed safe. Keep it that way.

## 🚫 What it deliberately does NOT do

**It does not remove statistical / token-choice watermarks** — the kind Claude applies to models
launched on or after 2026-08-02 under EU AI Act Article 50.

That signal lives in *which words were chosen*, so the only way to strip it is to rewrite the text
with another model. **For fiction that is exactly backwards:** the whole point of
[`de-sloppifier`](../de-sloppifier/SKILL.md) is to make prose sound like the author, and a
model-based "watermark removal" pass pushes it straight back toward the machine register.

**The de-slop + hand-edit pipeline is already the better remover.** Anthropic's own documentation
concedes the mark only *"may persist through some editing"* and that heavy editing, paraphrasing or
mixing renders it undetectable. Three substantive passes plus an author's edits rewrite enough tokens
to degrade it — and unlike a rewrite pass, that work *improves* the prose.

Also worth knowing, from the same source: a detected mark *"provides a signal that content was
processed by Claude, but is not fully conclusive."* Even a proofread leaves a trace, so the mark
cannot distinguish *written by AI* from *checked by AI*.

## Where it sits in the pipeline

```
braindump → dossier → outline → draft → story-hacker → de-sloppifier → edit-pass → CLEAN-EXPORT
```

Always last. Anything earlier and later steps re-introduce characters.

## Related
- [[de-sloppifier]] — the three-pass voice cleanup; the real watermark degrader
- [[edit-pass]] · [[voice]] — the passes immediately before this one
