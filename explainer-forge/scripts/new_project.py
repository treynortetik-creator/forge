#!/usr/bin/env python3
"""Scaffold one explainer project: every file the recipe needs, filled in from a profile, the style and your overlay.

  python3 new_project.py --title "How a parcel gets sorted" --profile concept-video --out work/2026-01-01-parcels
                         [--style clay-factory] [--mascot ember|none] [--voice coworker-baritone] [--overlay DIR]
  python3 new_project.py --list-profiles
  python3 new_project.py --show-overlay
  python3 new_project.py --check-rules          every house rule has a number and a reason
  python3 new_project.py --cues-for stage|deck --audio audio --out build      one-take cues in the other pages' formats

Makes in --out (which must be new or empty):
  brief.md  facts.md  script.md  saymap.json  names.txt  allow.txt  owner-notes.md  retro.md  run.md  project.json
  sprites.json  prompts/  refs/  img/  raw/  fonts/  theme.css  scenes.html  scenes.js  voice/  audio/  proof/  review/  env.sh
script.md is in the format make_narration.py reads; run.md holds the command for every step, for this profile's build
path (front matter `build: page | deck | footage | drawn`), and env.sh the paths each block sources. Private overlay (overlay.py): names.txt, allow.txt,
say-map.json and profiles/ in it are merged in; its house.md is named in brief.md. Pure Python, no models, no network.
"""
import argparse
import datetime
import json
import os
import re
import shlex
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import overlay as ov  # noqa: E402


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------------ profiles, rules, overlay

def read_profile(path):
    text = rd(path)
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"{path}: no front matter")
    meta = {}
    for ln in m.group(1).splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def profiles(overlay_path=None):
    """{name: (path, source)}; an overlay profile of the same name replaces the public one."""
    out = {}
    for base, src in ((os.path.join(ROOT, "profiles"), "plugin"), (ov.find("profiles", overlay_path), "overlay")):
        if base and os.path.isdir(base):
            for f in sorted(os.listdir(base)):
                if f.endswith(".md"):
                    out[f[:-3]] = (os.path.join(base, f), src)
    return out


def check_rules(path=None):
    """-> list of problems in rules.md (a rule with no reason, a duplicate number)."""
    path = path or os.path.join(ROOT, "skills", "house-style", "rules.md")
    seen, bad = set(), []
    for n, ln in enumerate(rd(path).splitlines(), 1):
        m = re.match(r"\| ([A-Z]\d+) \|(.*)\|(.*)\|\s*$", ln)
        if not m:
            continue
        rid, rule, why = m.group(1), m.group(2).strip(), m.group(3).strip()
        if rid in seen:
            bad.append(f"line {n}: {rid} used twice")
        seen.add(rid)
        if not rule or not why:
            bad.append(f"line {n}: {rid} has no {'rule' if not rule else 'reason'}")
    text = rd(path)
    sup = text.split("## Superseded", 1)
    if len(sup) < 2:
        bad.append("no Superseded section")
    else:
        for rid in re.findall(r"\b([A-Z]\d+)\b", sup[1]):
            if rid not in seen:
                bad.append(f"Superseded names {rid}, which is not a rule")
    if not seen:
        bad.append("no rules found")
    return bad, len(seen)


def merge_lines(*paths):
    out = []
    for p in paths:
        if p and os.path.exists(p):
            for ln in rd(p).splitlines():
                if ln and ln not in out:
                    out.append(ln)
    return out


# ------------------------------------------------------------------ text builders

def words_range(meta):
    n = [int(x) for x in re.findall(r"\d+", meta.get("words", "800 to 900"))]
    return (n[0] + n[-1]) // 2 if n else 800


def scene_count(meta):
    n = [int(x) for x in re.findall(r"\d+", meta.get("scenes", "7"))]
    return n[-1] if n else 7


STARTERS = {
    1: ("Title", "One plain sentence that says what this is. Then one that says why the viewer should care.",
        "The first object lands within about one second. The title sits on a clay sign."),
    2: ("The words you need", "A word is the everyday thing. Say what it is, in one sentence, before you use it.",
        "One object, one label. The specialist word sits on a small tag."),
    3: ("The whole thing working", "Follow one example from start to finish. Say the problem first, then the fix.",
        "The wow scene: everything moving, the camera pulling back to show it all."),
}


def script_text(title, meta, n):
    per = max(20, round(words_range(meta) / n / 10) * 10)
    out = [f"# {title}", "",
           f"Profile `{meta['profile']}`. Aim: {meta.get('length_target', '?')}, {meta.get('words', '?')} words, "
           f"{meta.get('wpm', '?')} words per minute while speaking. Third person.", "",
           "Format (read by `make_narration.py`): `## Scene N. Title`, a `**Narration (N words):**` block, then notes such as",
           "`**On screen:**`. One sentence becomes one caption chunk, so write sentences people can hear once and follow.", "---"]
    for i in range(1, n + 1):
        t, nar, scr = STARTERS.get(i, (f"Step {i}", "One idea, in plain speech. Replace this line.", "What the viewer sees while this is said."))
        if i == n and n > 3:
            t, nar, scr = "Close", meta.get("close", "Say the answer again, in one sentence."), "Everything still, the whole idea in one picture."
        out += [f"## Scene {i}. {t}", "", f"**Narration ({len(nar.split())} words):**", nar, "",
                f"**On screen:** {scr}", ""]
    return "\n".join(out).replace("\n---\n## Scene 1.", "\n\n## Scene 1.") + f"\n<!-- target about {per} words per scene -->\n"


