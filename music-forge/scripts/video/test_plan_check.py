#!/usr/bin/env python3
"""Tests for plan_lib.py and plan_check.py. Needs ffmpeg only for the audio-length case.

    uv run python test_plan_check.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan_check as pc  # noqa: E402
import plan_lib as pl  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "example-plan.json")
FRAMES = os.path.join(HERE, "fixtures", "frames")


def load():
    return pl.load_plan(FIXTURE)


def reparse(plan):
    for s in plan["shots"]:
        s["start"], s["end"] = pl.parse_range(s["time"])
    return plan


class Times(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(pl.parse_time("01:06.11"), 66.11)
        self.assertEqual(pl.parse_time("0:42.8"), 42.8)
        self.assertEqual(pl.parse_time("12"), 12.0)
        self.assertEqual(pl.parse_range("00:20.00-00:28.50"), (20.0, 28.5))
        with self.assertRaises(ValueError):
            pl.parse_time("soon")

    def test_identities_are_looks(self):
        out = pl.apply_identities("Maren's lamp and Bolt", {"Maren": "a grey keeper", "Bolt": "a copper robot"})
        self.assertEqual(out, "a grey keeper's lamp and a copper robot")


class Check(unittest.TestCase):
    def test_fixture_is_clean(self):
        r = pc.check(load(), FRAMES)
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["planned_seconds"], 36.0)

    def test_gap(self):
        p = load()
        p["shots"][1]["time"] = "00:06.50-00:12.50"
        r = pc.check(reparse(p), FRAMES)
        self.assertTrue(any(e.startswith("GAP 0.50s") for e in r["errors"]), r["errors"])

    def test_overlap(self):
        p = load()
        p["shots"][2]["time"] = "00:12.00-00:20.00"
        r = pc.check(reparse(p), FRAMES)
        self.assertTrue(any(e.startswith("OVERLAP 0.50s") for e in r["errors"]), r["errors"])

    def test_start_gap(self):
        p = load()
        p["shots"][0]["time"] = "00:01.00-00:06.00"
        r = pc.check(reparse(p), FRAMES)
        self.assertTrue(any("not 00:00.00" in e for e in r["errors"]), r["errors"])

    def test_total_vs_audio(self):
        p = load()
        p["audio_duration_seconds"] = 41.0
        r = pc.check(p, FRAMES)
        self.assertTrue(any(e.startswith("TOTAL") and "short of" in e for e in r["errors"]), r["errors"])

    def test_missing_frame_and_duplicate_id(self):
        p = load()
        p["shots"][3]["frame"] = "nope"
        p["shots"][4]["id"] = "01"
        r = pc.check(p, FRAMES)
        self.assertTrue(any("keyframe 'nope' not found" in e for e in r["errors"]))
        self.assertTrue(any("duplicate shot id" in e for e in r["errors"]))

    def test_measured_audio_wins(self):
        with tempfile.TemporaryDirectory() as d:
            wav = os.path.join(d, "t.wav")
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=f=440:d=30", wav], check=True)
            r = pc.check(load(), FRAMES, audio_override=wav)
            self.assertTrue(any(e.startswith("TOTAL") and "past" in e for e in r["errors"]), r["errors"])

    def test_long_slot_warning(self):
        p = load()
        p["shots"][1].update(face="human", time="00:06.00-00:30.00")
        p["shots"][2]["time"] = "00:30.00-00:31.00"
        p["shots"][3]["time"] = "00:31.00-00:32.00"
        p["shots"][4]["time"] = "00:32.00-00:35.00"
        p["shots"][5]["time"] = "00:35.00-00:36.00"
        r = pc.check(reparse(p), FRAMES, routing=pl.load_routing())
        self.assertEqual(r["errors"], [], r["errors"])
        self.assertTrue(any("longer than" in w for w in r["warnings"]), r["warnings"])

    def test_cli_exit_codes(self):
        self.assertEqual(pc.main([FIXTURE]), 0)
        with tempfile.TemporaryDirectory() as d:
            bad = load()
            del bad["_dir"], bad["_path"]
            for s in bad["shots"]:
                del s["start"], s["end"]
            bad["shots"][1]["time"] = "00:07.00-00:12.50"
            path = os.path.join(d, "p.json")
            with open(path, "w") as f:
                json.dump(bad, f)
            self.assertEqual(pc.main([path, "--frames-dir", FRAMES]), 1)
            self.assertEqual(pc.main([os.path.join(d, "missing.json")]), 2)


class Routing(unittest.TestCase):
    def test_rules_and_override(self):
        r = pl.load_routing()
        self.assertEqual(pl.pick_model({"sing": True}, r)[0], "minimax/hailuo-3")
        self.assertEqual(pl.pick_model({"sing": True, "framing": "wide"}, r)[0], "minimax/hailuo-3")
        self.assertEqual(pl.pick_model({"sing": True, "framing": "close"}, r)[0], "heygen/heygen-video-1")
        self.assertEqual(pl.pick_model({"audio_ref": "instrumental"}, r)[0], "minimax/hailuo-3")
        self.assertEqual(pl.pick_model({"kind": "acting", "face": "human"}, r)[0], "minimax/hailuo-3-max")
        self.assertEqual(pl.pick_model({"kind": "action"}, r)[0], "bytedance/seedance-2.5")
        self.assertEqual(pl.pick_model({"face": "human"}, r)[0], "bytedance/seedance-1-5-pro")
        self.assertEqual(pl.pick_model({"face": "creature"}, r)[0], "bytedance/seedance-1-5-pro")
        self.assertEqual(pl.pick_model({}, r)[0], r["default_model"])
        self.assertEqual(pl.pick_model({"sing": True, "model": "x/y"}, r), ("x/y", "shot override"))

    def test_every_rule_carries_checked_and_note(self):
        r = pl.load_routing()
        for rule in r["rules"]:
            self.assertEqual(rule["checked"], "2026-10-14")
            self.assertTrue(rule["note"])
            self.assertIn(rule["use"], r["models"])
        for m in r["models"].values():
            self.assertTrue(m["checked"] and m["price_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
