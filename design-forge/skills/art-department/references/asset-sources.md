# Asset sources — verified 2026-08-07

Every row was hit live unless marked CLAIMED. Full research writeup with the failure analysis:
`memory/reference/artifacts/2026-08-07-free-asset-libraries-crawlable.md`.

---

## Tier 1 — keyless, CC0 or PD, use freely

### Iconify — icons
```
https://api.iconify.design/{prefix}/{name}.svg
https://api.iconify.design/collections            # 234 sets with SPDX license per set
https://api.iconify.design/search?query=…&limit=64
```
326,325 icons. **License is PER COLLECTION** and machine-readable in `/collections` — 145 sets are
MIT/Apache/CC0. **`healthicons` is 2,709 icons, MIT, a broad general-purpose set** and is the single
largest permissively-licensed set available. Check the set's SPDX before using; some sets in
the catalog are not commercial-friendly.

### Poly Haven — HDRIs, textures, 3D models
```
https://api.polyhaven.com/assets?type=hdris|textures|models
https://api.polyhaven.com/files/{id}
```
2,295 assets, **CC0**, no key, no attribution required. **Already wired into the `blender-assets`
MCP** — inside Blender you request them by name, no HTTP needed. Verified end to end.

### ambientCG — materials, HDRIs, models
```
https://ambientcg.com/api/v2/full_json?type=Material&limit=100
```
5,695 assets: 2,006 materials, 418 HDRIs, 2,876 models. **CC0.**

### Cleveland Museum of Art
```
https://openaccess-api.clevelandart.org/api/artworks/?cc0=1&has_image=1&q=…&limit=100
```
41,479 CC0 works with images. Print-resolution and TIFF available. Filter on
`share_license_status == "CC0"`. **Verified pipeline:** API → 3400×2060 source → ImageMagick →
85KB 1200px WebP.

### Art Institute of Chicago
```
https://api.artic.edu/api/v1/artworks/search?q=…&fields=id,title,image_id,is_public_domain
https://www.artic.edu/iiif/2/{image_id}/full/{width},/0/default.jpg
```
62,046 public-domain works. **IIIF means arbitrary crop and size server-side** — ask for exactly the
region and pixel width you need, no local processing. ⚠️ Use the `image_id` the API returns; an
invented one 404s (that trap cost a research agent a cycle).

### Wikimedia Commons
```
https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=…
  &gsrnamespace=6&prop=imageinfo&iiprop=url|extmetadata&format=json
```
88.6M images, 247,566 videos (19,367 at 4K+). Commercial use guaranteed by site policy; read
`extmetadata.LicenseShortName` and `extmetadata.AttributionRequired` per file.
⚠️ **`gsrnamespace=6` is required** — omitting it returns empty and looks like no results.

### DiceBear — Open Peeps illustrated characters
```
https://api.dicebear.com/9.x/open-peeps/svg?seed=whatever
```
Keyless, deterministic by seed, **CC0**, and the returned SVG self-documents its provenance.

### Google Fonts / Fontsource
Keyless CSS → `.woff2`, OFL. See the font note in `house-style.md`.

### Noto Emoji
**Apache-2.0** image assets. Cleaner than Twemoji (CC-BY), much cleaner than OpenMoji (CC-BY-SA).
Prefer Noto.

---

## Tier 2 — free key, worth the 30 seconds

### Smithsonian Open Access
```
https://api.si.edu/openaccess/api/v1.0/search?q=…&api_key=…      # api.data.gov key
```
5.24M CC0 images. Cooper Hewitt textiles and design alone is 54,626 items — an outstanding source for
pattern and ornament. Per-item `usage.access == "CC0"` is the field to trust (confirmed live). ⚠️ The
prose terms page 403s behind a JS wall, so the CC0 claim rests on the API field, not the legal page.

### Pexels — photography and video
```
https://api.pexels.com/v1/search?query=…      Authorization: <key>
```
🔴 **NOT keyless.** An earlier pass here concluded it was, from a response served out of a **6.4-day
Cloudflare cache** (`cf-cache-status: HIT`, `age: 549402`); the "control test" with a bogus key hit
the same cached entry. Any novel query returns `401 Missing API key`. Free key, instant signup, 200
req/hr and 20,000/mo.

