# Sprites: prompts, references, prep

A clay-sprite explainer is one transparent PNG per object, placed by `sprite(parent, name, x, y, h)` and moved by the
timeline. No mask work, no hand cutouts: the image tool is asked for a real alpha channel, a script trims it.

## The batch, in order
1. **Style header** (`prompt-header.txt`): the material, palette, light, framing and transparency rules. Identical for
   every sprite in the project. Edit it once, then run everything through it.
2. **Item list** (`items.example.json`): one line per object. `python3 scripts/sprite_prompts.py --items items.json --out prompts`
   writes `prompts/<name>.txt` (header + item) and `prompts/index.json`. Keep `prompts/` in the project: a sprite
   you must redo next week should be one command, not a memory.
3. **Reference-image attachment pattern.** Attach 1 to 3 images to EVERY request: the approved style frame, one finished
   sprite of the same kind of object, and (for a character) its sheet. The prompt says what to take from them
   ("material, palette, lighting, proportions") and what not to ("not the pose, not the layout"). Without attachments
   the look drifts after the third sprite; with them it holds. Name the attachments inside the prompt.
4. **Generate** with whichever image tool you have and can afford. Test ONE sprite side by side with a second route
   before paying for the batch; check the cost plan first. Label every image you show the owner.
5. **Prep** (`scripts/prep_sprites.py --src raw --out img --heights sprites.json`): trim to the alpha bounding box
   (alpha under 24 ignored), size to the largest on-screen height x 1.6 (camera zoom), WebP quality 88. Write the height
   table from your storyboard: for each sprite, the biggest `h` you pass to `sprite()`.
6. **Look at them on the page's paper colour** before building scenes: halos, a baked shadow, a floating base.

## Rules that held up
- A fresh sprite is placed by its CENTRE x and BOTTOM y. Trim first, or "bottom" is a lie.
- One shared set of sprites for the whole video: the camera moves over one set instead of drawing a new set per shot.
- Sprites that must touch (a token on a belt) are generated at the same scale and light, then sized by the height table.
- Ask for the object only. Backgrounds, floors and shadows are made on the page (`.sh` disc, `#grain` filter).
- Text inside a sprite is never legible after a downscale and may be misspelled. Put text on the page.

## Your character (keep one on-model)
The templates in this folder are neutral. A ready-made house style lives in `styles/` and a bundled mascot in
`mascots/` (see their READMEs). If your project has its own recurring character, write it down once
as `character.txt` and keep these habits:
- **Describe it in words in every prompt** (head, face, body, colours, proportions, one signature item). Do not rely on
  the reference image alone: references carry pose, words carry identity. `sprite_prompts.py --character character.txt`
  appends the block to every item listed under `"characters"` in `items.json`.
- **A character sheet first**: front, three-quarter, side, a few expressions, one neutral pose. Approve it, then
  attach it to every later request.
- **Fix the neutral**: say "calm, closed-mouth smile, eyes open" so the default is not laughing.
- **Check scale against the props** on a chart before the batch: a character that is the same height as a door is a
  re-do.
- **One accessory is the tell** (a scarf, a hat): keep its colour and silhouette identical.
- **Judge on the page, small**: an off-model character is obvious at 360 px tall; check the contact sheet, not one big render.
