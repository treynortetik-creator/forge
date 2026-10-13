#!/usr/bin/env python3
"""
lyric_meter.py - measure a lyric sheet so the model does not have to guess.

WHY THIS EXISTS
---------------
Syllable counts, rhyme classes and "did the title land in the chorus" are numbers and
lookups. Models miscount syllables and misjudge rhymes with total confidence, so this
script computes them. Whether a line is *good* is not computed here; that stays with the
model (and the human).

WHAT IT MEASURES (per file)
  * per line: syllable count + stress pattern (CMU dict via `pronouncing`; words the dict
    does not know fall back to a vowel-group heuristic and are marked `~`)
  * per section: line count, word count
  * syllable RANGES: words with more than one CMU pronunciation (fire 1-2, every 2-3,
    hour 1-2) make the line a range ("13-14") and are listed after the line with `≈`
  * repeated sections (verse 1 vs verse 2, chorus vs chorus...): line-by-line syllable
    difference, flagging pairs that miss by more than --tolerance (default 2) even at the
    closest pronunciation; plus a BEAT MATCH: the share of stressed/unstressed slots that
    agree (best of start- or end-aligned), flagged under --stress-min (default 0.6) when
    the syllable counts already fit. Same count, different beats = fights the melody.
  * end-rhyme scheme per section, each link classed perfect / slant / repeat
      perfect = identical CMU rhyming part     (night / white)
      slant   = same final stressed vowel only (night / mind)
      repeat  = literally the same end word
  * repeated end-words (within a section, and song-wide across unique lines)
  * title-in-chorus check (--title)
  * verse-to-chorus echo (last 2 lines of a section vs first 2 of the chorus it feeds)
  * cliche / AI-tell scan from data/cliches.txt (--cliches to swap the list)
  * optional GENRE CHECK (--genre emo-pop-punk): loads data/genres/<name>.json and reports
    PASS / WARN per measurable genre norm (word count, repeat share, chorus shape, perfect-rhyme
    share, long verse lines, "you" count, title, receipts proxy, line-length swing, genre word
    lists). Norms, not laws: WARN, never FAIL, and WARNs do not affect --strict.

RUN IT (pronouncing is the only dependency; uv fetches it on the fly)
    uv run --with pronouncing python lyric_meter.py song.txt --title "My Title"
    uv run --with pronouncing python lyric_meter.py song.txt --json
    uv run --with pronouncing python lyric_meter.py song.txt --max-lines verse=6,chorus=4 --words 150-250

INPUT
    Plain text. `[Section]` lines open a section. Known section words (verse, chorus,
    pre-chorus, bridge, intro, outro, hook, refrain, breakdown, interlude, post-chorus,
    instrumental, solo...) are sections; any other bracketed line (`[Whispered]`) is
    treated as a performance cue and ignored. Text in (parentheses) is treated as backing
    vocals and left out of the meter/rhyme measurement.

KNOWN LIMITS (read before trusting a number)
  * CMU gives one stress pattern per word. Single-syllable function words (the, a, and,
    to...) are shown unstressed because a singer reduces them; everything else is as the
    dictionary has it. Stress patterns are a dictionary view of speech, not of a melody.
  * Syllable counts are speech counts. A singer can stretch or elide.
  * `~` marks a heuristic count. Names, invented spellings and phonetic respellings
    ("Rah-mohs") land here. Treat those lines' counts as +/-1.
  * Slant-rhyme detection is vowel-based; consonance-only slant (blank/think) is not caught.
Exit code: 0 normally; with --strict, 1 if any flag was raised.
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

try:
    import pronouncing
except ImportError:  # pragma: no cover
    sys.exit("lyric_meter.py needs the `pronouncing` package. Run it with:\n"
             "  uv run --with pronouncing python lyric_meter.py <file>")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CLICHES = os.path.join(HERE, "data", "cliches.txt")
GENRES_DIR = os.path.join(HERE, "data", "genres")

SECTION_WORDS = {
    "intro", "verse", "pre-chorus", "prechorus", "pre chorus", "chorus", "post-chorus",
    "postchorus", "post chorus", "hook", "refrain", "bridge", "outro", "breakdown",
    "interlude", "instrumental", "solo", "drop", "build", "build-up", "spoken", "end",
    "break", "middle 8", "tag", "coda", "vamp",
}
# singers reduce these; CMU marks many of them stressed
FUNCTION_WORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "at", "by", "for", "with",
    "as", "is", "was", "are", "were", "be", "been", "am", "i", "me", "my", "you", "your",
    "he", "she", "it", "we", "they", "him", "her", "us", "them", "his", "its", "our",
    "their", "that", "this", "than", "so", "if", "do", "did", "can", "will", "would",
    "could", "should", "from", "into", "up", "out", "off", "not", "no", "just", "all",
}

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")


# ---------------------------------------------------------------- syllables
def heuristic_syllables(word):
    w = word.lower().replace("'", "")
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if n > 1 and w.endswith("e") and not re.search(r"[^aeiouy]le$", w):
        n -= 1
    if n > 1 and re.search(r"(?:[^aeiouy]|^)(?:es|ed)$", w) and not re.search(
            r"(?:[sxzct]h?|[dt])(?:es|ed)$", w):
        n -= 1
    return max(n, 1)


def word_info(word):
    """-> dict(word, syl, syl_min, syl_max, stress[str of 0/1/2], oov, phones)

    syl is the count of CMU's first pronunciation. syl_min/syl_max span every pronunciation
    CMU lists (fire 1-2, every 2-3, hour 1-2), so a line can report a range instead of
    silently picking one. A singer can land either way; the range is the honest answer."""
    lw = word.lower()
    phones_list = pronouncing.phones_for_word(lw)
    if not phones_list and "'" in lw:
        phones_list = pronouncing.phones_for_word(lw.replace("'", ""))
    if phones_list:
        ph = phones_list[0]
        st = pronouncing.stresses(ph)
        if len(st) == 1 and lw in FUNCTION_WORDS:
            st = "0"
        counts = [len(pronouncing.stresses(p)) for p in phones_list]
        return {"word": lw, "syl": len(st), "syl_min": min(counts), "syl_max": max(counts),
                "stress": st, "oov": False, "phones": ph}
    n = heuristic_syllables(lw)
    st = ("1" + "0" * (n - 1)) if n > 1 else "1"
    if n == 1 and lw in FUNCTION_WORDS:
        st = "0"
    return {"word": lw, "syl": n, "syl_min": n, "syl_max": n, "stress": st, "oov": True,
            "phones": None}


def stress_match(a, b):
    """Share of beats that agree between two stress strings (0/1/2), or None if either is empty.

    Matching lines of repeated sections are sung to one melody, so their stressed syllables
    should land in the same slots. Equal syllable counts do not guarantee that: 12 and 12 can
    put the beats in different places. Compared twice, aligned from the start and from the
    end (lines are sung to the rhyme, so end alignment often matters more); the better
    alignment wins. Secondary stress (2) counts as a match either way. Single-syllable
    function words are already reduced to unstressed by word_info."""
    if not a or not b:
        return None

    def score(x, y):
        agree = sum(1 for p, q in zip(x, y) if p == q or "2" in (p, q))
        return agree / min(len(x), len(y))

    return round(max(score(a, b), score(a[::-1], b[::-1])), 2)


def stress_glyphs(stress):
    return "".join({"1": "/", "2": "\\", "0": "."}.get(c, "?") for c in stress)


def line_words(text):
    text = re.sub(r"\([^)]*\)", " ", text)           # backing vocals out
    text = text.replace("’", "'")
    return WORD_RE.findall(text)


# ---------------------------------------------------------------- parsing
def base_of(label):
    t = label.lower()
    t = re.split(r"\s+[-:|]\s+|[:|]", t)[0]
    t = re.sub(r"\d+", "", t).strip()
    t = re.sub(r"^(final|last|double|big|half|short|extended)\s+", "", t).strip()
    t = t.replace("pre chorus", "pre-chorus").replace("prechorus", "pre-chorus")
    t = t.replace("post chorus", "post-chorus").replace("postchorus", "post-chorus")
    return t


def parse(text):
    sections = []   # each: {label, base, index, lines:[{n, text}]}
    cur = None
    cues = []
    notes = []
    for no, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s:
            continue
        m = re.fullmatch(r"\[(.+?)\]", s)
        if m:
            label = m.group(1).strip()
            if base_of(label) in SECTION_WORDS:
                cur = {"label": label, "base": base_of(label), "line_no": no, "lines": []}
                sections.append(cur)
            else:
                cues.append((no, label))
            continue
        if cur is None:
            if re.match(r"^(title|style|lyrics)\s*:", s, re.I):
                continue
            cur = {"label": "(untagged)", "base": "(untagged)", "line_no": no, "lines": []}
            sections.append(cur)
            notes.append(f"line {no}: lyric text before any [Section] tag")
        cur["lines"].append({"n": no, "text": s})
    seen = Counter()
    for sec in sections:
        seen[sec["base"]] += 1
        sec["index"] = seen[sec["base"]]
    return sections, cues, notes


# ---------------------------------------------------------------- rhyme
def end_word(text):
    ws = line_words(text)
    return ws[-1].lower() if ws else None


def rhyme_keys(word):
    """(rhyming_part, final_stressed_vowel) or None if the dictionary does not know it."""
    phones_list = pronouncing.phones_for_word(word) or (
        pronouncing.phones_for_word(word.replace("'", "")) if "'" in word else [])
    if not phones_list:
        return None
    parts = []
    for ph in phones_list:
        rp = pronouncing.rhyming_part(ph)
        parts.append((rp, re.sub(r"\d", "", rp.split()[0]) if rp else ""))
    return parts   # list of alternates


def rhyme_class(w1, w2):
    if w1 == w2:
        return "repeat"
    k1, k2 = rhyme_keys(w1), rhyme_keys(w2)
    if not k1 or not k2:
        return None
    if any(a[0] == b[0] for a in k1 for b in k2):
        return "perfect"
    if any(a[1] and a[1] == b[1] for a in k1 for b in k2):
        return "slant"
    return "none"


def scheme_for(end_words):
    """Label end-rhyme groups A, B, C by first appearance.
    Pass 1 groups lines that rhyme perfectly or repeat the same end word.
    Pass 2 attaches still-unpaired lines to a group by slant rhyme (shown with *), but a
    slant link never merges two groups that already stand on their own.
    Returns (scheme_string, links) - links = [(i, j, class)]."""
    n = len(end_words)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    links, mark = [], {}
    for j in range(n):
        if not end_words[j]:
            continue
        cand = []
        for i in range(j):
            if not end_words[i]:
                continue
            c = rhyme_class(end_words[i], end_words[j])
            if c in ("perfect", "repeat"):
                cand.append((3 if c == "perfect" else 2, -(j - i), i, c))
        if cand:
            cand.sort(reverse=True)
            _, _, i, c = cand[0]
            parent[find(j)] = find(i)
            links.append((i, j, c))
            mark[j] = c
    size = Counter(find(k) for k in range(n))
    for k in range(n):
        if not end_words[k] or size[find(k)] > 1:
            continue
        near = sorted((abs(k - i), i) for i in range(n)
                      if i != k and end_words[i] and rhyme_class(end_words[i], end_words[k]) == "slant")
        if near:
            i = near[0][1]
            a, b = (i, k) if i < k else (k, i)
            links.append((a, b, "slant"))
            parent[find(k)] = find(i)
            mark[b] = "slant"
    groups = defaultdict(list)
    for k in range(n):
        groups[find(k)].append(k)
    letters, nxt, out = {}, 0, []
    for k in range(n):
        root = find(k)
        if len(groups[root]) < 2:
            out.append("x")
            continue
        if root not in letters:
            letters[root] = chr(ord("A") + nxt % 26)
            nxt += 1
        out.append(letters[root] + {"slant": "*", "repeat": "="}.get(mark.get(k), ""))
    return "".join(out), sorted(links, key=lambda t: (t[1], t[0]))


# ---------------------------------------------------------------- cliches
def load_cliches(path):
    pats = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            e = raw.split("#", 1)[0].strip().lower()
            if not e:
                continue
            body = r"\s+".join(re.escape(p) for p in e.split())
            if " " not in e:
                body += r"(?:s|es|ed|ing|d)?"
            pats.append((e, re.compile(r"(?<![A-Za-z])" + body + r"(?![A-Za-z])", re.I)))
    return pats



# ---------------------------------------------------------------- genre profile
YOU_WORDS = {"you", "your", "you're", "yours"}
NUMBER_WORDS = {
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
    "twelve", "twenty", "thirty", "forty", "fifty", "hundred", "thousand", "million",
    "midnight", "noon", "o'clock",
}
SELF_WORDS = {"i", "i'm", "i'll", "i've", "i'd"}
CHORUS_BASES = ("chorus", "hook", "refrain")


def load_genre(name):
    path = os.path.join(GENRES_DIR, f"{name}.json")
    if not os.path.isfile(path):
        have = sorted(f[:-5] for f in os.listdir(GENRES_DIR) if f.endswith(".json")) \
            if os.path.isdir(GENRES_DIR) else []
        sys.exit(f"no genre profile '{name}' at {path}. Available: {', '.join(have) or 'none'}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_sectioned_wordlist(path):
    """[section] headers, one entry per line, '#' comments -> {section: [(entry, regex)]}"""
    out, cur = {}, None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            e = raw.split("#", 1)[0].strip().lower()
            if not e:
                continue
            m = re.fullmatch(r"\[(.+)\]", e)
            if m:
                cur = m.group(1).strip()
                out[cur] = []
                continue
            if cur is None:
                continue
            body = r"\s+".join(re.escape(p) for p in e.split())
            if " " not in e:
                body += r"(?:s|es|ed|ing|d)?"
            out[cur].append((e, re.compile(r"(?<![A-Za-z])" + body + r"(?![A-Za-z])", re.I)))
    return out


def receipts_in(text):
    """Proxy for concrete detail: digits, number/time words, and capitalised words that are
    not the first word of a line or sentence (names, places, brands)."""
    t = re.sub(r"\([^)]*\)", " ", text.replace("’", "'"))
    found = set(re.findall(r"\d+(?:[:.]\d+)?", t))
    toks = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*|[.!?]", t)
    start = True
    for tok in toks:
        if tok in ".!?":
            start = True
            continue
        low = tok.lower()
        if low in NUMBER_WORDS:
            found.add(low)
        elif not start and tok[0].isupper() and tok[1:].islower() and low not in SELF_WORDS:
            found.add(tok)
        start = False
    return found


def genre_check(sections, result, args, profile):
    C = profile["checks"]
    checks = []

    def add(cid, status, value, norm, why, note=None):
        checks.append({"id": cid, "status": status, "value": value, "norm": norm,
                       "why": why, "note": note})

    rows = [r for s in sections for r in s["rows"]]
    total_lines = len(rows)
    total_words = result["total_words"]

    c = C["total_words"]
    lo, hi = c["target"]
    wlo, whi = c["warn_outside"]
    note = None
    if lo <= total_words <= hi:
        st = "PASS"
    elif wlo <= total_words <= whi:
        st, note = "PASS", f"inside the corpus range but off the {lo}-{hi} sweet spot"
    else:
        st = "WARN"
    add("total_words", st, total_words, f"{lo}-{hi} (warn outside {wlo}-{whi})", c["why"], note)

    c = C["repeated_line_share"]
    uniq = len({norm_line(r["text"]) for r in rows})
    share = (total_lines - uniq) / total_lines if total_lines else 0.0
    lo, hi = c["typical"]
    note = None
    if share < lo:
        note = "low share; if you wrote repeats as 'Chorus x2' or listed the chorus once, write them out"
    add("repeated_line_share", "PASS" if lo <= share <= hi else "WARN",
        f"{share:.0%} ({total_lines - uniq}/{total_lines} lines)", f"{lo:.0%}-{hi:.0%}",
        c["why"], note)

    choruses = [s for s in sections if s["base"] in CHORUS_BASES]
    c = C["chorus_lines"]
    lo, hi = c["range"]
    if choruses:
        n = len(choruses[0]["rows"])
        add("chorus_lines", "PASS" if lo <= n <= hi else "WARN", n, f"{lo}-{hi}", c["why"],
            "measured on the first chorus")
    else:
        add("chorus_lines", "WARN", "no chorus", f"{lo}-{hi}", c["why"])

    c = C["chorus_occurrences"]
    n = len(choruses)
    note = None
    if n < c["min"]:
        note = ("the file lists the chorus fewer than 3 times; if you write repeats elsewhere "
                "(e.g. a chorus marked 'x2'), this undercounts. Write repeats out.")
    add("chorus_occurrences", "PASS" if n >= c["min"] else "WARN", n, f">={c['min']}",
        c["why"], note)

    c = C["chorus_perfect_rhyme_share"]
    if choruses:
        links = choruses[0]["links"]
        perfect = sum(1 for l in links if l["class"] == "perfect")
        if links:
            sh = perfect / len(links)
            add("chorus_perfect_rhyme_share", "PASS" if sh <= c["max"] else "WARN",
                f"{sh:.0%} ({perfect}/{len(links)} end-rhyme pairs)", f"<={c['max']:.0%}",
                c["why"], "first chorus; repeat and slant links count as non-perfect")
        else:
            add("chorus_perfect_rhyme_share", "PASS", "no end-rhyme pairs", f"<={c['max']:.0%}",
                c["why"], "unrhymed chorus; nothing to be nursery-rhyme about")
    else:
        add("chorus_perfect_rhyme_share", "WARN", "no chorus", f"<={c['max']:.0%}", c["why"])

    c = C["verse_lines_over"]
    long_lines = [r for s in sections if s["base"] == "verse" for r in s["rows"]
                  if r["syllables"] > c["syllables"]]
    add("verse_lines_over_16", "PASS" if len(long_lines) <= c["max_count"] else "WARN",
        len(long_lines), f"<={c['max_count']} lines over {c['syllables']} syllables", c["why"],
        ("file lines " + ", ".join(str(r["n"]) for r in long_lines)) if long_lines else None)

    c = C["you_count"]
    you = sum(1 for r in rows for w in line_words(r["text"]) if w.lower() in YOU_WORDS)
    add("you_count", "PASS" if you >= c["min"] else "WARN", you,
        f">={c['min']} (median {c['median']})", c["why"], "counts repeats; backing vocals excluded")

    c = C["title_in_chorus"]
    if "title_check" in result:
        t = result["title_check"]
        ok = bool(t["in_chorus_lines"])
        add("title_in_chorus", "PASS" if ok else "WARN",
            f"chorus lines {t['in_chorus_lines']}" if ok else "not in chorus",
            "in the chorus (single) or deliberately never sung (deep cut)", c["why"],
            None if ok else "fine if the title is a deliberate never-sung side door")
    else:
        add("title_in_chorus", "N/A", "no --title given", "-", c["why"])

    c = C["receipts_proxy"]
    seen, found = set(), set()
    for r in rows:
        k = norm_line(r["text"])
        if k in seen:
            continue
        seen.add(k)
        found |= receipts_in(r["text"])
    nums = sorted(f for f in found if f[0].isdigit() or f.lower() in NUMBER_WORDS)
    names = sorted(f for f in found if f not in nums)
    add("receipts_proxy", "PASS" if found else "WARN",
        f"{len(found)} (numbers/times {nums or '-'}; capitalised names/places {names or '-'})",
        f">={c['min']}", c["why"],
        "PROXY only: capitalised words may be names, places or brands; a prop like 'a jukebox' "
        "is not counted. You judge the real receipts.")

    c = C["line_length_swing"]
    syls = [r["syllables"] for r in rows]
    sd = statistics.pstdev(syls) if len(syls) > 1 else 0.0
    add("line_length_swing", "PASS" if sd >= c["min_stdev"] else "WARN",
        f"stdev {sd:.2f} (range {min(syls)}-{max(syls)})" if syls else "no lines",
        f"stdev >= {c['min_stdev']}", c["why"])

    wl = profile.get("word_lists")
    if wl:
        lists = load_sectioned_wordlist(os.path.join(GENRES_DIR, wl["file"]))
        for sect, cfg in wl["sections"].items():
            hits, seen = [], set()
            for s in sections:
                for r in s["rows"]:
                    clean = re.sub(r"\([^)]*\)", " ", r["text"].replace("’", "'"))
                    for entry, rx in lists.get(sect, []):
                        key = (entry, norm_line(r["text"]))
                        if key not in seen and rx.search(clean):
                            seen.add(key)
                            hits.append({"entry": entry, "line": r["n"], "text": r["text"]})
            mx = cfg["max_hits"]
            add(sect, "PASS" if len(hits) <= mx else "WARN", len(hits),
                f"<={mx} (distinct line hits)", cfg["why"],
                "; ".join(f"'{h['entry']}' line {h['line']}" for h in hits) or None)

    return {"genre": profile["genre"], "guide": profile.get("guide"), "note": profile.get("note"),
            "warns": sum(1 for c in checks if c["status"] == "WARN"), "checks": checks}

# ---------------------------------------------------------------- analysis
def norm_line(t):
    return " ".join(w.lower() for w in line_words(t))


def analyse(text, args):
    sections, cues, notes = parse(text)
    cl = load_cliches(args.cliches)
    result = {"sections": [], "flags": [], "notes": notes, "cues": [c[1] for c in cues]}
    flags = result["flags"]

    for sec in sections:
        rows = []
        for ln in sec["lines"]:
            infos = [word_info(w) for w in line_words(ln["text"])]
            syl = sum(i["syl"] for i in infos)
            oov = [i["word"] for i in infos if i["oov"]]
            flex = [i["word"] for i in infos if i["syl_min"] != i["syl_max"]]
            stress = "".join(i["stress"] for i in infos)
            ew = infos[-1]["word"] if infos else None
            rows.append({
                "n": ln["n"], "text": ln["text"], "syllables": syl,
                "syl_min": sum(i["syl_min"] for i in infos),
                "syl_max": sum(i["syl_max"] for i in infos), "flex": flex,
                "approx": bool(oov), "oov": oov, "stress": stress_glyphs(stress),
                "stress_raw": stress, "end_word": ew, "words": len(infos),
            })
        sec["rows"] = rows

    # --- per-section scheme, repeated end-words
    for sec in sections:
        ews = [r["end_word"] for r in sec["rows"]]
        scheme, links = scheme_for(ews)
        sec["scheme"] = scheme
        sec["links"] = [{"from": sec["rows"][i]["n"], "to": sec["rows"][j]["n"],
                         "words": [ews[i], ews[j]], "class": c} for i, j, c in links]
        sec["unknown_end_words"] = sorted({w for w in ews if w and rhyme_keys(w) is None})
        cnt = Counter(w for w in ews if w)
        sec["repeated_end_words"] = sorted(w for w, c in cnt.items() if c > 1)
        if len(set(ews)) < len(ews) and sec["base"] != "chorus":
            for w in sec["repeated_end_words"]:
                flags.append(f"[{sec['label']}] end-word '{w}' used {cnt[w]}x in one section")
        elif sec["base"] == "chorus" and sec["index"] == 1:
            for w in sec["repeated_end_words"]:
                flags.append(f"[{sec['label']}] end-word '{w}' used {cnt[w]}x in the chorus "
                             "(fine if it is the hook; a flag if it is filler)")
        for a, b in zip(sec["rows"], sec["rows"][1:]):
            if a["end_word"] and a["end_word"] == b["end_word"]:
                flags.append(f"[{sec['label']}] consecutive lines {a['n']}-{b['n']} "
                             f"both end on '{a['end_word']}'")

    # --- song-wide end-word reuse across UNIQUE lines
    seen_lines, uniq_ends = set(), Counter()
    for sec in sections:
        for r in sec["rows"]:
            k = norm_line(r["text"])
            if k in seen_lines or not r["end_word"]:
                continue
            seen_lines.add(k)
            uniq_ends[r["end_word"]] += 1
    result["songwide_end_words"] = {w: c for w, c in uniq_ends.items() if c >= args.reuse}
    for w, c in result["songwide_end_words"].items():
        flags.append(f"song-wide: end-word '{w}' closes {c} different lines")

    # --- repeated-section line-by-line syllable variance
    first_of = {}
    comps = []
    stress_min = getattr(args, "stress_min", 0.6)
    for sec in sections:
        b = sec["base"]
        if b not in first_of:
            first_of[b] = sec
            continue
        ref = first_of[b]
        pairs = []
        for k in range(min(len(ref["rows"]), len(sec["rows"]))):
            ra, rb = ref["rows"][k], sec["rows"][k]
            d = rb["syllables"] - ra["syllables"]
            # closest the two lines can get if a singer picks either pronunciation of the
            # flexible words (fire, every...): flag only when even the best case misses
            gap = max(0, rb["syl_min"] - ra["syl_max"], ra["syl_min"] - rb["syl_max"])
            sm = stress_match(ra["stress_raw"], rb["stress_raw"])
            pairs.append({"line": k + 1, "ref_n": ra["n"], "n": rb["n"],
                          "ref_syl": ra["syllables"], "syl": rb["syllables"], "diff": d,
                          "ref_range": [ra["syl_min"], ra["syl_max"]],
                          "range": [rb["syl_min"], rb["syl_max"]], "gap": gap,
                          "flag": gap > args.tolerance,
                          "stress_match": sm, "ref_stress": ra["stress"], "stress": rb["stress"],
                          "stress_flag": (sm is not None and sm < stress_min
                                          and gap <= args.tolerance),
                          "approx": ra["approx"] or rb["approx"]})
        comp = {"ref": ref["label"], "section": sec["label"], "pairs": pairs,
                "line_count_ref": len(ref["rows"]), "line_count": len(sec["rows"])}
        comps.append(comp)
        if len(ref["rows"]) != len(sec["rows"]) and b in ("verse", "chorus", "pre-chorus"):
            flags.append(f"[{sec['label']}] has {len(sec['rows'])} lines vs "
                         f"{len(ref['rows'])} in [{ref['label']}]")
        for p in pairs:
            if p["flag"]:
                flags.append(f"[{sec['label']}] line {p['line']} (file line {p['n']}): "
                             f"{fmt_range(p['range'])} syl vs {fmt_range(p['ref_range'])} "
                             f"in [{ref['label']}] "
                             f"(off by {p['gap']} at best, tolerance {args.tolerance})"
                             + (" ~approx" if p["approx"] else ""))
            elif p["stress_flag"]:
                flags.append(f"[{sec['label']}] line {p['line']} (file line {p['n']}): "
                             f"syllables fit but only {round(p['stress_match'] * 100)}% of "
                             f"the beats line up with [{ref['label']}] line {p['line']} "
                             f"(min {round(stress_min * 100)}%): "
                             f"{p['stress']} vs {p['ref_stress']}")
    result["repeat_comparisons"] = comps

    # --- title check
    if args.title:
        tk = norm_line(args.title)
        t = {"title": args.title, "in_chorus_lines": [], "in_verse_lines": [],
             "first_or_last_chorus_line": False}
        for sec in sections:
            for pos, r in enumerate(sec["rows"]):
                if tk and tk in norm_line(r["text"]):
                    if sec["base"] in ("chorus", "hook", "refrain"):
                        t["in_chorus_lines"].append(r["n"])
                        if pos == 0 or pos == len(sec["rows"]) - 1:
                            t["first_or_last_chorus_line"] = True
                    elif sec["base"] in ("verse", "pre-chorus"):
                        t["in_verse_lines"].append(r["n"])
        result["title_check"] = t
        if not t["in_chorus_lines"]:
            flags.append(f"title '{args.title}' never appears in a chorus/hook")
        elif not t["first_or_last_chorus_line"]:
            flags.append(f"title '{args.title}' is in the chorus but not on its first or last line")
        if t["in_verse_lines"]:
            flags.append(f"title '{args.title}' also appears in verse/pre-chorus line(s) "
                         f"{t['in_verse_lines']} (gives the hook away early?)")

    # --- verse-to-chorus echo
    echoes = []
    stop = FUNCTION_WORDS | {"oh", "yeah", "ooh", "ah", "hey", "like", "when", "what", "where"}
    for i, sec in enumerate(sections[:-1]):
        nxt = sections[i + 1]
        if nxt["base"] not in ("chorus", "hook", "refrain") or sec["base"] in (
                "chorus", "hook", "refrain") or not sec["rows"] or not nxt["rows"]:
            continue
        tail, head = sec["rows"][-2:], nxt["rows"][:2]
        tw = {w.lower() for r in tail for w in line_words(r["text"])} - stop
        hw = {w.lower() for r in head for w in line_words(r["text"])} - stop
        shared = sorted(tw & hw)
        rhyme_shared = [r["end_word"] for r in tail if r["end_word"] in
                        {h["end_word"] for h in head}]
        if shared or rhyme_shared:
            echoes.append({"from": sec["label"], "to": nxt["label"], "shared_words": shared,
                           "shared_end_words": sorted(set(rhyme_shared))})
            flags.append(f"echo: end of [{sec['label']}] shares {shared or rhyme_shared} "
                         f"with the start of [{nxt['label']}]")
    result["verse_chorus_echo"] = echoes

    # --- cliches
    hits = []
    for sec in sections:
        for r in sec["rows"]:
            clean = re.sub(r"\([^)]*\)", " ", r["text"].replace("’", "'"))
            for entry, rx in cl:
                if rx.search(clean):
                    hits.append({"line": r["n"], "section": sec["label"], "entry": entry,
                                 "text": r["text"]})
    result["cliches"] = hits
    seen_h = set()
    for h in hits:
        key = (h["entry"], norm_line(h["text"]))
        if key in seen_h:
            continue
        seen_h.add(key)
        flags.append(f"cliche '{h['entry']}' in [{h['section']}] line {h['line']}: {h['text']!r}")

    # --- limits
    total_words = sum(r["words"] for s in sections for r in s["rows"])
    result["total_words"] = total_words
    result["total_lines"] = sum(len(s["rows"]) for s in sections)
    if args.words:
        lo, hi = args.words
        if total_words < lo:
            flags.append(f"total {total_words} words is under the {lo}-{hi} target")
        elif total_words > hi:
            flags.append(f"total {total_words} words is over the {lo}-{hi} target")
    for sec in sections:
        mx = args.max_lines.get(sec["base"])
        if mx is not None and len(sec["rows"]) > mx:
            flags.append(f"[{sec['label']}] has {len(sec['rows'])} lines, over the max {mx}")

    # --- per-section syllable spread (informational)
    for sec in sections:
        syls = [r["syllables"] for r in sec["rows"]]
        sec["syl_min"], sec["syl_max"] = (min(syls), max(syls)) if syls else (0, 0)
        sec["syl_mean"] = round(sum(syls) / len(syls), 1) if syls else 0
        if syls and sec["syl_max"] - sec["syl_min"] > args.spread:
            flags.append(f"[{sec['label']}] syllables range {sec['syl_min']}-{sec['syl_max']} "
                         f"inside one section (spread > {args.spread})")

    genre = getattr(args, "genre", None)
    if genre:
        result["genre_check"] = genre_check(sections, result, args, load_genre(genre))

    result["sections"] = [{
        "label": s["label"], "base": s["base"], "index": s["index"],
        "line_count": len(s["rows"]), "word_count": sum(r["words"] for r in s["rows"]),
        "syl_min": s["syl_min"], "syl_max": s["syl_max"], "syl_mean": s["syl_mean"],
        "scheme": s["scheme"], "links": s["links"],
        "repeated_end_words": s["repeated_end_words"],
        "unknown_end_words": s["unknown_end_words"], "lines": s["rows"],
    } for s in sections]
    return result


# ---------------------------------------------------------------- output
def render(res, args):
    out = []
    P = out.append
    for s in res["sections"]:
        P(f"[{s['label']}]  {s['line_count']} lines, {s['word_count']} words, "
          f"syl {s['syl_min']}-{s['syl_max']} (mean {s['syl_mean']}), scheme {s['scheme'] or '-'}")
        for r in s["lines"]:
            syl = f"{fmt_range([r['syl_min'], r['syl_max']])}{'~' if r['approx'] else ''}"
            tail = f"   ~ {','.join(r['oov'])}" if r["oov"] else ""
            if r["flex"]:
                tail += f"   ≈ {','.join(r['flex'])}"
            P(f"  {r['n']:>3} | {syl:>5} | {r['stress']:<26} | {r['text']}{tail}")
        if s["links"]:
            P("      rhymes: " + ", ".join(
                f"{l['words'][0]}/{l['words'][1]}={l['class']}" for l in s["links"]))
        if s["unknown_end_words"]:
            P("      end-words not in CMU (rhyme unmeasured): " + ", ".join(s["unknown_end_words"]))
    P("")
    P("legend: / stressed  \\ secondary  . unstressed  ~ heuristic count (word not in CMU)")
    P("        13-14 = a range: ≈ words have more than one pronunciation (fire, every, hour)")
    P("scheme: letters = rhyme groups, * slant link, = same end word, x unrhymed")
    P("")
    P(f"TOTAL {res['total_lines']} lines, {res['total_words']} words")
    if res["repeat_comparisons"]:
        P("")
        P("REPEATED-SECTION COMPARISON (line by line vs first occurrence)")
        P("  syllables ref>new (! = off past tolerance) · beat match % (? = below --stress-min)")
        for c in res["repeat_comparisons"]:
            row = " ".join(
                f"{fmt_range(p['ref_range'])}>{fmt_range(p['range'])}{'!' if p['flag'] else ''}"
                + (f" {round(p['stress_match'] * 100)}%{'?' if p['stress_flag'] else ''}"
                   if p["stress_match"] is not None else "")
                for p in c["pairs"])
            P(f"  [{c['section']}] vs [{c['ref']}]: {row}")
    if "title_check" in res:
        t = res["title_check"]
        P("")
        P(f"TITLE '{t['title']}': chorus lines {t['in_chorus_lines'] or 'NONE'}, "
          f"first/last chorus line: {'yes' if t['first_or_last_chorus_line'] else 'no'}, "
          f"verse lines {t['in_verse_lines'] or 'none'}")
    if "genre_check" in res:
        g = res["genre_check"]
        P("")
        P(f"GENRE CHECK: {g['genre']} ({g['warns']} WARN). Norms, not laws.")
        for c in g["checks"]:
            P(f"  {c['status']:<4} {c['id']}: {c['value']}   [norm {c['norm']}]")
            P(f"       why: {c['why']}")
            if c["note"]:
                P(f"       note: {c['note']}")
    P("")
    P(f"FLAGS ({len(res['flags'])})")
    for f in res["flags"] or ["none"]:
        P(f"  - {f}")
    if res["notes"]:
        P("NOTES")
        for n in res["notes"]:
            P(f"  - {n}")
    return "\n".join(out)


def fmt_range(r):
    return str(r[0]) if r[0] == r[1] else f"{r[0]}-{r[1]}"


def parse_range(s):
    a, b = s.split("-")
    return int(a), int(b)


def parse_maxlines(s):
    d = {}
    for part in filter(None, (s or "").split(",")):
        k, v = part.split("=")
        d[k.strip().lower()] = int(v)
    return d


def main():
    ap = argparse.ArgumentParser(description="Measure syllables, stress, rhyme and cliches in a lyric sheet.")
    ap.add_argument("lyrics", help="text file with [Section] tags")
    ap.add_argument("--title", help="song title, for the title-in-chorus check")
    ap.add_argument("--tolerance", type=int, default=2, help="max syllable difference between matching lines of repeated sections (default 2)")
    ap.add_argument("--stress-min", type=float, default=0.6, help="flag matching lines whose beats agree less than this share, when syllables already fit (default 0.6)")
    ap.add_argument("--spread", type=int, default=6, help="flag a section whose line syllables span more than this (default 6)")
    ap.add_argument("--reuse", type=int, default=3, help="song-wide: flag an end-word closing this many different lines (default 3)")
    ap.add_argument("--max-lines", type=parse_maxlines, default={}, help="e.g. verse=6,chorus=4,bridge=4")
    ap.add_argument("--words", type=parse_range, help="target total word range, e.g. 150-250")
    ap.add_argument("--cliches", default=DEFAULT_CLICHES, help="wordlist file (default: data/cliches.txt)")
    ap.add_argument("--genre", help="genre profile name in data/genres/<name>.json, e.g. emo-pop-punk")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any flag is raised")
    args = ap.parse_args()
    with open(args.lyrics, encoding="utf-8") as f:
        text = f.read()
    res = analyse(text, args)
    print(json.dumps(res, indent=2) if args.json else render(res, args))
    if args.strict and res["flags"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
