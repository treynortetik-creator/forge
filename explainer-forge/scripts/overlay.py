"""Optional private overlay: a folder OUTSIDE the plugin that holds what must never be public (brand logos and colours,
real-name lists, house-style notes). Looked up, in order, from: an explicit path, $EXPLAINER_FORGE_OVERLAY,
~/.config/explainer-forge/overlay (a folder or a symlink). Everything works without one.

Layout the scripts read (all optional):
  overlay/names.txt       people to grep for (name_check.py --names default)
  overlay/allow.txt       capitalised pairs that are fine (name_check.py --allow default)
  overlay/theme.css       palette and font tokens appended to the page CSS (build_explainer.py)
  overlay/assets/<name>.txt   text pasted into the page for a /*ASSET:name*/ placeholder (e.g. an SVG path string)
  overlay/assets/<file>       any file; /*ASSETURI:file*/ becomes its data: URI
  overlay/house.md            private house rules and brand notes (read first; see skill house-style)
  overlay/say-map.json        pronunciations merged into a project's saymap.json (new_project.py)
  overlay/profiles/*.md       extra profiles, or replacements with the same file name (new_project.py)
  overlay/public-terms.txt    words that must never reach a public repo, one per line (pre-push grep)
  overlay/lessons.md          lessons too private for the plugin (lessons-loop)
"""
import os


def overlay_dir(explicit=None):
    for cand in (explicit, os.environ.get("EXPLAINER_FORGE_OVERLAY"), os.path.expanduser("~/.config/explainer-forge/overlay")):
        if cand and os.path.isdir(os.path.expanduser(cand)):
            return os.path.realpath(os.path.expanduser(cand))
    return None


def find(rel, explicit=None):
    d = overlay_dir(explicit)
    if d:
        p = os.path.join(d, rel)
        if os.path.exists(p):
            return p
    return None
