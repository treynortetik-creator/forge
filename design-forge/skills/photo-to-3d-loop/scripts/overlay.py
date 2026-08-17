#!/usr/bin/env python3
"""Overlay the model's silhouette on the photograph's, normalised to the same height.

A W:H ratio is one number and it hides everything about WHERE the outline disagrees.
This draws both silhouettes on top of each other so the disagreement is visible:

    red   = photo only   (model is missing material here)
    blue  = model only   (model has grown material the device does not have)
    white = both agree

Both silhouettes are scaled to a common height and centred on their own centroid,
because absolute size is meaningless — the renders are framed to fill the frame.

    python3 overlay.py <tag> [view ...]
"""
import os, pathlib, subprocess, sys

# Project root: the cwd, or P23D_ROOT. Full note in driver.py — this was
# __file__.parent.parent back when the scripts lived inside the project they served.
ROOT    = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
REFS    = ROOT / "refs"
RENDERS = ROOT / "renders"
SIZE    = 520          # canvas the normalised silhouettes are drawn into
# macOS system Arial by default; set P23D_FONT on any other OS. magick has no font config
# here, so an absent font makes the labelling step exit 1 having written nothing.
FONT    = os.environ.get("P23D_FONT", "/System/Library/Fonts/Supplemental/Arial.ttf")
# Scratch for the normalised silhouettes. Rewritten every run and read immediately, so it
# is disposable — but two projects running at once would share it. Set P23D_TMP to split.
TMP     = pathlib.Path(os.environ.get("P23D_TMP") or "/tmp/p23d")

# ⚠️ WORKED EXAMPLE, and the THIRD copy of the view→photograph mapping (driver.VIEWS and
# measure.VIEWS are the other two). loop.py iterates THIS one to decide what to score, so a
# view missing here is a view that never gets judged. Keep all three in sync.
PAIRS = [("front",  "ref-01.jpg"), ("threeq", "ref-04.jpg"),
         ("side",   "ref-06.jpg"), ("side2",  "ref-03-upright.jpg"),
         ("rear",   "ref-02.jpg"), ("upperq", "ref-05.jpg"),
         ("upperq2","ref-07.jpg")]


def norm(src, is_render, out, roll=0.0):
    """Binary silhouette -> trimmed -> optionally de-rolled -> scaled to SIZE height."""
    if is_render:
        pre = ["-alpha", "extract", "-threshold", "50%"]
    else:
        pre = ["-alpha", "off", "-colorspace", "gray",
               "-white-threshold", "99%", "-negate", "-threshold", "1%"]
    cmd = ["magick", str(src), *pre]
    if abs(roll) > 0.05:
        # rotate the silhouette upright so the two are compared in the same frame
        cmd += ["-background", "black", "-rotate", f"{-roll}"]
    cmd += ["-trim", "+repage",
            "-resize", f"x{SIZE}",
            "-background", "black", "-gravity", "center", "-extent", f"{SIZE}x{SIZE}",
            str(out)]
    subprocess.run(cmd, check=True)
    return out


def pair(tag, view, ref, roll_photo=0.0, roll_model=0.0, tmp=TMP):
    tmp.mkdir(parents=True, exist_ok=True)
    m = norm(RENDERS / tag / "mask" / f"{view}.png", True,  tmp / f"_m_{view}.png", roll_model)
    p = norm(REFS / ref,                            False, tmp / f"_p_{view}.png", roll_photo)
    out = tmp / f"_ov_{view}.png"
    # -combine consumes exactly THREE images, one per channel. Feeding it two silently
    # produces a greyscale composite that looks like a result and encodes nothing.
    # R = photo, G = intersection, B = model, so:
    #   photo only -> red · model only -> blue · agreement -> white
    inter = tmp / f"_and_{view}.png"
    subprocess.run(["magick", str(p), str(m), "-compose", "darken", "-composite",
                    str(inter)], check=True)
    subprocess.run(["magick", str(p), str(inter), str(m),
                    "-colorspace", "sRGB", "-combine", str(out)], check=True)
    return out


def iou(tag, view, ref, roll_photo=0.0):
    """Intersection-over-union of the two normalised silhouettes. One honest number
    for 'how much of the outline actually agrees', which a W:H ratio cannot express."""
    tmp = TMP; tmp.mkdir(parents=True, exist_ok=True)
    m = norm(RENDERS / tag / "mask" / f"{view}.png", True,  tmp / f"_im_{view}.png")
    p = norm(REFS / ref,                            False, tmp / f"_ip_{view}.png", roll_photo)
    def bits(path):
        raw = subprocess.run(["magick", str(path), "-colorspace", "gray",
                              "-threshold", "50%", "-depth", "8", "gray:-"],
                             capture_output=True).stdout
        return [v > 127 for v in raw]
    a, b = bits(m), bits(p)
    n = min(len(a), len(b))
    inter = sum(1 for i in range(n) if a[i] and b[i])
    union = sum(1 for i in range(n) if a[i] or b[i])
    return inter / union if union else 0.0


if __name__ == "__main__":
    tag = sys.argv[1]
    want = sys.argv[2:] or [v for v, _ in PAIRS]
    # 🔴 ZERO. The RENDER now carries the in-plane roll (driver.VIEWS has a roll field),
    # so the photograph must be used exactly as shot. De-rolling it here as well applies
    # the correction twice and leaves the pair misaligned by 2x the roll — a bug that
    # reported threeq's baseline as 74.1% against a true 82.0% and sent a pose search off
    # to swing elevation 36 degrees to compensate for it.
    ROLL = {}
    cells, scores = [], []
    for view, ref in PAIRS:
        if view not in want:
            continue
        o = pair(tag, view, ref, roll_photo=ROLL.get(ref, 0.0))
        j = iou(tag, view, ref, roll_photo=ROLL.get(ref, 0.0))
        scores.append((view, j))
        lab = TMP / f"_lab_{view}.png"
        subprocess.run(["magick", str(o), "-background", "#111", "-gravity", "north",
                        "-splice", "0x28", "-font",
                        FONT, "-pointsize", "20",
                        "-fill", "#ffcc55", "-annotate", "+0+4",
                        f"{view}  IoU {j*100:.1f}%", str(lab)], check=True)
        cells.append(str(lab))
    out = RENDERS / tag / "_overlay.png"
    subprocess.run(["magick", *cells, "+append", str(out)], check=True)
    print(f"  red = photo only (missing) · blue = model only (extra) · white = agree")
    for v, j in scores:
        print(f"  {v:<8} IoU {j*100:5.1f}%")
    print(f"  mean IoU {sum(j for _, j in scores)/len(scores)*100:.1f}%")
    print(f"  {out}")
