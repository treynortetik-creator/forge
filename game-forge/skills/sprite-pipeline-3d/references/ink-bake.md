# The look: engraved "ink" bake vs toon

## Ranked options we tried (at ~150 screen px, silhouette, value bands, outline and palette carry the look; texture detail does not)

| # | Look | How | Verdict |
|---|---|---|---|
| 1 | Toon-shaded albedo | Diffuse -> Shader to RGB -> constant ColorRamp (3 bands: 0.50/0.78/1.0 at 0/0.28/0.62) x albedo -> Emission; inverted-hull outline, -0.012 unit solidify, flipped normals, backface cull, ~1.3 px final | the default; judge beside existing art at 1x in a real fight capture |
| 2 | Palette LUT | per-channel histogram match of the render to a painted reference (`fitlut.mjs`), applied after down-sampling | fit on several directions pooled (S-only left the sides at p90 106 vs 169 front), optionally trim per direction |
| 3 | Project a painting into the model's UVs | from S/SE, keep the generator's texels elsewhere | try if toon reads plastic; not built |
| 4 | Kuwahara filter | compositor node, size 2-3 at 2x | brush feel; confirm it does not smear faces |
| - | Engraved / hatched ink | the section below | the base of both final looks we used (engrave for heroes, sketch for first-biome enemies) |

No Freestyle (~9 min per frame measured, plus wrinkle noise). No baked light rim and no baked glow: engine
filters make halos and impacts.

## The hatch look (`bake_sprites.py --look hatch`)

Per pixel, in the material (Emission only, so what you author is what you get):
1. tone = key-light diffuse x albedo luminance^0.4 x gain 5 (the generator's albedo is dark).
2. FINE tone hatch: one anti-aliased stripe family at -45 degrees, 1.9 screen px pitch, whose WIDTH grows with
   darkness (0 at tone 0.60, 0.70 of the period at tone 0.20, gamma 0.8). Bare paper when lit.
3. CROSS set at 55 degrees, only in the darkest core (tone < 0.20), up to 0.55 of the period.
4. LONG shadow strokes at 20 degrees, 4.7 screen px pitch, tone < 0.11 only.
5. SOLID ink below tone 0.035.
6. Colours: two tokens, paper `#E8DCC4`, ink `#120A10`, mixed by the ink coverage.
Outline = hull RIM only: render the hull alone (constant ink), the body alone, composite body over hull. The
hull then shows only outside the body silhouette and never as crease ink inside folds. Inner contours = a
camera-space normal pass, smoothed (1 screen px), differenced over a +-k px step, thresholded at 0.45, thickened to 1.2 screen px,
kept off the silhouette band.

Stripe coordinates: object Generated coords (bbox-normalised, REST pose), dotted with a per-direction vector that
makes planes containing the view ray, so they project to exact straight screen lines whatever the surface and,
being fixed in the mesh's rest space, ride the body through the clip. `aim_stripes()` recomputes the vector once per
direction from the idle pose. Limitation: it reads the first mesh's bounding box, so join meshes first.

## Super-sampling and the finish

- Bake at SUPER x the cell (4 = 1024 px for a 256 cell; 3 if a bake passes 10 minutes). One frame of the full
  ink bake with line sidecar took ~0.3 s on the stand-in at super 4 and 256 cell (48 frames + sidecars = 15 s);
  the real character's full rebuild (6 clips x 8 directions, gates, skin and region passes) was 6-8 minutes on a 16 GB laptop.
- Finish: AREA average down by SUPER (alpha = 50% coverage so the outline stays crisp; colour = mean of the opaque
  sub-pixels). Never Lanczos for hatch.
- Palette ramp projection: the ramp is a polyline in Lab through five stops (ink, ink-2, ink-3, paper, paper-hot).
  Every opaque pixel is projected to the nearest point on the polyline and quantised to 10 levels along it. The
  hatch look then uses at most ten colours, which is what makes an off-palette audit a pass/fail number instead
  of an opinion. Our audit counted a pixel ON the ramp when within dE 9 of the polyline.
- Alpha floor: alpha 1-3 is a resample residue (a faint rectangle around every trimmed cell); clamp it to nothing.
- Accent colours (we used one acid green for emissive parts) are kept EXACT through the average and the snap
  (a pixel with >= 40% accent sub-pixels becomes exact accent). Not in `finish-frames.mjs`; add it if you need one.

## Darken defining lines, not overall value

A sketch bake read too light. The ask was darker defining lines (silhouette, major form edges), not
thicker. Mechanism: `bake_sprites.py --line-pass` writes `<frame>.ln.png`, the coverage of the hull rim plus the
contour mask at super size. `finish-frames.mjs --line-dark k` pulls exactly those cell pixels toward ink by
k x core(coverage), core = 0 below 0.3, 1 above 0.8, so the anti-aliased fringe keeps its value and the line does
not widen. `LINE_DARK=0` in our build restores the old bake. `linewidth.py` prints the FWHM at game size and the line
contrast so "same width, darker" is checkable. Same call applied to all 3D sketch bakes.

## Looks we kept out of this skill

The graphite sketch look (paper-fill alpha, wobbling stroke breaks, wash) and region-mask retexturing (lift the
face and hands toward paper, bias the coat dark) were built in the original renderer and are game-specific; the
mechanism is the same as hatch with a different token set, noise-broken strokes and per-region tone multipliers
read from a UV mask.
