#!/usr/bin/env python3
"""Tests for the post tools on synthetic media: post_sweep.py, sync_offset.py, chain_join.py.

Each suite asserts the benign case stays quiet before asserting the bad case is caught. Needs ffmpeg and ffprobe.
post_sweep needs nothing else; sync_offset needs numpy; chain_join align needs OpenCV (skipped when missing):

    uv run --with numpy --with opencv-python-headless python test_post_tools.py
"""
import io
import json
import contextlib
import os
import subprocess
import sys
import tempfile
import unittest
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import post_sweep  # noqa: E402

try:
    import numpy as np
    import sync_offset
    HAVE_NP = True
except (ImportError, SystemExit):
    HAVE_NP = False
try:
    import cv2  # noqa: F401
    import chain_join
    HAVE_CV = HAVE_NP
except (ImportError, SystemExit):
    HAVE_CV = False

FF = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]


def frame_rgb(video, t, w=64, h=36):
    raw = subprocess.run(FF[:-1] + ["-ss", f"{t}", "-i", video, "-frames:v", "1", "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                                    "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return raw


def mean_abs(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / max(1, len(a))


def probe_wh(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return r.stdout.strip()


class PostSweep(unittest.TestCase):
    def test_filter_string(self):
        vf = post_sweep.sweep_filter(4.0, 854, 480)
        self.assertIn("eval=frame", vf)
        self.assertIn("cos(PI*t/4.000)", vf)
        self.assertIn("crop=1708:960", vf)
        self.assertTrue(vf.endswith("scale=854:480,setsar=1"))

    def test_sweep_moves_the_frame(self):
        with tempfile.TemporaryDirectory() as d:
            src, out, still = (os.path.join(d, n) for n in ("src.mp4", "out.mp4", "still.mp4"))
            subprocess.run(FF + ["-f", "lavfi", "-i", "testsrc2=s=2560x1440:r=24:d=2", "-pix_fmt", "yuv420p", src], check=True)
            # benign: zoom and pan pinned give a static framing, so start and end frames of a static source match
            subprocess.run(FF + ["-f", "lavfi", "-i", "color=c=gray:s=2560x1440:r=24:d=2", "-pix_fmt", "yuv420p", still], check=True)
            self.assertEqual(post_sweep.main([still, out, "--zoom", "1.2", "1.2", "--pan", "0.5", "0.5"]), 0)
            self.assertLess(mean_abs(frame_rgb(out, 0), frame_rgb(out, 1.9)), 2.0)
            # the sweep: output size and duration hold, and the framing really travels
            self.assertEqual(post_sweep.main([src, out]), 0)
            self.assertEqual(probe_wh(out), "854,480")
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                                       capture_output=True, text=True).stdout)
            self.assertAlmostEqual(dur, 2.0, delta=0.1)
            self.assertGreater(mean_abs(frame_rgb(out, 0), frame_rgb(out, 1.9)), 10.0)

    def test_bad_zoom_refused(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src.mp4")
            subprocess.run(FF + ["-f", "lavfi", "-i", "color=c=gray:s=640x360:r=24:d=1", "-pix_fmt", "yuv420p", src], check=True)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                post_sweep.main([src, os.path.join(d, "o.mp4"), "--zoom", "0.8", "1.2"])


def write_wav(path, x, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32000).astype("<i2").tobytes())


@unittest.skipUnless(HAVE_NP, "sync_offset needs numpy: uv run --with numpy ...")
class SyncOffset(unittest.TestCase):
    SR = 16000

    def make(self, d):
        rng = np.random.default_rng(7)
        # a "vocal stem": 20 s of bursty noise (syllable-like envelope) so the correlation has one clear peak
        t = np.arange(20 * self.SR) / self.SR
        stem = rng.standard_normal(t.size) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * t) ** 2) * 0.3
        stem_p = os.path.join(d, "vocals.wav")
        write_wav(stem_p, stem, self.SR)
        # a "generated clip" whose soundtrack is the stem from 10.40 s: asked for 10.00, came back 0.40 s late
        seg = stem[int(10.4 * self.SR): int(14.4 * self.SR)]
        seg_p = os.path.join(d, "seg.wav")
        write_wav(seg_p, seg, self.SR)
        clip = os.path.join(d, "14-sings.mp4")
        subprocess.run(FF + ["-f", "lavfi", "-i", "color=c=gray:s=64x36:r=24:d=4", "-i", seg_p, "-shortest", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "128k", clip], check=True)
        with open(os.path.join(d, "14-sings.json"), "w") as f:
            json.dump({"job": "x", "audio_ref_start": 10.0}, f)
        other = os.path.join(d, "other.mp4")
        noise = os.path.join(d, "noise.wav")
        write_wav(noise, rng.standard_normal(4 * self.SR) * 0.3, self.SR)
        subprocess.run(FF + ["-f", "lavfi", "-i", "color=c=gray:s=64x36:r=24:d=4", "-i", noise, "-shortest", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", other], check=True)
        return stem_p, clip, other

    def test_finds_offset_and_writes_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            stem, clip, _ = self.make(d)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sync_offset.main([clip, "--ref", stem, "--slot", "10.0", "--write-sidecar", "--json"])
            self.assertEqual(rc, 0)
            r = json.loads(buf.getvalue())[clip]
            self.assertAlmostEqual(r["T"], 10.4, delta=0.01)   # AAC priming may shift a few ms
            self.assertGreater(r["peak"], 0.9)
            self.assertAlmostEqual(r["enter_at"], -0.4, delta=0.01)
            with open(os.path.join(d, "14-sings.json")) as f:
                side = json.load(f)
            self.assertAlmostEqual(side["song_t0"], 10.4, delta=0.01)
            self.assertEqual(side["job"], "x")  # existing sidecar fields kept

    def test_unrelated_audio_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            stem, _, other = self.make(d)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sync_offset.main([other, "--ref", stem, "--nominal", "10.0", "--write-sidecar"])
            self.assertEqual(rc, 1)
            self.assertIn("LOW PEAK", buf.getvalue())
            self.assertFalse(os.path.exists(os.path.join(d, "other.json")))  # an unreliable T is never written


@unittest.skipUnless(HAVE_CV, "chain_join needs numpy + OpenCV: uv run --with numpy --with opencv-python-headless ...")
class ChainJoin(unittest.TestCase):
    def test_check_quiet_on_smooth_motion_then_flags_jump(self):
        with tempfile.TemporaryDirectory() as d:
            smooth, jump = os.path.join(d, "smooth.mp4"), os.path.join(d, "jump.mp4")
            subprocess.run(FF + ["-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=2", "-pix_fmt", "yuv420p", smooth], check=True)
            subprocess.run(FF + ["-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=1", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=1",
                                 "-filter_complex", "[1:v]scale=352:198,crop=320:180:20:12[b];[0:v][b]concat=n=2:v=1[v]", "-map", "[v]",
                                 "-pix_fmt", "yuv420p", jump], check=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                chain_join.main(["check", smooth, "1.0"])
            self.assertIn("-> ok", buf.getvalue())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                chain_join.main(["check", jump, "1.0"])
            self.assertIn("-> JUMP", buf.getvalue())

    def test_align_undoes_scale_shift_and_grade(self):
        with tempfile.TemporaryDirectory() as d:
            src, ref, inc, out = (os.path.join(d, n) for n in ("src.mp4", "ref.png", "inc.mp4", "out.mp4"))
            subprocess.run(FF + ["-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=2", "-pix_fmt", "yuv420p", src], check=True)
            subprocess.run(FF + ["-i", src, "-frames:v", "1", ref], check=True)
            # the chained generation: same content, 2.5% larger, shifted, slightly regraded
            subprocess.run(FF + ["-i", src, "-vf", "scale=328:184,crop=320:180:6:3,eq=contrast=1.08:brightness=0.03",
                                 "-pix_fmt", "yuv420p", inc], check=True)
            r = chain_join.align(ref, inc, out)
            self.assertAlmostEqual(r["scale"], 1.025, delta=0.01)
            self.assertLess(r["first_frame_diff_after"], r["first_frame_diff_before"] / 2)
            self.assertEqual(r["frames_written"], r["frames_in"] - 1)  # the repeated reference frame is dropped
            self.assertEqual(probe_wh(out), "320,180")
            # end to end: the outgoing shot holds on ref.png, then the incoming clip. Aligned join is quiet, raw join jumps
            hold = os.path.join(d, "hold.mp4")
            subprocess.run(FF + ["-loop", "1", "-i", ref, "-t", "1", "-r", "24", "-pix_fmt", "yuv420p", hold], check=True)
            for name, clip, verdict in (("fixed", out, "-> ok"), ("raw", inc, "-> JUMP")):
                joined = os.path.join(d, f"{name}.mp4")
                subprocess.run(FF + ["-i", hold, "-i", clip, "-filter_complex",
                                     "[0:v]fps=24,setsar=1[a];[1:v]fps=24,setsar=1[b];[a][b]concat=n=2:v=1[v]", "-map", "[v]",
                                     "-pix_fmt", "yuv420p", joined], check=True)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    chain_join.main(["check", joined, "1.0"])
                self.assertIn(verdict, buf.getvalue(), (name, buf.getvalue()))
            # last-frame grabs the final frame, which differs from the first in a moving source
            lf = os.path.join(d, "last.png")
            chain_join.main(["last-frame", src, lf])
            self.assertTrue(os.path.getsize(lf) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