def brief_text(title, meta, args, opath, house):
    return f"""# Brief: {title}

One page. The owner approves it before any script is written.

- **Profile:** {meta['profile']} ({meta.get('title', '')}); rules in `{os.path.join(ROOT, 'profiles', meta['profile'] + '.md')}`
- **Length:** {meta.get('length_target', '?')}, never over {meta.get('length_cap_s', '?')} s
- **Who watches:**
- **After watching they can:**
- **Where it plays:**
- **One sentence they should repeat to a friend:**
- **Real example we can show (and who agreed):**
- **Do not claim or show:**
- **Output:** {meta.get('output', '?')}
- **Style:** {args.style} · **Guide character:** {args.mascot} · **Voice:** {args.voice}
- **Storyboard needed:** {meta.get('storyboard', 'no')}
- **Last approved build to copy from (folder):**
- **Private house notes:** {house or 'none found'}
- **Cost:** 0 unless written here and approved

## Ruled out (the owner's list, give it to every reviewer)

-

## Approvals

| Gate | Date | Yes / notes |
|---|---|---|
| Brief | | |
| Script | | |
| Style frame | | |
| Voice | | |
| Go | | |
| Cut | | |
"""


FACTS = """# Fact pack: {title}

Every number, name and quote in the script has a row here, opened the day it was used. If it is not here, it is not in
the script. Never round up; write the exact figure and the words that are true (4,873 is "almost 4,900").

| # | Claim, as it will be said | Exact source words or number | Source (title, link or path) | Opened | Checked by |
|---|---|---|---|---|---|
| 1 | | | | | |

## Dropped (looked true, was not)

| Claim | Why |
|---|---|
| | |
"""

CAPTURES = """# Captures: {title}

One row per clip. Sample data only; read the frames, don't assume.

| Clip | Shows, with clip times | Names and numbers on screen | Sped-up spans | Ugly spots to hide |
|---|---|---|---|---|
| | | | | |
"""

STORYBOARD = """# Storyboard: {title}

The owner approves this before anything is drawn. One row per shot.

| Shot | Scene | Spoken line | What happens (wind-up, action, settle) | Screen direction | Who and which props | Drawings |
|---|---|---|---|---|---|---|
| | | | | | | |

## Scale chart (characters and props, heights relative to one character)

-
"""

OWNER = """# Owner notes: {title}

Verbatim, dated, with the time code they refer to. Wait for all of them, say them back, then rebuild once.

| When | Cut | Time code | The owner's words | What we will do | Done |
|---|---|---|---|---|---|
| | | | | | |

## State back and wait for go

-
"""

def scenes_html(titles):
    out = ["<!-- scenes.html: one section per scene. This starter only shows each title; build the real scenes here.",
           "     Worked example: templates/example/scenes.html and scenes.js in the plugin. -->",
           '<div id="world"><div id="wprops"></div></div>']
    for i, t in titles:
        out += [f'<section class="scene" id="sc{i}">', f'  <div class="plq ttl pre" id="t{i}"><div class="h">{t}</div></div>',
                f'  <div id="p{i}"></div>', "</section>"]
    return "\n".join(out) + "\n"


def scenes_js(titles, guide):
    out = ["// scenes.js: animations hang off spoken words. S('s1a') is when the first sentence of scene 1 starts, E('s1a')",
           "// when it ends, SC(1) when scene 1 starts. Never type seconds."]
    for i, _ in titles:
        out.append(f"fade('#t{i}', SC({i}) + .1);")
        if guide:
            out.append(f"popIn(sprite($('#p{i}'), '{guide}', 960, 880, 520), S('s{i}a') + .1);")
    return "\n".join(out) + "\n"


KINDS = {
    "page": ("complete", "The sprite page: one HTML file and a frame-exact MP4 from it."),
    "deck": ("partial", "Runs today as the sprite page: one HTML file with its audio inside, play, pause, seek and speed. "
                        "Click-through slides and click-for-detail stations are yours to write; no slide engine is bundled."),
    "footage": ("complete", "Real app footage on the stage page, with one-take cues. You record the footage."),
    "drawn": ("partial", "Voice, cues, prompts, sprite prep, render and proof are scripted. Drawing the poses, the shot "
                         "list and timing the drawings are hand work; nothing here checks motion for you."),
}


def kind_of(meta):
    k = meta.get("build", "page").split()[0]
    if k not in KINDS:
        raise SystemExit(f"profile {meta.get('profile')}: build: {k!r} is not one of {', '.join(KINDS)}")
    return k


