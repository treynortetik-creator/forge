"""Pure helpers shared by make_narration.py, audio_build.py, take_check.py and sync_check.py.

Nothing here needs a model, a GPU or ffmpeg, so every function can be unit-tested (scripts/test_narration_lib.py).

Data shapes
  narration.json  [{"scene": 1, "title": "...", "chunks": [{"id": "s1a", "show": "caption text", "say": "spoken text"}]}]
                  `show` is what the viewer reads (captions). `say` is what the voice reads; it is only present when
                  it differs from `show` (respellings such as "AI" -> "A I", numbers and times as words).
  say map JSON    {"replace": [["Acme", "Ack-me"], ["3:22", "three twenty-two"]],
                   "regex": [["\\bAIs\\b", "A Is"], ["\\bAI\\b", "A I"]], "drop": ["\"", "“", "”"]}
                  Applied in that order: literal replaces, regex replaces, then the characters in `drop` are removed.
"""
import difflib
import json
import math
import re

# --------------------------------------------------------------------------------------------- script parsing

SCENE_RE = re.compile(r"^##\s+(?:Scene\s+)?(\d+)[.:)]?\s*(.*?)\s*$", re.M | re.I)
ANY_H2_RE = re.compile(r"^##[ \t]+\S.*$", re.M)
NARR_MARK_RE = re.compile(r"^\*\*Narration(?:\s*\([^)]*\))?\s*:?\*\*:?[ \t]*\n?", re.M | re.I)
# a label ends the narration only when it carries a colon: **On screen:** or **On screen**:  (a bold word is not a label)
LABEL_RE = re.compile(r"^\*\*[A-Za-z][^*\n]*:\*\*|^\*\*[A-Za-z][^*\n]*\*\*:", re.M)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def strip_inline_markdown(text):
    """Remove markup the voice and the captions must never see: HTML comments, links (keep the text), bold, italics, code."""
    t = COMMENT_RE.sub(" ", text)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t, flags=re.S)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t, flags=re.S)
    t = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", t, flags=re.S)
    return t


def parse_script(md, plain=False):
    """Script markdown -> [(scene_number, title, narration_text)].

    Contract: `## Scene N. Title` (or `## N Title`), then a `**Narration (N words):**` block, then optional other
    bold-labelled blocks such as `**On screen:**`. The narration block runs to the next label WITH A COLON, a `---`
    rule or the next heading (a bold word inside a sentence does not end it). With plain=True there is no label: the
    scene's whole body is narration. Scenes without a narration block are skipped.
    ValueError (never a silent loss) for: an unnumbered `## ` heading that holds narration, and two scenes with the
    same number. HTML comments, links, bold, italics and code are stripped from the narration."""
    md = COMMENT_RE.sub("", md)
    heads = list(ANY_H2_RE.finditer(md))
    out, seen = [], set()
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        body = md[m.end():end]
        body = re.split(r"^\s*---+\s*$", body, maxsplit=1, flags=re.M)[0]
        sm = SCENE_RE.match(m.group(0))
        if not sm:
            if NARR_MARK_RE.search(body) or (plain and body.strip()):
                raise ValueError(f"heading {m.group(0).strip()!r} has narration but no scene number: write '## Scene N. Title'")
            continue
        n = int(sm.group(1))
        title = re.sub(r"\s*\(.*?\)\s*$", "", sm.group(2)).strip() or f"Scene {n}"
        if plain:
            text = body
        else:
            nm = NARR_MARK_RE.search(body)
            if not nm:
                continue
            rest = body[nm.end():]
            lab = LABEL_RE.search(rest)
            text = rest[:lab.start()] if lab else rest
        text = " ".join(p.strip() for p in re.split(r"\n\s*\n", text) if p.strip())
        text = re.sub(r"\s+", " ", strip_inline_markdown(text)).strip()
        if text:
            if n in seen:
                raise ValueError(f"scene number {n} appears twice: chunk ids would collide")
            seen.add(n)
            out.append((n, title, text))
    return out


def split_sentences(text):
    """One chunk per sentence. Splits after . ? ! (and any closing quote or bracket that belongs to the sentence) when
    the next sentence starts with a capital, digit, quote or bracket."""
    nxt = r"(?=[A-Z0-9\"“‘(])"
    pat = r"(?<=[.?!][\"')”’][\"')”’])\s+" + nxt + r"|(?<=[.?!][\"')”’])\s+" + nxt + r"|(?<=[.?!])\s+" + nxt
    return [s for s in re.split(pat, text.strip()) if s.strip()]


