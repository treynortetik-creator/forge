#!/usr/bin/env python3
"""
sung_check.py - compare what a generated song actually SANG against the lyrics you wrote.

    python3 sung_check.py song.m4a --lyrics lyrics.txt
    python3 sung_check.py song.m4a --lyrics lyrics.txt --vocals stems/vocals.wav   # skip separation
    python3 sung_check.py song.wav --lyrics lyrics.txt --json
    python3 sung_check.py song.wav --lyrics lyrics.txt --only-problems

PIPELINE
  1. Separate vocals with Demucs (htdemucs, two stems). Done FIRST on purpose: whisper on a
     full mix hallucinates "[MUSIC PLAYING]" and drops sung words under the band.
     Needs `uv` and `ffmpeg`. m4a/mp3 are converted to wav first (libsndfile cannot read m4a).
  2. Transcribe the vocal stem with whisper: whisper.cpp (`whisper-cli` + a ggml model, via
     --model or $WHISPER_MODEL) if present, else faster-whisper through `uv run`.
  3. Align the transcript to your written words (difflib SequenceMatcher on normalised
     words) and report, per written line: matched / misheard / dropped / different,
     plus audio material that is not in your lyrics (added, or a repeat of a section).

READ THIS BEFORE TRUSTING A RESULT
  The transcript is itself a model's guess at sung audio. A "misheard" line means "a
  speech model heard something else here - go LISTEN to this timestamp". It is not proof
  the singer got it wrong, and a "matched" line is not proof the pronunciation was good.
  Sung vowels are stretched, harmonies overlap, whisper can swap near-homophones
  (sail/sale) in either direction. Timestamps are word-level estimates, good to a few
  seconds. The script deliberately does NOT feed your lyrics to whisper as a prompt:
  that would bias it toward agreeing with you and hide exactly the errors you want.

Exit code: 0 always (it reports, it does not judge); 2 if a pipeline step failed.
"""
import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SELF = os.path.abspath(__file__)
SECTION_RE = re.compile(r"^\[(.+?)\]$")


# ------------------------------------------------------------------ helpers
def die(msg, code=2):
    print(f"sung_check: {msg}", file=sys.stderr)
    sys.exit(code)


def run(cmd, what, quiet=True):
    p = subprocess.run(cmd, capture_output=quiet, text=True)
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-1500:]
        die(f"{what} failed (exit {p.returncode}).\n{tail}")
    return p


def norm_word(w):
    w = w.lower().replace("’", "'")
    return re.sub(r"[^a-z0-9]", "", w)


def split_words(text):
    text = text.replace("’", "'")
    out = []
    for tok in re.split(r"[\s\-—]+", text):
        n = norm_word(tok)
        if n:
            out.append(n)
    return out


def fmt_time(t):
    if t is None:
        return "  ?  "
    m, s = divmod(int(t), 60)
    return f"{m}:{s:02d}"


# ------------------------------------------------------------------ lyrics
def read_lyrics(path):
    """-> list of lines {idx, section, text, words:[norm]}"""
    lines, section = [], "(untagged)"
    with open(path, encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            m = SECTION_RE.match(s)
            if m:
                label = m.group(1).strip()
                if re.match(r"(?i)^(intro|verse|pre|chorus|post|hook|refrain|bridge|outro|break|"
                            r"interlude|instrumental|solo|drop|build|coda|tag|vamp|spoken)", label):
                    section = label
                continue
            if re.match(r"(?i)^(title|style|lyrics)\s*:", s):
                continue
            s_vocal = re.sub(r"\([^)]*\)", " ", s)    # (backing vocals) are not graded
            w = split_words(s_vocal)
            if w:
                lines.append({"idx": len(lines), "section": section, "text": s, "words": w})
    return lines


# ------------------------------------------------------------------ audio
def to_wav(src, outdir):
    dst = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "44100", "-ac", "2", dst],
        "ffmpeg conversion to wav")
    return dst


def separate_vocals(wav, outdir):
    cmd = ["uv", "run", "--with", "demucs", "--with", "numpy", "--with", "soundfile",
           "--with", "torchcodec", "python", "-m", "demucs", "--two-stems=vocals",
           "-n", "htdemucs", "-o", outdir, wav]
    print("separating vocals with Demucs (first run downloads the model; a few minutes on CPU)...",
          file=sys.stderr)
    run(cmd, "demucs separation")
    stem = os.path.splitext(os.path.basename(wav))[0]
    v = os.path.join(outdir, "htdemucs", stem, "vocals.wav")
    if not os.path.exists(v):
        die(f"demucs finished but {v} does not exist")
    return v