def player_gaps():
    """What the bundled page player lacks against the house rule (full-screen key, speed to 2x), read from its source."""
    src = rd(os.path.join(ROOT, "templates", "engine", "engine.js"))
    gaps = []
    if "requestFullscreen" not in src:
        gaps.append("no F key for full screen")
    m = re.search(r"RATES\s*=\s*\[([^\]]*)\]", src)
    rates = [float(x) for x in re.findall(r"[\d.]+", m.group(1))] if m else []
    if not rates or max(rates) < 2:
        gaps.append(f"speed stops at {max(rates) if rates else '?'}x, not 2x")
    return gaps


def env_text(out, overlay):
    q = shlex.quote
    ovl = f"export EXPLAINER_FORGE_OVERLAY={q(overlay)}\n" if overlay else ""
    return f"""# Sourced first by every block in run.md, because a shell forgets its variables between calls.
# It also moves into the project folder. If you move the folder or the plugin, edit the two paths below.
PROJECT={q(out)}
P={q(ROOT)}
VOICE_PY="${{EXPLAINER_VOICE_PY:-$PROJECT/voice/.venv/bin/python}}"   # set EXPLAINER_VOICE_PY to reuse one venv for every project
export P PROJECT VOICE_PY
{ovl}if [ -z "${{PLAYWRIGHT_PATH:-}}" ] && [ -d "$PROJECT/node_modules/playwright" ]; then export PLAYWRIGHT_PATH="$PROJECT/node_modules/playwright"; fi
cd "$PROJECT" || return 1 2>/dev/null || exit 1
"""


