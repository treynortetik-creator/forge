#!/usr/bin/env python3
"""Write the keyframe still prompts and a character-sheet template from a shot plan (markdown to stdout or a file).

One prompt per shot, built from the plan's style line, the shot description with names swapped for looks
(looks, not names: image models do not know your characters either), and the exact filename each frame must be
saved under so build_clips.py finds it. You generate the stills with any image model; this only writes the words.

Run (stdlib only):
    uv run python still_prompts.py shot-plan.json [--out still-prompts.md]
"""
from __future__ import annotations

import argparse
import os
import sys

import plan_lib as pl

SHEET = """## Character sheet template (generate one per recurring character BEFORE the shots)

Prompt: "Character reference sheet, plain light-grey background, the SAME character shown full body front, three-quarter
and back view plus one close-up of the face. <LOOK STRING, copied word for word from the plan's identities>. Neutral
lighting, no text, no logos, no props that are not part of the costume."

Keep one reference image per character and attach it to every still that contains them. Copy the look string
unchanged into every prompt; re-wording it between shots tends to cause identity drift."""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write per-shot keyframe still prompts and a character-sheet template from a shot plan.")
    ap.add_argument("plan")
    ap.add_argument("--out", help="write markdown here instead of stdout")
    a = ap.parse_args(argv)
    plan = pl.load_plan(a.plan)
    aspect = plan.get("aspect", "16:9")
    lines = [f"# Keyframe prompts: {plan.get('title', '')}", "",
             f"Style line (prepended to every prompt): {plan.get('style', '')}", ""]
    ids = plan.get("identities") or {}
    if ids:
        lines += ["## Characters (looks, never names)", ""] + [f"- **{n}**: {look}" for n, look in ids.items()] + [""]
    lines += [SHEET, "", "## Shot stills", ""]
    for s in plan["shots"]:
        look_desc = pl.apply_identities(s["description"], ids)
        lines += [f"### {s['id']} {s['slug']}  ({pl.fmt_time(s['start'])}-{pl.fmt_time(s['end'])}{', singing' if s.get('sing') else ''})",
                  f"Save as: `{s.get('frame', s['id'] + '-' + s['slug'])}.png`", "",
                  f"> One cinematic {aspect} keyframe, a single scene, never a collage or storyboard grid. {plan.get('style', '')} "
                  f"{look_desc} State exactly who is in frame and how many. No words, letters, logos or watermarks.", ""]
    text = "\n".join(lines)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
