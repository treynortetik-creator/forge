#!/usr/bin/env python3
"""
deck_audit.py — measure a .pptx instead of eyeballing it.

WHY THIS EXISTS
---------------
Same thesis as the page harness: a person looking at a slide cannot tell whether the
18pt caption will be legible from the back row, whether a colour pair clears 4.5:1,
or whether a native chart is about to flatten into a dead image on import. All of
those are arithmetic.

🔴 THE TRAP THIS IS BUILT AROUND. `run.font.size` returns **None** whenever the size
is inherited from a layout, a master, or the master's txStyles — which is the normal
case for placeholder text. A naive reader sees None, skips the shape, and reports a
clean deck. So this resolves the real inheritance chain before measuring anything:

    run.rPr → paragraph.defRPr → layout placeholder → master placeholder
            → master txStyles (title / body / other) → 18pt PowerPoint default

Every check reports `checked: n` and refuses to pass at zero, for the same reason.

USAGE
    python3 deck_audit.py deck.pptx
    python3 deck_audit.py deck.pptx --room-depth 30 --json
    python3 deck_audit.py deck.pptx --fail-on any

Requires python-pptx.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Emu, Pt
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    print("ERROR: needs python-pptx.  pip3 install python-pptx", file=sys.stderr)
    sys.exit(1)

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
EMU_PER_IN = 914400


# ── colour ───────────────────────────────────────────────────────────────────

def _srgb(el):
    """Pull an explicit sRGB value out of a fill/colour element, if there is one."""
    if el is None:
        return None
    c = el.find(f"{A}srgbClr")
    if c is not None and c.get("val"):
        return c.get("val").upper()
    return None


def theme_colours(prs):
    """Map scheme names (dk1, lt1, accent1…) to concrete RGB from the theme part."""
    out = {}
    try:
        theme = prs.slide_master.part.part_related_by(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme")
        root = theme._element if hasattr(theme, "_element") else None
        if root is None:
            from lxml import etree
            root = etree.fromstring(theme.blob)
        scheme = root.find(f".//{A}clrScheme")
        if scheme is not None:
            for child in scheme:
                name = child.tag.split("}")[-1]
                val = _srgb(child)
                if val is None:
                    sysc = child.find(f"{A}sysClr")
                    if sysc is not None and sysc.get("lastClr"):
                        val = sysc.get("lastClr").upper()
                if val:
                    out[name] = val
    except Exception:
        pass
    return out


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rel_lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    l1, l2 = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# WCAG 2.x SC 1.4.3 defines large-scale text as **18 point, or 14 point bold**.
# The familiar 24px / 18.66px figures are those same sizes expressed in CSS pixels
# at 96dpi (18pt = 24px, 14pt = 18.67px). A .pptx is measured in POINTS, so using
# the pixel numbers here is a 1.333x unit error that holds every run between 18pt
# and 24pt to 4.5:1 when the spec asks 3:1 -- manufacturing failures that are not
# failures. This harness had exactly that bug, copied from its browser sibling.
LARGE_PT, LARGE_BOLD_PT = 18.0, 14.0


def is_large_text(pt, bold=False):
    return pt >= LARGE_PT or (bold and pt >= LARGE_BOLD_PT)


# ── the inheritance resolver — the reason this file exists ───────────────────

def _size_from_rpr(rpr):
    if rpr is not None and rpr.get("sz"):
        return int(rpr.get("sz")) / 100.0
    return None


def _ph_idx(shape):
    try:
        pf = shape.placeholder_format
        return pf.idx, str(pf.type)
    except Exception:
        return None, None


def _find_layout_ph(layout, idx):
    for ph in layout.placeholders:
        try:
            if ph.placeholder_format.idx == idx:
                return ph
        except Exception:
            continue
    return None


def _lvl_size_from_liststyle(el, lvl=0):
    """Read lvlNpPr/defRPr@sz out of a lstStyle or txStyles block."""
    if el is None:
        return None
    tag = f"{A}lvl{lvl + 1}pPr"
    node = el.find(tag)
    if node is None:
        return None
    return _size_from_rpr(node.find(f"{A}defRPr"))


def resolve_font_pt(run, para, shape, slide, prs, master_styles):
    """
    Effective point size for a run, walking the real chain.
    Returns (points, source) so the report can say WHERE the size came from.
    """
    # 1. explicit on the run
    if run is not None and run.font.size is not None:
        return run.font.size.pt, "run"
    rpr = run._r.find(f"{A}rPr") if run is not None else None
    v = _size_from_rpr(rpr)
    if v:
        return v, "run"

    # 2. paragraph defaults
    ppr = para._p.find(f"{A}pPr") if para is not None else None
    if ppr is not None:
        v = _size_from_rpr(ppr.find(f"{A}defRPr"))
        if v:
            return v, "paragraph"
    lvl = 0
    if ppr is not None and ppr.get("lvl"):
        lvl = int(ppr.get("lvl"))

    # 3. the shape's own lstStyle
    tx = shape.text_frame._txBody if shape.has_text_frame else None
    if tx is not None:
        v = _lvl_size_from_liststyle(tx.find(f"{A}lstStyle"), lvl)
        if v:
            return v, "shape lstStyle"

    idx, ph_type = _ph_idx(shape)

    # 4. matching placeholder on the layout
    if idx is not None:
        lay_ph = _find_layout_ph(slide.slide_layout, idx)
        if lay_ph is not None and lay_ph.has_text_frame:
            body = lay_ph.text_frame._txBody
            v = _lvl_size_from_liststyle(body.find(f"{A}lstStyle"), lvl)
            if v:
                return v, "layout placeholder"
            for p2 in body.findall(f"{A}p"):
                v = _size_from_rpr(p2.find(f"{A}pPr/{A}defRPr"))
                if v:
                    return v, "layout placeholder"

    # 5. master txStyles, keyed by placeholder role
    key = "body"
    t = (ph_type or "").lower()
    if "title" in t or "ctrtitle" in t:
        key = "title"
    elif idx is None:
        key = "other"
    v = _lvl_size_from_liststyle(master_styles.get(key), lvl)
    if v:
        return v, f"master txStyles/{key}"

    # 6. PowerPoint's own default
    return 18.0, "PowerPoint default (18pt)"


def _colour_from_rpr(rpr, theme):
    if rpr is None:
        return None
    fill = rpr.find(f"{A}solidFill")
    return _solid_to_rgb(fill, theme) if fill is not None else None


def _lvl_colour_from_liststyle(el, theme, lvl=0):
    if el is None:
        return None
    node = el.find(f"{A}lvl{lvl + 1}pPr")
    return _colour_from_rpr(node.find(f"{A}defRPr"), theme) if node is not None else None


def resolve_font_colour(run, para, shape, slide, prs, master_styles, theme):
    """Effective text colour, walking the SAME chain as resolve_font_pt.

    Without this the contrast check only covers runs with an explicit colour, which on
    a real deck is a small minority -- everything else inherits from the layout or the
    master. Reporting those as 'unmeasured' is honest but nearly useless; resolving
    them is what makes the check actually cover the deck.
    """
    got = run_colour_rgb(run, theme)
    if got:
        return got, "run"
    ppr = para._p.find(f"{A}pPr") if para is not None else None
    lvl = int(ppr.get("lvl")) if (ppr is not None and ppr.get("lvl")) else 0
    if ppr is not None:
        got = _colour_from_rpr(ppr.find(f"{A}defRPr"), theme)
        if got:
            return got, "paragraph"
    if shape.has_text_frame:
        got = _lvl_colour_from_liststyle(
            shape.text_frame._txBody.find(f"{A}lstStyle"), theme, lvl)
        if got:
            return got, "shape lstStyle"
    idx, ph_type = _ph_idx(shape)
    if idx is not None:
        lay_ph = _find_layout_ph(slide.slide_layout, idx)
        if lay_ph is not None and lay_ph.has_text_frame:
            got = _lvl_colour_from_liststyle(
                lay_ph.text_frame._txBody.find(f"{A}lstStyle"), theme, lvl)
            if got:
                return got, "layout placeholder"
    key = "body"
    t = (ph_type or "").lower()
    if "title" in t or "ctrtitle" in t:
        key = "title"
    elif idx is None:
        key = "other"
    got = _lvl_colour_from_liststyle(master_styles.get(key), theme, lvl)
    if got:
        return got, f"master txStyles/{key}"
    # Office's default body text is tx1/dk1. Use it, but SAY it was assumed.
    if "dk1" in theme:
        return hex_to_rgb(theme["dk1"]), "theme dk1 (assumed)"
    return None, "unresolved"


def master_txstyles(prs):
    out = {}
    try:
        tx = prs.slide_master.element.find(f"{P}txStyles")
        if tx is not None:
            for name, tag in (("title", "titleStyle"), ("body", "bodyStyle"), ("other", "otherStyle")):
                out[name] = tx.find(f"{P}{tag}")
    except Exception:
        pass
    return out


# ── shape colour resolution ──────────────────────────────────────────────────

UNKNOWN_FILL = "UNKNOWN"   # picture or gradient: refuse to guess, skip the check

SCHEME_ALIAS = {"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}


def _solid_to_rgb(fill, theme):
    """An <a:solidFill> element -> concrete RGB, resolving scheme colours."""
    v = _srgb(fill)
    if v:
        return hex_to_rgb(v)
    sc = fill.find(f"{A}schemeClr")
    if sc is not None and sc.get("val"):
        name = SCHEME_ALIAS.get(sc.get("val"), sc.get("val"))
        if name in theme:
            return hex_to_rgb(theme[name])
    return None


def _fill_of(props, theme):
    """Resolve the fill on a properties element (spPr / bgPr / grpSpPr).

    Only DIRECT children are considered. A descendant search here is a real bug:
    `.//solidFill` on a shape walks into <a:txBody> and returns the TEXT colour as
    the shape fill, which makes foreground and background identical and reports a
    perfect 1.0:1 on a shape that has no fill at all. It also means the true slide
    background is never used, so genuine contrast failures go unmeasured.
    <a:ln> (the outline colour) is a direct child too, and is likewise not the fill.
    """
    if props is None:
        return None
    for child in props:
        tag = child.tag
        if tag == f"{A}solidFill":
            return _solid_to_rgb(child, theme)
        if tag == f"{A}noFill":
            return None                 # explicitly transparent -> inherit
        if tag in (f"{A}blipFill", f"{A}gradFill", f"{A}pattFill"):
            return UNKNOWN_FILL
    return None                          # no fill specified -> inherit


def shape_fill_rgb(shape, theme):
    """Concrete RGB for a shape's own fill, or UNKNOWN_FILL, or None to inherit."""
    try:
        sp = shape._element
        for tag in (f"{P}spPr", f"{A}spPr", f"{P}grpSpPr", f"{A}grpSpPr"):
            props = sp.find(tag)
            if props is not None:
                return _fill_of(props, theme)
    except Exception:
        pass
    return None