**Standing lesson: cache-bust before concluding any endpoint is open.**
```bash
curl -H 'Cache-Control: no-cache' "https://host/path?cb=$RANDOM" -D- -o/dev/null
# then LOOK at cf-cache-status / age / x-cache in the headers
```

---

## Tier 3 — usable with a per-item gate

- **Openverse** (`api.openverse.org/v1/images/?q=…&license=cc0,pdm`) — 915M assets across 52 sources,
  keyless discovery layer. ⚠️ **Anonymous pagination hard-caps at 240 results.** That is a cap, not an
  inventory count; do not report it as one.
- **Wellcome Collection** — 126,559 items, medical and science history. Filter
  `locations.license` and drop the 4,208 NC.
- **Coverr** — 8,026 videos, keyless browse, **attribution required**, no model releases.
- **Mixkit** — **two licenses.** The "Restricted" tier bans Commercial Projects, Advertising, and
  Company Social Media. The sitemap does **not** carry the license field; you must fetch each item
  page and read the JSON-LD `license` value. Per-item gate or skip it.
- **Internet Archive video** — **3.41% usable.** Of 16.78M movie items, 92.7% carry no `licenseurl`
  at all; NC outnumbers CC-BY roughly 4:1.
- **Openclipart** — JSON API is dead (silently 302s to the homepage). Direct `/download/{id}` works.

---

## 🔴 Do not use

| Source | Why |
|---|---|
| **unDraw** | `robots.txt` disallows `/api/`, and the license bars automated download and AI training. Great art, cannot be automated |
| **Absurd Design** | Free tier is non-commercial only and explicitly bans use "for a client" |
| **SVG Repo** | Raw SVGs fetch, but the license-bearing page sits behind a Vercel bot challenge. Catalog provably contains CC BY-NC. **You can pull bytes you cannot prove you may use** |
| **Videvo, Mazwai** | Dead. Both 301 to freepik.com |
| **Hover.css** | Not free for commercial use post-2017 |
| **21st.dev / Aceternity / ReactBits** | All React. Aceternity's effects are Framer Motion physics — there is largely no CSS to extract. $199 lifetime buys a stack migration, not assets |
| **Blush** | Login-only, vectors paid |

---

## 🎵 Audio — Free Music Archive

An account plus a small donation supports the archive and unlocks full download access.

🔴 **An automated agent cannot crawl it.** `freemusicarchive.org/robots.txt` explicitly lists:
```
User-agent: ClaudeBot
Disallow: /
```
plus `Content-Signal: search=yes, ai-train=no, use=reference`, and the legacy JSON API
(`/api/get/tracks.json`) is **dead — 404**. There is no programmatic path that respects their terms.

**How to actually use it:**
1. A human picks and downloads tracks, or drives a browser session they are present for.
2. Files land in a known folder; the agent takes it from there (ffmpeg, ducking, mixing, timing to cut).
3. 🔴 **The license gate is per track and it matters.** FMA carries CC BY, CC BY-SA, CC BY-NC,
   CC BY-NC-ND and CC0 side by side. **NC tracks cannot go in commercial material.** ND blocks editing,
   which includes trimming to length. **Check the license on the track page, capture it, and put the
   attribution line in the deliverable.**

**Keyless alternatives an agent CAN reach unattended, when the license gate is the priority:**
Wikimedia Commons audio (same API, `gsrnamespace=6`, per-file `extmetadata`) · ccMixter ·
Musopen (public-domain classical recordings).

---

## The four traps that produced wrong answers during this research

Recording these because the same shapes will bite any code built on these sources.

1. **Wikimedia returned empty** — missing `gsrnamespace`, not empty inventory.
2. **AIC IIIF 404'd** — an invented `image_id`, not the one the API returned.
3. **Openverse "240"** — a pagination cap, nearly reported as total inventory.
4. **Pexels cache HIT** — reported as keyless; four control variants all shared the cached component.
   **Verifying the checker with the checker.**

**A zero, a 404, or a suspiciously round number is a claim about your query, not about the world.**
