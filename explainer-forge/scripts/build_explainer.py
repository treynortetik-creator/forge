#!/usr/bin/env python3
"""Build ONE self-contained explainer page: engine + your scenes + sprites + fonts + GSAP + narration audio + cues.

  python3 build_explainer.py project.json [--out page.html] [--gsap path/to/gsap.min.js] [--overlay DIR]
                             [--caption-width 70] [--engine-dir DIR]

project.json (paths relative to the file; see templates/example/project.json):
  title, description, scenes_html, scenes_js, audio, cues, out, storage_key, play_label
  sprites_dir   folder of .webp/.png sprites (from prep_sprites.py); each becomes IMGS[name] and its aspect IMGAR[name]
  fonts         [{"family": "EF Body", "weight": 400, "file": "fonts/Body.ttf"}, ...]   family names EF Body / EF Head are the
                engine's CSS variables; any other family you name yourself in your CSS
  theme_css     your palette/font tokens (overrides engine.css variables); defaults to overlay/theme.css when present
GSAP is found from --gsap, $GSAP_JS, <project>/vendor/gsap.min.js, a node_modules/gsap/dist/gsap.min.js above the project,
or `npm root -g`. It is not bundled (check its licence for your use); `npm i gsap` is enough.
Private overlay (overlay.py): /*ASSET:name*/ in your scenes becomes overlay/assets/name.txt, /*ASSETURI:file*/ the data: URI
of overlay/assets/file, so brand marks stay out of the public project. A placeholder with no file is an error.
Prints the page size. Keep a page meant for chat or email under about 10 MB.
"""
import argparse
import base64
import glob
import json
import mimetypes
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import narration_lib as nl  # noqa: E402
import overlay as ov  # noqa: E402

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("audio/mp4", ".m4a")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def data_uri(path):
    return f"data:{mimetypes.guess_type(path)[0] or 'application/octet-stream'};base64,{b64(path)}"


def js_json(obj):
    """JSON for a <script> block: '</' must not appear inside a string."""
    return json.dumps(obj, separators=(",", ":")).replace("</", "<\\/")


def find_gsap(explicit, project_dir):
    cands = [explicit, os.environ.get("GSAP_JS"), os.path.join(project_dir, "vendor", "gsap.min.js")]
    d = project_dir
    for _ in range(6):
        cands.append(os.path.join(d, "node_modules", "gsap", "dist", "gsap.min.js"))
        d = os.path.dirname(d)
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=20).stdout.strip()
        if root:
            cands.append(os.path.join(root, "gsap", "dist", "gsap.min.js"))
    except Exception:
        pass
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise SystemExit("GSAP not found: pass --gsap, set GSAP_JS, put it at <project>/vendor/gsap.min.js, or run `npm i gsap` in/above the project")


def sprites(folder):
    from PIL import Image
    imgs, ar = {}, {}
    if folder and os.path.isdir(folder):
        for p in sorted(glob.glob(os.path.join(folder, "*.webp")) + glob.glob(os.path.join(folder, "*.png"))):
            name = os.path.splitext(os.path.basename(p))[0]
            imgs[name] = data_uri(p)
            with Image.open(p) as im:
                ar[name] = round(im.width / im.height, 4)
    return imgs, ar