def run_colour_rgb(run, theme):
    try:
        if run.font.color and run.font.color.rgb is not None:
            return hex_to_rgb(str(run.font.color.rgb))
    except Exception:
        pass
    try:
        rpr = run._r.find(f"{A}rPr")
        if rpr is not None:
            fill = rpr.find(f"{A}solidFill")
            v = _srgb(fill)
            if v:
                return hex_to_rgb(v)
            sc = fill.find(f"{A}schemeClr") if fill is not None else None
            if sc is not None and sc.get("val"):
                alias = {"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}
                nm = alias.get(sc.get("val"), sc.get("val"))
                if nm in theme:
                    return hex_to_rgb(theme[nm])
    except Exception:
        pass
    return None


def slide_bg_rgb(slide, prs, theme):
    """Background for a slide: its own, else the layout's, else the master's.

    Returns UNKNOWN_FILL for a picture or gradient background rather than falling
    through to a white guess. Text over a photo cannot be contrast-checked from the
    file, and pretending otherwise is worse than saying so.
    """
    for src in (slide, slide.slide_layout, prs.slide_master):
        try:
            bg = src.element.find(f".//{P}bg")
            if bg is None:
                continue
            props = bg.find(f"{P}bgPr")
            if props is not None:
                got = _fill_of(props, theme)
                if got is not None:
                    return got
            # <p:bgRef idx="..."> points at the theme's fill style list and carries
            # its own colour override, which is the usual shape of a branded master.
            ref = bg.find(f"{P}bgRef")
            if ref is not None:
                got = _solid_to_rgb(ref, theme)
                if got:
                    return got
        except Exception:
            continue
    return (255, 255, 255)


# ── traversal ────────────────────────────────────────────────────────────────

def _group_transform(grp):
    """Map a group's child coordinate space onto the slide.

    A group has an offset/extent on the slide (off/ext) AND a child coordinate
    system (chOff/chExt) which is usually the same numbers but need not be. A child
    at chOff sits at off, and the space scales by ext/chExt. Ignoring this reports
    grouped shapes at their raw child coordinates, which are meaningless on the slide.
    """
    try:
        xfrm = grp._element.find(f".//{A}xfrm")
        if xfrm is None:
            return (0, 0, 1.0, 1.0, 0, 0)
        off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
        cho, che = xfrm.find(f"{A}chOff"), xfrm.find(f"{A}chExt")
        ox, oy = int(off.get("x")), int(off.get("y"))
        cx, cy = (int(cho.get("x")), int(cho.get("y"))) if cho is not None else (0, 0)
        sx = (int(ext.get("cx")) / int(che.get("cx"))) if (ext is not None and che is not None
                                                          and int(che.get("cx"))) else 1.0
        sy = (int(ext.get("cy")) / int(che.get("cy"))) if (ext is not None and che is not None
                                                          and int(che.get("cy"))) else 1.0
        return (ox, oy, sx, sy, cx, cy)
    except Exception:
        return (0, 0, 1.0, 1.0, 0, 0)


def _compose(outer, inner):
    """Nest one group transform inside another."""
    ox, oy, sx, sy, cx, cy = outer
    ix, iy, isx, isy, icx, icy = inner
    return (ox + (ix - cx) * sx, oy + (iy - cy) * sy, sx * isx, sy * isy, icx, icy)


def _apply(tf, x, y):
    ox, oy, sx, sy, cx, cy = tf
    return ox + (x - cx) * sx, oy + (y - cy) * sy


IDENTITY = (0, 0, 1.0, 1.0, 0, 0)


def walk_shapes(shapes, tf=IDENTITY, depth=0):
    """Yield every (shape, transform, in_group) on a slide, recursing into GROUPS.

    🔴 Without this the harness is blind to exactly the decks it exists to check.
    deck-forge MANDATES building every visual from grouped rectangles and text boxes
    (because native charts flatten on Google Slides import), so a non-recursive
    `for shape in slide.shapes` measures none of the real content. Tested: a slide of
    grouped 7pt bars plus a 6pt table cell reported "0 runs, all PASS, exit 0".
    """
    if depth > 12:
        return
    for shape in shapes:
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
            yield shape, tf, depth > 0
            child_tf = _compose(tf, _group_transform(shape))
            yield from walk_shapes(shape.shapes, child_tf, depth + 1)
        else:
            yield shape, tf, depth > 0


def text_frames_of(shape):
    """Every text frame a shape carries, INCLUDING every table cell.

    A table is one shape with no `.text_frame`; its text lives in cell frames. Skipping
    them silently drops every number in every table, which on a data deck is the
    majority of the text on the slide.
    """
    out = []
    if getattr(shape, "has_table", False) and shape.has_table:
        for r, row in enumerate(shape.table.rows):
            for c, cell in enumerate(row.cells):
                out.append((cell.text_frame, f"table[{r}][{c}]", cell))
    elif shape.has_text_frame:
        out.append((shape.text_frame, None, None))
    return out


def _bounds(shape, tf):
    """Absolute slide-coordinate bounds in EMU, or None."""
    try:
        if shape.left is None or shape.top is None:
            return None
        x0, y0 = _apply(tf, shape.left, shape.top)
        x1, y1 = _apply(tf, shape.left + (shape.width or 0), shape.top + (shape.height or 0))
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    except Exception:
        return None


def _contains(outer, inner, slack=9144):    # 0.01in of slack
    if not outer or not inner:
        return False
    return (outer[0] <= inner[0] + slack and outer[1] <= inner[1] + slack
            and outer[2] >= inner[2] - slack and outer[3] >= inner[3] - slack)


def backdrop_for(i, layers, slide_bg):
    """What is actually BEHIND layers[i]'s text.

    A shape with no fill of its own is not sitting on the slide background if some
    filled shape is painted underneath it. Placing a text box over a coloured
    rectangle is one of the most common ways a real deck is built, and without this
    the harness reports white-on-white at 1.0:1 for perfectly legible text -- a false
    positive, which is the failure that makes a checker untrustworthy.

    So: walk DOWN the z-order from just below this shape and take the first filled
    shape that fully contains it.
    """
    own = layers[i]["fill"]
    if own is not None:
        return own, "own fill"
    me = layers[i]["bounds"]
    for j in range(i - 1, -1, -1):
        under = layers[j]
        if under["fill"] is None or not _contains(under["bounds"], me):
            continue
        if under["fill"] is UNKNOWN_FILL:
            return UNKNOWN_FILL, "sits on a picture or gradient"
        return under["fill"], f"behind it: {under['name']}"
    return slide_bg, "slide background"


# ── the checks ───────────────────────────────────────────────────────────────

CAP_HEIGHT_RATIO = 0.70   # a capital letter is ~70% of the point size
SUBTENSE_DIVISOR = 200.0  # element height >= viewing distance / 200 (angular subtense)
# The AV "4/6/8 rule": the farthest viewer sits at most N x the screen height away.
VIEWING_NEED = {"analytical": 4.0, "basic": 6.0, "passive": 8.0}


def legibility_floor_pt(slide_h_in, need="basic", screen_h_in=None, room_depth_ft=None):
    """Minimum legible point size on a projected slide.

    A point is a DOCUMENT unit, not a physical one. Its physical height on the wall
    depends entirely on how large the slide is projected, so the chain is:

        fraction_of_image = (pt / 72) * CAP_HEIGHT_RATIO / slide_h_in
        physical_cap_in   = fraction_of_image * screen_h_in
        require             physical_cap_in >= viewing_distance_in / 200

    Treating points as physical inches (the naive version of this function) reports a
    ~185pt floor for a 30ft room, which is off by an order of magnitude.

    If the screen size is unknown, derive it from the 4/6/8 rule -- and note that the
    viewing distance then CANCELS, because screen size scales with room depth. The
    floor becomes a property of the viewing need and the slide's aspect, not the room.
    """
    if screen_h_in and room_depth_ft:
        dist_in = room_depth_ft * 12.0
        need_cap_in = dist_in / SUBTENSE_DIVISOR
        return round(need_cap_in / screen_h_in * slide_h_in * 72.0 / CAP_HEIGHT_RATIO, 1)
    ratio = VIEWING_NEED.get(need, VIEWING_NEED["basic"])
    return round(ratio / SUBTENSE_DIVISOR * slide_h_in * 72.0 / CAP_HEIGHT_RATIO, 1)


def audit(path, room_depth_ft=None, min_pt=None, need="basic", screen_h_in=None):
    prs = Presentation(str(path))
    theme = theme_colours(prs)
    mstyles = master_txstyles(prs)
    slide_w_in = prs.slide_width / EMU_PER_IN
    slide_h_in = prs.slide_height / EMU_PER_IN

    derived_pt = legibility_floor_pt(slide_h_in, need, screen_h_in, room_depth_ft)
    # What screen the stated room actually needs, which is the useful thing the
    # room depth tells you once the point-size floor stops depending on it.
    needed_screen_h_ft = (room_depth_ft / VIEWING_NEED.get(need, 6.0)) if room_depth_ft else None

    floor_pt = min_pt or derived_pt

    findings = {"tiny_text": [], "native_charts": [], "low_contrast": [], "offslide": [],
                "unresolved_size": [], "empty_placeholders": [], "unmeasured_contrast": []}
    sizes, checked_runs, checked_shapes = set(), 0, 0
    per_slide = []

    for n, slide in enumerate(prs.slides, 1):
        bg = slide_bg_rgb(slide, prs, theme)
        s_words, s_shapes = 0, 0
        ordered = list(walk_shapes(slide.shapes))
        layers = [{"fill": shape_fill_rgb(sh, theme), "bounds": _bounds(sh, t),
                   "name": sh.name} for sh, t, _ in ordered]
        for zi, (shape, tf, in_group) in enumerate(ordered):
            checked_shapes += 1
            s_shapes += 1
            loc = f"slide {n}" + (" (in group)" if in_group else "")

            # native chart -> flattens to a dead image on Google Slides import
            if getattr(shape, "has_chart", False) and shape.has_chart:
                findings["native_charts"].append({
                    "where": loc, "name": shape.name,
                    "why": "a native chart converts to a STATIC IMAGE on Google Slides import and "
                           "cannot be made editable — Slides only keeps a chart live when linked to "
                           "a Sheet, and that link cannot exist in an uploaded .pptx. Rebuild from "
                           "rectangles and text boxes."})

            # off-slide / bleeding geometry, in SLIDE coordinates
            try:
                if shape.left is not None and shape.top is not None:
                    x0, y0 = _apply(tf, shape.left, shape.top)
                    x1, y1 = _apply(tf, shape.left + (shape.width or 0),
                                    shape.top + (shape.height or 0))
                    l, t = x0 / EMU_PER_IN, y0 / EMU_PER_IN
                    r, b = x1 / EMU_PER_IN, y1 / EMU_PER_IN
                    if l < -0.05 or t < -0.05 or r > slide_w_in + 0.05 or b > slide_h_in + 0.05:
                        findings["offslide"].append({
                            "where": loc, "name": shape.name,
                            "detail": f"({l:.2f},{t:.2f})–({r:.2f},{b:.2f})in vs "
                                      f"{slide_w_in:.2f}×{slide_h_in:.2f}in"})
            except Exception:
                pass

            frames = text_frames_of(shape)
            if not frames:
                continue
            shape_fill, fill_src = backdrop_for(zi, layers, bg)

            for tframe, cell_ref, cell in frames:
                where = loc + (f" {cell_ref}" if cell_ref else "")
                fill = shape_fill
                if cell is not None:
                    cf = _fill_of(cell._tc.find(f"{A}tcPr"), theme)
                    if cf is not None:
                        fill = cf
                text_here = tframe.text.strip()
                if not text_here:
                    idx, _ = _ph_idx(shape)
                    if idx is not None and cell is None:
                        findings["empty_placeholders"].append({"where": where, "name": shape.name})
                    continue
                s_words += len(text_here.split())

                for para in tframe.paragraphs:
                    for run in para.runs:
                        if not run.text.strip():
                            continue
                        checked_runs += 1
                        pt, src = resolve_font_pt(run, para, shape, slide, prs, mstyles)
                        sizes.add(round(pt, 1))
                        if src.startswith("PowerPoint default"):
                            findings["unresolved_size"].append({
                                "where": where, "text": run.text.strip()[:40],
                                "why": "no size found anywhere in the chain; assumed 18pt"})
                        if pt < floor_pt:
                            findings["tiny_text"].append({
                                "where": where, "pt": pt, "floor": floor_pt, "source": src,
                                "text": run.text.strip()[:48]})
                        fg, fg_src = resolve_font_colour(
                            run, para, shape, slide, prs, mstyles, theme)
                        if fg is None:
                            # Inherited from theme/placeholder. Say so; do not assume black.
                            findings["unmeasured_contrast"].append({
                                "where": where, "why": "text colour resolves nowhere in the chain",
                                "text": run.text.strip()[:40]})
                        elif fill is UNKNOWN_FILL:
                            findings["unmeasured_contrast"].append({
                                "where": where, "why": f"background is indeterminate ({fill_src})",
                                "text": run.text.strip()[:40]})
                        else:
                            ratio = contrast(fg, fill)
                            large = is_large_text(pt, run.font.bold)
                            need_ratio = 3.0 if large else 4.5
                            if ratio < need_ratio:
                                findings["low_contrast"].append({
                                    "where": where, "ratio": round(ratio, 2), "need": need_ratio,
                                    "pt": pt, "text": run.text.strip()[:40]})
        per_slide.append({"slide": n, "shapes": s_shapes, "words": s_words})

    return {
        "file": Path(path).name,
        "slides": len(prs.slides),
        "aspect": f"{slide_w_in:.2f}x{slide_h_in:.2f}in",
        "checked": {"shapes": checked_shapes, "runs": checked_runs},
        "type_sizes": sorted(sizes),
        "legibility_floor_pt": floor_pt,
        "legibility_source": "explicit --min-pt" if min_pt else f"{need} viewing need",
        "room_depth_ft": room_depth_ft,
        "needed_screen_height_ft": round(needed_screen_h_ft, 1) if needed_screen_h_ft else None,
        "findings": findings,
        "per_slide": per_slide,
        "theme_colours": theme,
    }


def report(r, fail_on):
    f = r["findings"]
    n = {k: len(v) for k, v in f.items()}
    ok = lambda c: "PASS" if c == 0 else "FAIL"
    print(f"\n{r['file']} — {r['slides']} slides, {r['aspect']}")
    print(f"  checked {r['checked']['shapes']} shapes / {r['checked']['runs']} text runs")
    if r["checked"]["runs"] == 0:
        print("  🔴 NO TEXT RUNS MEASURED — not a pass. The deck may be image-only, "
              "or the reader failed.")
    print()
    print(f"  nativeCharts   {n['native_charts']} {ok(n['native_charts'])}"
          f"   — flatten to dead images on Google Slides import")
    print(f"  legibility     {n['tiny_text']} below {r['legibility_floor_pt']}pt "
          f"{ok(n['tiny_text'])}   — {r['legibility_source']}")
    print(f"  contrast       {n['low_contrast']} WCAG AA failures {ok(n['low_contrast'])}")
    print(f"  offSlide       {n['offslide']} {ok(n['offslide'])}")
    print(f"  emptyPlaceholder {n['empty_placeholders']} {ok(n['empty_placeholders'])}")
    print(f"  unresolvedSize {n['unresolved_size']}"
          + ("  ⚠️  assumed 18pt — verify by hand" if n["unresolved_size"] else ""))
    print(f"  unmeasured     {n['unmeasured_contrast']} run(s) whose contrast could NOT be "
          f"computed" + ("  ⚠️  not a pass" if n["unmeasured_contrast"] else ""))
    print(f"  typeSizes      {r['type_sizes']}")
    if r["needed_screen_height_ft"]:
        print(f"\n  A {r['room_depth_ft']:.0f}ft room at the '{r['legibility_source']}' needs a "
              f"screen at least {r['needed_screen_height_ft']}ft high")
        print(f"  ({r['needed_screen_height_ft'] * 16 / 9:.1f}ft wide at 16:9). Undersize the "
              f"screen and no point size saves you.")
    print()
    for key, label, mark in (("native_charts", "NATIVE CHART", "🔴"),
                             ("tiny_text", "TOO SMALL", "🔴"),
                             ("low_contrast", "LOW CONTRAST", "⚠️ "),
                             ("offslide", "OFF-SLIDE", "⚠️ ")):
        for item in f[key][:8]:
            detail = item.get("why") or item.get("detail") or ""
            extra = ""
            if key == "tiny_text":
                extra = f" {item['pt']}pt (from {item['source']}) “{item['text']}”"
            elif key == "low_contrast":
                extra = f" {item['ratio']}:1 need {item['need']} “{item['text']}”"
            print(f"  {mark} [{label}] {item['where']}{extra}")
            if detail:
                print(f"      {detail}")
    print("\n  caveat: static file analysis. Says nothing about whether the deck is any good,")
    print("  whether the story works, or how it reads when projected in a lit room.\n")
    total = sum(n.values())
    hard = n["native_charts"] + n["tiny_text"] + n["low_contrast"]
    # Measuring nothing is not passing. A reader that silently traverses no text is
    # the single most dangerous state this tool can be in, because it reports green.
    if r["checked"]["runs"] == 0:
        hard += 1
        total += 1
    if fail_on == "none":
        return 0
    return 1 if (total if fail_on == "any" else hard) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--room-depth", type=float, default=None,
                    help="farthest viewer distance in feet; reports the screen size it demands")
    ap.add_argument("--screen-height", type=float, default=None,
                    help="actual screen height in INCHES; with --room-depth this measures the "
                         "real room instead of assuming the 4/6/8 rule")
    ap.add_argument("--viewing-need", choices=list(VIEWING_NEED), default="basic",
                    help="analytical (dense tables) / basic (default) / passive (back of a hall)")
    ap.add_argument("--min-pt", type=float, default=None, help="override the point-size floor")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["hard", "any", "none"], default="hard")
    a = ap.parse_args()
    if not a.file.exists():
        print(f"ERROR: file not found: {a.file}", file=sys.stderr)
        return 1
    if a.screen_height and not a.room_depth:
        print("ERROR: --screen-height needs --room-depth to mean anything.", file=sys.stderr)
        return 2
    try:
        r = audit(a.file, a.room_depth, a.min_pt, a.viewing_need, a.screen_height)
    except Exception as e:
        print(f"ERROR: could not read {a.file}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(r, indent=2))
        f = r["findings"]
        hard = len(f["native_charts"]) + len(f["tiny_text"]) + len(f["low_contrast"])
        return 0 if a.fail_on == "none" else (1 if hard else 0)
    return report(r, a.fail_on)


if __name__ == "__main__":
    sys.exit(main())