def run_text(title, meta, args, seed, has_voice, mascot_dir, slug, out, style_refs, fonts):
    kind = kind_of(meta)
    wpm = meta.get("wpm", "200")
    env = f". {shlex.quote(os.path.join(out, 'env.sh'))}"
    ref_wav, ref_txt = ("voice/reference.wav", "voice/reference.txt") if has_voice else ("voice/CHOSEN.wav", "voice/CHOSEN.txt")
    ref = f"--ref-wav {ref_wav} --ref-text-file {ref_txt} "

    def sh(*lines):
        return "```bash\n" + env + "\n" + "\n".join(x for x in lines if x) + "\n```\n"

    sans = [f["file"] for f in fonts if f["family"] == "EF Body" and f["weight"] == 600] or [f["file"] for f in fonts]
    label_font = f"-font ../../{sans[0]} " if sans else ""          # some ImageMagick installs have no default font
    status, what = KINDS[kind]
    L = [f"# Run: {title}", "",
         f"Profile `{meta['profile']}`, build path **{status}**: {what}", "",
         "Sections have the same numbers as the steps in skill `make-an-explainer`. Every block starts by sourcing `env.sh`, so "
         "each one works in a fresh shell. Written by new_project.py for plugin version " + plugin_version() + "; after a plugin "
         "update, scaffold a temp project and compare, because flags can change.", "",
         "## 0. Setup", "", "Per project. `EXPLAINER_VOICE_PY` reuses a voice venv you already have.", "",
         sh('(cd voice && uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python mlx-audio mlx-whisper soundfile numpy librosa Pillow)',
            'npm i gsap playwright                    # ffmpeg is also needed, and Chrome',
            'npx playwright install chromium          # ring_check and deck_proof use it' if kind in ("footage", "deck") else "",
            'python3 "$P/scripts/new_project.py" --check-rules'),
         "## 1. Brief", "", "Fill `brief.md` with the owner, on one page. **Gate: the owner approves the brief.**", "",
         "## 2. Fact pack", "",
         "Fill `facts.md`: every claim, the exact source words, the source, the day it was opened. Re-count numbers today. A cheaper "
         "model gathers, the strongest checks. Put everyone named in the sources into `names.txt` now: an empty list checks nobody. "
         "**Gate: no claim without a row.**", "",
         "## 3. Script", "",
         "Write `script.md` (already in the parser's format). Spoken spellings go in `saymap.json`.", "",
         sh('python3 "$P/scripts/make_narration.py" script.md --say-map saymap.json --out narration.json --list',
            'python3 "$P/scripts/name_check.py" --names names.txt --allow allow.txt script.md facts.md narration.json'),
         "**Gate: every word a beginner would not know is gone, defined before use, or on a tag.**", "",
         "## 4. Cold script review", "",
         "A fresh strongest-model reader gets this file and nothing else, and reports where a beginner gets lost:", "",
         sh("python3 - <<'EOF'", "import json", "for s in json.load(open('narration.json')):",
            "    print(f\"\\n[{s['scene']}] \" + ' '.join(c['show'] for c in s['chunks']))", "EOF") .replace(
             "python3 - <<'EOF'", "python3 - > review/narration-only.txt <<'EOF'"),
         "Save the findings to `review/script-review.md`. **Gate: each one fixed, or ruled out by the owner.**", "",
         "## 5. Style frame", "",
         "One image of the wow scene. Write the scene into `prompts/style-frame.txt` (one place marked `SCENE:`). Any image tool that "
         "takes reference pictures works: attach the files below, use the prompt word for word. `codex exec` is the shape "
         "that made this style's sprites (OpenAI Codex CLI, on its own plan limits); swap in your own tool. The last line burns in the label.", "",
         sh("mkdir -p review/style-frame && cd review/style-frame",
            'for f in ../../refs/*.webp; do ffmpeg -v error -y -i "$f" "$(basename "$f" .webp).png"; done',
            "cp ../../prompts/style-frame.txt prompt.txt",
            "codex exec --skip-git-repo-check -s workspace-write " + " ".join(f"-i {r}.png" for r in style_refs) + " - < prompt.txt",
            f'magick style-frame.png {label_font}-gravity north -pointsize 40 -annotate +0+16 "Style frame A" style-frame-labelled.png'),
         "Open it yourself first. **Gate: the owner approves the look, from a labelled image.**", "",
         "## 6. Voice pick", ""]
    if has_voice:
        L += [f"This profile's voice is `{args.voice}`, copied to `voice/reference.wav`. Play the sample; if the owner says no, audition.", "",
              sh(f'open "$P/voices/{args.voice}/sample.m4a" || true')]
    else:
        L += [f"**No voice is chosen** (profile says {meta.get('voice', 'ASK')}). The owner must pick one. The commands in step 8 point at "
              "`voice/CHOSEN.wav` and fail until you put the pick there.", "",
              "Play both bundled samples (a man's and a woman's voice), and design candidates when neither fits:", "",
              sh('ls "$P"/voices/*/sample.m4a')]
    L += ["Audition three candidates (skill `narrator-voice`; put your own descriptions in `voice/auditions/voice.json` first):", "",
          sh("mkdir -p voice/auditions && cd voice/auditions",
             '"$VOICE_PY" "$P/scripts/voice/design_voices.py" --out . --voices A B C'),
          "Send `samples/candidate-A.m4a`, B and C, labelled. When the owner names a letter (or a bundled voice), copy that pair:", "",
          sh("cp voice/auditions/ref/ref-B.wav " + ref_wav, "cp voice/auditions/ref/ref-B.txt " + ref_txt,
             ("" if has_voice else f'# or a bundled one: cp "$P/voices/coworker-baritone/reference.wav" {ref_wav}; cp "$P/voices/coworker-baritone/reference.txt" {ref_txt}')),
          "Bundled seeds: coworker-baritone 7, default-narrator 42. **Gate: the owner picked by ear.**", "",
          "## 7. Owner go", "",
          "One message to the owner: `script.md`, the labelled style frame, the voice letter, the cost plan (0 unless written), "
          + ("`storyboard.md`, " if meta.get("storyboard") == "yes" else "") +
          "and what is not decided. Record the answer in the Approvals table of `brief.md`. **Gate: an explicit go. Nothing is built "
          "or bought before it.**", "",
          "## 8. Voice, one take", "",
          "Run from the approved script. Re-run step 3 if the script changed; rename a take made from older words.", "",
          sh(f'"$VOICE_PY" "$P/scripts/voice/one_take.py" --narration narration.json --out audio/take-raw.wav {ref}--seed {seed}',
             '"$VOICE_PY" "$P/scripts/take_check.py" --take audio/take-raw.wav --narration narration.json',
             f'"$VOICE_PY" "$P/scripts/audio_build.py" --take audio/take-raw.wav --narration narration.json --out audio --wpm {wpm} --words-json audio/take-raw.stt.json',
             '"$VOICE_PY" "$P/scripts/sync_check.py" --audio audio/narration.m4a --cues audio/cues.json --narration narration.json'),
          "Same thing in one command (it writes the same files):", "",
          sh(f'PY="$VOICE_PY" WPM={wpm} SEED={seed} REF_WAV={ref_wav} REF_TEXT_FILE={ref_txt} NAME={slug} bash "$P/scripts/make_onetake_video.sh" narration take check audio'),
          "Misread line: change the seed, or reword and redo the whole take. **Gate: no word missing or added, and the owner heard the "
          "product names.**", "",
          "## 9. Build", ""]
    char = f'--character "$P/mascots/{args.mascot}/character.txt" ' if mascot_dir else ""
    sprites = [sh(f'python3 "$P/scripts/sprite_prompts.py" --items prompts/items.json --header prompts/prompt-header.txt {char}--out prompts/out'),
               "Send each `prompts/out/<name>.txt` with the files in `refs/` (same command shape as step 5), one object per image, into "
               "`raw/`. Name each one's largest height on screen in `sprites.json`, then:", "",
               sh('"$VOICE_PY" "$P/scripts/prep_sprites.py" --src raw --out img --heights sprites.json'),
               "Skip that line while `raw/` is empty: starter sprites are already in `img/`. Delete the unused ones before the last build.", ""]
    page = ["Write `scenes.html` and `scenes.js` (skill `sprite-explainer`), then:", "",
            sh('python3 "$P/scripts/build_explainer.py" project.json')]
    if kind in ("page", "deck"):
        L += sprites + page
    if kind == "deck":
        gaps = player_gaps()
        L += (["Player gaps in this plugin version: " + "; ".join(gaps) + ". The house rule wants both, so tell the owner or add "
               "them to the page before shipping.", ""] if gaps else [])
        L += ["**Click-through slides instead** (advance by key, click a station for detail): write `deck/src.html` to the contract in "
              f"`{os.path.join(ROOT, 'references', 'formats.md')}` (`window.__deck`, one step per sentence), starting from the last "
              "approved deck's folder. This makes its cue file from the one take (each build 0.3 s early) and one file with the audio "
              "inside:", "",
              sh("mkdir -p deck", 'python3 "$P/scripts/new_project.py" --cues-for deck --audio audio --out deck',
                 f'python3 "$P/scripts/inline_build.py" deck/src.html {slug}-deck.html --root deck')]
    if kind == "footage":
        L += ["Record the real app with sample data only (skill `app-footage`) into `captures/clips/*.mp4`, one row per clip in "
              "`captures/manifest.md`. Then make the stage page:", "",
              sh("mkdir -p captures/clips build/vendor",
                 'for f in stage.html timeline.js; do [ -e "build/$f" ] || cp "$P/templates/$f" build/; done',
                 '[ -e build/scenes.js ] || cp "$P/templates/scenes.example.js" build/scenes.js',
                 "cp node_modules/gsap/dist/gsap.min.js build/vendor/",
                 'python3 "$P/scripts/new_project.py" --cues-for stage --audio audio --out build',
                 'python3 "$P/scripts/prep_media.py" --build build --src captures/clips'),
              "Edit `build/stage.html` and `build/scenes.js`: every time comes from `T(id)` or `E(id)` (the ids in `audio/cues.json`). "
              "`W(id, word)` has no word times on this route and falls back to the line start. Every ring gets a box measured on the "
              "frame and an out time. Clay sprites for the parts you can't film are in `img/`. Cover what must not show with "
              "`track_patch.py` or `detect_band.py` (skill `app-footage`).", ""]
    if kind == "drawn":
        L += ["1. `storyboard.md`: one row per shot, with the action, its screen direction and the spoken line. The owner approved it in step 7.",
              "2. Kit first: a cast sheet (turnaround and expressions) and a scale chart, characters AND props. Attach both to every request.",
              "3. One prompt per drawing, named `<shot>-01.png`, `-02`, and so on, in `prompts/items.json`:", ""] + sprites + [
              "4. Build with drawings swapped on the timeline. This works in `scenes.js` (a new drawing every 3 frames from the spoken "
              "word on):", "", "```js",
              "const act = sprite($('#p2'), 'throw-01', 960, 880, 520);",
              "['throw-01', 'throw-02', 'throw-03'].forEach((n, i) => tl.set(act, { attr: { src: IMGS[n] } }, S('s2a') + i * 3 / 30));",
              "```", "", "   Give every drawing the same canvas and foot position. `prep_sprites.py` trims each image alone, so compare the sizes: "
              "a trimmed pose can jump.", "", *page,
              "5. Prove motion with a strip of every 3rd frame per action (change the times):", "",
              sh(f'ffmpeg -v error -y -ss 12 -t 1.5 -i {slug}.mp4 -vf "fps=10,scale=480:-1,tile=5x3" -frames:v 1 proof/strip-throw.png'),
              "   (Run it after step 10 has made the MP4.)", ""]
    L += ["## 10. Proof", ""]
    if kind == "footage":
        L += [sh('python3 "$P/scripts/dead_air.py" --cues audio/cues.json --audio audio/narration.m4a',
                 'node "$P/scripts/ring_check.mjs" --page build/stage.html --out proof/rings',
                 f'node "$P/scripts/render_frames.mjs" --page build/stage.html --audio build/narration.m4a --out {slug}.mp4 --workers 4',
                 f'SYNC_LIMIT_MS=150 bash "$P/scripts/verify_video.sh" {slug}.mp4 build/cues.json proof',
                 f"cp audio/captions.srt {slug}.srt")]
    else:
        L += [sh(f'node "$P/scripts/proof.mjs" --page {slug}.html --out proof --cues audio/cues.json --audio audio/narration.m4a',
                 'python3 "$P/scripts/dead_air.py" --cues audio/cues.json --audio audio/narration.m4a',
                 f'node "$P/scripts/hero.mjs" --page {slug}.html --out hero.png')]
        if kind == "deck":
            L += ["The HTML file is the deliverable. Only if the click-through deck exists:", "",
                  sh(f'node "$P/scripts/deck_proof.mjs" --page {slug}-deck.html --out proof/deck',
                     f'node "$P/scripts/deck_proof.mjs" --page {slug}-deck.html --sync deck/cues.json',
                     f'node "$P/scripts/deck_proof.mjs" --page {slug}-deck.html --sync deck/cues.json --rate 2'),
                  "Only if an MP4 was asked for:", ""]
        L += [sh(f'node "$P/scripts/render_frames.mjs" --page {slug}.html --audio audio/narration.m4a --out {slug}.mp4 --workers 4',
                 f'SYNC_LIMIT_MS=150 bash "$P/scripts/verify_video.sh" {slug}.mp4 audio/cues.json proof',
                 f"cp audio/captions.srt {slug}.srt")]
    L += ["Open every still in `proof/` and every sheet in `proof/review/`. One browser render at a time on a small machine. Names:", "",
          sh('python3 "$P/scripts/name_check.py" --names names.txt --allow allow.txt script.md facts.md narration.json '
             + ("build/scenes.js build/stage.html" if kind == "footage" else "scenes.html scenes.js")),
          "For chat (about 35 MB or less):", "",
          sh(f"ffmpeg -v error -y -i {slug}.mp4 -vf scale=1280:-2 -c:v libx264 -b:v 900k -c:a aac -b:a 96k -movflags +faststart {slug}-720p.mp4"),
          "**Gate: every still opened, the numbers printed, 0 names.**", "",
          "## 11. Independent review", "",
          "A fresh strongest-model reviewer who did not build it gets the cut, the proof sheets, `script.md`, `facts.md`, the rules, the "
          "ruled-out list in `brief.md` and the flaws you know. It returns SHIP or FIX FIRST, at most 8 ranked findings with time code "
          "and smallest fix, saved to `review/cut-review.md`. Drop any finding that breaks an owner ruling.", "",
          "## 12. Owner viewing", "",
          "Send the draft to the owner only, known flaws first. Notes go in `owner-notes.md`, word for word, with time codes.", "",
          "## 13. Batch edits", "",
          "Wait for all the notes, say them back, get a go, then rebuild once. A visual change repeats 9 and 10. A changed word "
          "repeats 3 and 8 with a whole new take, after:", "",
          sh("mv audio/take-raw.wav audio/take-raw.old-$(date +%Y%m%d-%H%M).wav"),
          "**Gate: the owner says ship.**", "",
          "## 14. Post", "",
          "Draft `post.md`: one line on what it is, one image, never the story. Check it for names. The owner posts.", "",
          "## 15. Retro", "", "Fill `retro.md` (skill `lessons-loop`)."]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ one-take cues for the other two page types

