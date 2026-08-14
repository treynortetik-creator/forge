---
name: art-department
description: >
  The visual-deliverable playbook. Load this BEFORE making anything a person will
  actually look at: HTML report, deck slide, diagram, cover image, site, social
  asset, video, cue card. Covers the decision tree (which tool for which job), the
  verified free asset sources, the OpenRouter image/video models with real costs,
  the local toolchain (Blender, Inkscape, ImageMagick, Graphviz), the house style
  that keeps output from looking like AI slop, and the license gate. Triggers:
  "make this look good", "design", "visual", "slide", "diagram", "image",
  "render", "cover", "asset", "brand", "wow factor".
---

# Art Department

**The standing order:**

> *"if you're able to create 3D objects that we could have been putting into our HTML files… everything
> that we've done to this point could have looked substantially better."*
>
> *"Be sure, for this software, that you figure out ways for yourself to interact with them on your
> own… I don't want to have to learn to use new software! These would be tools that you would
> leverage, not me."*

**He never opens these tools. You drive all of them.** He looks at the output.

And 2026-08-07: *"I just want to make our shit look good and look nice and crisp and just have wow
factors to it."*

---

## 🔴 The one rule that changes the most

**Source before you generate.** The AI-slop look does not come from bad taste. It comes from
*synthesizing* every pixel: CSS gradients standing in for texture, a generated illustration standing
in for a real object, a Mermaid box standing in for a diagram.

A real CC0 botanical plate from the Cleveland Museum, a real concrete texture at 8% opacity, a real
traced vector — these carry provenance the eye reads as *made*, not *emitted*.

## 📦 START AT `library/` — it is already on disk and already license-cleared

**61 assets, ~20 MB, zero network calls, 100% license coverage** (`library/manifest.json` records the
license AND where it was verified, per file).

```
library/icons/     10,775 icons — healthicons (2,709 MIT), tabler (6,232 MIT), lucide (1,834 ISC)
library/ornament/  36 public-domain botanical plates, textiles, wallpaper, manuscripts, woodblocks
library/textures/  6 CC0 material maps — paper, fabric, concrete, plaster, wood, marble
library/fonts/     a complete house stack as woff2, including the Poppins 800 most kits omit
```

```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/art-department/library/icon.py --search chart                             # find an icon
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/art-department/library/icon.py tabler:chart-bar --color '#1f2937'     # emit the SVG
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/art-department/library/fetch.py all                                      # refresh / extend
```

Read `library/README.md` for the SVG-rasterization trap before you convert any icon to PNG.
Only go to `references/asset-sources.md` when the library does not already have it.

---

## The decision tree

| I need… | Reach for | Not |
|---|---|---|
| A chart in a report | **Hand-authored inline SVG** (`viewBox`, `<rect rx=6>`, one bar in accent) | Chart.js, a CDN, a generated image |
| A system/architecture diagram | **Graphviz** `dot -Tsvg` (big graphs) or **hand SVG** (<12 nodes) | Mermaid on anything branded — it reads "Windows 95" |
| Depth, a hero object, a texture with real light | **Blender** → render → optionally **Inkscape** `object-trace` → vector | A CSS `box-shadow` approximation |
| A photographic background / material / HDRI | **Poly Haven** or **ambientCG** (CC0, keyless) | Generating one |
| An icon | **Iconify** (326k, per-set SPDX; `healthicons` = 2,709 MIT) | Generating one, or SVG Repo |
| Ornament, pattern, botanical, editorial texture | **Cleveland / AIC / Smithsonian / Wikimedia** (CC0 or PD) | A generated "vintage-style" image |
| A photo of a real person, **product/marketing** work | ⭐ **Your own cleared photo library**, if you have one. Record each subject's crop position once and look it up; faces cut at the chin is the most damaging defect available and it is invisible in the source | Stock, when you own releases already |
| A photo of a real person, work in a **different register** | 🔴 **Usually nothing. Don't.** A product photo library carries the register it was shot for, and reusing it off-domain reads as a category error. Reach for type, texture, ornament or a diagram instead | Product photography borrowed into an unrelated context |
| A photo of a real person, anything else | **Keyed stock, non-identifiable framing.** See the privacy note below | Generating one. Museums have nothing modern |
| An illustrated scene | **illlustrations.co / IRA Design** (MIT) or **DiceBear Open Peeps** (CC0) | unDraw (license bars automation), Absurd Design (non-commercial) |
| A stylized image that must not exist anywhere else | **OpenRouter image models** — `references/generation-models.md` | Stock |
| Motion where the SUBJECT moves | **OpenRouter `/videos`** (Seedance/Veo/Kling) | Blender camera-push. That gets caught immediately: a zoom-in/zoom-out is not animation, it is a pan over a still |
| Motion where only the CAMERA moves | **Blender** 2.5D displacement — free, instant, no API cost | Burning $0.75 on a video call |
| Music / audio bed | **Free Music Archive** — but read the license gate below | Assuming FMA is crawlable. It is not |
| A branded HTML deliverable | A templated converter with your brand baked in, so the tokens cannot drift per-document | Hand-rolling the brand each time |

