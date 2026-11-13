# Wave brief template

Copy this into `waveN-<slug>-<date>/WAVEN.md` and fill the brackets. The return checker
(`scripts/wave-pack.py check --brief`) reads the table rows, so keep the row shape. Model it on a brief
that worked: a wave brief for 3D source images, 2D portraits and one repaint ran to about 60 lines.

```markdown
# [Game]: Wave N ([theme, five words])

Game: [one paragraph: genre, camera, look in one sentence, what is off limits]. Why this wave: [the gap it fills].
Every file in `refs/` has its name burned into a grey strip at the top. Ignore that strip.
STYLE target: `refs/STYLE-target-*`. Sources that worked: `refs/FORMAT-*`. Match their framing and finish.

## Rules for every [asset class] image (Part 1)
- [W]x[H] PNG, [transparent | flat #RRGGBB background], subject centred with margin.
- [Camera: 3/4 view about 35 degrees from horizontal, characters face screen-right.]
- [Pose and separation rules: limbs apart from the body, props held clear, nothing touching.]
- [Palette: tokens or "pale warm grey only, no colour"; a reserved colour that must not appear.]
- No text, no signature, no watermark, no frame, no real person's likeness. Original designs only.
- One file per item, named exactly as listed.

## Part 1: [subject]

| File | Look | Silhouette must show |
|---|---|---|
| `exact-name.png` | 1024x1024, transparent. [look in two sentences, with the one distinguishing feature] | [what must read as a black shadow] |
| `exact-name-back.png` | OPTIONAL, 1024x1024, transparent. Same figure from behind. | [shape] |

## Part 2: [subject, perhaps a different size or an opaque background]

| File | Look | Silhouette must show |
|---|---|---|
| `portrait-x.png` | 967x1002, opaque #1A1410. This one IS a painting, so a background is fine. | [framing] |

### Where it shows (for the builder, no model work)
[Table of screen, asset file today, size today, source file in code, what to ship.]

## Checklist before returning
- [Canon check: next to `refs/CANON-*.png`, same costume and features?]
- [Silhouette check against `refs/SILHOUETTES-*.png`: can you name each from a black shadow alone?]
- [Background: flat #RRGGBB, nothing touching the body, no glow baked in.]

## Return
A zip with exactly [N] files named as above, plus one line per file that could not match.
```

## Rules for the table (what the checker parses)
- The FIRST cell of a deliverable row starts with a backticked filename ending `.png`, `.webp`, `.jpg` or `.jpeg`.
  Names starting `STYLE-` or `FORMAT-` are ignored (they are refs).
- On the same row: `WxH` (also `W×H`) is the expected size; the word `transparent` or `alpha` in the first 160
  characters after the name means real transparency is required (unless the word `opaque` also appears); a
  `#RRGGBB` means a flat opaque background of that colour; `OPTIONAL` in the first 200 characters downgrades a
  missing file to a warning.
- Bullets that start with `- ` or `* ` and a backticked name also count.
- Files outside `refs/` and not named in a row are reported as "not in brief".

## Reference hygiene
- Look at every ref and every number in the brief before packing. A brief with a wrong canvas size produces a
  wave of files that all fail the check.
- Layout-only refs from other products are labelled layout-only, and the brief says "copy the layout, never the art".
- A returned wave of "gaps the designer found" works as an appendix batch (batch 5 on the first game): same style
  rules, new files, appended to the spec list so the ingest knows the names.
- For a long batch, let the model finish one part, look, then say "go part 2". The first game's first four batches
  ran this way: heroes and bosses first (highest priority), then enemies and the world, then gifts and rewards, then UI.
- Ask the model, at the end, to list the files it made and anything it could not make. It tells you which ones to look at first.

## Sprite-sheet prompts (a strip of frames)
Rules that earned their place in a test prompt for 4 animation rows of one character:
- One PNG per animation, transparent, frames left to right, each frame exactly [N]x[N], no gaps, borders, numbers or text.
- Same camera and scale in every frame; state the baseline (feet at y = 450 of a 512 cell) and the centre (x = 256).
- Loops must flow: last frame into first. Strike frames are the extreme poses.
- "If you cannot keep the character consistent across frames in one image, generate them one at a time from the
  reference plus the previous frame, then assemble the row yourself. Consistency beats speed."
- Use the character's approved still as the image reference for EVERY call.
- Result of that test: identity was excellent, motion was too subtle (push each frame's pose harder), and several
  figures in one wide image worked better than one frame per image; the ingest does the slicing and registration.