def find_model(arg):
    cand = arg or os.environ.get("WHISPER_MODEL")
    if cand and os.path.exists(os.path.expanduser(cand)):
        return os.path.expanduser(cand)
    return None


def clean_tokens(entries):
    """entries: [(text, start)] -> [(word, start)] with [MUSIC]/(sigh) style tokens removed."""
    out = []
    for text, start in entries:
        text = re.sub(r"\[[^\]]*\]|\([^)]*\)|\*[^*]*\*|♪|♫", " ", text)
        for w in split_words(text):
            out.append((w, start))
    return out


def transcribe_cpp(vocals, model, workdir):
    wav16 = to_16k(vocals, workdir)
    prefix = os.path.join(workdir, "whisper")
    # -ml 1 -sow: one word per segment => word-level timestamps; -sns: suppress non-speech tokens
    run(["whisper-cli", "-m", model, "-f", wav16, "-oj", "-ml", "1", "-sow", "-sns",
         "-np", "-of", prefix], "whisper-cli")
    with open(prefix + ".json", encoding="utf-8") as f:
        data = json.load(f)
    # whisper.cpp back-fills a word's start to the previous word's end, so after a long
    # silence the start is wildly early. The end is the reliable edge: clamp start to
    # at most 0.5 s before it.
    ents = []
    for seg in data.get("transcription", []):
        a, b = seg["offsets"]["from"] / 1000.0, seg["offsets"]["to"] / 1000.0
        ents.append((seg.get("text", ""), max(a, b - 0.5)))
    return clean_tokens(ents)


def to_16k(vocals, workdir):
    wav16 = os.path.join(workdir, "vocals16k.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", vocals, "-ar", "16000", "-ac", "1", wav16],
        "ffmpeg resample to 16 kHz")
    return wav16


def transcribe_fw(vocals, model_name, workdir):
    vocals = to_16k(vocals, workdir)
    print("transcribing with faster-whisper via uv (first run downloads the model)...",
          file=sys.stderr)
    p = run(["uv", "run", "--with", "faster-whisper", "python", SELF, "--_fw-worker",
             vocals, model_name], "faster-whisper")
    ents = [(e["text"], e["start"]) for e in json.loads(p.stdout.strip().splitlines()[-1])]
    return clean_tokens(ents)


def fw_worker(path, model_name):
    import wave
    import numpy as np
    from faster_whisper import WhisperModel
    # Decode here (16 kHz mono wav from ffmpeg) so faster-whisper's own PyAV decoder,
    # which breaks on some av versions, is never used.
    with wave.open(path, "rb") as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, word_timestamps=True, language="en", vad_filter=False,
                           condition_on_previous_text=False)
    out = []
    for s in segs:
        for w in (s.words or []):
            out.append({"text": w.word, "start": w.start})
    print(json.dumps(out))


