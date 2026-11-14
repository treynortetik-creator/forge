"""Shared settings and helpers for the narrator voice (local Qwen3-TTS through mlx-audio, Apple Silicon only).

Method: VoiceDesign makes ONE reference clip from a text description, then the Base model clones that clip for every
line, so every line is the same person. All settings live here. A `voice.json` in the working directory (or the path
in $VOICE_CONFIG) overrides any of them; see templates/voice.example.json.

Setup (once, in the folder you run the voice scripts from):
    uv venv --python 3.12 .venv
    uv pip install --python .venv/bin/python mlx-audio mlx-whisper librosa soundfile
"""
import json, os, re, subprocess, time

import numpy as np

DESIGN_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"   # designs a voice from a text description
CLONE_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"           # clones it (ref_audio + ref_text) for every line
SR = 24000
SEED = 42            # mx.random.seed() before every clip: same text + same ref + same model = identical audio
TEMPERATURE = 0.6    # library default is 0.9; lower is steadier and less animated
TOP_K = 50
REF_TEMPO = 0.75     # the reference clip is slowed 25% (pitch preserved) so clones inherit a calmer delivery
TARGET_WPM = 160     # per-clip pace target for --pace mode only; final speed is normally set once in stitch_narration.py
MIN_TEMPO, MAX_TEMPO = 0.80, 1.00
EDGE_PAD = 0.12      # seconds of silence kept at each end of a clip after trimming

# A neutral audition passage about no product in particular: steps, a list of choices, a short close. About 77
# words, with a spread of vowels, plosives and sibilants so the clone has plenty to learn from.
PASSAGE = ("Let's walk through it together. First, open the settings panel and find the section marked Sharing. "
           "You'll see three choices: just you, your group, or everyone. Each option shows a short note about who "
           "can view, edit, or measure your work. Pick the one that fits, then press Save. A small green check "
           "appears when the change is stored. If something looks off, you can always undo it later. "
           "Quick, quiet, and nothing breaks along the way.")

COMMON = ("Speaks American English with a neutral General American accent, no foreign accent. Adult woman around 30. "
          "Casual and smooth, warm, low-key and conversational, like a friendly coworker walking you through a tool. "
          "Slow, relaxed medium pace, calm and restrained intonation with modest pitch variation. "
          "Not bubbly, not dramatic, not announcer-like, not breathy.")
VOICES = {
    "A": "A mid-range alto voice, mellow and even. " + COMMON,
    "B": "A lower-pitched, soft alto voice, grounded and calm, a bit deeper than average. " + COMMON,
    "C": "A mid-range voice, a touch brighter and clearer, friendly and easygoing but still understated. " + COMMON,
}
DEFAULT_VOICE = "A"

_cfg_path = os.environ.get("VOICE_CONFIG", "voice.json")
if os.path.exists(_cfg_path):
    _cfg = json.load(open(_cfg_path))
    for _k, _v in _cfg.items():
        if _k.upper() in globals():
            globals()[_k.upper()] = _v


def load(model_id):
    from mlx_audio.tts.utils import load_model
    return load_model(model_id)


def gen(model, text, **kw):
    """One clip -> (float32 mono array at SR, seconds taken). Seeded, sampling params baked in."""
    import mlx.core as mx
    mx.random.seed(SEED)
    t = time.time(); parts = []
    for r in model.generate(text=text, lang_code="english", verbose=False,
                            temperature=TEMPERATURE, top_k=TOP_K, **kw):
        parts.append(np.array(r.audio, dtype=np.float32))
    return np.concatenate(parts), time.time() - t


def n_words(text):
    return len(re.findall(r"[a-z0-9']+", text.lower().replace("-", " ")))


def trim(y, sr=SR, top_db=30, pad=EDGE_PAD):
    import librosa
    iv = librosa.effects.split(y, top_db=top_db, frame_length=512, hop_length=128)
    s, e = max(0, iv[0][0] - int(pad * sr)), min(len(y), iv[-1][1] + int(pad * sr))
    return y[s:e]


def atempo(y, tempo, sr=SR):
    """Pitch-preserving tempo change through ffmpeg (on PATH)."""
    if abs(tempo - 1.0) < 0.005:
        return y
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-filter:a", f"atempo={tempo:.4f}", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-"],
                       input=y.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def normalize_pace(y, text):
    """Trim edge silence, then slow the clip toward TARGET_WPM (never speeds up; floor MIN_TEMPO)."""
    y = trim(y)
    wpm = n_words(text) / ((len(y) / SR - 2 * EDGE_PAD) / 60)
    tempo = float(np.clip(TARGET_WPM / wpm, MIN_TEMPO, MAX_TEMPO))
    return atempo(y, tempo), round(tempo, 3), round(wpm)


def write_wav(path, y):
    import soundfile as sf
    sf.write(path, y, SR)


def m4a(wav, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "aac", "-b:a", "128k", out], check=True)