def chunk_id(scene, i):
    letters = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        letters = chr(97 + r) + letters
    return f"s{scene}{letters}"


def empty_say_map():
    return {"replace": [], "regex": [], "drop": ["\"", "“", "”"]}


def apply_say_map(text, say_map):
    """The spoken form of `text`. Quotes are typographic-normalised so the voice never reads a quote mark."""
    s = text
    for a, b in say_map.get("replace", []):
        s = s.replace(a, b)
    for pat, rep in say_map.get("regex", []):
        s = re.sub(pat, rep, s)
    s = s.replace("’", "'").replace("‘", "'")
    for ch in say_map.get("drop", []):
        s = s.replace(ch, "")
    return re.sub(r"\s+", " ", s).strip()


def build_narration(scenes, say_map=None):
    """[(n, title, text)] -> narration.json structure. `say` is set only when it differs from `show`."""
    say_map = say_map or empty_say_map()
    out, seen = [], set()
    for n, title, text in scenes:
        if n in seen:
            raise ValueError(f"scene number {n} appears twice")
        seen.add(n)
        chunks = []
        for i, sent in enumerate(split_sentences(text)):
            c = {"id": chunk_id(n, i), "show": sent}
            sp = apply_say_map(sent, say_map)
            if not words(sp):
                raise ValueError(f"chunk {c['id']} has no speakable word: {sent!r} (remove it or write words)")
            if sp != sent:
                c["say"] = sp
            chunks.append(c)
        out.append({"scene": n, "title": title, "chunks": chunks})
    return out


def say_text(chunk):
    """What the voice reads for one chunk."""
    return chunk.get("say", chunk["show"]).replace("’", "'").replace("“", "").replace("”", "").replace('"', "")


def spoken_text(scenes):
    """The whole script as one string for a one-take render: a scene is its chunks joined by spaces, scenes by blank lines."""
    return "\n\n".join(" ".join(say_text(c) for c in s["chunks"]) for s in scenes)


# --------------------------------------------------------------------------------------------- words, alignment

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words(text):
    return [norm(w) for w in re.split(r"[\s\-]+", text) if norm(w)]


def flatten(scenes):
    """-> (chunks, ref) where chunks = [(scene, chunk)] and ref = [(chunk_index, word)] in script order."""
    chunks = [(s["scene"], c) for s in scenes for c in s["chunks"]]
    for _, c in chunks:
        if not words(say_text(c)):
            raise ValueError(f"chunk {c['id']} has no speakable word")
    ref = [(i, w) for i, (_, c) in enumerate(chunks) for w in words(say_text(c))]
    return chunks, ref


def hyp_words(whisper_words):
    """[(text, start, end)] from whisper -> normalised [(word, start, end)] (a whisper token may hold a hyphen)."""
    return [(p, s, e) for w, s, e in whisper_words for p in words(w)]


def align(ref, hyp):
    """Align script words to heard words with difflib. -> (t_of, matched)
    t_of[k] = (start, end) of script word k; unmatched words are interpolated between the nearest matched
    neighbours (or pinned to the first/last match at the edges). matched = set of script-word indexes heard exactly."""
    sm = difflib.SequenceMatcher(None, [w for _, w in ref], [w for w, _, _ in hyp], autojunk=False)
    t_of = [None] * len(ref)
    matched = set()
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            t_of[blk.a + k] = (float(hyp[blk.b + k][1]), float(hyp[blk.b + k][2]))
            matched.add(blk.a + k)
    known = [i for i, t in enumerate(t_of) if t]
    if not known:
        raise ValueError("no script word was heard: wrong take, wrong script, or a silent file")
    for i in range(len(t_of)):
        if t_of[i] is None:
            lo = max((k for k in known if k < i), default=None)
            hi = min((k for k in known if k > i), default=None)
            if lo is None:
                t_of[i] = (t_of[hi][0], t_of[hi][0])
            elif hi is None:
                t_of[i] = (t_of[lo][1], t_of[lo][1])
            else:
                f = (i - lo) / (hi - lo)
                t = t_of[lo][1] + f * (t_of[hi][0] - t_of[lo][1])
                t_of[i] = (t, t)
    return t_of, matched


def chunk_spans(ref, t_of):
    """-> {chunk_index: [start, end]} from the aligned word times."""
    cs = {}
    for (ci, _), t in zip(ref, t_of):
        cs.setdefault(ci, [t[0], t[1]])
        cs[ci][1] = t[1]
    return cs


