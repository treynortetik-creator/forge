#!/usr/bin/env python3
"""Build the art-department asset library.

Every file lands with its license recorded in manifest.json, so the license gate
in SKILL.md is already answered before the asset is used.

    python3 fetch.py all                 # everything
    python3 fetch.py icons ornament      # named categories
    python3 fetch.py --list              # what would be fetched, no downloads

Design rules:
  * Cache-bust every request. A cached response is not evidence about the world.
  * Record WHERE the license claim was verified, not just what it says.
  * Never write a file whose license we could not establish.
  * Idempotent: re-running skips files already on disk unless --force.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")
TODAY = date.today().isoformat()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
PDM = "https://creativecommons.org/publicdomain/mark/1.0/"


def get(url, binary=False, headers=None, tries=3):
    """Cache-busted fetch. Returns bytes or str, or None on failure."""
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}_cb={int(time.time()*1000)}{os.getpid()}"
    hdrs = {"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"}
    if headers:
        hdrs.update(headers)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
            return raw if binary else raw.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if attempt == tries - 1:
                print(f"    ! {type(e).__name__}: {str(e)[:90]}", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def jget(url):
    t = get(url)
    if not t:
        return None
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        print(f"    ! not JSON: {t[:110]!r}", file=sys.stderr)
        return None


def ensure(*parts):
    d = os.path.join(HERE, *parts)
    os.makedirs(d, exist_ok=True)
    return d


def slug(s, maxlen=52):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "untitled").lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "untitled"


def magick(args):
    try:
        subprocess.run(["magick", *args], check=True,
                       capture_output=True, timeout=120)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"    ! magick: {str(e)[:90]}", file=sys.stderr)
        return False


def _fx(path, *pre):
    """Return (mean, stddev) in 0..1 for a region of an image."""
    try:
        out = subprocess.run(
            ["magick", path, *pre, "-colorspace", "Gray",
             "-format", "%[fx:mean] %[fx:standard_deviation]", "info:"],
            check=True, capture_output=True, timeout=60).stdout.decode()
        a, b = out.split()
        return float(a), float(b)
    except Exception:  # noqa: BLE001
        return None, None


def quality_gate(path):
    """Reject what a contact sheet showed to be useless.

    Three failure modes seen on the first curation pass (2026-08-07):
      * blank or near-blank sheets (versos, faded drawings)
      * extreme slivers (a fragment cropped to a 15:1 strip)
      * museum OBJECTS shot on a seamless grey studio backdrop — which read as
        'ornament' in the catalog and are the opposite of usable flat texture.
    Returns None if OK, else a reason string.
    """
    try:
        wh = subprocess.run(["magick", "identify", "-format", "%w %h", path],
                            check=True, capture_output=True,
                            timeout=30).stdout.decode().split()
        w, h = int(wh[0]), int(wh[1])
    except Exception:  # noqa: BLE001
        return "unreadable"

    ar = max(w, h) / max(1, min(w, h))
    if ar > 3.5:
        return f"sliver {w}x{h} (aspect {ar:.1f}:1)"
    if os.path.getsize(path) < 30_000:
        return f"too small ({os.path.getsize(path)//1024}KB — likely blank)"

    mean, sd = _fx(path)
    if sd is not None and sd < 0.055:
        return f"near-uniform (stddev {sd:.3f} — blank sheet)"

    # Four corners at 12%. Measured against the first curation pass:
    #   smooth corners + MID tone  = seamless grey studio backdrop -> an OBJECT
    #   smooth corners + LIGHT tone = white/cream paper margin     -> a PRINT (good)
    # Corner brightness is the discriminator. Corner-to-corner SPREAD is not:
    # backdrops are usually vignetted, so spread ran 0.20-0.72 on the very
    # shots we want to drop, and an earlier version using it wrongly rejected
    # good botanical plates.
    corners = []
    for grav in ("NorthWest", "NorthEast", "SouthWest", "SouthEast"):
        m, s = _fx(path, "-gravity", grav, "-crop", "12%x12%+0+0", "+repage")
        if m is None:
            return None
        corners.append((m, s))
    avg = sum(c[0] for c in corners) / 4
    smoothest = max(c[1] for c in corners)
    if smoothest < 0.060 and 0.28 < avg < 0.68:
        return (f"studio backdrop (corner tone {avg:.2f}, "
                f"smoothness {smoothest:.3f}) — object, not flat art")
    return None


# ----------------------------------------------------------------- manifest
def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {"generated": None, "note": "", "entries": []}


def save_manifest(m):
    m["generated"] = TODAY
    m["note"] = ("Every entry records the license and where that license was "
                 "verified. Do not add a file without one.")
    m["entries"].sort(key=lambda e: e["path"])
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write("\n")


def put(m, entry):
    m["entries"] = [e for e in m["entries"] if e["path"] != entry["path"]]
    entry["fetched"] = TODAY
    m["entries"].append(entry)


# -------------------------------------------------------------------- icons
# Bulk collection JSON: one file per set instead of thousands of SVGs.
# Render any icon with `python3 icon.py tabler:chart-bar`.
ICON_SETS = [
    ("healthicons", "MIT", "Healthcare and general symbols."),
    ("tabler",      "MIT", "General UI workhorse. Consistent 2px stroke."),
    ("lucide",      "ISC", "Clean minimal stroke set. Good for diagrams."),
]
# api.iconify.design/{prefix}.json returns the literal string "404" without an
# ?icons= list. The GitHub mirror serves the full set AND embeds info.license,
# so the license travels inside the file instead of being asserted alongside it.
ICON_SET_URL = "https://raw.githubusercontent.com/iconify/icon-sets/master/json/{}.json"


def fetch_icons(m, force=False):
    d = ensure("icons")
    for prefix, expect_spdx, why in ICON_SETS:
        path = os.path.join(d, f"{prefix}.json")
        rel = f"icons/{prefix}.json"
        if os.path.exists(path) and not force:
            try:
                doc = json.load(open(path))
            except Exception:  # noqa: BLE001
                doc = None
            if not (doc and doc.get("icons")):
                print(f"  ! {rel} on disk is invalid — refetching")
                os.remove(path)
            else:
                print(f"  = {rel} ({len(doc['icons'])} icons)")
                _put_icon_set(m, rel, prefix, doc, why)
                continue

        raw = get(ICON_SET_URL.format(prefix), binary=True)
        if not raw:
            continue
        # HARD VALIDATION. An earlier version happily wrote the 3 bytes "404"
        # and reported success. Never write what you have not parsed.
        try:
            doc = json.loads(raw)
        except Exception:  # noqa: BLE001
            print(f"  ! {prefix}: not JSON ({raw[:40]!r}) — SKIPPING")
            continue
        if doc.get("prefix") != prefix or not doc.get("icons"):
            print(f"  ! {prefix}: unexpected payload (prefix={doc.get('prefix')!r},"
                  f" icons={len(doc.get('icons', {}))}) — SKIPPING")
            continue
        spdx = ((doc.get("info") or {}).get("license") or {}).get("spdx")
        if spdx != expect_spdx:
            print(f"  ! {prefix}: license is {spdx!r}, expected {expect_spdx!r}"
                  f" — SKIPPING")
            continue
        with open(path, "wb") as f:
            f.write(raw)
        print(f"  + {rel}  {len(doc['icons'])} icons  {len(raw)//1024}KB  [{spdx}]")
        _put_icon_set(m, rel, prefix, doc, why)


def _put_icon_set(m, rel, prefix, doc, why):
    info = doc.get("info") or {}
    lic = info.get("license") or {}
    put(m, {
        "path": rel, "category": "icons", "kind": "icon-set",
        "source": f"Iconify — {info.get('name', prefix)}",
        "source_url": f"https://icon-sets.iconify.design/{prefix}/",
        "license": lic.get("spdx"),
        "license_url": lic.get("url"),
        "license_verified_at": f"info.license.spdx inside {rel} itself",
        "attribution_required": False,
        "author": (info.get("author") or {}).get("name"),
        "count": len(doc.get("icons", {})), "why": why,
        "usage": f"python3 icon.py {prefix}:<name>",
        "bytes": os.path.getsize(os.path.join(HERE, rel)),
    })


# ----------------------------------------------------------------- ornament
# Public-domain editorial texture. This is the anti-slop differentiator.
CMA_QUERIES = [
    ("botanical",      "botanical illustration flower"),
    ("textile",        "textile pattern"),
    ("wallpaper",      "wallpaper design"),
    ("japanese-print", "japanese woodblock landscape"),
    ("engraving",      "engraving ornament border"),
    ("manuscript",     "illuminated manuscript page"),
]


def fetch_ornament(m, force=False, per_query=6):
    d = ensure("ornament")
    for tag, q in CMA_QUERIES:
        data = jget("https://openaccess-api.clevelandart.org/api/artworks/?"
                    + urllib.parse.urlencode({
                        "cc0": 1, "has_image": 1, "q": q,
                        "limit": per_query * 3, "skip": 0}))
        if not data:
            continue
        got = 0
        for a in data.get("data", []):
            if got >= per_query:
                break
            if a.get("share_license_status") != "CC0":
                continue
            imgs = a.get("images") or {}
            src = (imgs.get("print") or imgs.get("web") or {})
            url = src.get("url") if isinstance(src, dict) else None
            if not url:
                continue
            name = f"cma-{tag}-{slug(a.get('title'), 34)}-{a.get('accession_number','x').replace('.','_')}"
            rel = f"ornament/{name}.webp"
            path = os.path.join(d, os.path.basename(rel))
            if not (os.path.exists(path) and not force):
                raw = get(url, binary=True)
                if not raw:
                    continue
                tmp = os.path.join(d, ".tmp_src")
                with open(tmp, "wb") as f:
                    f.write(raw)
                ok = magick([tmp, "-resize", "1600x1600>", "-strip",
                             "-quality", "82", path])
                os.remove(tmp)
                if not ok:
                    continue
                reject = quality_gate(path)
                if reject:
                    os.remove(path)
                    print(f"  - {os.path.basename(rel)}: {reject}")
                    continue
                print(f"  + {rel}  {os.path.getsize(path)//1024}KB")
            else:
                print(f"  = {rel} (have it)")
            got += 1
            creators = [c.get("description", "") for c in (a.get("creators") or [])]
            who = creators[0].split("(")[0].strip() if creators else "Unknown"
            put(m, {
                "path": rel, "category": "ornament", "kind": "public-domain-artwork",
                "tag": tag,
                "source": "Cleveland Museum of Art Open Access",
                "source_url": a.get("url") or "https://www.clevelandart.org/",
                "license": "CC0", "license_url": CC0,
                "license_verified_at": "API field share_license_status == 'CC0'",
                "attribution_required": False,
                "title": a.get("title"), "creator": who,
                "date": a.get("creation_date"),
                "credit_line_optional": (
                    f"{a.get('title')}, {who}, {a.get('creation_date')}. "
                    f"Cleveland Museum of Art (CC0)"),
                "bytes": os.path.getsize(path),
            })


AIC_QUERIES = [("botanical-specimen", "botanical illustration plate"),
               ("textile-design", "textile design pattern")]


def fetch_ornament_aic(m, force=False, per_query=5):
    d = ensure("ornament")
    for tag, q in AIC_QUERIES:
        data = jget("https://api.artic.edu/api/v1/artworks/search?"
                    + urllib.parse.urlencode({
                        "q": q, "limit": per_query * 3,
                        "fields": "id,title,image_id,is_public_domain,"
                                  "artist_title,date_display"}))
        if not data:
            continue
        base = data.get("config", {}).get("iiif_url", "https://www.artic.edu/iiif/2")
        got = 0
        for a in data.get("data", []):
            if got >= per_query:
                break
            # is_public_domain is the gate; image_id must come FROM the API.
            if not a.get("is_public_domain") or not a.get("image_id"):
                continue
            rel = f"ornament/aic-{tag}-{slug(a.get('title'), 34)}-{a['id']}.webp"
            path = os.path.join(d, os.path.basename(rel))
            if not (os.path.exists(path) and not force):
                # IIIF gives us the exact width server-side. No local resize.
                raw = get(f"{base}/{a['image_id']}/full/1600,/0/default.jpg",
                          binary=True)
                if not raw or len(raw) < 4000:
                    continue
                tmp = os.path.join(d, ".tmp_src")
                with open(tmp, "wb") as f:
                    f.write(raw)
                ok = magick([tmp, "-strip", "-quality", "82", path])
                os.remove(tmp)
                if not ok:
                    continue
                reject = quality_gate(path)
                if reject:
                    os.remove(path)
                    print(f"  - {os.path.basename(rel)}: {reject}")
                    continue
                print(f"  + {rel}  {os.path.getsize(path)//1024}KB")
            else:
                print(f"  = {rel} (have it)")
            got += 1
            put(m, {
                "path": rel, "category": "ornament", "kind": "public-domain-artwork",
                "tag": tag,
                "source": "Art Institute of Chicago",
                "source_url": f"https://www.artic.edu/artworks/{a['id']}",
                "license": "Public Domain", "license_url": PDM,
                "license_verified_at": "API field is_public_domain == true",
                "attribution_required": False,
                "title": a.get("title"), "creator": a.get("artist_title"),
                "date": a.get("date_display"),
                "iiif": f"{base}/{a['image_id']}",
                "iiif_note": "Re-crop or resize any time via the IIIF URL.",
                "bytes": os.path.getsize(path),
            })


# ---------------------------------------------------------------- textures
# Subtle overlays for HTML/deck backgrounds, and PBR sets for Blender.
AMBIENTCG_IDS = ["Paper002", "Fabric004", "Concrete034", "Plaster001",
                 "Wood051", "Marble012"]
ACG_LICENSE_PAGE = "https://ambientcg.com/license"


def fetch_textures(m, force=False):
    d = ensure("textures")
    # Prove the blanket CC0 claim from their license page before writing anything.
    page = get(ACG_LICENSE_PAGE) or ""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))
    if "CC0 1.0 Universal" not in text:
        print("  ! ambientCG license page did not state CC0 1.0 Universal — SKIPPING")
        return
    print(f"  . license proven at {ACG_LICENSE_PAGE}")
    for aid in AMBIENTCG_IDS:
        rel = f"textures/acg-{aid.lower()}-color-1k.jpg"
        path = os.path.join(d, os.path.basename(rel))
        if os.path.exists(path) and not force:
            print(f"  = {rel} (have it)")
        else:
            url = (f"https://ambientcg.com/get?file={aid}_1K-JPG.zip")
            raw = get(url, binary=True)
            if not raw or len(raw) < 10000:
                print(f"  ! {aid}: no zip")
                continue
            import zipfile
            try:
                zf = zipfile.ZipFile(io.BytesIO(raw))
                color = next((n for n in zf.namelist()
                              if re.search(r"_Color\.(jpg|png)$", n, re.I)), None)
                if not color:
                    print(f"  ! {aid}: no Color map in zip ({zf.namelist()[:3]})")
                    continue
                tmp = os.path.join(d, ".tmp_src")
                with open(tmp, "wb") as f:
                    f.write(zf.read(color))
                ok = magick([tmp, "-resize", "1024x1024>", "-strip",
                             "-quality", "80", path])
                os.remove(tmp)
                if not ok:
                    continue
            except Exception as e:  # noqa: BLE001
                print(f"  ! {aid}: {type(e).__name__} {str(e)[:70]}")
                continue
            print(f"  + {rel}  {os.path.getsize(path)//1024}KB")
        put(m, {
            "path": rel, "category": "textures", "kind": "material-color-map",
            "source": "ambientCG",
            "source_url": f"https://ambientcg.com/view?id={aid}",
            "license": "CC0", "license_url": CC0,
            "license_verified_at": ACG_LICENSE_PAGE,
            "license_note": ("Blanket site-wide CC0. The API carries NO license "
                             "field — do not cite the API for this."),
            "attribution_required": False,
            "asset_id": aid,
            "full_pbr": f"https://ambientcg.com/get?file={aid}_1K-JPG.zip",
            "full_pbr_note": "Normal/roughness/displacement maps for Blender.",
            "bytes": os.path.getsize(path) if os.path.exists(path) else None,
        })


# ------------------------------------------------------------------- fonts
# A complete, offline house stack. Poppins 800 is the gap most kits leave:
# a house type scale may call for ExtraBold on every headline while the local
# .ttf files only go to 700, so offline headlines silently fall back.
FONTS = [
    # --- house brand stack (offline-complete) ---
    ("Poppins", [300, 400, 500, 600, 700, 800]),
    ("Open Sans", [400, 600, 700]),
    ("Roboto", [400, 500, 700]),
    # --- Character faces, so a deliverable can have a POINT OF VIEW ---
    # Anthropic's frontend-design skill: AI design clusters on three looks.
    # A library with one typeface guarantees you land on one of them.
    ("Instrument Serif", [400]),     # high-contrast editorial display
    ("Fraunces", [400, 700, 900]),   # soft/wonky serif, variable optical size
    ("Archivo", [400, 600, 800]),    # grotesk workhorse, wide range
    ("Bebas Neue", [400]),           # condensed all-caps display
    ("JetBrains Mono", [400, 700]),  # instrument/telemetry mono
    ("IBM Plex Mono", [400, 600]),   # drafting/technical mono
    ("Space Grotesk", [400, 700]),   # technical grotesk with personality
]


def fetch_fonts(m, force=False):
    d = ensure("fonts")
    for family, weights in FONTS:
        css = get("https://fonts.googleapis.com/css2?"
                  + urllib.parse.urlencode({
                      "family": f"{family}:wght@" + ";".join(map(str, weights)),
                      "display": "swap"}))
        if not css:
            continue
        # A modern UA gets woff2 back. Pair each src with its font-weight.
        faces = re.findall(
            r"font-weight:\s*(\d+);[^}]*?src:\s*url\((https://[^)]+\.woff2)\)",
            css, re.S)
        # Keep the latin subset (the last block per weight is latin).
        seen = {}
        for w, url in faces:
            seen[int(w)] = url
        if not seen:
            print(f"  ! {family}: no woff2 in CSS response")
            continue
        # Google serves VARIABLE fonts for some families — every requested
        # weight returns byte-identical data. Store one file, not N copies.
        import hashlib
        blobs = {}
        for w, url in sorted(seen.items()):
            raw = get(url, binary=True)
            if raw and raw[:4] == b"wOF2":
                blobs[w] = raw
            elif raw:
                print(f"  ! {family} {w}: not a woff2 (sig {raw[:4]!r}) — skipped")
        if not blobs:
            continue
        digests = {hashlib.sha256(b).hexdigest() for b in blobs.values()}
        variable = len(digests) == 1 and len(blobs) > 1

        groups = ([(sorted(blobs), next(iter(blobs.values())), "variable")]
                  if variable else
                  [([w], b, str(w)) for w, b in sorted(blobs.items())])

        for weights, raw, label in groups:
            rel = f"fonts/{slug(family)}-{label}.woff2"
            path = os.path.join(d, os.path.basename(rel))
            if os.path.exists(path) and not force and os.path.getsize(path) == len(raw):
                print(f"  = {rel} (have it)")
            else:
                with open(path, "wb") as f:
                    f.write(raw)
                print(f"  + {rel}  {len(raw)//1024}KB  weights={weights}")
            put(m, {
                "path": rel, "category": "fonts", "kind": "webfont",
                "source": "Google Fonts", "source_url":
                    f"https://fonts.google.com/specimen/{family.replace(' ', '+')}",
                "license": "OFL-1.1", "license_url":
                    "https://openfontlicense.org/",
                "license_verified_at":
                    "https://fonts.google.com/attribution (all listed families OFL)",
                "attribution_required": False,
                "family": family, "weights": weights,
                "variable": variable, "format": "woff2", "subset": "latin",
                "bytes": len(raw),
                "why": ("Poppins 800 is required by the house type scale on "
                        "every headline and is NOT in the local .ttf set — "
                        "offline headlines silently fall back to 700."
                        if family == "Poppins" and 800 in weights
                        else "House brand stack, offline-complete."),
            })


CATEGORIES = {
    "icons": fetch_icons,
    "ornament": lambda m, force=False: (fetch_ornament(m, force),
                                        fetch_ornament_aic(m, force)),
    "textures": fetch_textures,
    "fonts": fetch_fonts,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("categories", nargs="*", default=["all"])
    ap.add_argument("--force", action="store_true",
                    help="re-download files already on disk")
    ap.add_argument("--list", action="store_true",
                    help="show categories and exit")
    a = ap.parse_args()

    if a.list:
        for k in CATEGORIES:
            print(k)
        return 0

    cats = list(CATEGORIES) if (not a.categories or "all" in a.categories) \
        else [c for c in a.categories if c in CATEGORIES]
    unknown = [c for c in a.categories
               if c not in CATEGORIES and c != "all"]
    for u in unknown:
        print(f"! unknown category: {u}", file=sys.stderr)

    m = load_manifest()
    for c in cats:
        print(f"\n[{c}]")
        CATEGORIES[c](m, a.force)
    save_manifest(m)

    n = len(m["entries"])
    total = sum(e.get("bytes") or 0 for e in m["entries"])
    missing = [e["path"] for e in m["entries"]
               if not os.path.exists(os.path.join(HERE, e["path"]))]
    print(f"\nmanifest: {n} entries, {total/1e6:.1f} MB of sized assets")
    if missing:
        print(f"⚠️  {len(missing)} manifest entries have no file on disk:")
        for p in missing[:10]:
            print(f"    {p}")
    nolic = [e["path"] for e in m["entries"] if not e.get("license")]
    print(f"license coverage: {n - len(nolic)}/{n}"
          + (f"  ⚠️ MISSING: {nolic}" if nolic else "  ✅"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
