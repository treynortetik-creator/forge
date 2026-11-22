#!/usr/bin/env python3
"""Turn ONE raw narration take into the final narration audio, the cue sheet and the captions.

  python3 audio_build.py --take audio/take-raw.wav --narration narration.json --out audio --wpm 200
                         [--words-json take-raw.stt.json] [--scale-words] [--gap-base 0.45] [--gap-before 6=0.35]
                         [--head 0.8] [--tail 0.8] [--max-gap 1.2] [--pad 0.12] [--lufs -16] [--tempo 0.94]

What it does, in order:
 1. Trims the take's own edge silence and transcribes it with whisper (or reads --words-json: word timestamps of the
    UNTRIMMED take, [[word, start, end], ...] or the take_check.py output). That transcript is used for the pace.
 2. Measures the SPEAKING pace (words divided by the summed per-scene speech spans, pauses not counted) and derives ONE
    uniform pitch-preserving tempo that moves the take to --wpm. Faster or slower are both allowed: the owner sets the
    target by ear (two approved cuts measured about 180 and about 207 speaking wpm). --tempo skips the arithmetic.
 3. Transcribes the SPED take with whisper and aligns the script words to the heard words with difflib (unmatched
    words are interpolated), giving every chunk a start and end. --scale-words skips that second whisper run and
    scales the first transcript's times by the tempo instead: faster, but measured 0.45 s mean (0.9 s worst) off the
    retranscribed cues on a 4-minute take, so use it for drafts only.
 4. Shortens any pause inside the take longer than --max-gap (--keep-pauses skips it), cuts the take only between
    scenes (mid-gap), keeps a short pad of each segment's own edge silence, inserts a scene gap (--gap-base plus
    --gap-before extras) capped at --max-gap, counts the kept tail pad in the tail cap, and snaps each scene's first cue
    to the first audible sample of its segment. cues.json gaps.max_audible_s is MEASURED on the finished m4a. The take is cut at the
    last script word + 0.35 s, which drops any tail the voice model made up.
 5. Peak-normalises, loudness-normalises to --lufs with ffmpeg and encodes AAC.
Writes into --out: narration.wav, narration.m4a, take-tempo.wav, cues.json, captions.srt, check.json.
cues.json: {duration, tempo, raw_speech_wpm, speech_wpm, overall_wpm, words, scenes[{n,title,start}],
chunks[{id,scene,start,end,show}], captions[{start,end,text}], gaps}.
Needs numpy, soundfile and ffmpeg; whisper (mlx-whisper) to time the sped take (and the raw take when no --words-json is given).
"""
import argparse
import json
import os
import subprocess
import sys

try:
    import numpy as np
    import soundfile as sf
except ImportError:      # --help must work without them
    np = sf = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_lib as nl  # noqa: E402
import dead_air  # noqa: E402

SR = 24000


def trim_edges(y, thr=0.01, pre=2400, post=4800):
    """Trim leading and trailing silence of the raw take. -> (trimmed, lead_samples)"""
    nz = np.where(np.abs(y) > thr)[0]
    if not len(nz):
        raise SystemExit("the take is silent")
    a = max(0, nz[0] - pre)
    return y[a: nz[-1] + post], a


def load_take(path):
    """Read the raw take as mono float32 at SR (24 kHz). A file at any other rate (a cloud narrator, a supplied wav)
    is resampled with ffmpeg: reading it as if it were 24 kHz would shift the pitch and the pace."""
    y, rate = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if rate != SR:
        print(f"take is {rate} Hz: resampling to {SR} Hz")
        p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(rate), "-ac", "1", "-i", "-",
                            "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                           input=np.ascontiguousarray(y, dtype=np.float32).tobytes(), capture_output=True, check=True)
        y = np.frombuffer(p.stdout, dtype=np.float32).copy()
    return y


def silent_runs(y, thr=0.012):
    """[(start, end)] sample runs where |y| < thr."""
    quiet = np.abs(y) < thr
    d = np.diff(np.concatenate(([0], quiet.astype(np.int8), [0])))
    return list(zip(np.where(d == 1)[0].tolist(), np.where(d == -1)[0].tolist()))


def squeeze_silences(y, keep):
    """Shorten every silence inside the audio that is longer than `keep` seconds. -> (audio, removals[(time, seconds)])"""
    cuts = nl.squeeze_plan(silent_runs(y), SR, keep, len(y))
    if not cuts:
        return y, []
    out, pos = [], 0
    for a, n in cuts:
        out.append(y[pos:a])
        pos = a + n
    out.append(y[pos:])
    return np.concatenate(out), nl.removals_seconds(cuts, SR)


