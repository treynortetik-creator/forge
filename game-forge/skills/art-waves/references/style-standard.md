# Writing a style standard the model and the builders can obey

A style standard is the document every brief links to. These rules come from two standards (a painted
dark-fantasy one for the roguelite, a moonlit toon one for the tower-defense game), and from the bible that replaced
the first. No canon here, only structure and the rules that proved themselves.

## Sections a standard needs
1. **Status line.** Date written, what it supersedes, what supersedes it, and "when this file and an older prompt
   disagree, this file wins".
2. **Reference images** by job (overall look, world lighting, UI metal, icons, props, busts), with file paths.
   Pass one or two as image references on EVERY model call. Receipt: references are the strongest consistency lever
   you have; a prompt alone drifts.
3. **Rendering style** in plain words, plus a negative list (see below).
4. **Palette** as a table of role, hex, use. Rules beside it: which hues never colour which surfaces (for example,
   a world-magic colour never colours menu chrome), no pure white except tiny glints, no cool grey (warm neutrals read
   as game, cool neutrals read as phone UI).
5. **Lighting** per context (UI icons, world, hub, characters). One key direction for all UI.
6. **Outline and edge** weight as a percentage of image size (about 1 to 1.5%, 3 to 4 px at 256), and "never a single
   flat stroke as the only edge on code-drawn shapes: bevel it".
7. **Perspective** per asset type. The roguelite's table: floors and floor decals straight down and tiling; walls
   in front elevation strips tiling left-right; props, doors, characters 3/4 at about 35 degrees from horizontal,
   verticals upright, characters facing screen-right; hub props in the hub's own camera and turned to the surface they stand
   on; UI icons flat to camera. The tower-defense game's equivalent: orthographic camera pitched 35 degrees
   (Blender camera rotation X 55), fixed everywhere, directions are yaw rotations of the model, never camera moves.
8. **Icons**: a small number of families (never invent another), display size to source size table, safe areas.
9. **Frames and panels**: built from painted kit pieces, nine-sliced; stretch only the mid sections, tile long rails.
10. **What a placeholder is** (section 11 of SKILL.md) and the grading scale.
11. **Image-model recipe**: model, quality, aspect, references, cost, procedure.
12. **Acceptance check** every asset passes before it ships.

## Icon sizes (the roguelite's table)
| Display size | Source | Subject fills | Notes |
|---|---|---|---|
| 16 to 32 px (HUD) | 256, shipped at 128 | 90% (trim padding) | one silhouette, high value contrast, a rim light so it holds on the UI colour |
| 40 to 64 px (buttons, rows, cards) | 256 to 512, shipped at 256 | 80% | the main tier |
| 96 to 240 px (detail panes) | 512 | 80% | full detail allowed |
| Portraits | 1024, chest-up | head in the top third | must crop to a roundel without cutting the face |

Transparent PNG, centred, no text, no baked ground shadow (the game adds one). Test every icon AT ITS DISPLAY SIZE on
the real background; if it turns into a smudge or a squiggle it fails. Pick icons from the data of the thing they
represent, never by slot or position. Icons everywhere or icons nowhere on a given menu type.

## The prompt template (fill the brackets)
```
[SUBJECT, one concrete sentence: material, shape, one distinguishing detail].
A [style words] game [icon | prop | portrait] in exactly the painting style, palette and line weight of
the reference image: [tone words], a crisp dark rim around the silhouette, [key light direction],
small bright specular glints. [VIEW]. A bold silhouette that reads at [N] px.
Transparent background, the subject centred and filling about [80|90]% of the frame.
No text, no letters. Original design.
Avoid: [NEGATIVE].
```
VIEW by asset type: emblem "straight on, flat to the camera"; room prop "3/4 top-down about 35 degrees from
horizontal, front-facing, verticals upright"; floor item "seen straight down, lying flat"; portrait "chest-up bust,
three-quarter turn, head in the upper third" (image-to-image from the in-game sprite so face and costume match).

NEGATIVE (the API has no negative field, so it goes in as an `Avoid:` sentence): flat vector, clip art, emoji,
icon font, line art only, flat fills, cel shading, cartoon mascot, chibi, big cute eyes, anime face, photo, 3D render,
plastic, neon, pastel, cool grey, pure white, light or white background, a square tile or card behind the subject,
extra frame or border, text, letters, numbers, watermark, logo, multiple objects, cropped edges, motion blur, noise,
posterized banding. (Remove "text" from it when you WANT lettering, and then spell the lettering out.)

## Faction and value rules from the tower-defense standard
- Readability first: the player's units wear one colour family, the opposing wave another; one deliberately
  different unit carries a trim colour so it never reads as the wrong team.
- The map sits mid-to-dark; units are one step lighter on their lit side and always carry a rim light so they pop
  off the ground; UI is the lightest value on screen.
- Shading: toon, three value bands plus the rim, no photoreal gradient, one hard specular ping on metal and eyes.
- Emissive accents (eyes, lanterns, brew) are the only saturated highlights.

## The ink-and-paper bible's rules, generalised (a restricted-palette style)
- Ink and paper only; every other colour on screen is a bug unless a table allows it.
- Solid silhouettes: every character is one solid shape with a fixed outline weight that reads as a blob at its
  smallest display size. Line weight ladder (characters heavier than props heavier than walls, floors none) measured at 1x.
- Quiet floors: mostly bare paper; cross-hatching only in the shadow band under walls.
- Line direction separates layers (characters on the diagonal, stone along its courses).
- Light is the absence of ink.
- Telegraphs are shapes, not colours (hatch fill plus a hard border), so they work for colour-blind players.
- Every colour has a meaning and ships in three tones.
- Hard-to-tell pairs get a written fix (a table: pair, problem, fix) and a colour-blind filter test.
- Exemptions stated up front (the hub and the portraits were in full colour; the rules applied to runs).