**Full command reference and every gotcha that will otherwise cost an hour:
`references/asset-sources.md`. Read it before writing Blender or Inkscape code.**

---

## The three reference files

- **`references/asset-sources.md`** — every verified third-party source, its endpoint, whether it
  needs a key, its license, and the traps. Verified 2026-08-07.
- **`references/generation-models.md`** — OpenRouter image + video, live model IDs, real observed
  costs, the request shapes that actually work.
- **`references/house-style.md`** — the visual rules. This is the "wow factor" file.

**Start of every branded visual task:** find the real brand assets before you make anything. Logos,
type stack, tokens, and any approved photography should come off disk or out of the brand system, not
out of your memory of what the brand looks like. **Stop approximating the brand** — an approximated
logo is the single most obvious tell in a deliverable.

> Keep your own house brand in a `references/house-brand.md` beside this file: the real logo files,
> the token values, the type stack, and the hard rules ("never on a busy background", "never recolour
> the mark"). It is deliberately not shipped with this plugin, because a house brand is yours.

---

## 🔴 The license gate — run it every time, before the asset lands in a deliverable

**Scope:** third-party assets only. Your own organisation's brand assets, used within that
organisation, are already cleared. Everything from a museum, a stock site, an icon set, or a music
library still runs the gate.

Four questions, in order. Any "no" and the asset does not ship.

1. **Do I know the license for THIS item?** Not for the site. Per item. Mixkit, SVG Repo, Wikimedia,
   Wellcome and Internet Archive all mix commercial-OK and NonCommercial in one catalog.
2. **Does it permit commercial use?** Almost all professional work is commercial. NC is out. ND blocks cropping,
   recoloring, and compositing, which is most of what we do.
3. **Does it require attribution?** If yes, the credit line goes in the deliverable, not in a note to
   add later.
4. **Is a real person identifiable?** If yes, stop. See below.

### The rule that has no license workaround

**No third-party source in this stack provides model releases.** Pexels states the responsibility
"rests solely and exclusively with you." Coverr obtains them and will not hand them over.

**This is exactly why an owned, cleared photo library matters.** If your organisation has shot and
released its own people, those frames are the right answer for any deliverable that needs a person in
it. If it has not, the honest answer is usually to use no person at all.

**An identifiable face placed next to language about a health condition, a financial situation, or a
legal matter implies that fact about a real person.** That is a privacy exposure a stock licence does
not cure, whatever the sector.

**Default to non-identifiable framing** — hands, a doorway, a window, over-the-shoulder, depth of
field, backs of heads. It is also, consistently, the better photograph.

---

## 🔴 Verify by looking. Always.

You cannot judge a visual deliverable from the code you wrote. **Render it and read the PNG.**

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --virtual-time-budget=3500 --window-size=1240,3000 \
  --screenshot=/tmp/check.png "file:///abs/path.html"
```
Then `Read` the PNG. Force `.reveal{opacity:1!important}` in a temp copy so scroll-reveal content
appears in a static shot.

### 🔴 "Look at it" is not enough. Run this checklist against the screenshot.

Earned 2026-08-07: I rendered a page, **looked at the screenshot, and shipped it with both subjects'
heads cropped off.** It was spotted in about two seconds. The gate ran and I still
missed the most obvious defect on the page, because I was checking whether my code worked instead of
looking at what was actually there.

1. **Faces.** Is every head fully in frame? A portrait photo in a landscape box with `center/cover`
   crops faces by default. Set `background-position` deliberately (`center 30%` for a standing shot),
   or pick a photo whose aspect matches the box.
2. **Edges.** Is anything clipped, running off, or touching a boundary it shouldn't? (`viewBox`
   overflow silently ate a target pill and a whole year-totals row on 2026-08-06.)
3. **Empty space.** Does the page end well above the fold with dead space below it?
4. **Text.** Any overflow, orphan word on its own line, or overlapping label?
5. **Did every asset actually load?** A missing base64 leaves a blank box, not an error.
6. **Squint at it.** Blur your reading and check the hierarchy still works. What draws the eye first —
   is that the thing that should?

**Look at the artifact as a viewer, not as its author.** A screenshot that proves the code ran is not
the same as a screenshot that proves the thing is good.

**For a Blender render:** the `blender` MCP (port 9877) takes viewport screenshots. Look before you
commit to a 96-sample Cycles run.

---

## Cost discipline

- **Local toolchain is free and instant.** Blender, Inkscape, ImageMagick, Graphviz, DuckDB. Exhaust
  these first.
- **Museum + CC0 APIs are free.** Six of the eight primary sources need no key at all.
- **Image generation is cheap** — fractions of a cent per image. Not worth asking about.
- **Video is not.** A 5-second 720p Seedance clip billed **$0.756** against a $0.34 sticker. Budget
  **2× the advertised per-second price.** Four clips ≈ $3, which is over the $1 dry-run threshold —
  **quote the real number and ask first.**

---

## Related

- `references/asset-sources.md` — the verified command reference and every gotcha
- `memory/reference/artifacts/2026-08-07-free-asset-libraries-crawlable.md` — the source research
- `skills/scroll-film-studio/` — the scroll-film build path
