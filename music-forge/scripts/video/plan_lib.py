"""Shared helpers for the music-video scripts: shot-plan loading, time parsing, routing, audio probing.

Pure standard library (Python 3.11+). ffprobe is used when an audio file has to be measured.
Not a CLI; imported by plan_check.py, build_clips.py, cut.py and still_prompts.py.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROUTING = os.path.join(HERE, "data", "model-routing.json")
FRAME_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def parse_time(text) -> float:
    """'MM:SS.ss' (or 'H:MM:SS.ss', or plain seconds) -> seconds."""
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    if not 2 <= len(parts) <= 3:
        raise ValueError(f"bad time {text!r} (want MM:SS.ss)")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        raise ValueError(f"bad time {text!r} (want MM:SS.ss)") from None
    total = 0.0
    for n in nums:
        total = total * 60 + n
    return total


def fmt_time(seconds: float) -> str:
    m, s = divmod(max(0.0, seconds), 60)
    return f"{int(m):02d}:{s:05.2f}"


def parse_range(text: str) -> tuple[float, float]:
    a, sep, b = str(text).partition("-")
    if not sep:
        raise ValueError(f"bad time range {text!r} (want MM:SS.ss-MM:SS.ss)")
    return parse_time(a), parse_time(b)


def load_plan(path: str) -> dict:
    """Load a shot plan; adds shot['start'], shot['end'] (seconds) and plan['_dir']. Raises ValueError on bad times."""
    with open(path, encoding="utf-8") as f:
        plan = json.load(f)
    plan["_dir"] = os.path.dirname(os.path.abspath(path))
    plan["_path"] = os.path.abspath(path)
    for i, shot in enumerate(plan.get("shots", [])):
        try:
            shot["start"], shot["end"] = parse_range(shot.get("time", ""))
        except ValueError as e:
            raise ValueError(f"shot #{i + 1} ({shot.get('id', '?')}): {e}") from None
    return plan


def resolve_path(plan: dict, rel: str | None, base: str | None = None) -> str | None:
    if not rel:
        return None
    return rel if os.path.isabs(rel) else os.path.join(base or plan["_dir"], rel)


def probe_duration(path: str) -> float | None:
    if not shutil.which("ffprobe") or not os.path.exists(path):
        return None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def audio_duration(plan: dict, audio_override: str | None = None) -> tuple[float | None, str]:
    """Measured audio length if the file is there, else plan['audio_duration_seconds']. Returns (seconds, source)."""
    path = audio_override or resolve_path(plan, plan.get("audio"))
    d = probe_duration(path) if path else None
    if d is not None:
        return d, "ffprobe"
    if plan.get("audio_duration_seconds") is not None:
        return float(plan["audio_duration_seconds"]), "plan.audio_duration_seconds"
    return None, "unknown"


def resolve_frame(shot: dict, frames_dir: str) -> str | None:
    """Find the keyframe for a shot. 'frame' may carry an extension or not."""
    name = shot.get("frame")
    if not name:
        return None
    cands = [name] if os.path.splitext(name)[1].lower() in FRAME_EXTS else [name + e for e in FRAME_EXTS]
    for c in cands:
        p = c if os.path.isabs(c) else os.path.join(frames_dir, c)
        if os.path.isfile(p):
            return p
    return None


def apply_identities(text: str, identities: dict | None) -> str:
    """Looks, not names: swap each character name for its look string (video models do not know your names)."""
    out = text
    for name, look in sorted((identities or {}).items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"\b{re.escape(name)}'s\b", look + "'s", out)
        out = re.sub(rf"\b{re.escape(name)}\b", look, out)
    return out


def load_routing(path: str | None = None) -> dict:
    with open(path or DEFAULT_ROUTING, encoding="utf-8") as f:
        return json.load(f)


def _rule_matches(cond: dict, shot: dict) -> bool:
    for key, want in cond.items():
        have = bool(shot.get("sing")) if key == "sing" else shot.get(key, "unknown")
        if isinstance(want, list):
            if have not in want:
                return False
        elif have != want:
            return False
    return True


def pick_model(shot: dict, routing: dict, forced: str | None = None) -> tuple[str, str]:
    """(model id, why). Order: --model flag, the shot's own 'model', first matching rule, routing default."""
    if forced:
        return forced, "--model flag"
    if shot.get("model"):
        return shot["model"], "shot override"
    for rule in routing.get("rules", []):
        if _rule_matches(rule.get("if", {}), shot):
            return rule["use"], f"rule {rule['id']}"
    return routing["default_model"], "default"


def model_info(routing: dict, model: str) -> dict:
    return routing.get("models", {}).get(model, {})


def clip_duration_for(shot: dict, info: dict) -> int:
    """Whole seconds to request: the slot length rounded up, clamped to the model's range."""
    import math
    lo, hi = info.get("duration", [4, 15])
    return int(min(hi, max(lo, math.ceil(shot["end"] - shot["start"]))))


def estimate_cost(shot: dict, info: dict, resolution: str | None, dur: int, n_ref_images: int) -> float | None:
    rates = info.get("est_usd_per_second")
    if not rates:
        return None
    rate = rates.get(resolution or "", rates.get("default"))
    if rate is None:
        return None
    return dur * rate + n_ref_images * info.get("est_usd_per_ref_image", 0.0)


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)