def match_rates(ref, matched, n_chunks):
    rate = {}
    for ci in range(n_chunks):
        idx = [k for k, (c, _) in enumerate(ref) if c == ci]
        rate[ci] = (sum(1 for k in idx if k in matched) / len(idx)) if idx else 1.0
    return rate


def scene_spans(chunks, cs):
    """-> {scene: [start, end]} over the chunks' aligned spans."""
    sp = {}
    for ci, (sn, _) in enumerate(chunks):
        a, b = cs[ci]
        sp.setdefault(sn, [a, b])
        sp[sn][0] = min(sp[sn][0], a)
        sp[sn][1] = max(sp[sn][1], b)
    return sp


# --------------------------------------------------------------------------------------------- pace and tempo

def speech_wpm(n_words, spans):
    """Speaking pace: words divided by the summed per-scene speech spans. Pauses between scenes are not counted.
    spans = iterable of (start, end) seconds."""
    total = sum(e - s for s, e in spans)
    return n_words / (total / 60.0) if total > 0 else 0.0


def overall_wpm(n_words, duration):
    return n_words / (duration / 60.0)


def tempo_for(raw_speech_wpm, target_wpm):
    """The ONE uniform tempo that moves the take from its measured speaking pace to the target.
    > 1 speeds the take up, < 1 slows it down. The owner decides the target by ear; this only does the arithmetic."""
    if raw_speech_wpm <= 0 or target_wpm <= 0:
        raise ValueError("wpm must be positive")
    return target_wpm / raw_speech_wpm


def atempo_filter(t):
    """ffmpeg filter string for a pitch-preserving tempo. One atempo handles 0.5-100; below that chain by halves."""
    if t <= 0:
        raise ValueError("tempo must be positive")
    parts = []
    while t < 0.5:
        parts.append("atempo=0.5")
        t /= 0.5
    parts.append(f"atempo={t:.4f}")
    return ",".join(parts)


def tempo_note(t, lo=0.8, hi=1.25):
    """A warning string when a tempo is outside the range that sounds natural, else ''."""
    if t < lo:
        return f"tempo {t:.3f} slows the take a lot (below {lo}); it may sound drawn out, check by ear"
    if t > hi:
        return f"tempo {t:.3f} speeds the take a lot (above {hi}); it may sound hurried, check by ear"
    return ""


# --------------------------------------------------------------------------------------------- gaps

def plan_gaps(scene_ids, base=0.45, before=None, head=0.8, tail=0.8, max_gap=1.2, pad=0.12, last_pad=0.35):
    """Silence to insert between scenes.

    scene_ids: scene numbers in order. before: {scene: extra seconds before that scene}, for example a longer
    beat before the scene that shows the big picture. max_gap caps the AUDIBLE gap, which is the inserted silence
    plus the two edge pads (pad) each scene keeps. Returns
        {"head": s, "tail": s, "after": {scene: inserted_silence}, "capped": [scene or "tail" or "head", ...],
         "audible_max": largest audible gap}
    The tail cap also counts the silence the last segment keeps after its final word (last_pad, the cut_points value),
    so the AUDIBLE tail is tail + last_pad at most max_gap. Head: the first segment keeps pad of its own silence.
    Only silence the script inserts is planned here; a pause INSIDE a scene is shortened by squeeze_silences().
    Inserted silence is never negative, so a cap below 2*pad gives butt-joined scenes."""
    before = {int(k): float(v) for k, v in (before or {}).items()}
    room = max(0.0, max_gap - 2 * pad)
    after, capped = {}, []
    for a, b in zip(scene_ids, scene_ids[1:]):
        want = base + before.get(b, 0.0)
        got = min(want, room)
        if got < want - 1e-9:
            capped.append(a)
        after[a] = got
    t_got, h_got = max(0.0, min(tail, max_gap - last_pad)), min(head, room + pad)
    if t_got < tail - 1e-9:
        capped.append("tail")
    if h_got < head - 1e-9:
        capped.append("head")
    audible = [v + 2 * pad for v in after.values()] + [t_got + last_pad, h_got + pad]
    return {"head": h_got, "tail": t_got, "after": after, "capped": capped, "audible_max": max(audible) if audible else 0.0}


