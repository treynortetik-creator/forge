#!/usr/bin/env python3
"""
test_render_diff.py — regression tests for the render diff.

Generates its own fixtures with ffmpeg, so there is nothing to check in and nothing
to go stale. Needs ffmpeg and Pillow.

The two cases that matter most are the first two, and they pull in opposite
directions: a heavy re-encode must produce NOTHING, and one bad second in one corner
must produce a marker. A tool that only satisfies one of those is useless — either it
cries wolf on every export or it misses the thing you are looking for.

    python3 test_render_diff.py
"""
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
import pathlib

sys.path.insert(0, str(Path(__file__).parent))
import render_diff as R

FAILS, RUN = [], 0
TMP = Path(tempfile.mkdtemp(prefix="renderdiff-test-"))


def check(name, cond, detail=""):
    global RUN
    RUN += 1
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}  {detail}")
        FAILS.append(name)


def ff(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"fixture build failed: {r.stderr[:300]}")


def md5(p):
    import hashlib
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


if not shutil.which("ffmpeg"):
    print("SKIP: ffmpeg not on PATH")
    sys.exit(0)

print(f"\nfixtures in {TMP}")
src = TMP / "src.mp4"
ff("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=6",
   "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(src))

# ── 1. a heavy re-encode must be SILENT ──────────────────────────────────────
print("\nfalse positives (the property that makes it usable)")
reenc = TMP / "reencode.mp4"
ff("-i", str(src), "-c:v", "libx264", "-crf", "32", "-pix_fmt", "yuv420p", str(reenc))
frames = R.video_psnr(src, reenc)
flagged, base, thr, _m = R.flag_frames(frames)
check("CRF 18 vs CRF 32 produces no markers", len(flagged) == 0,
      f"{len(flagged)} frames flagged at baseline {base:.1f}dB")
check("...and the baseline reflects the real noise floor", 25 < base < 55, f"{base:.2f}dB")

# a second, even harsher re-encode
reenc2 = TMP / "reencode2.mp4"
ff("-i", str(src), "-c:v", "mpeg4", "-q:v", "8", str(reenc2))
f2, b2, _, _ = R.flag_frames(R.video_psnr(src, reenc2))
check("a different CODEC entirely still produces no markers", len(f2) == 0,
      f"{len(f2)} flagged at baseline {b2:.1f}dB")

# ── 2. one corner, one second, must be FOUND ─────────────────────────────────
print("\ntrue positives")
corner = TMP / "corner.mp4"
ff("-i", str(src), "-vf",
   "drawbox=x=560:y=280:w=70:h=70:color=magenta@1.0:t=fill:enable='between(t,3,4)'",
   "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(corner))
fc, bc, _, _ = R.flag_frames(R.video_psnr(src, corner))
ranges = R.group_ranges(fc, 24.0)
check("a 70x70 box for 1s in a 640x360 frame is caught", len(fc) > 0)
check("...and collapses to ONE marker, not 24", len(ranges) == 1, f"{len(ranges)} ranges")
if ranges:
    r0 = ranges[0]
    check("the marker lands in the right second",
          2.8 <= r0["start_frame"] / 24 <= 3.3 and 3.8 <= r0["end_frame"] / 24 <= 4.3,
          f"{r0['start_tc']} -> {r0['end_tc']}")
    check("the marker carries the worst dB", r0["worst_psnr_db"] < bc)

# ── 3. grouping and timecode ─────────────────────────────────────────────────
print("\ngrouping and timecode")
g = R.group_ranges([(10, 20.0), (11, 19.0), (12, 21.0), (60, 15.0), (61, 16.0)], 24.0)
check("two clusters group into two markers", len(g) == 2, str(len(g)))
check("the worst value in a run wins", g[0]["worst_psnr_db"] == 19.0)
check("timecode is HH:MM:SS:FF", R.timecode(0, 24) == "00:00:00:00", R.timecode(0, 24))
check("one second in is 00:00:01:00", R.timecode(24, 24) == "00:00:01:00", R.timecode(24, 24))
check("an hour in is 01:00:00:00", R.timecode(24 * 3600, 24) == "01:00:00:00",
      R.timecode(24 * 3600, 24))
check("no fps degrades to a frame number", "frame" in R.timecode(5, None))

# ── 4. structural mismatch is reported BEFORE pixels ─────────────────────────
print("\nstructural mismatch")
small = TMP / "small.mp4"
ff("-i", str(src), "-vf", "scale=320:180", "-c:v", "libx264", "-crf", "18",
   "-pix_fmt", "yuv420p", str(small))
cont = R.compare_containers(R.probe(src), R.probe(small))
check("a resolution mismatch is reported", any(c["kind"] == "resolution" for c in cont),
      str(cont))
shorter = TMP / "short.mp4"
ff("-i", str(src), "-t", "2", "-c", "copy", str(shorter))
cont2 = R.compare_containers(R.probe(src), R.probe(shorter))
check("a duration mismatch is reported", any(c["kind"] == "duration" for c in cont2))
check("identical files report no structural difference",
      R.compare_containers(R.probe(src), R.probe(src)) == [])

# ── 5. stills ────────────────────────────────────────────────────────────────
print("\nstills")
try:
    from PIL import Image
    a_png, b_png, c_png = TMP / "a.png", TMP / "b.png", TMP / "c.png"
    ff("-i", str(src), "-vframes", "1", str(a_png))
    shutil.copy(a_png, b_png)
    im = Image.open(a_png).convert("RGB")
    im.putpixel((500, 300), (0, 255, 0) if im.getpixel((500, 300)) != (0, 255, 0) else (255, 0, 0))
    im.save(c_png)
    check("identical stills report identical", R.image_diff(a_png, b_png)["identical"])
    d = R.image_diff(a_png, c_png)
    check("a ONE PIXEL change is caught", not d["identical"])
    check("...and the bounding box is exactly that pixel", d["bbox"] == (500, 300, 501, 301),
          str(d["bbox"]))
    check("a one-pixel change is classified LOCALISED", d["mode"] == "localised", d["mode"])

    # ── the blind spot ────────────────────────────────────────────────────────
    # Every "identical" stills fixture above is a shutil.copy, so until 2026-08-14 the
    # still path had NEVER been run against a re-encode. A JPEG round-trip -- a partner
    # re-exporting from Canva, the commonest way a file comes back changed-but-not-edited
    # -- returned a flat DIFFERS, indistinguishable from someone altering the start time.
    # This is the same blind spot the video path already confesses to, in the other
    # medium, and byte-identical fixtures are how both of them hid.
    j_png = TMP / "jpeg_roundtrip.png"
    Image.open(a_png).convert("RGB").save(TMP / "rt.jpg", quality=92)
    Image.open(TMP / "rt.jpg").convert("RGB").save(j_png)
    check("FIXTURE CONTROL: the round-trip actually changed the bytes",
          md5(a_png) != md5(j_png))
    rt = R.image_diff(a_png, j_png)
    check("a JPEG round-trip is NOT reported identical", not rt["identical"])
    check("...and is classified WHOLE-FRAME, not localised", rt["mode"] == "whole-frame", rt["mode"])
    check("...and covers essentially the entire frame", rt["bbox_coverage"] > 0.9,
          str(rt["bbox_coverage"]))
    check("a targeted edit is never classified whole-frame", d["mode"] == "localised", d["mode"])

    # The evidence that killed the "harmless re-encode" classifier. A real global grade
    # scores BELOW a harmless re-save on both mean and peak, so no amplitude threshold
    # can separate them. If someone re-adds a --ignore-reencode flag, this test is why
    # they should not.
    from PIL import ImageEnhance
    sat = TMP / "saturated.png"
    ImageEnhance.Color(Image.open(a_png).convert("RGB")).enhance(1.15).save(sat)
    rs = R.image_diff(a_png, sat)
    check("a REAL 15% saturation shift is quieter than a harmless JPEG re-save",
          rs["mean_delta"] < rt["mean_delta"] and rs["peak_delta"] < rt["peak_delta"],
          f"grade mean={rs['mean_delta']} peak={rs['peak_delta']} vs "
          f"roundtrip mean={rt['mean_delta']} peak={rt['peak_delta']}")
    check("...so BOTH land in whole-frame and neither is auto-forgiven",
          rs["mode"] == "whole-frame" and rt["mode"] == "whole-frame")

    try:
        R.image_diff(a_png, TMP / "mismatch.png")
        check("missing file raises", False)
    except Exception:
        check("a missing still raises rather than returning a verdict", True)
except ImportError:
    print("  SKIP stills (Pillow missing)")

# ── 6. audio null ────────────────────────────────────────────────────────────
print("\naudio null test")
s1, s2, s6 = TMP / "s1.wav", TMP / "s2.wav", TMP / "s6.wav"
ff("-f", "lavfi", "-i", "sine=frequency=440:duration=3:sample_rate=48000", str(s1))
shutil.copy(s1, s2)
w = wave.open(str(s1), "rb")
prm = w.getparams()
buf = bytearray(w.readframes(w.getnframes()))
w.close()
step = prm.sampwidth * prm.nchannels
buf[int(1.5 * prm.framerate) * step:int(1.51 * prm.framerate) * step] = \
    b"\x00" * (int(0.01 * prm.framerate) * step)
o = wave.open(str(s6), "wb")
o.setparams(prm)
o.writeframes(bytes(buf))
o.close()
# The fixture must actually differ. A previous version of this test used an ffmpeg
# filter that silently did nothing, so both files were byte-identical and the tool's
# correct "identical" verdict looked like a bug. Assert the premise.
check("the dropout fixture really differs from the source", md5(s1) != md5(s6))
check("identical audio nulls to silence", R.audio_null(s1, s2)["nulls"])
n6 = R.audio_null(s1, s6)
check("a 10ms dropout does NOT null", not n6["nulls"],
      f"residual {n6['residual_peak_db']}")
check("...and the residual is loud enough to notice", n6["residual_peak_db"] > -60,
      str(n6["residual_peak_db"]))

# ── 7. helpers ───────────────────────────────────────────────────────────────
print("\nhelpers")
check("median of an even list averages the middle", R.median([1, 2, 3, 4]) == 2.5)
check("median of an odd list is the middle", R.median([5, 1, 3]) == 3)
check("median of nothing is 0", R.median([]) == 0.0)
check("all-inf frames means identical", R.flag_frames([(0, float("inf"))])[0] == [])
check("--absolute overrides the derived threshold",
      R.flag_frames([(0, 30.0), (1, 30.0)], absolute=40.0)[2] == 40.0)
check("flag_frames returns a mode", len(R.flag_frames([(0, 30.0)])) == 4)
check("kind_of recognises video/image/audio",
      (R.kind_of("x.mov"), R.kind_of("x.PNG"), R.kind_of("x.wav")) == ("video", "image", "audio"))
check("kind_of returns None for junk", R.kind_of("x.docx") is None)


# ── 8. findings from the full-project review ─────────────────────────────────
print("\nthe majority-identical case (a smart-render / segment re-export)")

# 🔴 The threshold went VACUOUS on exactly this input. Excluding bit-identical frames
# from the median made the defect its own baseline, so nothing could fall 6dB below
# itself: 120 identical + 24 defect frames reported ZERO and exited 0. Both original
# fixtures were FULL re-encodes, where every frame is finite, so nothing caught it.
fl, base, thr, mode = R.flag_frames(
    [(i, float("inf")) for i in range(120)] + [(120 + i, 20.0) for i in range(24)])
check("a mostly-identical file reports its changed frames", len(fl) == 24, f"{len(fl)} flagged")
check("...and says it was a partial re-encode, not a uniform one", mode == "partial", mode)

fl2, b2, t2, m2 = R.flag_frames(
    [(i, 38.0 + (i % 3)) for i in range(140)] + [(140 + i, 20.0) for i in range(4)])
check("a FULL re-encode still uses the derived threshold", m2 == "reencode", m2)
check("...and still finds only the outliers", len(fl2) == 4, f"{len(fl2)} flagged")

check("a wholly identical pair reports nothing",
      R.flag_frames([(i, float("inf")) for i in range(50)])[0] == [])
check("--absolute overrides the mode choice",
      R.flag_frames([(0, 30.0), (1, 30.0)], absolute=40.0)[3] == "absolute")

print("\nSMPTE timecode at the rates NLEs actually deliver")
# timecode counts FRAMES at the nominal rate, not wall-clock seconds. Dividing by the
# real fps drifts 3.6 s/hour at 29.97 -- ~215 frames into a two-hour sequence, which
# is precisely the scale this tool exists for. The old suite only used fps=24, where
# wall-clock and frame-count happen to coincide.
check("24fps: one hour is 01:00:00:00", R.timecode(86400, 24) == "01:00:00:00",
      R.timecode(86400, 24))
check("25fps: one hour is 01:00:00:00", R.timecode(90000, 25) == "01:00:00:00",
      R.timecode(90000, 25))
check("30fps NDF: one hour is 01:00:00:00", R.timecode(108000, 30) == "01:00:00:00",
      R.timecode(108000, 30))
check("29.97 uses DROP FRAME and lands on the hour",
      R.timecode(107892, 29.97) == "01:00:00;00", R.timecode(107892, 29.97))
check("29.97 marks drop-frame with a semicolon", ";" in R.timecode(100, 29.97))
check("23.976 stays non-drop (drop-frame is undefined for it)",
      ";" not in R.timecode(100, 23.976), R.timecode(100, 23.976))
# the old implementation produced 00:01:60:00 here — seconds never carried to minutes
bad = [f for f in range(0, 200000, 977)
       if int(R.timecode(f, 23.976).replace(";", ":").split(":")[2]) > 59]
check("seconds never exceed 59 (the old carry bug)", not bad, f"{len(bad)} bad frames")
bad2 = [f for f in range(0, 200000, 991)
        if int(R.timecode(f, 29.97).replace(";", ":").split(":")[3]) > 29]
check("frames never exceed the nominal rate", not bad2, f"{len(bad2)} bad")
check("no fps still degrades to a frame number", "frame" in R.timecode(5, None))

# the EDL header must match the timecode it carries
import tempfile as _tf
_p = pathlib.Path(_tf.mktemp(suffix=".edl"))
R.write_edl([{"start_tc": R.timecode(100, 29.97), "end_tc": R.timecode(130, 29.97),
              "frames": 30, "worst_psnr_db": 20.0}], 29.97, _p)
_t = _p.read_text()
check("an EDL at 29.97 declares DROP FRAME", "FCM: DROP FRAME" in _t, _t.splitlines()[1])
R.write_edl([{"start_tc": R.timecode(100, 24), "end_tc": R.timecode(130, 24),
              "frames": 30, "worst_psnr_db": 20.0}], 24, _p)
check("an EDL at 24 declares NON-DROP FRAME", "FCM: NON-DROP FRAME" in _p.read_text())


print(f"\n{RUN - len(FAILS)}/{RUN} passed")
if FAILS:
    print("FAILED: " + ", ".join(FAILS))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
