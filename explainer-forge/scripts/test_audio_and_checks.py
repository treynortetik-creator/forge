#!/usr/bin/env python3
"""Tests that run real code paths with synthetic audio (needs numpy, soundfile, ffmpeg; no model, no whisper).
   python3 scripts/test_audio_and_checks.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import numpy as np
    import soundfile as sf
    import audio_build as ab
    HAVE = shutil.which("ffmpeg") is not None
except ImportError:
    HAVE = False


def make_take(rate):
    """Noise bursts that stand in for speech. Layout (s): 0.5 silence, burst 1.0, 0.5 pause, burst 1.0, 0.8 silence,
    burst 1.0, 2.5 pause (INSIDE the scene), burst 1.0, 0.8 silence."""
    rng = np.random.default_rng(1)

    def burst():
        return (rng.standard_normal(int(1.0 * rate)) * 0.2).astype(np.float32)

    def z(s):
        return np.zeros(int(s * rate), np.float32)
    return np.concatenate([z(0.5), burst(), z(0.5), burst(), z(0.8), burst(), z(2.5), burst(), z(0.8)])


NARR = [{"scene": 1, "title": "a", "chunks": [{"id": "s1a", "show": "alpha beta"}, {"id": "s1b", "show": "gamma delta"}]},
        {"scene": 2, "title": "b", "chunks": [{"id": "s2a", "show": "epsilon zeta"}, {"id": "s2b", "show": "eta theta"}]}]
# whisper-like words for the take above, in seconds of the untrimmed take
WORDS = [["alpha", 0.5, 1.0], ["beta", 1.0, 1.5], ["gamma", 2.0, 2.5], ["delta", 2.5, 3.0],
         ["epsilon", 4.3, 4.8], ["zeta", 4.8, 5.3], ["eta", 7.8, 8.3], ["theta", 8.3, 8.8]]


@unittest.skipUnless(HAVE, "needs numpy, soundfile, ffmpeg")
class SampleRate(unittest.TestCase):
    def test_48k_take_is_resampled_not_misread(self):
        d = tempfile.mkdtemp()
        try:
            y48 = make_take(48000)
            p24, p48 = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
            sf.write(p24, make_take(24000), 24000)
            sf.write(p48, y48, 48000)
            a, b = ab.load_take(p24), ab.load_take(p48)
            self.assertAlmostEqual(len(a) / 24000, len(b) / 24000, delta=0.02)       # same duration, not half or double
            self.assertAlmostEqual(len(b) / 24000, len(y48) / 48000, delta=0.02)
        finally:
            shutil.rmtree(d)

    def test_full_build_same_tempo_at_both_rates(self):
        d = tempfile.mkdtemp()
        try:
            json.dump(NARR, open(os.path.join(d, "n.json"), "w"))
            json.dump(WORDS, open(os.path.join(d, "w.json"), "w"))
            res = {}
            for rate in (24000, 48000):
                take = os.path.join(d, f"t{rate}.wav")
                sf.write(take, make_take(rate), rate)
                out = os.path.join(d, f"o{rate}")
                ab.main(["--take", take, "--narration", os.path.join(d, "n.json"), "--out", out, "--wpm", "70",
                         "--words-json", os.path.join(d, "w.json"), "--scale-words"])
                res[rate] = json.load(open(os.path.join(out, "cues.json")))
            self.assertAlmostEqual(res[24000]["tempo"], res[48000]["tempo"], places=2)
            self.assertAlmostEqual(res[24000]["duration"], res[48000]["duration"], delta=0.1)
            # the 2.5 s pause inside scene 2 is shortened, and the cap is MEASURED on the finished audio
            g = res[24000]["gaps"]
            self.assertLessEqual(g["max_audible_s"], 1.2 + 0.1)
            self.assertTrue(g["pauses_shortened"])
        finally:
            shutil.rmtree(d)


@unittest.skipUnless(HAVE, "needs numpy, soundfile, ffmpeg")
class SqueezeAudio(unittest.TestCase):
    def test_inner_pause_shortened_edges_kept(self):
        y = make_take(24000)
        out, rem = ab.squeeze_silences(y, 1.2)
        self.assertEqual(len(rem), 1)
        self.assertAlmostEqual((len(y) - len(out)) / 24000, 1.3, delta=0.01)


class NameCheck(unittest.TestCase):
    def run_nc(self, *args, home=None):
        env = dict(os.environ)
        if home:
            env.update(HOME=home, EXPLAINER_FORGE_OVERLAY="")
        return subprocess.run([sys.executable, os.path.join(HERE, "name_check.py"), *args], capture_output=True, text=True, env=env)

    def test_hit_late_in_a_long_single_line_after_base64(self):
        d = tempfile.mkdtemp()
        try:
            names = os.path.join(d, "names.txt")
            open(names, "w").write("Zebediah Quillfeather\n")
            page = os.path.join(d, "page.html")
            cues = [{"text": "filler words here"} for _ in range(900)] + [{"text": "then Quillfeather arrives"}]
            open(page, "w").write("var IMG='data:image/png;base64," + "A" * 200000 + "';var CUES=" + json.dumps(cues) + ";\n")
            r = self.run_nc("--names", names, page)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("1 name hit", r.stdout)
        finally:
            shutil.rmtree(d)

    def test_no_names_list_is_an_error_unless_candidates_only(self):
        d = tempfile.mkdtemp()
        try:
            f = os.path.join(d, "a.md")
            open(f, "w").write("Hello there.\n")
            self.assertEqual(self.run_nc(f, home=d).returncode, 2)
            self.assertEqual(self.run_nc("--candidates-only", f, home=d).returncode, 0)
            r = self.run_nc("--overlay", os.path.join(d, "nope"), "--candidates-only", f, home=d)
            self.assertEqual(r.returncode, 2)
            self.assertIn("not a folder", r.stderr)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