def squeeze_plan(runs, sr, keep, total_len):
    """Which silences to shorten. runs = (start_sample, end_sample) silent runs; keep = longest silence to leave (s).
    The first run (it starts at sample 0) and the last (it ends at total_len) are edge silence and are left alone.
    -> [(cut_start_sample, cut_len_samples)] and the same as [(time, removed_seconds)] via removals_seconds()."""
    cuts = []
    k = int(round(keep * sr))
    for a, b in runs:
        if a == 0 or b >= total_len:
            continue
        if b - a > k:
            # keep k samples: half before and half after the removed middle
            cuts.append((a + k // 2, (b - a) - k))
    return cuts


def removals_seconds(cuts, sr):
    return [(a / sr, n / sr) for a, n in cuts]


def map_time(t, removals):
    """Map a time in the audio BEFORE the cuts to the audio after them. removals = [(time, removed_seconds)] sorted."""
    shift = 0.0
    for at, rm in removals:
        if t >= at + rm:
            shift += rm
        elif t > at:
            shift += t - at
    return t - shift


def audible_gaps(sil):
    """From ffmpeg silencedetect pairs [(start, duration)] -> the longest silence anywhere in the finished audio."""
    return max((d for _, d in sil), default=0.0)


def cut_points(scene_ids, scene_span_map, total_len, last_pad=0.35):
    """Where to cut the sped take: mid-gap between scenes, and `last_pad` after the last script word (which drops any
    tail the voice model made up). Returns len(scene_ids)+1 times."""
    cuts = [0.0]
    for sn, nxt in zip(scene_ids, scene_ids[1:]):
        e, s = scene_span_map[sn][1], scene_span_map[nxt][0]
        cuts.append((e + s) / 2 if s > e else e)
    cuts.append(min(total_len, scene_span_map[scene_ids[-1]][1] + last_pad))
    return cuts


# --------------------------------------------------------------------------------------------- captions

def caption_pieces(text, width=70):
    """Split one chunk's caption text into pieces of at most `width` characters: at clause marks first, then balanced
    word wraps. ONE implementation, so the SRT, the page and the proof all agree."""
    pieces = []
    for part in re.split(r"(?<=[.,:?!])\s+", text):
        if pieces and len(pieces[-1]) + 1 + len(part) <= width:
            pieces[-1] += " " + part
            continue
        k = -(-len(part) // width)
        if k > 1:
            tgt, cur = len(part) / k, ""
            for x in part.split(" "):
                if cur and len(cur) + 1 + len(x) > tgt + 8:
                    pieces.append(cur)
                    cur = x
                else:
                    cur = (cur + " " + x).strip()
            pieces.append(cur)
        else:
            pieces.append(part)
    return pieces


def caption_track(chunks, width=70):
    """chunks: [{"start","end","show"}] -> [{"start","end","text"}] timed by character share inside each chunk."""
    caps = []
    for c in chunks:
        ps = caption_pieces(c["show"], width)
        total = sum(len(p) for p in ps) or 1
        t0 = c["start"]
        for p in ps:
            d = (c["end"] - c["start"]) * len(p) / total
            caps.append({"start": round(t0, 3), "end": round(t0 + d, 3), "text": p})
            t0 += d
    return caps


def srt_time(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def to_srt(caps):
    return "".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n" for i, c in enumerate(caps, 1))


# --------------------------------------------------------------------------------------------- checks

def diff_script_vs_heard(ref_words, hyp):
    """Word-level diff of the script against what whisper heard. -> (ratio, [(op, script_words, heard_words, at_seconds)])
    A replace whose letters are the same once spaces are removed ("q r" heard as "qr", "web site" as "website") is a
    tokenisation difference, not a misread: it counts as matched and is not listed."""
    heard = [h[0] for h in hyp]
    sm = difflib.SequenceMatcher(None, ref_words, heard, autojunk=False)
    bad, m_ref, m_heard = [], 0, 0
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            m_ref += a1 - a0
            m_heard += a1 - a0
            continue
        if op == "replace" and "".join(ref_words[a0:a1]) == "".join(heard[b0:b1]):
            m_ref += a1 - a0
            m_heard += b1 - b0
            continue
        at = hyp[min(b0, len(hyp) - 1)][1] if hyp else 0.0
        bad.append((op, " ".join(ref_words[a0:a1]), " ".join(heard[b0:b1]), round(at, 1)))
    total = len(ref_words) + len(heard)
    return ((m_ref + m_heard) / total if total else 1.0), bad


def long_gaps(whisper_words, limit=1.0):
    """[(end_of_previous_word, gap_seconds)] for silences longer than `limit` inside a take."""
    return [(round(a[2], 2), round(b[1] - a[2], 2)) for a, b in zip(whisper_words, whisper_words[1:]) if b[1] - a[2] > limit]


def sync_offsets(cue_chunks, ref_by_chunk, hit_times):
    """Compare each chunk's cue with where its first and last script word were actually heard in the final audio.
    ref_by_chunk: {chunk_id: [global word indexes]}; hit_times: {global word index: (start, end)}.
    -> list of dicts with start_off and end_off (heard minus cue, seconds). Chunks with no word heard are skipped."""
    out = []
    for c in cue_chunks:
        idx = ref_by_chunk.get(c["id"], [])
        f = next((hit_times[i] for i in idx if i in hit_times), None)
        l = next((hit_times[i] for i in reversed(idx) if i in hit_times), None)
        if not f:
            continue
        out.append({"id": c["id"], "cue": c["start"], "heard": round(f[0], 3),
                    "start_off": round(f[0] - c["start"], 3), "end_off": round(l[1] - c["end"], 3)})
    return out


def sync_summary(offs, over=0.15, exclude=()):
    """Mean, median and worst start offset. Chunks in `exclude` (the file's first word: whisper's timestamp for it
    is unreliable) are listed in the detail but left out of the mean, median and worst."""
    import statistics
    use = [o for o in offs if o["id"] not in set(exclude)] or offs
    a = [abs(o["start_off"]) for o in use]
    worst = max(use, key=lambda o: abs(o["start_off"]))
    return {"chunks": len(use), "excluded": [o["id"] for o in offs if o["id"] in set(exclude)],
            "mean_abs_start_offset_s": round(statistics.mean(a), 3),
            "median_abs_s": round(statistics.median(a), 3), "worst": worst,
            "over_150ms": [o["id"] for o in use if abs(o["start_off"]) > over]}


def onset_offsets(scene_cues, onsets, window=0.8):
    """Scene-opening cues against measured speech onsets (silence_end times of the final audio, not whisper).
    scene_cues = [(scene, cue_start)]. -> [{"scene", "cue", "onset", "off"}] with off = onset - cue, using the nearest
    onset within `window` seconds; scenes with none are skipped."""
    out = []
    for sn, c in scene_cues:
        near = [o for o in onsets if abs(o - c) <= window]
        if near:
            o = min(near, key=lambda x: abs(x - c))
            out.append({"scene": sn, "cue": round(c, 3), "onset": round(o, 3), "off": round(o - c, 3)})
    return out


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def transcribe_words(path, model="mlx-community/whisper-large-v3-turbo", language="en"):
    """whisper word timestamps for an audio file -> [(word, start, end)]. Lazy import: Apple Silicon, mlx-whisper."""
    try:
        import mlx_whisper
    except ImportError:
        raise SystemExit("needs the mlx-whisper package: uv pip install mlx-whisper (Apple Silicon). "
                         "Or pass --words-json with word timestamps from any other tool.")
    r = mlx_whisper.transcribe(path, path_or_hf_repo=model, word_timestamps=True, language=language)
    return [(w["word"].strip(), w["start"], w["end"]) for s in r["segments"] for w in s["words"]]


def words_from_json(path):
    """Accepts {"words": [[w, s, e], ...]} (take_check output) or a bare list."""
    d = load_json(path)
    d = d["words"] if isinstance(d, dict) else d
    return [(w[0], w[1], w[2]) for w in d]


# --------------------------------------------------------------------------------------------- layout and args

def parse_gap_before(spec):
    """'6=0.35,13=0.4' -> {6: 0.35, 13: 0.4}. Extra silence before that scene, on top of the base gap."""
    out = {}
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition("=")
        out[int(k)] = float(v)
    return out


def scale_words(words_in, lead, tempo):
    """Move whisper word times from the raw take to the sped take without a second transcription.
    lead = seconds trimmed off the start of the raw take; tempo > 1 shortens. atempo is linear, so t' = (t - lead) / tempo.
    Words that end before the trim point are dropped."""
    out = []
    for w, s, e in words_in:
        if e - lead <= 0:
            continue
        out.append((w, max(0.0, (s - lead) / tempo), max(0.0, (e - lead) / tempo)))
    return out


def place_segments(lens, head, gaps_after):
    """Lay trimmed scene segments end to end on the output timeline.
    lens = seconds of each segment, gaps_after = silence after each segment (the last one is the tail).
    -> (out_starts, total_seconds)"""
    t, out = head, []
    for ln, g in zip(lens, gaps_after):
        out.append(t)
        t += ln + g
    return out, t
