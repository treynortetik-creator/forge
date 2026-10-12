#!/usr/bin/env python3
"""Compare a singer's isolated vocals across tracks: median sung pitch plus a speaker-embedding similarity.

READ THIS BEFORE TRUSTING A NUMBER. The embedding model (TitaNet via sherpa-onnx) is trained on SPEECH. It
under-reads sung timbre and delivery: in one real case two takes scored almost identical while a human heard
a "massive" difference. Human ears are ground truth. Use this tool for (1) pitch register, and (2) catching a
gross singer swap (a different person scores clearly lower than the same song's own halves). NEVER treat a high
score as "these takes match".

Control (always printed): each track's first half vs second half. Those two halves are the same singer in the
same take, so that number is the ceiling for "same voice"; cross-track scores are meaningful only next to it.

Setup: fetch the model once, ~40 MB (sherpa-onnx release asset; the tag really is spelled "recongition"):
    curl -L -o titanet_small.onnx https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/nemo_en_titanet_small.onnx
    export TITANET_MODEL=/path/to/titanet_small.onnx          # or pass --model
Isolate vocals first (numpy must be explicit; output lands in OUT/htdemucs/<name>/vocals.wav):
    uv run --with demucs --with numpy --with soundfile --with torchcodec python -m demucs --two-stems=vocals -n htdemucs -o OUT file.wav

Run:
    uv run --with sherpa-onnx --with soundfile --with librosa --with numpy python voice_match.py nameA=vocalsA.wav nameB=vocalsB.wav
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys


def cos(a, b, np):
    return float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compare isolated vocal stems across tracks (pitch register + speaker-embedding similarity). "
                                 "A rough check only: the model is trained on speech, not singing.")
    ap.add_argument("tracks", nargs="+", metavar="NAME=VOCALS.wav", help="two or more labelled vocal stems")
    ap.add_argument("--model", default=os.environ.get("TITANET_MODEL"), help="path to nemo_en_titanet_small.onnx (or set TITANET_MODEL)")
    ap.add_argument("--chunk-seconds", type=float, default=4.0, help="embedding window (default 4)")
    ap.add_argument("--pitch-seconds", type=float, default=90.0, help="seconds of each stem used for pitch tracking (default 90)")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args(argv)
    if not a.model or not os.path.isfile(a.model):
        print("TitaNet model not found. Pass --model or set TITANET_MODEL. Fetch it once (~40 MB):\n"
              "  curl -L -o titanet_small.onnx https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/nemo_en_titanet_small.onnx",
              file=sys.stderr)
        return 2
    import librosa
    import numpy as np
    import sherpa_onnx

    ext = sherpa_onnx.SpeakerEmbeddingExtractor(sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=a.model, num_threads=a.threads))

    def emb(y, sr):
        s = ext.create_stream()
        s.accept_waveform(sr, y.astype(np.float32))
        s.input_finished()
        v = np.array(ext.compute(s))
        return v / np.linalg.norm(v)

    def voiced_chunks(y, sr):
        """Windows where the stem is actually singing (louder than the median window)."""
        n = int(a.chunk_seconds * sr)
        chunks = [y[i:i + n] for i in range(0, len(y) - n, n)]
        if not chunks:
            return []
        rms = np.array([np.sqrt(np.mean(c ** 2)) for c in chunks])
        return [c for c, v in zip(chunks, rms) if v > np.median(rms)]

    tracks = {}
    for arg in a.tracks:
        name, sep, path = arg.partition("=")
        if not sep or not os.path.isfile(path):
            print(f"expected NAME=existing.wav, got {arg!r}", file=sys.stderr)
            return 2
        y, sr = librosa.load(path, sr=16000, mono=True)
        chunks = voiced_chunks(y, sr)
        if len(chunks) < 4:
            print(f"{name}: only {len(chunks)} sung windows; need a longer stem", file=sys.stderr)
            return 2
        E = np.array([emb(c, sr) for c in chunks])
        f0 = librosa.pyin(y[: int(sr * a.pitch_seconds)], fmin=70, fmax=700, sr=sr)[0]
        med = float(np.nanmedian(f0))
        tracks[name] = (E, med)
        h = len(E) // 2
        print(f"{name:>10}: {len(E)} sung windows | median pitch {librosa.hz_to_note(med)} ({med:.0f} Hz) | "
              f"CONTROL same-track half vs half {cos(E[:h].mean(0), E[h:].mean(0), np):.3f}")
    print("\ncross-track (compare each against the CONTROL values above, not against 1.0):")
    for x, y_ in itertools.combinations(tracks, 2):
        semis = 12 * np.log2(tracks[y_][1] / tracks[x][1])
        print(f"  {x} vs {y_}: similarity {cos(tracks[x][0].mean(0), tracks[y_][0].mean(0), np):.3f} | median pitch {semis:+.1f} semitones")
    print("\nREMINDER: this model hears speech, not singing. Pitch gaps and a score far BELOW the control are informative; "
          "a score near the control proves nothing. Listen to the stems side by side before deciding anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
