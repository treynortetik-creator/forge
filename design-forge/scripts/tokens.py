#!/usr/bin/env python3
"""
tokens.py — pull real design tokens from first-party sources.

WHY THIS EXISTS
---------------
The previous workflow scraped a design-system gallery. That gallery's robots.txt
disallows ClaudeBot, anthropic-ai and Claude-Web outright (verified 2026-08-13),
so the workflow ran against the site's stated terms for automated access and
could break the moment they enforced it.

Every source below is the design system's OWN published token file, fetched from
npm/unpkg or the vendor's docs host. No gallery, no scraping, no middleman, no
rate limit, and the licence is the system's own (mostly MIT/Apache-2.0).

USAGE
    python3 tokens.py --list
    python3 tokens.py tailwind                  # summary + sample
    python3 tokens.py primer --category color   # filter
    python3 tokens.py carbon --json > carbon.json
    python3 tokens.py --all --check             # verify every URL still resolves

Stdlib only. No install step.
"""
import argparse, json, re, sys, urllib.request, urllib.error

UA = "Mozilla/5.0 (design-forge tokens.py)"

# Verified 2026-08-13: every URL returned HTTP 200 with the described content.
# Re-check with `--all --check` before trusting any of it.
SOURCES = {
    "tailwind": dict(
        name="Tailwind CSS v4", licence="MIT", fmt="css",
        url="https://unpkg.com/tailwindcss/theme.css",
        note="312 colours in oklch(). NOT hex-comparable to v3 -- v4 widened chroma "
             "(blue-500 v3 #3b82f6 -> chroma .188, v4 -> .214). Same hue, different gamut."),
    "primer": dict(
        name="GitHub Primer", licence="MIT", fmt="css",
        url="https://unpkg.com/@primer/primitives/dist/css/functional/themes/light.css",
        extra=["https://unpkg.com/@primer/primitives/dist/css/base/size/size.css",
               "https://unpkg.com/@primer/primitives/dist/css/base/typography/typography.css"],
        note="959 vars in the light theme, 682 of them colour, each with an inline "
             "/** description */. Radius and spacing live in SEPARATE files -- fetch the set."),
    "polaris": dict(
        name="Shopify Polaris", licence="see LICENSE", fmt="css",
        url="https://unpkg.com/@shopify/polaris-tokens/dist/css/styles.css",
        note="452 vars in ONE file: colour, radius, spacing, type, shadow, breakpoints."),
    "carbon": dict(
        name="IBM Carbon", licence="Apache-2.0", fmt="dtcg",
        url="https://unpkg.com/@carbon/themes/src/dtcg/white.json",
        extra=["https://unpkg.com/@carbon/themes/src/dtcg/g100.json",
               "https://unpkg.com/@carbon/themes/src/dtcg/color-palette.json"],
        note="True W3C DTCG. Theme tokens are ALIASES ({white.default}) -- resolve them "
             "against color-palette.json. Cleanest real DTCG file found."),
    "spectrum": dict(
        name="Adobe Spectrum", licence="Apache-2.0", fmt="json",
        url="https://unpkg.com/@adobe/spectrum-tokens/dist/json/variables.json",
        note="~1MB, light/dark/wireframe fully resolved. raw.githubusercontent paths 404 -- use unpkg."),
    "atlassian": dict(
        name="Atlassian", licence="Apache-2.0", fmt="figma",
        url="https://unpkg.com/@atlaskit/tokens/figma/atlassian-light.json",
        note="462 tokens, 459 PRE-RESOLVED to hex. No alias chasing, unlike Carbon."),
    "radix": dict(
        name="Radix Colors", licence="MIT", fmt="css",
        url="https://unpkg.com/@radix-ui/colors/blue.css",
        note="12 steps + P3 + alpha, one file per scale (~30 scales). Swap the filename."),
    "openprops": dict(
        name="Open Props", licence="MIT", fmt="css",
        url="https://unpkg.com/open-props/src/props.colors.css",
        extra=["https://unpkg.com/open-props/src/props.sizes.css",
               "https://unpkg.com/open-props/src/props.fonts.css"],
        note="247 colours; clean separate file per category."),
    "shadcn": dict(
        name="shadcn/ui", licence="free", fmt="json",
        url="https://ui.shadcn.com/r/colors/index.json",
        note="Every colour as hex + rgb + hsl + oklch. NB themes.css uses BARE HSL "
             "channels ('0 0% 100%'), which a normal colour regex will miss entirely."),
    "mantine": dict(
        name="Mantine", licence="MIT", fmt="css",
        url="https://unpkg.com/@mantine/core/styles.css",
        note="994 vars, 28 radii."),
    "uswds": dict(
        name="US Web Design System", licence="see LICENSE", fmt="scss",
        url="https://unpkg.com/@uswds/uswds/packages/uswds-core/src/styles/tokens/color/_blue.scss",
        note="SCSS maps with literal hex."),
    "fonts": dict(
        name="Google Fonts metadata", licence="metadata", fmt="gfonts",
        url="https://fonts.google.com/metadata/fonts",
        note="~2.7MB, 1,942 families, NO API KEY. Carries `stroke` (Sans Serif/Serif/Slab) "
             "and `classifications`, which is what makes pairing a query instead of a vibe. "
             "The official webfonts/v1 API 403s without a key -- use this instead. Cache it."),
}

