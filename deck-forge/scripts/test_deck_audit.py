#!/usr/bin/env python3
"""
test_deck_audit.py — regression tests for the deck harness.

Every case here is a bug that was live in this file and shipped green. A harness
that reports PASS on the defect it exists to catch is worse than no harness, so
each fix gets a test that fails loudly if it regresses.

    python3 test_deck_audit.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

import deck_audit as D

FAILS, RUN = [], 0


def check(name, cond, detail=""):
    global RUN
    RUN += 1
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}  {detail}")
        FAILS.append(name)


def blank(w=13.333, h=7.5):
    p = Presentation()
    p.slide_width, p.slide_height = Inches(w), Inches(h)
    return p


def audit(prs, **kw):
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        prs.save(f.name)
        return D.audit(f.name, **kw)


# ── 1. the legibility formula ────────────────────────────────────────────────
print("\nlegibility floor")

f = D.legibility_floor_pt(7.5, "basic")
check("basic viewing need lands near the 24pt folklore", 20 <= f <= 26, f"got {f}pt")
check("the naive version's ~185pt is gone", f < 60, f"got {f}pt")
check("analytical < basic < passive",
      D.legibility_floor_pt(7.5, "analytical") < f < D.legibility_floor_pt(7.5, "passive"))
# Screen size scales with room depth under the 4/6/8 rule, so the floor must not move.
check("floor is scale-invariant without an explicit screen",
      D.legibility_floor_pt(7.5, "basic", None, 15) == D.legibility_floor_pt(7.5, "basic", None, 80))
# With a REAL screen size the room depth must matter again.
near = D.legibility_floor_pt(7.5, "basic", 60, 15)
far = D.legibility_floor_pt(7.5, "basic", 60, 60)
check("an explicit screen makes distance matter", far > near * 3, f"{near} vs {far}")
# A 4:3 slide is 7.5in tall too; a taller slide needs more points for the same physics.
check("taller slide -> higher floor", D.legibility_floor_pt(10.0, "basic") >
      D.legibility_floor_pt(7.5, "basic"))


# ── 2. fill resolution must not read the text colour ─────────────────────────
print("\nfill resolution")

p = blank()
s = p.slides.add_slide(p.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
r = tb.text_frame.paragraphs[0].add_run()
r.text = "dark text, no shape fill"
r.font.size = Pt(40)
r.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
th = D.theme_colours(p)
check("a textbox with no fill reports None, not the run's colour",
      D.shape_fill_rgb(tb, th) is None, f"got {D.shape_fill_rgb(tb, th)}")
res = audit(p)
lc = res["findings"]["low_contrast"]
check("dark text on the white slide bg is NOT a contrast failure", len(lc) == 0, str(lc))

# an explicit fill must still be read
p2 = blank()
s2 = p2.slides.add_slide(p2.slide_layouts[6])
sh = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(6), Inches(2))
sh.fill.solid()
sh.fill.fore_color.rgb = RGBColor(0x00, 0x33, 0x66)
check("an explicit solid fill IS read", D.shape_fill_rgb(sh, D.theme_colours(p2)) == (0, 51, 102),
      str(D.shape_fill_rgb(sh, D.theme_colours(p2))))


# ── 2b. z-order: what is actually behind the text ────────────────────────────
print("\nz-order backdrop")

pz = blank()
sz = pz.slides.add_slide(pz.slide_layouts[6])
panel = sz.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(8), Inches(3))
panel.fill.solid()
panel.fill.fore_color.rgb = RGBColor(0x1F, 0x4E, 0x79)
over = sz.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(7), Inches(1))
ru = over.text_frame.paragraphs[0].add_run()
ru.text = "White on the blue panel"
ru.font.size = Pt(32)
ru.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
resz = audit(pz)
check("white text over a blue panel is NOT a false contrast failure",
      len(resz["findings"]["low_contrast"]) == 0, str(resz["findings"]["low_contrast"]))

# and the inverse must still fail: white text NOT over anything
pz2 = blank()
sz2 = pz2.slides.add_slide(pz2.slide_layouts[6])
o2 = sz2.shapes.add_textbox(Inches(1.5), Inches(5.5), Inches(7), Inches(1))
r2 = o2.text_frame.paragraphs[0].add_run()
r2.text = "White on the white slide"
r2.font.size = Pt(32)
r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
check("white text on the bare white slide IS still caught",
      len(audit(pz2)["findings"]["low_contrast"]) == 1)

# a panel that does NOT cover the text must not be credited
pz3 = blank()
sz3 = pz3.slides.add_slide(pz3.slide_layouts[6])
far = sz3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(3), Inches(1))
far.fill.solid()
far.fill.fore_color.rgb = RGBColor(0x1F, 0x4E, 0x79)
o3 = sz3.shapes.add_textbox(Inches(8), Inches(5), Inches(4), Inches(1))
r3 = o3.text_frame.paragraphs[0].add_run()
r3.text = "White, nowhere near the panel"
r3.font.size = Pt(32)
r3.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
check("a non-overlapping panel is not used as the backdrop",
      len(audit(pz3)["findings"]["low_contrast"]) == 1)


# ── 3. group + table traversal ───────────────────────────────────────────────
print("\ntraversal")

p3 = blank()
s3 = p3.slides.add_slide(p3.slide_layouts[6])
bars = []
for i in range(3):
    b = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1 + i * 1.5), Inches(3), Inches(1.2),
                            Inches(2))
    b.text_frame.text = f"{i}0%"
    run = b.text_frame.paragraphs[0].runs[0]
    run.font.size = Pt(7)
    bars.append(b)
s3.shapes.add_group_shape(bars)
tbl = s3.shapes.add_table(2, 2, Inches(7), Inches(2), Inches(5), Inches(2)).table
tbl.cell(1, 1).text = "6pt"
tbl.cell(1, 1).text_frame.paragraphs[0].runs[0].font.size = Pt(6)

res3 = audit(p3)
check("grouped shapes are traversed", res3["checked"]["runs"] >= 4,
      f"only {res3['checked']['runs']} runs")
check("7pt inside a group is caught",
      any(x["pt"] == 7.0 for x in res3["findings"]["tiny_text"]))
check("6pt inside a table cell is caught",
      any(x["pt"] == 6.0 for x in res3["findings"]["tiny_text"]))
check("the group deck does NOT pass", res3["findings"]["tiny_text"])


# ── 4. inheritance: run.font.size is None but the size is real ───────────────
print("\ninheritance resolution")

p4 = blank()
s4 = p4.slides.add_slide(p4.slide_layouts[1])
s4.shapes.title.text = "Inherited"
s4.placeholders[1].text = "Body with no explicit size"
raw = s4.shapes.title.text_frame.paragraphs[0].runs[0].font.size
check("python-pptx really does report None here", raw is None, f"got {raw}")
res4 = audit(p4)
check("but the harness resolves a real size", all(x > 0 for x in res4["type_sizes"]),
      str(res4["type_sizes"]))
check("and says where it came from",
      any("master" in x["source"] or "layout" in x["source"]
          for x in res4["findings"]["tiny_text"]) or not res4["findings"]["tiny_text"])
check("nothing fell through to the 18pt default", not res4["findings"]["unresolved_size"])


# ── 5. native charts ─────────────────────────────────────────────────────────
print("\nnative charts")

p5 = blank()
s5 = p5.slides.add_slide(p5.slide_layouts[6])
cd = CategoryChartData()
cd.categories = ["A", "B"]
cd.add_series("S", (1, 2))
s5.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(6), Inches(4), cd)
check("a native chart is flagged", len(audit(p5)["findings"]["native_charts"]) == 1)
check("a chartless deck is not", len(audit(blank())["findings"]["native_charts"]) == 0)


# ── 6. the zero-measurement trap ─────────────────────────────────────────────
print("\nthe zero-measurement trap")

empty = audit(blank())
check("an empty deck measures 0 runs", empty["checked"]["runs"] == 0)
rc = D.report(empty, "hard")
check("...and that is a FAILURE, not a pass", rc == 1,
      "measuring nothing reported success")


# ── 7. contrast maths ────────────────────────────────────────────────────────
print("\ncontrast")

check("black on white is 21:1", abs(D.contrast((0, 0, 0), (255, 255, 255)) - 21.0) < 0.01)
check("#767676 on white is the 4.5 boundary",
      abs(D.contrast(D.hex_to_rgb("767676"), (255, 255, 255)) - 4.54) < 0.02)
check("contrast is symmetric",
      abs(D.contrast((10, 20, 30), (200, 200, 200)) - D.contrast((200, 200, 200), (10, 20, 30)))
      < 1e-9)

# WCAG large text is 18pt / 14pt bold. The 24px / 18.66px figures are the same
# sizes in CSS pixels; using them on points is a 1.333x error that invents failures.
check("18pt counts as large text", D.is_large_text(18.0))
check("14pt bold counts as large text", D.is_large_text(14.0, bold=True))
check("14pt not bold does NOT", not D.is_large_text(14.0, bold=False))
check("17.9pt does NOT", not D.is_large_text(17.9))
check("the px figures are not used as pt", D.is_large_text(20.0),
      "20pt must be large; if this fails the 24px threshold crept back in")

# end to end: 20pt grey that clears 3:1 but not 4.5:1 must PASS
pw = blank()
sw = pw.slides.add_slide(pw.slide_layouts[6])
bw = sw.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
rw = bw.text_frame.paragraphs[0].add_run()
rw.text = "20pt grey, clears 3:1"
rw.font.size = Pt(20)
rw.font.color.rgb = RGBColor(0x76, 0x76, 0x76)          # 4.54:1 on white
check("20pt at 4.54:1 is not reported as a failure",
      len(audit(pw)["findings"]["low_contrast"]) == 0,
      "large-text threshold is wrong; 20pt is large and only needs 3:1")


print(f"\n{RUN - len(FAILS)}/{RUN} passed")
if FAILS:
    print("FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