def two_rows(text, width=42):
    if len(text) <= width:
        return [text]
    ws = text.split()
    k = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(" ".join(ws[k:])))) if len(ws) > 1 else 0
    return [" ".join(ws[:k]), " ".join(ws[k:])] if k else [text]


def cues_for(target, audio, out):
    """audio/cues.json (one take) -> the stage page's build/cues.json + captions.json, or a deck's [[slide start, builds...]]."""
    c = json.loads(rd(os.path.join(audio, "cues.json")))
    os.makedirs(out, exist_ok=True)
    if target == "deck":
        slides = []
        for s in c["scenes"]:
            t = [x["start"] for x in c["chunks"] if x["scene"] == s["n"]]
            slides.append([s["start"]] + [round(max(s["start"], x - .3), 3) for x in t[1:]])
        made = {"cues.json": slides}
        note = "data-steps per slide: " + ", ".join(str(len(s) - 1) for s in slides)
    else:
        title = {s["n"]: s["title"] for s in c["scenes"]}
        lines = [{"id": x["id"], "scene": x["scene"], "title": title[x["scene"]], "start": x["start"],
                  "dur": round(x["end"] - x["start"], 3), "end": x["end"], "caption": x["show"]} for x in c["chunks"]]
        made = {"cues.json": {"total": c["duration"], "fps": 30, "tempo": c.get("tempo"), "scenes": c["scenes"], "lines": lines},
                "captions.json": [{"start": k["start"], "end": k["end"], "rows": two_rows(k["text"])} for k in c["captions"]]}
        shutil.copyfile(os.path.join(audio, "narration.m4a"), os.path.join(out, "narration.m4a"))
        note = f"{len(lines)} lines, {len(made['captions.json'])} captions"
    for n, v in made.items():
        with open(os.path.join(out, n), "w", encoding="utf-8") as f:
            json.dump(v, f, indent=1, ensure_ascii=False)
    print(f"{target}: wrote {', '.join(made)} to {out}; {note}")
    return 0


