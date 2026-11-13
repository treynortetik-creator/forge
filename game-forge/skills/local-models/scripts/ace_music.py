#!/usr/bin/env python3
"""Generate an instrumental music clip locally with ACE-Step 1.5 (MIT), official repo, MLX LM backend.

Usage: python ace_music.py "<caption>" --out <dir> [--seconds 30] [--bpm 100] [--timesig 3] [--key "G minor"] [--seed 7] [--think]
Env:   ACE_REPO=<path to a clone of github.com/ACE-Step/ACE-Step-1.5>  (required)
       ACE_DIT (default acestep-v15-turbo)  ACE_LM (default acestep-5Hz-lm-0.6B)
Setup: uv venv --python 3.12 <venv> (the repo needs Python < 3.13); uv pip install --python <venv>/bin/python -e <repo> 'pillow<13';
       checkpoints (about 11 GB) auto-download into <repo>/checkpoints on first run.
Run with the venv's python, e.g.  <venv>/bin/python -I ace_music.py ...
RAM: peak footprint about 39 GB on a 32 GB Mac (it leans on swap). Close other heavy jobs first.
Without --think the built-in LM does NOT rewrite your caption or pick the tempo; WITH it, the LM rewrote
a waltz brief into a "somber cinematic" piece at 30 bpm. Pin bpm / timesig / key when the brief matters.
TESTED: only the original run (thinking on, 8 steps, seed 7, 30 s, instrumental). The flags here
(--think off, bpm, timesig, key) follow the repo's GenerationParams but were NOT run: smoke it first.
"""
import argparse, os, resource, sys, time
os.environ["ACESTEP_LM_BACKEND"] = "mlx"; os.environ["TOKENIZERS_PARALLELISM"] = "false"
ap = argparse.ArgumentParser()
ap.add_argument("caption"); ap.add_argument("--out", required=True)
ap.add_argument("--seconds", type=float, default=30); ap.add_argument("--bpm", type=int, default=None)
ap.add_argument("--timesig", default=""); ap.add_argument("--key", default="")
ap.add_argument("--seed", type=int, default=7); ap.add_argument("--think", action="store_true")
a = ap.parse_args()
ROOT = os.environ.get("ACE_REPO") or sys.exit("set ACE_REPO to the ACE-Step-1.5 clone")
sys.path.insert(0, ROOT)
from pathlib import Path
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music
from acestep.model_downloader import ensure_main_model, ensure_lm_model, ensure_dit_model
DIT = os.environ.get("ACE_DIT", "acestep-v15-turbo"); LM = os.environ.get("ACE_LM", "acestep-5Hz-lm-0.6B")
CK = Path(ROOT) / "checkpoints"
ensure_main_model(CK); ensure_lm_model(LM, CK)
if DIT != "acestep-v15-turbo": ensure_dit_model(DIT, CK)
t0 = time.time(); d = AceStepHandler()
d.initialize_service(project_root=ROOT, config_path=DIT, device="auto", offload_to_cpu=False)
l = LLMHandler()
l.initialize(checkpoint_dir=str(CK), lm_model_path=LM, backend="mlx", device="auto", offload_to_cpu=False, dtype=None)
print("LOAD_S", round(time.time() - t0, 1))
p = GenerationParams(task_type="text2music", thinking=a.think, use_cot_metas=a.think, use_cot_caption=a.think,
                     caption=a.caption, lyrics="[Instrumental]", instrumental=True, duration=a.seconds,
                     bpm=a.bpm, timesignature=a.timesig, keyscale=a.key,
                     inference_steps=8, guidance_scale=1.0, seed=a.seed, vocal_language="unknown")
t = time.time()
r = generate_music(d, l, params=p, config=GenerationConfig(batch_size=1, audio_format="wav"), save_dir=a.out)
print("GEN_S", round(time.time() - t, 1), "ok", r.success, r.error if not r.success else [x.get("path") for x in r.audios])
print("PEAK_RSS_GB", round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2))