def atempo(y, t, sr=SR):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-filter:a", nl.atempo_filter(t), "-f", "f32le", "-ar", str(sr), "-ac", "1", "-"],
                       input=y.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--take", required=True, help="raw one-take wav (mono)")
    ap.add_argument("--narration", required=True, help="narration.json from make_narration.py")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--wpm", type=float, default=200.0, help="target SPEAKING pace in words per minute (default 200; set by ear)")
    ap.add_argument("--tempo", type=float, help="use this tempo instead of deriving it from --wpm")
    ap.add_argument("--words-json", help="whisper word times of the untrimmed take; skips the first transcription")
    ap.add_argument("--scale-words", action="store_true", help="draft mode: scale the raw take's word times by the tempo instead of transcribing the sped take (less accurate)")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    ap.add_argument("--gap-base", type=float, default=0.45, help="silence between scenes (s)")
    ap.add_argument("--gap-before", default="", help="extra silence before scene N, e.g. 6=0.35,13=0.4")
    ap.add_argument("--head", type=float, default=0.8, help="silence before the first word (s)")
    ap.add_argument("--tail", type=float, default=0.8, help="silence after the last word (s); the old 2.6 s default was dead air; the kept tail pad (up to 0.35 s) counts toward --max-gap, so a --tail above max-gap minus 0.35 is capped")
    ap.add_argument("--max-gap", type=float, default=1.2, help="cap on any audible gap (s)")
    ap.add_argument("--pad", type=float, default=0.12, help="edge silence each scene segment keeps (s)")
    ap.add_argument("--keep-pauses", action="store_true", help="do not shorten pauses inside a scene (by default any silence in the take longer than --max-gap is cut to --max-gap, so the cap holds everywhere)")
    ap.add_argument("--lufs", type=float, default=-16.0, help="integrated loudness target")
    ap.add_argument("--caption-width", type=int, default=70)
    a = ap.parse_args(argv)
    if np is None:
        raise SystemExit("needs numpy and soundfile: uv pip install numpy soundfile")

    os.makedirs(a.out, exist_ok=True)
    scenes = nl.load_json(a.narration)
    chunks, ref = nl.flatten(scenes)
    n_words = len(ref)
    sns = []
    for sn, _ in chunks:
        if sn not in sns:
            sns.append(sn)
    raw = load_take(a.take)
    raw_t, lead = trim_edges(raw)
    lead_s = lead / SR

    # 1. words of the raw take
    if a.words_json:
        W0 = nl.words_from_json(a.words_json)
        W0 = [(w, s - lead_s, e - lead_s) for w, s, e in W0 if e - lead_s > 0]
    else:
        tmp = os.path.join(a.out, "_tmp.wav")
        sf.write(tmp, raw_t, SR)
        W0 = nl.transcribe_words(tmp, a.model)
        os.remove(tmp)
    # 2. pace and tempo
    t0_of, _ = nl.align(ref, nl.hyp_words(W0))
    raw_sp = nl.speech_wpm(n_words, nl.scene_spans(chunks, nl.chunk_spans(ref, t0_of)).values())
    tempo = a.tempo if a.tempo else nl.tempo_for(raw_sp, a.wpm)
    print(f"raw speaking wpm {raw_sp:.1f} -> uniform tempo {tempo:.4f}" + (" (given)" if a.tempo else ""))
    note = nl.tempo_note(tempo)
    if note:
        print("NOTE", note)
    y = atempo(raw_t, tempo)
    removals = []
    if not a.keep_pauses:
        y, removals = squeeze_silences(y, a.max_gap)
        if removals:
            print(f"shortened {len(removals)} pause(s) inside the take to {a.max_gap} s: " +
                  ", ".join(f"{t:.1f}s (-{r:.2f})" for t, r in removals))
    sf.write(os.path.join(a.out, "take-tempo.wav"), y, SR)
    # 3. alignment on the sped take
    if not a.scale_words:
        tmp = os.path.join(a.out, "_tmp.wav")
        sf.write(tmp, y, SR)
        W = nl.transcribe_words(tmp, a.model)
        os.remove(tmp)
    else:
        W = [(w, nl.map_time(s0, removals), nl.map_time(e0, removals)) for w, s0, e0 in nl.scale_words(W0, 0.0, tempo)]
    hyp = nl.hyp_words(W)
    t_of, matched = nl.align(ref, hyp)
    cs = nl.chunk_spans(ref, t_of)
    rates = nl.match_rates(ref, matched, len(chunks))
    sspan = nl.scene_spans(chunks, cs)

    scene_first, scene_last = {}, {}
    for ci, (sn, _) in enumerate(chunks):
        scene_first.setdefault(sn, ci)
        scene_last[sn] = ci
    # 4. cut between scenes, place with gaps
    cuts = nl.cut_points(sns, sspan, len(y) / SR)
    plan = nl.plan_gaps(sns, base=a.gap_base, before=nl.parse_gap_before(a.gap_before), head=a.head, tail=a.tail,
                        max_gap=a.max_gap, pad=a.pad)
    segs, a0s, onset = [], [], {}
    for k in range(len(sns)):
        seg = y[int(cuts[k] * SR): int(cuts[k + 1] * SR)]
        nz = np.where(np.abs(seg) > 0.012)[0]
        if len(nz):
            lo = max(0, nz[0] - int(a.pad * SR))
            hi = min(len(seg), nz[-1] + int(a.pad * SR))
        else:
            lo, hi = 0, len(seg)
        segs.append(seg[lo:hi])
        a0s.append(lo / SR)
        onset[sns[k]] = (nz[0] - lo) / SR if len(nz) else None     # first audible sample, relative to the kept segment
    gaps_after = [plan["after"][s] for s in sns[:-1]] + [plan["tail"]]
    starts, total = nl.place_segments([len(s) / SR for s in segs], plan["head"], gaps_after)
    pieces = [np.zeros(int(plan["head"] * SR), np.float32)]
    shift = {}
    for k, sn in enumerate(sns):
        shift[sn] = starts[k] - (cuts[k] + a0s[k])
        pieces.append(segs[k])
        pieces.append(np.zeros(int(gaps_after[k] * SR), np.float32))
    yy = np.concatenate(pieces)
    peak = float(np.max(np.abs(yy)))
    yy = yy * (0.89 / peak)
    wav = os.path.join(a.out, "narration.wav")
    m4a = os.path.join(a.out, "narration.m4a")
    sf.write(wav, yy, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11",
                    "-c:a", "aac", "-b:a", "128k", m4a], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", m4a]))

    # 5. cue sheet
    scene_first, scene_last = {}, {}
    for ci, (sn, _) in enumerate(chunks):
        scene_first.setdefault(sn, ci)
        scene_last[sn] = ci
    seg_start = {sn: starts[k] for k, sn in enumerate(sns)}
    cue_chunks, snapped = [], {}
    for ci, (sn, c) in enumerate(chunks):
        st = cs[ci][0] + shift[sn]
        if ci == scene_first[sn] and onset[sn] is not None:
            # whisper word starts can lead or lag the real sound; scene openings are what animation hangs on, so use
            # the first audible sample of the segment when it is close to the aligned time
            real = seg_start[sn] + onset[sn]
            if abs(real - st) <= 0.6:
                snapped[sn] = round(real - st, 3)
                st = real
        cue_chunks.append({"id": c["id"], "scene": sn, "start": round(st, 3),
                           "end": round(max(cs[ci][1] + shift[sn], st + 0.05), 3), "show": c["show"]})
    title_of = {s["scene"]: s["title"] for s in scenes}
    cue_scenes = [{"n": sn, "title": title_of[sn],
                   "start": round(cue_chunks[scene_first[sn]]["start"] - (min(0.35, a.gap_base / 2) if sn != sns[0] else plan["head"]), 3)}
                  for sn in sns]
    cue_scenes[0]["start"] = 0.0
    measured_gap = nl.audible_gaps(dead_air.silences(m4a, 0.25))     # from the finished file, not predicted
    caps = nl.caption_track(cue_chunks, a.caption_width)
    spans_out = [(cue_chunks[scene_first[sn]]["start"], cue_chunks[scene_last[sn]]["end"]) for sn in sns]
    cues = {"duration": round(dur, 3), "tempo": round(tempo, 4), "raw_speech_wpm": round(raw_sp, 1),
            "speech_wpm": round(nl.speech_wpm(n_words, spans_out), 1), "overall_wpm": round(nl.overall_wpm(n_words, dur), 1),
            "words": n_words, "scenes": cue_scenes, "chunks": cue_chunks, "captions": caps,
            "gaps": {"max_audible_s": round(measured_gap, 3), "predicted_scene_gap_max_s": round(plan["audible_max"], 3),
                     "capped": plan["capped"], "pauses_shortened": [[round(t, 2), round(r, 2)] for t, r in removals],
                     "scene_onset_snap_s": snapped, "max_gap_s": a.max_gap}}
    with open(os.path.join(a.out, "cues.json"), "w") as f:
        json.dump(cues, f, indent=1)
    with open(os.path.join(a.out, "captions.srt"), "w") as f:
        f.write(nl.to_srt(caps))
    check = {c["id"]: {"match": round(rates[i], 2), "start": round(cs[i][0], 2), "end": round(cs[i][1], 2)}
             for i, (_, c) in enumerate(chunks)}
    with open(os.path.join(a.out, "check.json"), "w") as f:
        json.dump({"chunks": check, "whisper": " ".join(w for w, _, _ in W)}, f, indent=1)
    print(f"tempo {tempo:.3f}  duration {dur:.2f} s  speech {cues['speech_wpm']} wpm  overall {cues['overall_wpm']} wpm  words {n_words}")
    if measured_gap > a.max_gap + 0.05:
        print(f"WARNING longest silence in the finished audio is {measured_gap:.2f} s, over --max-gap {a.max_gap}")
    if plan["capped"]:
        print("gap capped at", a.max_gap, "s before/after:", plan["capped"])
    for k, v in check.items():
        if v["match"] < 0.9:
            print("LOW MATCH", k, v)
    for s in cue_scenes:
        print("scene", s["n"], s["start"], s["title"])


if __name__ == "__main__":
    main()