def fill_assets(s, overlay_explicit):
    """/*ASSET:name*/ and /*ASSETURI:file*/ from the overlay's assets folder."""
    def one(kind):
        def rep(m):
            name = m.group(1)
            base = ov.find("assets", overlay_explicit)
            if kind == "ASSET":
                p = ov.find(os.path.join("assets", name + ".txt"), overlay_explicit)
                if not p:
                    raise SystemExit(f"placeholder /*ASSET:{name}*/ has no file: put assets/{name}.txt in the private overlay")
                return open(p, encoding="utf-8").read().strip()
            p = os.path.join(base, name) if base else None
            if not p or not os.path.isfile(p):
                raise SystemExit(f"placeholder /*ASSETURI:{name}*/ has no file in the private overlay assets folder")
            return data_uri(p)
        return rep
    s = re.sub(r"/\*ASSET:([^*]+)\*/", one("ASSET"), s)
    return re.sub(r"/\*ASSETURI:([^*]+)\*/", one("ASSETURI"), s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--gsap")
    ap.add_argument("--overlay")
    ap.add_argument("--engine-dir", default=os.path.join(os.path.dirname(HERE), "templates", "engine"))
    ap.add_argument("--caption-width", type=int, help="re-split captions at this width (default: keep the cue sheet's)")
    a = ap.parse_args(argv)
    pj = os.path.abspath(a.project)
    D = os.path.dirname(pj)
    P = lambda rel: rel if os.path.isabs(rel) else os.path.join(D, rel)
    cfg = json.load(open(pj))
    for k in ("title", "scenes_html", "scenes_js", "audio", "cues"):
        if k not in cfg:
            raise SystemExit(f"project.json needs '{k}'")
    cues = json.load(open(P(cfg["cues"])))
    if a.caption_width:
        cues["captions"] = nl.caption_track(cues["chunks"], a.caption_width)
    E = lambda f: open(os.path.join(a.engine_dir, f), encoding="utf-8").read()
    page = E("page.html")
    fonts = ""
    for f in cfg.get("fonts", []):
        fp = P(f["file"]) if os.path.exists(P(f["file"])) else (ov.find(f["file"], a.overlay) or P(f["file"]))
        if not os.path.exists(fp):
            raise SystemExit(f"font not found: {f['file']}")
        fonts += f'@font-face{{font-family:"{f["family"]}";src:url({data_uri(fp)});font-weight:{f.get("weight", 400)}}}\n'
    theme_path = P(cfg["theme_css"]) if cfg.get("theme_css") else ov.find("theme.css", a.overlay)
    theme = open(theme_path, encoding="utf-8").read() if theme_path else ""
    imgs, ar = sprites(P(cfg["sprites_dir"]) if cfg.get("sprites_dir") else None)
    gsap_path = find_gsap(a.gsap, D)
    # the big payloads go in LAST so nothing in them can be mistaken for a placeholder
    page = page.replace("<!--SCENES_HTML-->", open(P(cfg["scenes_html"]), encoding="utf-8").read())
    page = page.replace("/*ENGINE*/", E("engine.js")).replace("/*SCENES_JS*/", open(P(cfg["scenes_js"]), encoding="utf-8").read())
    page = page.replace("/*CSS*/", E("engine.css")).replace("/*THEME*/", theme).replace("/*FONTS*/", fonts)
    page = page.replace("/*FILTERS*/", E("filters.svg.html"))
    page = fill_assets(page, a.overlay)
    page = page.replace("/*TITLE*/", cfg["title"]).replace("/*DESCRIPTION*/", cfg.get("description", "").replace('"', "&quot;"))
    page = page.replace("/*PLAY_LABEL*/", cfg.get("play_label", "Play, with sound")).replace("/*STORAGE_KEY*/", cfg.get("storage_key", "ef-"))
    page = page.replace("/*CUES*/", js_json(cues)).replace("/*IMGS*/", js_json(imgs)).replace("/*IMGAR*/", js_json(ar))
    page = page.replace("/*AUDIO*/", data_uri(P(cfg["audio"])))
    page = page.replace("/*GSAP*/", open(gsap_path, encoding="utf-8").read().replace("</script", "<\\/script"))
    out = P(a.out or cfg.get("out", "explainer.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {out}  {len(page.encode()) / 1e6:.2f} MB  {len(imgs)} sprites  {len(cues['captions'])} captions  gsap {gsap_path}")
    left = re.findall(r"/\*(?:TITLE|CSS|THEME|FONTS|FILTERS|ENGINE|SCENES_JS|CUES|IMGS|IMGAR|AUDIO|GSAP|STORAGE_KEY|PLAY_LABEL)\*/", page)
    if left:
        print("WARNING: placeholders left in the page:", sorted(set(left)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