CSS_VAR = re.compile(r"^\s*(--[\w-]+)\s*:\s*([^;]+);", re.M)
COLOURISH = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla|oklch|oklab|color)\(", re.I)


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace"), r.status


def parse_css(text):
    out = {}
    for k, v in CSS_VAR.findall(text):
        out[k] = v.strip()
    return out


def walk_dtcg(node, prefix=""):
    """W3C DTCG 2025.10: $value + $type. Colour is an OBJECT with hex/components,
    not a string, which trips string-only extractors."""
    out = {}
    if isinstance(node, dict):
        if "$value" in node:
            v = node["$value"]
            if isinstance(v, dict):
                v = v.get("hex") or v.get("components") or json.dumps(v)
            return {prefix: v}
        for k, v in node.items():
            if k.startswith("$"):
                continue
            out.update(walk_dtcg(v, f"{prefix}.{k}" if prefix else k))
    return out


def walk_json(node, prefix="", depth=0):
    """Generic nested-json flattener for Figma-shaped and vendor-shaped files."""
    out = {}
    if depth > 8:
        return out
    if isinstance(node, dict):
        if "value" in node and not isinstance(node["value"], (dict, list)):
            return {prefix: node["value"]}
        for k, v in node.items():
            out.update(walk_json(v, f"{prefix}.{k}" if prefix else k, depth + 1))
    elif isinstance(node, (str, int, float)) and prefix:
        out[prefix] = node
    return out


def extract(key, text):
    fmt = SOURCES[key]["fmt"]
    if fmt in ("css", "scss"):
        d = parse_css(text)
        if not d and fmt == "scss":
            d = {m[0]: m[1] for m in re.findall(r"'([\w-]+)'\s*:\s*(#[0-9a-fA-F]{3,8})", text)}
        return d
    if fmt == "gfonts":
        return {f["family"]: f.get("stroke") or f.get("category", "")
                for f in json.loads(text.lstrip(")]}'\n")).get("familyMetadataList", [])}
    data = json.loads(text)
    if fmt == "dtcg":
        return walk_dtcg(data)
    return walk_json(data)


def summarise(key, toks):
    colours = {k: v for k, v in toks.items() if isinstance(v, str) and COLOURISH.search(v)}
    return dict(source=key, name=SOURCES[key]["name"], licence=SOURCES[key]["licence"],
                total=len(toks), colours=len(colours))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", help="registry key (see --list)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="verify URLs resolve; fetch nothing else")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--category", help="substring filter on the token name")
    ap.add_argument("--limit", type=int, default=12)
    a = ap.parse_args()

    if a.list or (not a.source and not a.all):
        print(f"{len(SOURCES)} first-party token sources\n")
        for k, s in SOURCES.items():
            print(f"  {k:<11} {s['name']:<26} {s['licence']:<14} {s['fmt']}")
        print("\nEvery URL is the system's own published file. No gallery, no scraping.")
        print("Details and gotchas: the table in this file")
        return 0

    keys = list(SOURCES) if a.all else [a.source]
    bad = [k for k in keys if k not in SOURCES]
    if bad:
        print(f"unknown source(s): {bad}. Try --list", file=sys.stderr)
        return 2

    results, failures = [], 0
    for k in keys:
        urls = [SOURCES[k]["url"]] + SOURCES[k].get("extra", [])
        merged = {}
        for u in urls:
            try:
                text, status = fetch(u)
                if a.check:
                    print(f"  {'OK ' if status == 200 else status} {k:<11} {u}")
                    continue
                merged.update(extract(k, text))
            except Exception as e:
                failures += 1
                print(f"  ERR {k:<11} {u}\n      {type(e).__name__}: {e}", file=sys.stderr)
        if a.check:
            continue
        if not merged:
            continue
        if a.category:
            merged = {kk: vv for kk, vv in merged.items() if a.category.lower() in kk.lower()}
        if a.json:
            results.append({"source": k, **SOURCES[k], "tokens": merged})
        else:
            s = summarise(k, merged)
            print(f"\n{s['name']}  ({s['licence']})  {s['total']} tokens, {s['colours']} colour-valued")
            print(f"  {SOURCES[k]['note']}")
            for kk, vv in list(merged.items())[: a.limit]:
                print(f"    {kk:<44} {str(vv)[:44]}")
            if len(merged) > a.limit:
                print(f"    ... and {len(merged) - a.limit} more  (--json for all)")

    if a.json:
        print(json.dumps(results, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
