#!/usr/bin/env python3
"""Regression tests for lyric_meter.py and the alignment half of sung_check.py.

    uv run --with pronouncing python test_lyric_meter.py

The fixture is fictional and carries three deliberate defects: a verse-2 line that
is far off its verse-1 partner, a cliche (neon), and a repeated end-word (thing).
"""
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lyric_meter as lm   # noqa: E402
import sung_check as sc    # noqa: E402


def args(**kw):
    d = dict(title="Lighthouse Keeper", tolerance=2, spread=6, reuse=3, max_lines={},
             words=None, cliches=lm.DEFAULT_CLICHES, genre=None)
    d.update(kw)
    return types.SimpleNamespace(**d)


class Meter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, "fixtures", "sample.txt"), encoding="utf-8") as f:
            cls.res = lm.analyse(f.read(), args())

    def flags(self):
        return " | ".join(self.res["flags"])

    def test_syllable_mismatch(self):
        self.assertIn("[Verse 2] line 1", self.flags())

    def test_cliche(self):
        self.assertTrue(any(h["entry"] == "neon" for h in self.res["cliches"]))

    def test_repeated_end_word(self):
        self.assertIn("end-word 'thing' used 2x", self.flags())

    def test_title_in_chorus(self):
        t = self.res["title_check"]
        self.assertTrue(t["in_chorus_lines"] and t["first_or_last_chorus_line"])

    def test_clean_pairs_not_flagged(self):
        pairs = self.res["repeat_comparisons"][0]["pairs"]
        self.assertEqual([p["flag"] for p in pairs], [True, False, False, False])

    def test_rhyme_classes(self):
        self.assertEqual(lm.rhyme_class("night", "white"), "perfect")
        self.assertEqual(lm.rhyme_class("night", "mind"), "slant")
        self.assertEqual(lm.rhyme_class("night", "tree"), "none")
        self.assertEqual(lm.rhyme_class("night", "night"), "repeat")

    def test_oov_marked(self):
        self.assertEqual(lm.word_info("zxqvblorp")["oov"], True)

    def test_flexible_word_range(self):
        w = lm.word_info("fire")
        self.assertEqual((w["syl_min"], w["syl_max"]), (1, 2))

    def test_stress_match(self):
        self.assertEqual(lm.stress_match("0101", "0101"), 1.0)
        self.assertEqual(lm.stress_match("0101", "1010"), 0.0)
        self.assertEqual(lm.stress_match("0121", "0101"), 1.0)   # secondary matches either
        self.assertIsNone(lm.stress_match("", "01"))


# Fictional. Same syllable count, beats in different places in verse 2 line 1; the
# flexible word "fire" puts verse 2 line 2 in range of its partner.
BEATS_SONG = """[Verse 1]
Running faster, running harder
Sit beside me by the evening tide

[Verse 2]
Again, again, again, again
Sit beside the fire with me tonight
"""


class Beats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = lm.analyse(BEATS_SONG, args(title=None))
        cls.pairs = cls.res["repeat_comparisons"][0]["pairs"]

    def test_same_count_different_beats_flagged(self):
        p = self.pairs[0]
        self.assertEqual(p["syl"], p["ref_syl"])
        self.assertTrue(p["stress_flag"], p)

    def test_range_reported(self):
        p = self.pairs[1]
        self.assertLess(p["range"][0], p["range"][1])
        self.assertFalse(p["flag"])


# Fictional. Deliberate violations: perfect-rhyme-only chorus, a therapy-speak word,
# one "you" in the whole song, uniform line lengths, no numbers or names, a short file.
BAD_SONG = """[Verse 1]
The cat sat by the door
The dog slept on the floor
The rain fell on the town
The sun went slowly down

[Chorus]
Stay here with me tonight
Keep the porch lamp light
Hold on to what is right
Hold on until it's light

[Verse 2]
The cat sat by the door
The dog slept on the floor
We need to set boundaries
The rain fell on the trees
"""

