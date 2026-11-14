#!/usr/bin/env python3
"""Inline every asset into ONE self-contained HTML file (for the interactive explainer, or to send a stage preview).

  python3 inline_build.py src.html out.html [--root DIR]

Placeholders in src.html, paths relative to --root (default: the folder of src.html):
  {{B64:fonts/body.woff2}}           base64 of the file (use inside a data: URI you write yourself)
  {{DATA:audio/narration.m4a}}       a full data: URI, media type from the extension
  {{IMG:img/hero.png:1400}}          image re-encoded as JPEG q84, max width 1400, as a data: URI (needs Pillow)
  {{TEXT:vendor/gsap.min.js}}        the file's text, pasted as is (vendored libraries, cues.json)
Fails if any {{...}} placeholder is left outside <script> blocks. Prints the output size: keep a file meant for chat
or email under about 10 MB (a narrated 3-minute explainer with six small 3D models came to about 10.6 MB).
"""
import argparse, base64, io, mimetypes, os, re, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--root")
a = ap.parse_args()
R = a.root or os.path.dirname(os.path.abspath(a.src))
mimetypes.add_type("font/woff2", ".woff2"); mimetypes.add_type("model/gltf-binary", ".glb"); mimetypes.add_type("audio/mp4", ".m4a")
P = lambda p: os.path.join(R, p)
b64 = lambda p: base64.b64encode(open(P(p), "rb").read()).decode()


def img(path, w):
    from PIL import Image
    im = Image.open(P(path)).convert("RGB")
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    bio = io.BytesIO(); im.save(bio, "JPEG", quality=84, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode()


def sub(m):
    kind, arg = m.group(1), m.group(2)
    if kind == "B64": return b64(arg)
    if kind == "DATA": return f"data:{mimetypes.guess_type(arg)[0] or 'application/octet-stream'};base64,{b64(arg)}"
    if kind == "IMG":
        path, _, w = arg.rpartition(":"); return img(path, int(w))
    if kind == "TEXT": return open(P(arg), encoding="utf-8").read()
    return m.group(0)


s = open(a.src, encoding="utf-8").read()
s = re.sub(r"\{\{(B64|DATA|IMG|TEXT):([^}]+)\}\}", sub, s)
left = re.findall(r"\{\{\w+(?::[^}]*)?\}\}", re.sub(r"<script>.*?</script>", "", s, flags=re.S))
if left:
    sys.exit(f"unresolved placeholders: {left[:5]}")
open(a.out, "w", encoding="utf-8").write(s)
print("wrote", a.out, "size MB", round(len(s.encode()) / 1e6, 2))
