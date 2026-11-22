#!/usr/bin/env python3
"""Tests for new_project.py: python3 test_new_project.py   (no models, no network, temp folders only)"""
import glob
import io
import json
import os
import re
import sys
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import narration_lib as nl  # noqa: E402
import new_project as np_  # noqa: E402


def rd(*p):
    with open(os.path.join(*p), encoding="utf-8") as f:
        return f.read()


def run(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = np_.main(list(argv))
    return rc, buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = {k: os.environ.pop(k, None) for k in ("EXPLAINER_FORGE_OVERLAY",)}
        self.home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp.name, "home")   # no overlay from this machine
        os.makedirs(os.environ["HOME"])

    def tearDown(self):
        os.environ["HOME"] = self.home
        for k, v in self.old.items():
            if v is not None:
                os.environ[k] = v
        self.tmp.cleanup()

    def out(self, n="p"):
        return os.path.join(self.tmp.name, n)


class Scaffold(Base):
    def test_every_profile_scaffolds_and_its_script_parses(self):
        for name in np_.profiles():
            d = self.out(name)
            rc, txt = run("--title", "A test title", "--profile", name, "--out", d)
            self.assertEqual(rc, 0)
            for f in ("brief.md", "facts.md", "script.md", "saymap.json", "names.txt", "owner-notes.md", "retro.md", "run.md", "project.json"):
                self.assertTrue(os.path.exists(os.path.join(d, f)), f"{name}: {f}")
            scenes = nl.parse_script(rd(d, "script.md"))
            self.assertEqual(len(scenes), np_.scene_count(np_.read_profile(np_.profiles()[name][0])[0]), name)
            for n, t, words in scenes:
                self.assertTrue(t and words)
            self.assertNotIn("{{", rd(d, "retro.md"))

    def test_shipped_script_template_parses_into_real_scenes(self):
        text = rd(np_.ROOT, "templates", "script-template.md")
        self.assertGreaterEqual(len(nl.parse_script(text)), 3, "templates/script-template.md is not in the parser format")
        self.assertIsNone(re.search(r"^## \d+ ", text, re.M), "old '## n Title' headers left in the template")

    def test_word_counts_in_the_script_headers_are_right(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d)
        for m in re.finditer(r"\*\*Narration \((\d+) words\):\*\*\n(.*)", rd(d, "script.md")):
            self.assertEqual(int(m.group(1)), len(m.group(2).split()))

    def test_run_md_names_only_real_scripts_and_real_flags(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d)
        text = rd(d, "run.md")
        self.check_commands(text, 10)

    def check_commands(self, text, at_least):
        self.assertEqual(np_.missing_scripts(text), [])
        found = re.findall(r"(?:node|python3|bash|\"\$VOICE_PY\") \"\$P/(scripts/[^\"]+)\"([^\n]*)", text)
        self.assertGreaterEqual(len(found), at_least)
        for script, rest in found:
            src = rd(np_.ROOT, script)
            for flag in re.findall(r"(?<=\s)--([a-z][\w-]*)", rest):
                self.assertTrue(f"--{flag}" in src or f"'{flag}'" in src, f"{script} has no --{flag}")

    def test_run_md_branches_by_build_path(self):
        has = {"concept-video": ("build_explainer.py", "proof.mjs"), "deck-voiceover": ("--cues-for deck", "deck_proof.mjs", "build_explainer.py"),
               "compliance-connector": ("--cues-for deck", "deck_proof.mjs"), "product-demo": ("--cues-for stage", "ring_check.mjs", "prep_media.py"),
               "story-film": ("storyboard.md", "IMGS[n]")}
        for name, needles in has.items():
            d = self.out(name)
            run("--title", "T", "--profile", name, "--out", d)
            text = rd(d, "run.md")
            for x in needles:
                self.assertIn(x, text, name)
            self.check_commands(text, 10)
            for n in range(16):
                self.assertRegex(text, rf"(?m)^## {n}\. ", f"{name}: no section {n}")
            self.assertEqual("storyboard.md" in os.listdir(d), name == "story-film")
        self.assertNotIn("build_explainer.py", rd(self.out("product-demo"), "run.md"))

    def test_run_md_sections_match_the_skill_steps(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d)
        want = {"Brief": 1, "Cold script review": 4, "Style frame": 5, "Voice pick": 6, "Owner go": 7, "Build": 9, "Retro": 15}
        skill, text = rd(np_.ROOT, "skills", "make-an-explainer", "SKILL.md"), rd(d, "run.md")
        for t, n in want.items():
            self.assertRegex(text, rf"(?m)^## {n}\. {t}")
            self.assertRegex(skill, rf"(?m)^\| {n} \| \*\*{t}\.\*\*")

    def test_every_block_sources_env_and_env_works_in_a_fresh_shell(self):
        d = self.out("a folder")
        run("--title", "T", "--profile", "concept-video", "--out", d)
        blocks = re.findall(r"```bash\n(.*?)```", rd(d, "run.md"), re.S)
        self.assertGreater(len(blocks), 10)
        for b in blocks:
            self.assertIn("env.sh", b.splitlines()[0], b)
        for shell in ("bash", "zsh", "sh"):
            if not shutil.which(shell):
                continue
            r = subprocess.run([shell, "-euc", blocks[0].splitlines()[0] + '\npython3 "$P/scripts/new_project.py" --check-rules && pwd'],
                               cwd="/", capture_output=True, text=True, env={"PATH": os.environ["PATH"], "HOME": "/"})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.splitlines()[-1], os.path.realpath(d))
        script = next(b for b in blocks if "make_narration.py" in b)
        r = subprocess.run(["bash", "-euc", script], cwd="/", capture_output=True, text=True)
        self.assertTrue(os.path.exists(os.path.join(d, "narration.json")), r.stderr)
        cold = next(b for b in blocks if "narration-only.txt" in b)
        self.assertEqual(subprocess.run(["bash", "-euc", cold], cwd="/").returncode, 0)
        self.assertIn("[1]", rd(d, "review", "narration-only.txt"))

    def test_no_voice_chosen_means_the_take_fails_before_any_model(self):
        for name in ("compliance-connector", "story-film"):
            d = self.out(name)
            run("--title", "T", "--profile", name, "--out", d)
            text = rd(d, "run.md")
            for line in text.splitlines():
                if "one_take.py" in line or "make_onetake_video.sh" in line:
                    self.assertIn("voice/CHOSEN.wav", line)
                    self.assertIn("voice/CHOSEN.txt", line)
            self.assertLess(text.index("design_voices.py"), text.index("one_take.py"))
            subprocess.run([sys.executable, os.path.join(HERE, "make_narration.py"), os.path.join(d, "script.md"), "--out", os.path.join(d, "narration.json")],
                           check=True, capture_output=True)
            block = next(b for b in re.findall(r"```bash\n(.*?)```", text, re.S) if "one_take.py" in b)
            cmd = "\n".join(ln for ln in block.splitlines() if "env.sh" in ln or "one_take" in ln)
            r = subprocess.run(["bash", "-c", cmd], env=dict(os.environ, EXPLAINER_VOICE_PY=sys.executable), capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("reference transcript not found", r.stderr)

    def test_style_frame_has_a_prompt_and_real_references(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d)
        self.assertIn("SCENE:", rd(d, "prompts", "style-frame.txt"))
        refs = re.findall(r"-i ([\w-]+)\.png", rd(d, "run.md"))
        self.assertGreaterEqual(len(refs), 4)
        for x in refs:
            self.assertTrue(os.path.exists(os.path.join(d, "refs", x + ".webp")), x)

    def test_player_gaps_are_read_from_the_engine(self):
        src = rd(np_.ROOT, "templates", "engine", "engine.js")
        self.assertEqual("no F key for full screen" in np_.player_gaps(), "requestFullscreen" not in src)

    def test_cues_for_stage_and_deck(self):
        a = self.out("audio")
        os.makedirs(a)
        open(os.path.join(a, "narration.m4a"), "wb").close()
        long = "This caption is well over forty two characters long, so it wraps."
        with open(os.path.join(a, "cues.json"), "w") as f:
            json.dump({"duration": 9.0, "tempo": 1, "scenes": [{"n": 1, "title": "A", "start": 0}, {"n": 2, "title": "B", "start": 5}],
                       "chunks": [{"id": "s1a", "scene": 1, "start": .8, "end": 2, "show": "Hi."}, {"id": "s1b", "scene": 1, "start": 2.5, "end": 4, "show": long},
                                  {"id": "s2a", "scene": 2, "start": 5.2, "end": 8, "show": "Bye."}],
                       "captions": [{"start": .8, "end": 2, "text": "Hi."}, {"start": 2.5, "end": 4, "text": long}]}, f)
        self.assertEqual(run("--cues-for", "deck", "--audio", a, "--out", self.out("deck"))[0], 0)
        self.assertEqual(json.loads(rd(self.out("deck"), "cues.json")), [[0, 2.2], [5]])
        self.assertEqual(run("--cues-for", "stage", "--audio", a, "--out", self.out("stage"))[0], 0)
        c = json.loads(rd(self.out("stage"), "cues.json"))
        self.assertEqual((c["total"], [x["id"] for x in c["lines"]], c["lines"][1]["title"]), (9.0, ["s1a", "s1b", "s2a"], "A"))
        caps = json.loads(rd(self.out("stage"), "captions.json"))
        self.assertEqual([len(k["rows"]) for k in caps], [1, 2])
        self.assertEqual(" ".join(caps[1]["rows"]), long)

    def test_project_json_paths_exist_or_are_made_later(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d)
        p = json.loads(rd(d, "project.json"))
        for f in p["fonts"]:
            self.assertTrue(os.path.exists(os.path.join(d, f["file"])))
        self.assertEqual(sorted((f["family"], f["weight"]) for f in p["fonts"]), [("EF Body", 400), ("EF Body", 600), ("EF Head", 600)])
        for k in ("scenes_html", "scenes_js", "theme_css", "sprites_dir"):
            self.assertTrue(os.path.exists(os.path.join(d, p[k])), k)
        self.assertIn("plaque.webp", os.listdir(os.path.join(d, "img")))
        self.assertIn("ember-point.webp", os.listdir(os.path.join(d, "img")))

    def test_refuses_a_non_empty_folder_and_an_unknown_profile(self):
        d = self.out()
        os.makedirs(d)
        open(os.path.join(d, "x"), "w").close()
        with self.assertRaises(SystemExit):
            run("--title", "T", "--profile", "concept-video", "--out", d)
        self.assertEqual(os.listdir(d), ["x"])
        with self.assertRaises(SystemExit):
            run("--title", "T", "--profile", "nope", "--out", self.out("q"))

    def test_mascot_none_copies_no_poses(self):
        d = self.out()
        run("--title", "T", "--profile", "concept-video", "--out", d, "--mascot", "none")
        self.assertFalse(glob.glob(os.path.join(d, "img", "ember-*")))
        self.assertNotIn("--character", rd(d, "run.md"))


class Overlay(Base):
    def test_overlay_is_merged_and_replaces_a_profile(self):
        o = self.out("ov")
        os.makedirs(os.path.join(o, "profiles"))
        open(os.path.join(o, "names.txt"), "w").write("# c\nZed Fakename\n")
        open(os.path.join(o, "say-map.json"), "w").write(json.dumps({"replace": [["Velloq", "Vell-ock"]], "regex": [], "drop": []}))
        open(os.path.join(o, "house.md"), "w").write("x")
        open(os.path.join(o, "profiles", "concept-video.md"), "w").write(
            rd(np_.ROOT, "profiles", "concept-video.md").replace("wpm: 207", "wpm: 201"))
        d = self.out()
        rc, txt = run("--title", "T", "--profile", "concept-video", "--out", d, "--overlay", o)
        self.assertIn("(overlay)", txt)
        self.assertIn("Zed Fakename", rd(d, "names.txt"))
        self.assertIn(["Velloq", "Vell-ock"], json.load(open(os.path.join(d, "saymap.json")))["replace"])
        self.assertIn("--wpm 201", rd(d, "run.md"))
        self.assertIn("house.md", rd(d, "brief.md"))

    def test_relative_overlay_becomes_absolute_and_a_missing_one_is_an_error(self):
        os.makedirs(self.out("ov"))
        old = os.getcwd()
        os.chdir(self.tmp.name)
        try:
            run("--title", "T", "--profile", "concept-video", "--out", "p", "--overlay", "ov")
            with self.assertRaises(SystemExit):
                run("--title", "T", "--profile", "concept-video", "--out", "q", "--overlay", "nope")
        finally:
            os.chdir(old)
        self.assertIn(f"EXPLAINER_FORGE_OVERLAY={os.path.realpath(self.out('ov'))}", rd(self.out(), "env.sh"))

    def test_no_overlay_works(self):
        rc, txt = run("--show-overlay")
        self.assertEqual(rc, 0)
        self.assertIn("none found", txt)


class Rules(Base):
    def test_shipped_rules_are_clean(self):
        bad, n = np_.check_rules()
        self.assertEqual(bad, [])
        self.assertGreater(n, 80)

    def test_bad_rules_are_caught(self):
        p = self.out("r.md")
        open(p, "w").write("| A1 | do it | because |\n| A1 | again | why |\n| A2 | no reason | |\n## Superseded\n| old | Z9 |\n")
        bad, _ = np_.check_rules(p)
        self.assertEqual(len(bad), 3)


if __name__ == "__main__":
    unittest.main()
