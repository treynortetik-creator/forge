# The asset library

**Local, license-cleared assets. Reach for these before hitting any network.**

**61 assets, ~20 MB, 100% license coverage.** Every file's license is recorded in `manifest.json`
along with **where that license was verified** — so the license gate in `../SKILL.md` is already
answered before you use anything.

```
library/
├── manifest.json     every file: source, license, where the license was proven, attribution
├── fetch.py          rebuild/refresh. Idempotent. `python3 fetch.py --list`
├── icon.py           pull an icon out of the sets. No network.
├── icons/      3 sets, 10,775 icons  (5.5 MB)
├── ornament/  36 public-domain images (13 MB)
├── textures/   6 CC0 material maps    (652 KB)
└── fonts/      16 woff2 files          (132 KB)
```

---

## icons/ — 10,775 icons, all permissive

| Set | Count | License | Why |
|---|---|---|---|
| `healthicons` | 2,709 | **MIT** | Healthcare and general symbols, 2,709 glyphs |
| `tabler` | 6,232 | **MIT** | General UI workhorse, consistent 2px stroke |
| `lucide` | 1,834 | **ISC** | Clean minimal, good in diagrams |

Stored as Iconify collection JSON (one file per set), **with `info.license` embedded** — the license
travels inside the file rather than being asserted next to it.

```bash
python3 icon.py --sets                      # what's installed
python3 icon.py --search chart               # find a name across all sets
python3 icon.py --search elderly --set healthicons
python3 icon.py tabler:chart-bar                        # SVG to stdout
python3 icon.py tabler:chart-bar --color '#1f2937' --size 32 -o out.svg
```

Icons emit `currentColor` and `width="1em"` by default, so inlined in HTML they inherit CSS color and
font-size. Pass `--color` only when the SVG has to stand alone.

## ornament/ — 36 public-domain images, 1600px WebP

Botanical plates, textile and wallpaper patterns, illuminated manuscript folios, Japanese woodblock
prints. **All CC0 or public domain**, from the Cleveland Museum of Art and the Art Institute of
Chicago. No attribution required (a courtesy credit line is in the manifest anyway).

**This is the anti-slop layer.** A real 18th-century botanical plate or a real textile pattern at low
opacity carries provenance the eye reads as *made*. A CSS gradient does not.

AIC entries carry an `iiif` field — re-crop or re-size any of them server-side at any time without
re-downloading.

## textures/ — 6 CC0 material maps, 1024px

Paper, fabric, concrete, plaster, wood, marble. From **ambientCG**, CC0.

⚠️ **The ambientCG API carries NO license field.** The blanket CC0 is stated on
<https://ambientcg.com/license> and `fetch.py` re-reads that page and aborts if the wording changes.
**Do not cite the API for the license.**

Each manifest entry has a `full_pbr` URL for the complete normal/roughness/displacement set when a
Blender scene needs real materials.

## fonts/ — a complete house stack, offline

`poppins-{300,400,500,600,700,800}.woff2` · `open-sans-variable.woff2` · `roboto-variable.woff2`.
All OFL. Latin subset. Open Sans and Roboto ship as variable fonts, so one file serves every weight.

🔴 **Why this exists: Poppins ExtraBold 800.** A house type scale that calls for 800 on
its display tiers, `h1` and `h2` — while many local `.ttf` builds only go to
700. Offline, **every such headline silently falls back to Bold.** Base64 these into
the CSS whenever a deliverable must be pixel-perfect without a network.

---

## 🔴 Rasterizing SVG — a real trap, verified 2026-08-07

`python3 icon.py tabler:chart-bar` produces an SVG that renders **correctly in Chrome and
`rsvg-convert`** and produces a **blank transparent PNG, exit code 0**, through both:

```bash
magick icon.svg -resize 96x96 out.png            # BLANK
inkscape icon.svg --export-type=png ...          # BLANK, exits 0
```

Controls run: a hand-written circle renders in Inkscape; a single path lifted out of the icon renders;
`<g fill="…">` inheritance renders. **Root cause not identified** — something in the combined path
data. The rule stands regardless:

```bash
rsvg-convert -w 96 -h 96 icon.svg -o out.png     # ✅ correct
# or inline the SVG in HTML and screenshot with headless Chrome
```

**Never trust an exit code for SVG rasterization. Look at the pixels.** Same family as
`soffice --convert-to` exiting 0 on failure.

---

## Refreshing

```bash
python3 fetch.py all                 # everything missing
python3 fetch.py ornament --force    # re-pull a category
python3 fetch.py --list
```

`fetch.py` will not write a file whose license it cannot establish, and prints a license-coverage
count at the end. An early version happily wrote the three bytes `404` as an "icon set" and reported
success, so it now **parses and validates every payload before writing it.**

**The quality gate is a first pass, not a judgment.** It rejects slivers, near-blank sheets, and
museum objects shot on seamless studio backdrops (smooth mid-tone corners). It cannot tell you whether
an image is *good*. After any `ornament` refresh, montage the result and look at it:

```bash
magick montage ornament/*.webp -tile 7x -geometry 200x200+5+5 -background '#141413' /tmp/sheet.png
```

The first curation pass shipped 45 images; the contact sheet showed roughly a quarter were porcelain
and jade objects on grey backdrops. The gate now catches most of them and four more were cut by hand.

---

## Why the binaries are committed rather than rebuilt

`fetch.py` is reproducible in the sense that it runs the same queries — but the museum APIs return
**different results over time** (sort order shifts, new acquisitions land). Re-running `fetch.py
ornament` on a fresh clone would produce a different 36 images than the ones `manifest.json`
describes.

So the assets are committed (~20 MB, one time). That keeps the manifest an accurate description of
what is actually on disk, which is the whole point of the license record. Refresh deliberately, look
at the contact sheet, and commit the new state.