# ------------------------------------------------------------------ alignment
def align(lines, heard):
    W = [(w, ln["idx"]) for ln in lines for w in ln["words"]]
    wwords = [w for w, _ in W]
    line_of = [l for _, l in W]
    hwords = [w for w, _ in heard]
    htimes = [t for _, t in heard]

    sm = difflib.SequenceMatcher(None, wwords, hwords, autojunk=False)
    owner = [None] * len(hwords)
    per = {ln["idx"]: {"matched": 0, "replaced": 0, "missing": 0, "added": 0,
                       "diffs": [], "owned": []} for ln in lines}
    extras = []   # heard material with no home in the written lyrics

    def split_by_line(i1, i2):
        runs, start = [], i1
        for i in range(i1 + 1, i2 + 1):
            if i == i2 or line_of[i] != line_of[start]:
                runs.append((line_of[start], start, i))
                start = i
        return runs

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                owner[j1 + k] = line_of[i1 + k]
                per[line_of[i1 + k]]["matched"] += 1
        elif tag == "delete":
            for li, a, b in split_by_line(i1, i2):
                per[li]["missing"] += b - a
                per[li]["diffs"].append({"written": " ".join(wwords[a:b]), "heard": ""})
        elif tag == "replace":
            nW, nH = i2 - i1, j2 - j1
            heard_by_line = {}
            for k in range(nH):
                li = line_of[i1 + min(nW - 1, (k * nW) // nH)]
                owner[j1 + k] = li
                heard_by_line.setdefault(li, []).append(hwords[j1 + k])
            for li, a, b in split_by_line(i1, i2):
                per[li]["replaced"] += b - a
                per[li]["diffs"].append({"written": " ".join(wwords[a:b]),
                                         "heard": " ".join(heard_by_line.get(li, []))})
        elif tag == "insert":
            inside = 0 < i1 < len(wwords) and line_of[i1 - 1] == line_of[i1]
            if inside and (j2 - j1) <= 3:
                li = line_of[i1]
                for k in range(j1, j2):
                    owner[k] = li
                per[li]["added"] += j2 - j1
                per[li]["diffs"].append({"written": "", "heard": " ".join(hwords[j1:j2])})
            else:
                extras.append({"j1": j1, "j2": j2,
                               "after_line": line_of[i1 - 1] if i1 > 0 else None})

    for j, li in enumerate(owner):
        if li is not None:
            per[li]["owned"].append(j)

    # classify extras: repeat of a written section, or added material
    sections = {}
    for ln in lines:
        sections.setdefault(ln["section"], []).extend(ln["words"])
    out_extras = []
    for ex in extras:
        words = hwords[ex["j1"]:ex["j2"]]
        best, cov = None, 0.0
        if len(words) >= 4:
            for name, sw in sections.items():
                m = difflib.SequenceMatcher(None, words, sw, autojunk=False)
                c = sum(b.size for b in m.get_matching_blocks()) / len(words)
                if c > cov:
                    best, cov = name, c
        kind = "repeat" if best and cov >= 0.5 else "added"
        inside = []
        if kind == "added" and len(words) >= 12:
            for name, sw in sections.items():
                m = difflib.SequenceMatcher(None, words, sw, autojunk=False)
                for b in m.get_matching_blocks():
                    if b.size >= 6:
                        inside.append({"of": name, "start": htimes[ex["j1"] + b.a],
                                       "words": b.size})
        out_extras.append({"contains_repeats": inside,"kind": kind, "of": best if kind == "repeat" else None,
                           "coverage": round(cov, 2), "start": htimes[ex["j1"]],
                           "after_line": ex["after_line"], "words": len(words),
                           "heard": " ".join(words)})

    results = []
    for ln in lines:
        p = per[ln["idx"]]
        n = len(ln["words"])
        heard_txt = " ".join(hwords[j] for j in p["owned"])
        written_txt = " ".join(ln["words"])
        sim = difflib.SequenceMatcher(None, written_txt, heard_txt).ratio() if heard_txt else 0.0
        if p["matched"] == n and p["added"] == 0:
            status = "matched"
        elif p["matched"] == 0 and not p["owned"]:
            status = "dropped"
        elif sim < 0.5:
            status = "different"
        else:
            status = "misheard"
        results.append({
            "line": ln["idx"] + 1, "section": ln["section"], "written": ln["text"],
            "heard": heard_txt, "status": status, "words": n,
            "matched": p["matched"], "replaced": p["replaced"], "missing": p["missing"],
            "added": p["added"], "similarity": round(sim, 2), "diffs": p["diffs"],
            "time": htimes[p["owned"][0]] if p["owned"] else None,
        })
    total_w = len(wwords)
    summary = {
        "written_words": total_w, "heard_words": len(hwords),
        "word_match_pct": round(100.0 * sum(r["matched"] for r in results) / max(total_w, 1), 1),
        "lines": {s: sum(1 for r in results if r["status"] == s)
                  for s in ("matched", "misheard", "different", "dropped")},
    }
    return results, out_extras, summary


# ------------------------------------------------------------------ output
ICON = {"matched": "ok       ", "misheard": "MISHEARD ", "different": "DIFFERENT",
        "dropped": "DROPPED  "}


def render(results, extras, summary, only_problems):
    o = ["NOTE: the transcript is a speech model's guess at sung audio. MISHEARD / DIFFERENT /",
         "DROPPED mean 'go listen at this timestamp', not 'the singer got it wrong'.", ""]
    cur = None
    for r in results:
        if only_problems and r["status"] == "matched":
            continue
        if r["section"] != cur:
            cur = r["section"]
            o.append(f"[{cur}]")
        o.append(f"  {ICON[r['status']]} {fmt_time(r['time']):>5}  L{r['line']:<3} {r['written']}")
        if r["status"] != "matched":
            if r["heard"]:
                o.append(f"{'':>20}heard:   {r['heard']}")
            for d in r["diffs"]:
                w, h = d["written"] or "(nothing)", d["heard"] or "(nothing)"
                o.append(f"{'':>20}  written '{w}'  ->  heard '{h}'")
    if extras:
        o += ["", "AUDIO MATERIAL NOT IN THE WRITTEN LYRICS"]
        for e in extras:
            where = f"after L{e['after_line'] + 1}" if e["after_line"] is not None else "before L1"
            what = (f"repeat of [{e['of']}] ({int(e['coverage'] * 100)}% covered)"
                    if e["kind"] == "repeat" else "ADDED words")
            txt = e["heard"] if len(e["heard"]) < 140 else e["heard"][:137] + "..."
            o.append(f"  {fmt_time(e['start']):>5} {where:<10} {what}: {txt}")
            for c in e.get("contains_repeats", []):
                o.append(f"{'':>20}...includes a run of {c['words']} words from [{c['of']}] "
                         f"at ~{fmt_time(c['start'])}")
    s = summary
    o += ["", f"SUMMARY: {s['word_match_pct']}% of written words matched in order "
          f"({s['written_words']} written, {s['heard_words']} transcribed). Lines: "
          + ", ".join(f"{k} {v}" for k, v in s["lines"].items())]
    return "\n".join(o)


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--_fw-worker":
        return fw_worker(sys.argv[2], sys.argv[3])
    ap = argparse.ArgumentParser(description="Compare the sung vocals of a song to the written lyrics.")
    ap.add_argument("audio", help="the generated song (wav, m4a, mp3...)")
    ap.add_argument("--lyrics", required=True, help="text file of the lyrics you wrote ([Section] tags ok)")
    ap.add_argument("--vocals", help="an existing vocal stem (wav) - skips Demucs")
    ap.add_argument("--model", help="whisper.cpp ggml model path (or $WHISPER_MODEL)")
    ap.add_argument("--engine", choices=["auto", "whisper-cli", "faster-whisper"], default="auto")
    ap.add_argument("--fw-model", default="small.en", help="faster-whisper model name (default small.en)")
    ap.add_argument("--work", help="working dir for stems/transcripts (default: a new temp dir, kept)")
    ap.add_argument("--only-problems", action="store_true", help="hide lines that matched")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.audio):
        die(f"audio not found: {a.audio}")
    lines = read_lyrics(a.lyrics)
    if not lines:
        die("no lyric lines found in --lyrics")
    work = a.work or tempfile.mkdtemp(prefix="sung_check_")
    os.makedirs(work, exist_ok=True)

    if a.vocals:
        vocals = a.vocals
        if not os.path.exists(vocals):
            die(f"--vocals not found: {vocals}")
    else:
        for tool in ("uv", "ffmpeg"):
            if not shutil.which(tool):
                die(f"{tool} not found on PATH (needed for vocal separation)")
        vocals = separate_vocals(to_wav(a.audio, work), os.path.join(work, "stems"))

    model = find_model(a.model)
    engine = a.engine
    if engine == "auto":
        engine = "whisper-cli" if shutil.which("whisper-cli") and model else "faster-whisper"
    if engine == "whisper-cli":
        if not shutil.which("whisper-cli") or not model:
            die("whisper-cli needs the binary on PATH and --model/$WHISPER_MODEL pointing at a ggml model")
        heard = transcribe_cpp(vocals, model, work)
    else:
        if not shutil.which("uv"):
            die("uv not found on PATH (needed for faster-whisper)")
        heard = transcribe_fw(vocals, a.fw_model, work)
    if not heard:
        die("transcript came back empty - is the vocal stem silent?")

    results, extras, summary = align(lines, heard)
    if a.json:
        print(json.dumps({"engine": engine, "vocals": vocals, "work_dir": work,
                          "summary": summary, "lines": results, "extras": extras}, indent=2))
    else:
        print(f"engine: {engine}   vocals: {vocals}   work dir: {work}\n")
        print(render(results, extras, summary, a.only_problems))


if __name__ == "__main__":
    main()
