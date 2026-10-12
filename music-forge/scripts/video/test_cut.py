#!/usr/bin/env python3
"""End-to-end tests on synthetic media: cut.py, teasers.py, and build_clips.py against a local mock API.

A 6 s sine "song", three solid-colour clips of the wrong lengths and sizes, and a plan that tiles the song.
Needs ffmpeg and ffprobe. The caption test needs ImageMagick (`magick`) or an ffmpeg with the subtitles filter.

    uv run python test_cut.py
"""
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_clips as bc  # noqa: E402
import cut  # noqa: E402
import plan_lib as pl  # noqa: E402
import review_frames  # noqa: E402
import teasers  # noqa: E402

FF = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]
SONG_S = 6.0
FPS = 30


def make_project(d):
    os.makedirs(os.path.join(d, "frames"))
    os.makedirs(os.path.join(d, "clips"))
    subprocess.run(FF + ["-f", "lavfi", "-i", f"sine=f=330:d={SONG_S}", "-c:a", "aac", os.path.join(d, "song.m4a")], check=True)
    colors = {"red": "red", "green": "green", "blue": "blue"}
    plan = {"title": "Synthetic Test", "audio": "song.m4a", "fps": FPS, "style": "test", "shots": []}
    spec = [("01", "00:00.00-00:02.50", 2.0, "640x360", 25), ("02", "00:02.50-00:04.00", 3.0, "320x240", 24),
            ("03", "00:04.00-00:06.00", 4.0, "1280x720", 30)]
    for (sid, t, clip_s, size, rate), col in zip(spec, colors):
        slug = f"shot-{col}"
        subprocess.run(FF + ["-f", "lavfi", "-i", f"color=c={col}:s={size}:r={rate}:d={clip_s}", "-pix_fmt", "yuv420p",
                             os.path.join(d, "clips", f"{sid}-{slug}.mp4")], check=True)
        subprocess.run(FF + ["-f", "lavfi", "-i", f"color=c={col}:s=64x36", "-frames:v", "1", os.path.join(d, "frames", f"{sid}.png")], check=True)
        plan["shots"].append({"id": sid, "time": t, "slug": slug, "description": "x", "frame": sid})
    path = os.path.join(d, "plan.json")
    with open(path, "w") as f:
        json.dump(plan, f)
    return path


