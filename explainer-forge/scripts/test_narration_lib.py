#!/usr/bin/env python3
"""Unit tests for the pure functions in narration_lib.py (no models, no ffmpeg).   python3 scripts/test_narration_lib.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_lib as nl  # noqa: E402
import dead_air  # noqa: E402

SCRIPT = """# Title

## Scene 1. Hello
**Narration (12 words):**
This is the first sentence. It has a second one!

Then a new paragraph starts here.

**On screen:**
A logo. Ignored.

## Scene 2. Numbers (about 30 s)
**Narration (8 words):**
At 3:22 AM the AI woke up. Done.

---
## Scene 3. No narration
Only notes here.
"""


class Parser(unittest.TestCase):
    def test_scenes_and_blocks(self):
        sc = nl.parse_script(SCRIPT)
        self.assertEqual([s[0] for s in sc], [1, 2])          # scene 3 has no narration block: skipped
        self.assertEqual(sc[0][1], "Hello")
        self.assertEqual(sc[1][1], "Numbers")                  # trailing parenthesis dropped from the title
        self.assertIn("new paragraph", sc[0][2])
        self.assertNotIn("Ignored", sc[0][2])                  # on-screen block excluded

    def test_plain_mode(self):
        sc = nl.parse_script("## 1 One\nJust words here.\n\n## 2 Two\nMore words.", plain=True)
        self.assertEqual(sc, [(1, "One", "Just words here."), (2, "Two", "More words.")])

    def test_sentences(self):
        self.assertEqual(nl.split_sentences("One. Two? Three!"), ["One.", "Two?", "Three!"])
        self.assertEqual(len(nl.split_sentences("It costs 3.5 dollars. Fine.")), 2)   # a decimal is not a boundary

    def test_chunk_ids(self):
        self.assertEqual([nl.chunk_id(4, i) for i in (0, 1, 25, 26)], ["s4a", "s4b", "s4z", "s4aa"])


class ParserEdges(unittest.TestCase):
    def test_bold_word_does_not_end_narration(self):
        sc = nl.parse_script("## Scene 1. A\n**Narration:**\n**Never** skip this step. It matters.\n\n**On screen:**\nx\n")
        self.assertEqual(sc[0][2], "Never skip this step. It matters.")

    def test_unnumbered_heading_with_narration_is_an_error(self):
        with self.assertRaises(ValueError):
            nl.parse_script("## Scene 1. A\n**Narration:**\nHi there.\n\n## Cold open\n**Narration:**\nYo.\n")
        # an unnumbered heading without narration (a notes section) ends the previous scene cleanly
        sc = nl.parse_script("## Scene 1. A\n**Narration:**\nHi there.\n\n## Notes\nNot spoken.\n")
        self.assertEqual(sc, [(1, "A", "Hi there.")])

    def test_duplicate_scene_numbers(self):
        with self.assertRaises(ValueError):
            nl.parse_script("## Scene 1. A\n**Narration:**\nHi.\n\n## Scene 1. B\n**Narration:**\nYo.\n")
        with self.assertRaises(ValueError):
            nl.build_narration([(1, "a", "One."), (1, "b", "Two.")])

    def test_inline_markdown_and_comments_stripped(self):
        sc = nl.parse_script("## Scene 1. A\n**Narration:**\nUse *care* with `code` and [a link](http://x.y). <!-- note -->Done.\n")
        self.assertEqual(sc[0][2], "Use care with code and a link. Done.")

    def test_closing_quote_stays_with_its_sentence(self):
        self.assertEqual(nl.split_sentences('He said "go now." Then left. (Really.) Yes.'),
                         ['He said "go now."', "Then left.", "(Really.)", "Yes."])

    def test_wordless_chunk_rejected_by_name(self):
        with self.assertRaises(ValueError) as cm:
            nl.build_narration([(2, "t", "Fine. (...) Next.")])
        self.assertIn("s2b", str(cm.exception))
        with self.assertRaises(ValueError):
            nl.flatten([{"scene": 1, "title": "t", "chunks": [{"id": "s1a", "show": "--"}]}])


class SayMap(unittest.TestCase):
    def test_show_say_split(self):
        sm = {"replace": [["Acme", "Ack-me"], ["3:22", "three twenty-two"]], "regex": [["\\bAI\\b", "A I"]], "drop": ["\""]}
        sc = nl.parse_script(SCRIPT)
        out = nl.build_narration(sc, sm)
        c = out[1]["chunks"][0]
        self.assertEqual(c["show"], "At 3:22 AM the AI woke up.")     # captions keep the real text
        self.assertEqual(c["say"], "At three twenty-two AM the A I woke up.")
        self.assertNotIn("say", out[1]["chunks"][1])                  # unchanged sentence: no say key

    def test_quotes_never_spoken(self):
        self.assertEqual(nl.apply_say_map("He said “hi”.", nl.empty_say_map()), "He said hi.")


class Alignment(unittest.TestCase):
    def setUp(self):
        self.scenes = [{"scene": 1, "title": "a", "chunks": [{"id": "s1a", "show": "one two three"}, {"id": "s1b", "show": "four five"}]},
                       {"scene": 2, "title": "b", "chunks": [{"id": "s2a", "show": "six seven eight nine"}]}]
        self.chunks, self.ref = nl.flatten(self.scenes)

    def test_exact_match(self):
        heard = [(w, i * 1.0, i * 1.0 + 0.5) for i, w in enumerate("one two three four five six seven eight nine".split())]
        t, matched = nl.align(self.ref, nl.hyp_words(heard))
        self.assertEqual(len(matched), 9)
        self.assertEqual(t[0], (0.0, 0.5))
        cs = nl.chunk_spans(self.ref, t)
        self.assertEqual(cs[1], [3.0, 4.5])

    def test_missed_words_are_interpolated(self):
        heard = [("one", 0, .5), ("two", 1, 1.5), ("four", 3, 3.5), ("five", 4, 4.5), ("six", 5, 5.5), ("seven", 6, 6.5), ("eight", 7, 7.5), ("nine", 8, 8.5)]
        t, matched = nl.align(self.ref, nl.hyp_words(heard))
        self.assertNotIn(2, matched)                                   # "three" was not heard
        self.assertTrue(1.5 <= t[2][0] <= 3.0)                         # but it sits between its neighbours
        self.assertAlmostEqual(nl.match_rates(self.ref, matched, 3)[0], 2 / 3)

    def test_silent_take_raises(self):
        with self.assertRaises(ValueError):
            nl.align(self.ref, [])

    def test_extra_words_and_hyphen(self):
        heard = [("uh", 0, .1), ("one", .2, .5), ("two-three", .6, 1.0), ("four", 1.1, 1.4), ("five", 1.5, 1.8)]
        t, matched = nl.align(self.ref[:5], nl.hyp_words(heard))
        self.assertEqual(len(matched), 5)                              # the filler is ignored, the hyphenated token splits

    def test_scene_spans(self):
        t = [(0, .5), (1, 1.5), (2, 2.5), (3, 3.5), (4, 4.5), (5, 5.5), (6, 6.5), (7, 7.5), (8, 8.5)]
        sp = nl.scene_spans(self.chunks, nl.chunk_spans(self.ref, t))
        self.assertEqual(sp, {1: [0, 4.5], 2: [5, 8.5]})

    def test_diff_reports_a_made_up_tail(self):
        ref_words = nl.words("one two three")
        hyp = nl.hyp_words([("one", 0, 1), ("two", 1, 2), ("three", 2, 3), ("thanks", 3, 4), ("bye", 4, 5)])
        ratio, bad = nl.diff_script_vs_heard(ref_words, hyp)
        self.assertEqual(bad[0][0], "insert")
        self.assertLess(ratio, 1.0)


    def test_spacing_difference_is_not_a_misread(self):
        ratio, bad = nl.diff_script_vs_heard(nl.words("scan the q r code now"), nl.hyp_words([("scan", 0, 1), ("the", 1, 2), ("qr", 2, 3), ("code", 3, 4), ("now", 4, 5)]))
        self.assertEqual(bad, [])
        self.assertGreater(ratio, 0.97)
        ratio2, bad2 = nl.diff_script_vs_heard(nl.words("scan the q r code now"), nl.hyp_words([("scan", 0, 1), ("the", 1, 2), ("code", 3, 4), ("now", 4, 5)]))
        self.assertEqual(bad2[0][0], "delete")                           # a really skipped word is still reported


class Tempo(unittest.TestCase):
    def test_speech_wpm_ignores_pauses(self):
        self.assertAlmostEqual(nl.speech_wpm(200, [(0, 30), (40, 70)]), 200.0)   # 60 s of speech, 10 s pause not counted
        self.assertAlmostEqual(nl.overall_wpm(200, 70), 200 / (70 / 60))

    def test_tempo_both_directions(self):
        self.assertAlmostEqual(nl.tempo_for(220.0, 200.0), 200 / 220)            # slow down
        self.assertAlmostEqual(nl.tempo_for(150.0, 180.0), 1.2)                  # speed up
        with self.assertRaises(ValueError):
            nl.tempo_for(0, 180)

    def test_atempo_filter_chain(self):
        self.assertEqual(nl.atempo_filter(1.2), "atempo=1.2000")
        self.assertEqual(nl.atempo_filter(0.3), "atempo=0.5,atempo=0.6000")
        with self.assertRaises(ValueError):
            nl.atempo_filter(0)

    def test_tempo_note(self):
        self.assertEqual(nl.tempo_note(1.0), "")
        self.assertIn("hurried", nl.tempo_note(1.4))
        self.assertIn("drawn out", nl.tempo_note(0.7))

    def test_scale_words(self):
        w = nl.scale_words([("a", 1.0, 1.5), ("b", 3.0, 4.0)], 1.0, 2.0)
        self.assertEqual(w, [("a", 0.0, 0.25), ("b", 1.0, 1.5)])
        self.assertEqual(nl.scale_words([("x", 0.1, 0.2)], 1.0, 1.0), [])        # before the trim point


class Gaps(unittest.TestCase):
    def test_defaults_and_extra(self):
        p = nl.plan_gaps([1, 2, 3], base=0.45, before={3: 0.35})
        self.assertAlmostEqual(p["after"][1], 0.45)
        self.assertAlmostEqual(p["after"][2], 0.80)                  # the extra beat sits BEFORE scene 3
        self.assertEqual(p["capped"], [])
        self.assertAlmostEqual(p["tail"], 0.8)

    def test_max_gap_cap(self):
        p = nl.plan_gaps([1, 2, 3], base=0.45, before={2: 2.0}, max_gap=1.2, pad=0.12)
        self.assertAlmostEqual(p["after"][1], 1.2 - 2 * 0.12)        # audible gap = inserted + two pads <= 1.2
        self.assertIn(1, p["capped"])
        self.assertLessEqual(p["audible_max"], 1.2 + 1e-9)

    def test_old_tail_default_is_capped(self):
        p = nl.plan_gaps([1, 2], tail=2.6, max_gap=1.2)
        self.assertLessEqual(p["tail"], 1.2)
        self.assertIn("tail", p["capped"])

    def test_tail_cap_counts_the_kept_tail_pad(self):
        p = nl.plan_gaps([1, 2], tail=0.95, max_gap=1.2)             # 0.95 + 0.35 kept pad would be 1.3 s of silence
        self.assertAlmostEqual(p["tail"], 0.85)
        self.assertIn("tail", p["capped"])
        self.assertLessEqual(p["audible_max"], 1.2 + 1e-9)
        self.assertEqual(nl.plan_gaps([1, 2], tail=0.8, max_gap=1.2)["capped"], [])

    def test_squeeze_plan_shortens_inner_pauses_only(self):
        sr = 1000
        runs = [(0, 500), (2000, 4500), (5000, 5200), (9000, 10000)]   # head, 2.5 s pause, 0.2 s pause, tail
        cuts = nl.squeeze_plan(runs, sr, 1.2, 10000)
        self.assertEqual(cuts, [(2600, 1300)])                          # keeps 1.2 s of the 2.5 s pause; head, short pause and tail untouched
        self.assertEqual(nl.removals_seconds(cuts, sr), [(2.6, 1.3)])

    def test_map_time_after_removals(self):
        rm = [(2.6, 1.3), (8.0, 1.0)]
        self.assertAlmostEqual(nl.map_time(1.0, rm), 1.0)
        self.assertAlmostEqual(nl.map_time(5.0, rm), 3.7)
        self.assertAlmostEqual(nl.map_time(9.5, rm), 7.2)
        self.assertAlmostEqual(nl.map_time(3.0, rm), 2.6)              # inside a removed stretch: clamps to its start

    def test_audible_gap_is_the_longest_silence(self):
        self.assertEqual(nl.audible_gaps([(1.0, 0.4), (5.0, 1.1)]), 1.1)
        self.assertEqual(nl.audible_gaps([]), 0.0)

    def test_cut_points(self):
        c = nl.cut_points([1, 2], {1: [0, 10], 2: [12, 20]}, total_len=30)
        self.assertEqual(c, [0.0, 11.0, 20.35])
        self.assertEqual(nl.cut_points([1], {1: [0, 10]}, total_len=10.1)[-1], 10.1)   # never past the end

    def test_place_segments(self):
        starts, total = nl.place_segments([5.0, 4.0], 0.8, [0.5, 0.9])
        self.assertEqual(starts, [0.8, 6.3])
        self.assertAlmostEqual(total, 11.2)

    def test_parse_gap_before(self):
        self.assertEqual(nl.parse_gap_before("6=0.35, 13=0.4"), {6: 0.35, 13: 0.4})
        self.assertEqual(nl.parse_gap_before(""), {})


class Captions(unittest.TestCase):
    def test_pieces_within_width(self):
        t = "A bakery is a place where ovens run before sunrise, and the first loaves are ready when the street wakes up."
        for p in nl.caption_pieces(t, 70):
            self.assertLessEqual(len(p), 78)
        self.assertEqual(" ".join(nl.caption_pieces(t, 70)).replace("  ", " "), t)

    def test_track_covers_chunk(self):
        caps = nl.caption_track([{"start": 10.0, "end": 14.0, "show": "Short one. And another sentence that follows it here."}], 30)
        self.assertAlmostEqual(caps[0]["start"], 10.0)
        self.assertAlmostEqual(caps[-1]["end"], 14.0, places=2)
        self.assertEqual(nl.srt_time(3661.5), "01:01:01,500")

    def test_long_gaps(self):
        self.assertEqual(nl.long_gaps([("a", 0, 1), ("b", 2.5, 3), ("c", 3.1, 4)], 1.0), [(1, 1.5)])


class Sync(unittest.TestCase):
    def test_offsets(self):
        cues = [{"id": "x", "start": 1.0, "end": 3.0}, {"id": "y", "start": 4.0, "end": 5.0}]
        offs = nl.sync_offsets(cues, {"x": [0, 1], "y": [2]}, {0: (1.1, 1.5), 1: (2.5, 3.2), 2: (4.4, 5.0)})
        self.assertAlmostEqual(offs[0]["start_off"], 0.1)
        self.assertAlmostEqual(offs[0]["end_off"], 0.2)
        s = nl.sync_summary(offs, 0.15)
        self.assertEqual(s["over_150ms"], ["y"])
        self.assertEqual(s["worst"]["id"], "y")


class SyncOnsets(unittest.TestCase):
    def test_first_chunk_excluded_from_mean_and_worst(self):
        offs = [{"id": "a", "cue": 0, "heard": -0.8, "start_off": -0.8, "end_off": 0},
                {"id": "b", "cue": 3, "heard": 3.1, "start_off": 0.1, "end_off": 0},
                {"id": "c", "cue": 6, "heard": 6.05, "start_off": 0.05, "end_off": 0}]
        s = nl.sync_summary(offs, 0.15, exclude=["a"])
        self.assertEqual(s["worst"]["id"], "b")
        self.assertAlmostEqual(s["mean_abs_start_offset_s"], 0.075)
        self.assertEqual(s["excluded"], ["a"])
        self.assertEqual(s["over_150ms"], [])

    def test_scene_onsets_from_silence_detection(self):
        o = nl.onset_offsets([(1, 0.9), (2, 10.0), (3, 20.0)], [0.95, 10.31, 40.0])
        self.assertEqual([x["scene"] for x in o], [1, 2])               # scene 3 has no onset within the window
        self.assertAlmostEqual(o[1]["off"], 0.31)


class DeadAir(unittest.TestCase):
    CUES = {"duration": 20.0, "chunks": [
        {"id": "a", "scene": 1, "start": 0.8, "end": 5.0}, {"id": "b", "scene": 1, "start": 5.3, "end": 9.0},
        {"id": "c", "scene": 2, "start": 11.0, "end": 15.0}]}

    def test_flags_scene_break_and_tail(self):
        bad = dead_air.gaps_from_cues(self.CUES, 1.2)
        kinds = [b[0] for b in bad]
        self.assertEqual(len(bad), 2)
        self.assertTrue(any("scene break" in k for k in kinds))      # 9.0 -> 11.0 is 2.0 s
        self.assertIn("tail", kinds)                                  # 15.0 -> 20.0 is 5.0 s

    def test_clean_sheet(self):
        ok = {"duration": 10.0, "chunks": [{"id": "a", "scene": 1, "start": 0.8, "end": 5.0}, {"id": "b", "scene": 2, "start": 5.6, "end": 9.4}]}
        self.assertEqual(dead_air.gaps_from_cues(ok, 1.2), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
