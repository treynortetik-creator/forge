#!/usr/bin/env python3
"""Render the WHOLE narration as ONE voice-clone take (Qwen3-TTS through mlx-audio, Apple Silicon).

  python one_take.py --narration narration.json --out audio/take-raw.wav
                     [--ref-wav ref.wav --ref-text-file ref.txt | --ref-text "..."] [--seed 42] [--temperature 0.6]
                     [--top-k 50] [--max-tokens N] [--model mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16]
  python one_take.py --text-file script.txt --out take.wav        (plain text instead of narration.json)

Why one take: a voice rendered line by line drifts in timbre and energy from line to line; one pass keeps the same
person, pitch and rhythm for the whole piece. The price is that a misread line cannot be patched alone: you re-render
the take (change --seed) or reword the line. Run take_check.py on every take before building anything from it.

Text: every chunk's `say` (or `show`), scenes joined by a blank line (narration_lib.spoken_text). No per-scene
renders, no stitching. The reference clip and its exact transcript are arguments; with none given the bundled
default narrator is used (voices/default-narrator). Same text + same reference + same model + same seed = same take.
Writes the wav and <out>.json (text, seed, settings, seconds, model) so the take can be reproduced.
Setup: uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python mlx-audio mlx-whisper soundfile numpy
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import narration_lib as nl  # noqa: E402

PLUGIN = os.path.dirname(os.path.dirname(HERE))
DEFAULT_REF = os.path.join(PLUGIN, "voices", "default-narrator")
SR = 24000


def max_tokens_for(n_words, per_word=14, floor=1500):
    """A token budget that scales with the script. 12 Hz codec frames: about 5 frames per spoken word at a natural
    pace, so 14 per word leaves a wide margin; the model stops at its own end token well before the limit."""
    return max(floor, int(n_words * per_word))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--narration", help="narration.json from make_narration.py")
    ap.add_argument("--text-file", help="plain text to read instead of narration.json")
    ap.add_argument("--out", required=True, help="output wav")
    ap.add_argument("--ref-wav", help="reference clip (default: the bundled narrator)")
    ap.add_argument("--ref-text", help="exact transcript of the reference clip")
    ap.add_argument("--ref-text-file", help="file holding the transcript (default: <ref-wav>.txt)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--max-tokens", type=int, help="token budget (default: 14 per word, at least 1500)")
    ap.add_argument("--model", default="mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16")
    ap.add_argument("--lang", default="english")
    ap.add_argument("--dry-run", action="store_true", help="print the text and settings, load no model")
    a = ap.parse_args(argv)
    if bool(a.narration) == bool(a.text_file):
        ap.error("give exactly one of --narration or --text-file")
    text = open(a.text_file, encoding="utf-8").read().strip() if a.text_file else nl.spoken_text(nl.load_json(a.narration))
    ref_wav = a.ref_wav or os.path.join(DEFAULT_REF, "reference.wav")
    if a.ref_text:
        ref_text = a.ref_text
    else:
        rt = a.ref_text_file or (os.path.join(DEFAULT_REF, "reference.txt") if not a.ref_wav else os.path.splitext(ref_wav)[0] + ".txt")
        if not os.path.exists(rt):
            ap.error(f"reference transcript not found: {rt} (give --ref-text or --ref-text-file)")
        ref_text = open(rt, encoding="utf-8").read().strip()
    n = len(nl.words(text))
    budget = a.max_tokens or max_tokens_for(n)
    settings = {"seed": a.seed, "temperature": a.temperature, "top_k": a.top_k, "max_tokens": budget,
                "model": a.model, "ref_wav": os.path.basename(ref_wav), "words": n}
    if a.dry_run:
        print(json.dumps(settings, indent=1))
        print(text)
        return 0
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model
    model = load_model(a.model)
    mx.random.seed(a.seed)
    t = time.time()
    parts = []
    for r in model.generate(text=text, ref_audio=ref_wav, ref_text=ref_text, lang_code=a.lang, verbose=False,
                            temperature=a.temperature, top_k=a.top_k, max_tokens=budget, split_pattern=""):
        parts.append(np.array(r.audio, dtype=np.float32))
    y = np.concatenate(parts)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    sf.write(a.out, y, SR)
    settings.update({"text": text, "segments": len(parts), "dur_s": round(len(y) / SR, 2), "gen_s": round(time.time() - t, 1)})
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=1)
    print(f"segments {len(parts)}  {len(y) / SR:.1f} s of audio  {n} words  generated in {time.time() - t:.0f} s -> {a.out}")
    if len(parts) != 1:
        print("NOTE: more than one segment came back; the take is not one pass. Check split_pattern support in your mlx-audio version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