def pixel(video, t):
    """RGB of the middle of the frame at time t."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=1:1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return tuple(r.stdout[:3])


class Cut(unittest.TestCase):
    def test_slots_tile_exactly(self):
        shots = [{"id": "a", "start": 0.0, "end": 2.5}, {"id": "b", "start": 2.5, "end": 4.0}, {"id": "c", "start": 4.0, "end": 6.0}]
        slots = cut.frame_slots(shots, 30, 6.0)
        self.assertEqual([n for _, n in slots], [75, 45, 60])
        self.assertEqual(sum(n for _, n in slots), 180)

    def test_cut_duration_within_one_frame(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            out = os.path.join(d, "cuts", "out.mp4")
            self.assertEqual(cut.main([plan, "--out", out, "--small-mb", "1"]), 0)
            audio = pl.probe_duration(os.path.join(d, "song.m4a"))
            video = pl.probe_duration(out)
            self.assertLessEqual(abs(video - audio), 1 / FPS + 1e-3, (video, audio))
            # video stream frame count is exact
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                                "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True)
            self.assertEqual(int(r.stdout.strip()), round(audio * FPS))
            # each slot shows its own clip: red 0-2.5 s, green 2.5-4 s (clip is 3 s, slot 1.5 s), blue 4-6 s (clip is 4 s, slot 2 s)
            for t, ch in ((1.0, 0), (3.0, 1), (5.0, 2)):
                px = pixel(out, t)
                self.assertEqual(max(range(3), key=lambda i: px[i]), ch, (t, px))
            small = os.path.join(d, "cuts", "out-small.mp4")
            self.assertTrue(os.path.exists(small))
            self.assertLessEqual(os.path.getsize(small), 1 * 1024 * 1024)

    def test_missing_clip_falls_back_to_still(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            os.remove(os.path.join(d, "clips", "02-shot-green.mp4"))
            out = os.path.join(d, "o.mp4")
            self.assertEqual(cut.main([plan, "--out", out, "--no-small"]), 0)
            self.assertLessEqual(abs(pl.probe_duration(out) - SONG_S), 1 / FPS + 1e-3)

    def test_gappy_plan_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            with open(plan) as f:
                p = json.load(f)
            p["shots"][1]["time"] = "00:03.00-00:04.00"
            with open(plan, "w") as f:
                json.dump(p, f)
            self.assertEqual(cut.main([plan, "--out", os.path.join(d, "o.mp4"), "--no-small"]), 1)

    @unittest.skipUnless(shutil.which("magick") or cut.has_subtitles_filter(), "no way to burn captions here")
    def test_captions(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            srt = os.path.join(d, "c.srt")
            with open(srt, "w") as f:
                f.write("1\n00:00:00,500 --> 00:00:02,000\nHello keeper\n\n2\n00:00:03,000 --> 00:00:05,000\nSecond line\n")
            out = os.path.join(d, "o.mp4")
            self.assertEqual(cut.main([plan, "--out", out, "--no-small", "--captions", srt]), 0)
            self.assertLessEqual(abs(pl.probe_duration(out) - SONG_S), 1 / FPS + 1e-3)


class Review(unittest.TestCase):
    def test_frames_per_shot(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            out = os.path.join(d, "o.mp4")
            cut.main([plan, "--out", out, "--no-small"])
            rd = os.path.join(d, "r")
            self.assertEqual(review_frames.main([plan, out, "--outdir", rd, "--edges"]), 0)
            self.assertEqual(sorted(os.listdir(rd)), sorted(f"{i}-{k}.jpg" for i in ("01", "02", "03") for k in ("mid", "start", "end")))


class Teasers(unittest.TestCase):
    def test_two_aspects(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            out = os.path.join(d, "o.mp4")
            cut.main([plan, "--out", out, "--no-small"])
            od = os.path.join(d, "t")
            self.assertEqual(teasers.main([out, "--window", "first=0:00.5-0:03", "--outdir", od]), 0)
            for name, wh in (("first-16x9.mp4", "1280,720"), ("first-9x16.mp4", "1080,1920")):
                p = os.path.join(od, name)
                self.assertTrue(os.path.exists(p), name)
                r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", p],
                                   capture_output=True, text=True)
                self.assertEqual(r.stdout.strip(), wh)
                self.assertAlmostEqual(pl.probe_duration(p), 2.5, delta=0.1)

    @unittest.skipUnless(shutil.which("magick"), "needs ImageMagick for the end card")
    def test_end_card_adds_time(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            out = os.path.join(d, "o.mp4")
            cut.main([plan, "--out", out, "--no-small"])
            od = os.path.join(d, "t")
            self.assertEqual(teasers.main([out, "--window", "a=0-2", "--title", "Test Title", "--no-vertical", "--outdir", od]), 0)
            self.assertAlmostEqual(pl.probe_duration(os.path.join(od, "a-16x9.mp4")), 3.5, delta=0.15)


class MockVideoAPI(http.server.BaseHTTPRequestHandler):
    submitted = []

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        MockVideoAPI.submitted.append((self.headers.get("Authorization"), body))
        if body["model"] == "refuse/me":
            return self._send(400, {"error": "InputImageSensitiveContentDetected.PrivacyInformation"})
        self._send(200, {"id": "job-" + str(len(MockVideoAPI.submitted)), "status": "pending"})

    def do_GET(self):
        if self.path.endswith("/content"):
            return self._send(200, MockVideoAPI.clip, "video/mp4")
        self._send(200, {"status": "completed", "usage": {"cost": 0.25}})


class BuildClips(unittest.TestCase):
    def test_live_run_against_mock(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            for f in os.listdir(os.path.join(d, "clips")):
                os.remove(os.path.join(d, "clips", f))
            sample = os.path.join(d, "sample.mp4")
            subprocess.run(FF + ["-f", "lavfi", "-i", "color=c=gray:s=64x36:d=1", "-pix_fmt", "yuv420p", sample], check=True)
            with open(sample, "rb") as f:
                MockVideoAPI.clip = f.read()
            MockVideoAPI.submitted = []
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockVideoAPI)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            bc.API = f"http://127.0.0.1:{srv.server_port}/videos"
            os.environ["OPENROUTER_API_KEY"] = "test-key-not-real"
            try:
                args = [plan, "--poll-interval", "0.01", "--workers", "2"]
                # ceiling below the estimate: refused before any request
                self.assertEqual(bc.main(args + ["--max-usd", "0.01"]), 1)
                self.assertEqual(MockVideoAPI.submitted, [])
                # real run
                self.assertEqual(bc.main(args + ["--max-usd", "50"]), 0)
                self.assertEqual(len(MockVideoAPI.submitted), 3)
                self.assertTrue(all(auth == "Bearer test-key-not-real" for auth, _ in MockVideoAPI.submitted))
                for sid, slug in (("01", "shot-red"), ("02", "shot-green"), ("03", "shot-blue")):
                    self.assertTrue(os.path.exists(os.path.join(d, "clips", f"{sid}-{slug}.mp4")))
                    with open(os.path.join(d, "clips", f"{sid}-{slug}.json")) as f:
                        side = json.load(f)
                    self.assertEqual(side["cost"], 0.25)
                    self.assertTrue(side["job"].startswith("job-"))
                # silent run: no audio fields were sent
                for _, body in MockVideoAPI.submitted:
                    self.assertNotIn("input_references", body)
                # resumable: second run submits nothing
                self.assertEqual(bc.main(args), 0)
                self.assertEqual(len(MockVideoAPI.submitted), 3)
            finally:
                srv.shutdown()

    def test_refusal_reports_hint(self):
        with tempfile.TemporaryDirectory() as d:
            plan = make_project(d)
            for f in os.listdir(os.path.join(d, "clips")):
                os.remove(os.path.join(d, "clips", f))
            MockVideoAPI.submitted = []
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockVideoAPI)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            bc.API = f"http://127.0.0.1:{srv.server_port}/videos"
            os.environ["OPENROUTER_API_KEY"] = "test-key-not-real"
            try:
                import io
                import contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    bc.main([plan, "--model", "refuse/me", "--only", "01", "--poll-interval", "0.01"])
                self.assertIn("face filter", buf.getvalue())
            finally:
                srv.shutdown()

    def test_dry_run_needs_no_key(self):
        os.environ.pop("OPENROUTER_API_KEY", None)
        fixture = os.path.join(HERE, "fixtures", "example-plan.json")
        self.assertEqual(bc.main([fixture, "--dry-run"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
