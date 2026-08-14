# Third-party notices

The MIT licence in `LICENSE` covers the original work in this repository — the skills, scripts,
documentation, and the measurement harness.

**It does not cover the bundled assets under `skills/art-department/library/`.** Those remain under
their own licences, listed below. Several of those licences carry obligations that travel with the
files if you fork or redistribute this repo.

Full per-file detail, including *where each licence was verified*, is in
`skills/art-department/library/manifest.json`. Licence texts are bundled in
`skills/art-department/library/licenses/`.

---

## Obligations at a glance

| Licence | Assets | On redistribution you must |
|---|---|---|
| **MIT** | Health Icons, Tabler Icons | Ship the copyright notice **and** the licence text. Both are in `library/licenses/`, and the SPDX id, author and licence URL are also embedded in each icon set's own `info.license` field. |
| **ISC** | Lucide | Same: notice + licence text. Bundled. |
| **OFL-1.1** | 16 webfonts, 10 families | Ship the licence with the fonts (bundled). **Do not sell the fonts on their own.** ⚠️ **Correction:** these are Google Fonts' **latin-subset** `woff2` builds, not full font files — Roboto ships 229 of 927 upstream codepoints, Poppins 217 of 504. Under OFL that subsetting is a Modified Version, though **Google Fonts produced the subsets, not this repo** (`fetch.py` pulls from the `css2` API). Family names are unaltered. Of the ten families, **only IBM Plex declares a Reserved Font Name ("Plex")** — the blanket "rename if you modify" line previously here was over-broad and missed the one real case. |
| **CC0** | ambientCG textures, Cleveland Museum of Art | No obligations. Attribution below is courtesy, not a requirement. |
| **CC0** | Art Institute of Chicago | No obligations. *(Previously labelled "Public Domain" here and in the manifest; AIC's own image-licensing page designates these CC0, "for any purpose, including commercial." Relabelled for accuracy.)* |

⚠️ **A note on the museum images.** "Public domain" can refer to the underlying *artwork* while the
institution asserts something narrower over its *photograph* of it. Both institutions used here
publish under open-access programmes that cover the image files, and `manifest.json` records the
specific API field that was checked per item (`share_license_status == 'CC0'` for Cleveland,
`is_public_domain == true` for AIC). If you reuse these commercially and it matters, re-verify at the
object URL — each one is recorded.

⚠️ **ambientCG carries no licence field in its API.** The CC0 grant is site-wide policy, verified at
`https://ambientcg.com/license`, not per-asset metadata. Do not cite the API for it.

---

## MIT License — 2 asset(s)

**Iconify — Health Icons** (1)
- https://icon-sets.iconify.design/healthicons/
- *licence verified via:* info.license.spdx inside icons/healthicons.json itself

**Iconify — Tabler Icons** (1)
- https://icon-sets.iconify.design/tabler/
- *licence verified via:* info.license.spdx inside icons/tabler.json itself


## ISC License — 1 asset(s)

**Iconify — Lucide** (1)
- https://icon-sets.iconify.design/lucide/
- *licence verified via:* info.license.spdx inside icons/lucide.json itself


## SIL Open Font License 1.1 — 16 asset(s)

**Google Fonts** (16)
- 10 objects; every object URL is recorded per-file in `manifest.json`
- e.g. https://fonts.google.com/specimen/Archivo
- *licence verified via:* https://fonts.google.com/attribution (all listed families OFL)


## CC0 1.0 Universal (public domain dedication) — 35 asset(s)

**Cleveland Museum of Art Open Access** (29)
- 29 objects; every object URL is recorded per-file in `manifest.json`
- e.g. https://clevelandart.org/art/1916.1142
- *licence verified via:* API field share_license_status == 'CC0'

**ambientCG** (6)
- 6 objects; every object URL is recorded per-file in `manifest.json`
- e.g. https://ambientcg.com/view?id=Concrete034
- *licence verified via:* https://ambientcg.com/license


## Public domain — 7 asset(s)

**Art Institute of Chicago** (7)
- 7 objects; every object URL is recorded per-file in `manifest.json`
- e.g. https://www.artic.edu/artworks/129318
- *licence verified via:* API field is_public_domain == true


---

## Methodology and adapted work

- **`skills/design-loop/`** is adapted from *The Design Loop*, itself a variation on the **Gauntlet
  Loop originated by Matt Shumer**. The method is his; the implementation, the critic briefs, and the
  additions documented in that file are this repository's.
- **`skills/de-sloppifier/`, `skills/voice/`, `skills/clean-export/`** are adapted from **story-forge**,
  by the same author.
- 🔴 **Wikipedia, [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
  — CC BY-SA.** The AI-vocabulary and puffery categories in `de-sloppifier` Pass 1 and Pass 3 overlap
  substantially with this community-maintained essay, including its groupings. **CC BY-SA requires
  attribution and share-alike, which an unattributed MIT redistribution does not satisfy.** If you
  reuse those word lists, carry this attribution with them. The rest of the skill — the three-pass
  structure, the 13 edit moves, the census/judge/apply discipline, and the participial-clause and
  sentence-length-CV work — is original to this repository.
- **Wulf Moon**, **Jason Hamilton / The Nerdy Novelist**, **Browne & King** — the craft behind the
  shared writing skills. Full detail in `../story-forge/NOTICES.md`.
- **Anthropic's `frontend-design` skill.** `skills/art-department/references/house-style.md` quotes it
  directly (marked inline as verbatim) and builds on its two-pass process. Anthropic's bundled skills
  are **not published under an open licence**; the quotation is short, attributed, and used for
  commentary. The surrounding rules are this repository's own.
- **`references/writing/`** — five notes bundled so `voice` and `de-sloppifier` actually run.
  `voice-matching.md` derives from a public YouTube tutorial, credited in its own frontmatter.
- **`references/mechanisms.md`** cites published research and standards. Every entry is tagged with how
  it was verified — normative, practitioner, convention, or folklore — and quotations are short and
  attributed. WCAG text is quoted from W3C Understanding documents, which are published under the
  **W3C Software and Document License**.
- The asset library was assembled by `skills/art-department/library/fetch.py`, which records the
  licence and its verification source for every file it writes. **It refuses to add a file without
  one.** You can rebuild or extend the library with `python3 fetch.py --list` then `fetch.py all`.