def plugin_version():
    try:
        return json.loads(rd(os.path.join(ROOT, ".claude-plugin", "plugin.json")))["version"]
    except (OSError, KeyError, ValueError):
        return "?"


# ------------------------------------------------------------------ main

def scaffold(args):
    if args.overlay:
        args.overlay = os.path.realpath(os.path.expanduser(args.overlay))
        if not os.path.isdir(args.overlay):
            raise SystemExit(f"no overlay folder {args.overlay}")
    profs = profiles(args.overlay)
    if args.profile not in profs:
        raise SystemExit(f"no profile {args.profile!r}; have: {', '.join(profs)}")
    ppath, psrc = profs[args.profile]
    meta, _ = read_profile(ppath)
    kind = kind_of(meta)
    out = os.path.realpath(os.path.expanduser(args.out))
    if os.path.isdir(out) and os.listdir(out):
        raise SystemExit(f"{out} is not empty; choose a new folder")
    if not args.style:
        args.style = "clay-factory"
    style_dir = os.path.join(ROOT, "styles", args.style)
    if not os.path.isdir(style_dir):
        raise SystemExit(f"no style {args.style!r} in {ROOT}/styles")
    asked = args.mascot or meta.get("mascot", "none")
    args.mascot = args.mascot or meta.get("mascot", "none").split()[0]
    mascot_dir = os.path.join(ROOT, "mascots", args.mascot) if args.mascot != "none" else None
    if mascot_dir and not os.path.isdir(mascot_dir):
        print(f"note: no bundled mascot for {asked!r}; using none")
        args.mascot, mascot_dir = "none", None
    args.voice = args.voice or meta.get("voice", "ASK")
    vdir = os.path.join(ROOT, "voices", args.voice)
    has_voice = os.path.isdir(vdir)
    seed = {"coworker-baritone": 7, "default-narrator": 42}.get(args.voice, 42)

    for d in ("prompts", "refs", "img", "raw", "fonts", "voice", "audio", "proof", "review"):
        os.makedirs(os.path.join(out, d))

    def w(n, t):
        with open(os.path.join(out, n), "w", encoding="utf-8") as f:
            f.write(t)

    house = ov.find("house.md", args.overlay)

    n = scene_count(meta)
    w("brief.md", brief_text(args.title, meta, args, ov.overlay_dir(args.overlay), house))
    w("facts.md", FACTS.format(title=args.title))
    w("script.md", script_text(args.title, meta, n))
    w("owner-notes.md", OWNER.format(title=args.title))
    tmpl = rd(os.path.join(ROOT, "skills", "lessons-loop", "retro-template.md"))
    w("retro.md", tmpl.replace("{{TITLE}}", args.title).replace("{{DATE}}", datetime.date.today().isoformat()).replace("{{PROFILE}}", args.profile))

    # names, allow, pronunciations (overlay merged in)
    names = ["# People who must not appear. Add everyone in the source documents. One per line, full name."]
    names += [x for x in merge_lines(ov.find("names.txt", args.overlay)) if not x.startswith("#")]
    w("names.txt", "\n".join(names) + "\n")
    w("allow.txt", "\n".join(merge_lines(ov.find("allow.txt", args.overlay)) or ["Claude Code"]) + "\n")
    base = {"replace": [], "regex": [["\\bAIs\\b", "A Is"], ["\\bAI\\b", "A I"]], "drop": ["\"", "“", "”"]}
    osm = ov.find("say-map.json", args.overlay)
    if osm:
        sm = json.loads(rd(osm))
        base["replace"] = sm.get("replace", []) + base["replace"]
        base["regex"] = sm.get("regex", []) + base["regex"]
        base["drop"] = list(dict.fromkeys(base["drop"] + sm.get("drop", [])))
    w("saymap.json", json.dumps(base, indent=1, ensure_ascii=False) + "\n")

    # style: prompts, fonts, sprites, theme
    for f in ("prompt-header.txt", "items.json", "header.md", "items.md", "style-frame.txt"):
        s = os.path.join(style_dir, "prompts", f)
        if os.path.exists(s):
            shutil.copyfile(s, os.path.join(out, "prompts", f))
    if os.path.isdir(os.path.join(style_dir, "refs")):
        for f in os.listdir(os.path.join(style_dir, "refs")):
            shutil.copyfile(os.path.join(style_dir, "refs", f), os.path.join(out, "refs", f))
    fonts = []
    fdir = os.path.join(style_dir, "fonts")
    if os.path.isdir(fdir):
        for f in sorted(os.listdir(fdir)):
            shutil.copyfile(os.path.join(fdir, f), os.path.join(out, "fonts", f))
            if f.endswith((".ttf", ".otf", ".woff2")):
                fam = "EF Head" if "Serif" in f else "EF Body"
                fonts.append({"family": fam, "weight": 600 if ("Semibold" in f or "Bold" in f) else 400, "file": f"fonts/{f}"})
    for src in (os.path.join(style_dir, "sprites"), os.path.join(mascot_dir, "poses") if mascot_dir else None):
        if src and os.path.isdir(src):
            for f in os.listdir(src):
                if f.endswith(".webp"):
                    shutil.copyfile(os.path.join(src, f), os.path.join(out, "img", f))
    theme = os.path.join(style_dir, "theme.css")
    if os.path.exists(theme):
        shutil.copyfile(theme, os.path.join(out, "theme.css"))
    if mascot_dir and os.path.isdir(os.path.join(mascot_dir, "refs")):
        for f in os.listdir(os.path.join(mascot_dir, "refs")):
            shutil.copyfile(os.path.join(mascot_dir, "refs", f), os.path.join(out, "refs", f))
    w("sprites.json", json.dumps({"_comment": "new raw sprite name -> largest height on screen in px", "heights": {}}, indent=1) + "\n")
    import narration_lib as nl
    titles = [(i, t) for i, t, _ in nl.parse_script(rd(os.path.join(out, "script.md")))]
    poses = sorted(f[:-5] for f in os.listdir(os.path.join(out, "img")) if f.startswith(args.mascot + "-"))
    w("scenes.html", scenes_html(titles))
    w("scenes.js", scenes_js(titles, next((p for p in poses if p.endswith("-point")), poses[0] if poses else None)))
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "explainer"
    w("project.json", json.dumps({
        "title": args.title, "description": f"A narrated explainer: {args.title}", "scenes_html": "scenes.html",
        "scenes_js": "scenes.js", "theme_css": "theme.css" if os.path.exists(theme) else None, "fonts": fonts,
        "sprites_dir": "img", "audio": "audio/narration.m4a", "cues": "audio/cues.json", "out": f"{slug}.html",
        "storage_key": f"{slug}-", "play_label": "Play, with sound"}, indent=1) + "\n")

    # voice
    if has_voice:
        shutil.copyfile(os.path.join(vdir, "reference.wav"), os.path.join(out, "voice", "reference.wav"))
        shutil.copyfile(os.path.join(vdir, "reference.txt"), os.path.join(out, "voice", "reference.txt"))
    if kind == "footage":
        os.makedirs(os.path.join(out, "captures", "clips"))
        w("captures/manifest.md", CAPTURES.format(title=args.title))
    if meta.get("storyboard") == "yes":
        w("storyboard.md", STORYBOARD.format(title=args.title))
    refs = sorted((f[:-5] for f in os.listdir(os.path.join(out, "refs")) if f.endswith(".webp")), key=lambda f: (f != "style-reference", f))
    w("env.sh", env_text(out, ov.overlay_dir(args.overlay)))
    w("run.md", run_text(args.title, meta, args, seed, has_voice, mascot_dir, slug, out, refs, fonts))
    return out, meta, psrc, names, has_voice, house


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title")
    ap.add_argument("--profile")
    ap.add_argument("--out")
    ap.add_argument("--style", default="clay-factory")
    ap.add_argument("--mascot", help="mascot folder name, or none (default: the profile's)")
    ap.add_argument("--voice", help="voices/<name> (default: the profile's)")
    ap.add_argument("--overlay", help="overlay folder (default: $EXPLAINER_FORGE_OVERLAY or ~/.config/explainer-forge/overlay)")
    ap.add_argument("--list-profiles", action="store_true")
    ap.add_argument("--show-overlay", action="store_true")
    ap.add_argument("--check-rules", action="store_true")
    ap.add_argument("--cues-for", choices=("stage", "deck"), help="convert one-take cues (with --audio and --out)")
    ap.add_argument("--audio", default="audio", help="folder with cues.json, for --cues-for")
    a = ap.parse_args(argv)
    if a.cues_for:
        if not a.out:
            ap.error("--cues-for needs --out")
        return cues_for(a.cues_for, a.audio, a.out)
    if a.check_rules:
        bad, n = check_rules()
        print(f"{n} rules, {len(bad)} problems")
        print("\n".join(bad))
        return 1 if bad else 0
    if a.show_overlay:
        d = ov.overlay_dir(a.overlay)
        print("overlay:", d or "none found (fine, the plugin works without one)")
        if d:
            print("  files:", ", ".join(sorted(os.listdir(d))))
        return 0
    if a.list_profiles:
        for k, (p, src) in profiles(a.overlay).items():
            m, _ = read_profile(p)
            print(f"{k:24} {m.get('title', '')} | {m.get('length_target', '')} | {m.get('words', '')} words | {src}")
        return 0
    if not (a.title and a.profile and a.out):
        ap.error("--title, --profile and --out are required")
    out, meta, psrc, names, has_voice, house = scaffold(a)
    print(f"project: {out}\nprofile: {a.profile} ({psrc}) · style {a.style} · mascot {a.mascot} · voice {a.voice}")
    print(f"names to grep: {len(names) - 1} · house notes: {house or 'none'}")
    if not has_voice:
        print(f"note: no voice chosen ({a.voice}); step 6 auditions, and the take in step 8 fails until voice/CHOSEN.wav exists")
    status, what = KINDS[kind_of(meta)]
    print(f"build path: {status}. {what}")
    missing = missing_scripts(rd(os.path.join(out, "run.md")))
    if missing:
        print("WARNING: run.md names scripts this plugin version does not have:", ", ".join(missing))
    print("next: fill brief.md, then follow run.md")
    return 0


def missing_scripts(text):
    return [m for m in sorted(set(re.findall(r'\$P/(scripts/[\w./-]+)', text))) if not os.path.exists(os.path.join(ROOT, m))]


if __name__ == "__main__":
    sys.exit(main())
