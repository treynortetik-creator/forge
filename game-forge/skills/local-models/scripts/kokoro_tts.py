#!/usr/bin/env python3
"""Local TTS via Kokoro-82M (ONNX): free, on-device, no voice cloning.

Usage: python kokoro_tts.py <out.wav> "text" [voice]
  voice default: am_michael (deep American male)
  male: am_adam am_eric am_liam am_onyx bm_george bm_lewis bm_daniel   female: af_heart af_bella af_nicole bf_emma
Env:   KOKORO_DIR=<dir holding kokoro-v1.0.onnx and voices-v1.0.bin>  (default ~/models/kokoro)
Setup: a venv with `kokoro-onnx` and `soundfile`; run this with that venv's python.
"""
import os
import sys

from kokoro_onnx import Kokoro
import soundfile as sf

D = os.environ.get("KOKORO_DIR", os.path.expanduser("~/models/kokoro"))


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit('usage: kokoro_tts.py <out.wav> "text" [voice]')
    out, text = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
    kokoro = Kokoro(f"{D}/kokoro-v1.0.onnx", f"{D}/voices-v1.0.bin")
    samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
    sf.write(out, samples, sample_rate)
    print(out)


if __name__ == "__main__":
    main()