# Fictional. Meets the norms: repeats written out, varied lengths, many "you", a time, a name.
GOOD_SONG = """[Verse 1]
Yesterday at 3am you left your charger in my car
Your voicemail picks up on the second ring, so I know where we are
You said you'd call me back, Dana, and you didn't
Your brother says you're fine

[Chorus]
Keep your hands off my stereo
You took the good one, you can go
Keep your hands off my stereo
I know you know

[Verse 2]
You borrowed my flip phone and my favorite hoodie, then you bailed on everything we planned for June
Your mom still waves at me at the mall
Your name is on my wall

[Chorus]
Keep your hands off my stereo
You took the good one, you can go
Keep your hands off my stereo
I know you know

[Bridge]
Your side of the bed is cold, you're not here
(you're not here)

[Chorus]
Keep your hands off my stereo
You took the good one, you can go
Keep your hands off my stereo
I know you know
"""


class Genre(unittest.TestCase):
    def check(self, text, title):
        res = lm.analyse(text, args(title=title, genre="emo-pop-punk"))
        return {c["id"]: c for c in res["genre_check"]["checks"]}, res

    def test_bad_song_warns(self):
        c, res = self.check(BAD_SONG, "Porch Lamp")
        self.assertEqual(c["chorus_perfect_rhyme_share"]["status"], "WARN")
        self.assertEqual(c["therapy-speak"]["status"], "WARN")
        self.assertIn("boundaries", c["therapy-speak"]["note"])
        self.assertEqual(c["you_count"]["status"], "WARN")
        self.assertEqual(c["line_length_swing"]["status"], "WARN")
        self.assertEqual(c["receipts_proxy"]["status"], "WARN")
        self.assertEqual(c["chorus_occurrences"]["status"], "WARN")
        self.assertEqual(c["total_words"]["status"], "WARN")
        self.assertTrue(all(x["status"] in ("PASS", "WARN", "N/A")
                            for x in res["genre_check"]["checks"]))

    def test_good_song_passes(self):
        c, _ = self.check(GOOD_SONG, "Keep Your Hands Off My Stereo")
        for cid in ("chorus_lines", "chorus_occurrences", "chorus_perfect_rhyme_share",
                    "verse_lines_over_16", "you_count", "title_in_chorus", "receipts_proxy",
                    "line_length_swing", "therapy-speak", "anachronism", "generic-angst"):
            self.assertEqual(c[cid]["status"], "PASS", cid)

    def test_generic_angst_allows_one(self):
        one = "[Verse 1]\nThe pain stayed in the drawer\n[Chorus]\nOh no\n"
        two = "[Verse 1]\nThe pain stayed in the drawer\nAll the darkness in the hall\n[Chorus]\nOh no\n"
        self.assertEqual(self.check(one, None)[0]["generic-angst"]["status"], "PASS")
        self.assertEqual(self.check(two, None)[0]["generic-angst"]["status"], "WARN")

    def test_anachronism(self):
        c, _ = self.check("[Verse 1]\nI checked Instagram twice\n[Chorus]\nOh no\n", None)
        self.assertEqual(c["anachronism"]["status"], "WARN")

    def test_no_genre_no_block(self):
        res = lm.analyse(GOOD_SONG, args())
        self.assertNotIn("genre_check", res)


class Align(unittest.TestCase):
    def test_misheard_dropped_added(self):
        lines = [{"idx": 0, "section": "Verse 1", "text": "the harbor lamps burn low and slow", "words": "the harbor lamps burn low and slow".split()},
                 {"idx": 1, "section": "Verse 1", "text": "I keep the log in a salt-stained coat", "words": "i keep the log in a salt stained coat".split()},
                 {"idx": 2, "section": "Verse 1", "text": "come home before the tide", "words": "come home before the tide".split()}]
        heard = [(w, float(i)) for i, w in enumerate(
            "the harbor lamps burn low and so come home before the tide oh yeah".split())]
        res, extras, summary = sc.align(lines, heard)
        self.assertEqual(res[0]["status"], "misheard")
        self.assertEqual(res[1]["status"], "dropped")
        self.assertEqual(res[2]["status"], "matched")
        self.assertTrue(any(d["written"] == "slow" and d["heard"] == "so" for d in res[0]["diffs"]))
        self.assertEqual(extras[0]["kind"], "added")


if __name__ == "__main__":
    unittest.main(verbosity=2)
