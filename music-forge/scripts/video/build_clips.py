#!/usr/bin/env python3
"""Animate each shot's keyframe into a video clip through OpenRouter's /api/v1/videos endpoint.

Per shot: pick a model from data/model-routing.json (shot override > rules > default), send the keyframe
(and, only with --audio-refs, an audio reference: the shot's slice of the song, of a stem, or a whole file such as a
TTS line; see the shot's `audio_ref`), poll, download, and write a sidecar JSON next to the clip with job id, model,
prompt, cost and the audio window it was given (sync_offset.py reads that). Resumable (existing clips are skipped), parallel (5 workers),
with a cost ceiling and a --dry-run that makes no API call and needs no key.

Run (stdlib + ffmpeg on PATH; needs OPENROUTER_API_KEY in the environment for live runs, never printed):
    uv run python build_clips.py shot-plan.json --dry-run
    uv run python build_clips.py shot-plan.json --max-usd 15 [--audio-refs] [--only 03 07] [--model ID] [--force]

Audio reference per shot (`audio_ref`, only sent with --audio-refs and only to models that take audio):
    "mix" (default)      the song itself, sliced at the shot start. Use for sung wides: hands and drums move to it.
    "vocals", "instrumental", any key of the plan's "stems" map
                         that stem, sliced at the shot start. Vocals for sung close-ups; an instruments-only mix for
                         band shots in an instrumental (with "nobody sings, mouths closed" in the description).
    a file path          used from its own start (padded), e.g. a TTS clip of a spoken line to drive the mouth.
A shot with `sing: true` or any `audio_ref` gets audio; everything else is generated silent.

PRIVACY: --audio-refs uploads each singing shot's audio slice (a few seconds of your song) to a PUBLIC
temporary file host (uguu.se, falling back to litterbox.catbox.moe with a 1 hour expiry) so the video
provider can fetch it by https URL. It is OFF by default. Keyframes are sent inline as base64, not uploaded.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import plan_lib as pl

API = os.environ.get("MUSIC_FORGE_VIDEOS_URL", "https://openrouter.ai/api/v1/videos")  # override only for tests
SING_SUFFIX = " The singer's mouth matches the vocals of the reference audio."


class Ledger:
    """Thread-safe spend tracker that enforces the --max-usd ceiling before each submit."""

    def __init__(self, ceiling: float | None):
        self.ceiling, self.spent, self.reserved, self.lock = ceiling, 0.0, 0.0, threading.Lock()

    def reserve(self, est: float) -> bool:
        with self.lock:
            if self.ceiling is not None and self.spent + self.reserved + est > self.ceiling:
                return False
            self.reserved += est
            return True

    def settle(self, est: float, actual: float) -> None:
        with self.lock:
            self.reserved -= est
            self.spent += actual


def build_job(plan: dict, shot: dict, routing: dict, forced_model: str | None, resolution: str | None,
              audio_refs: bool, frames_dir: str) -> dict:
    """Everything decided about one shot, with no side effects. Used by both --dry-run and the live run."""
    model, why = pl.pick_model(shot, routing, forced_model)
    info = pl.model_info(routing, model)
    dur = pl.clip_duration_for(shot, info)
    res = resolution if resolution is not None else info.get("resolution")
    wants_audio = bool(shot.get("sing")) or bool(shot.get("audio_ref"))
    with_audio = wants_audio and audio_refs and info.get("audio_reference", False)
    src, src_start = audio_source(plan, shot)
    notes = []
    if wants_audio and not audio_refs:
        notes.append("wants audio, no --audio-refs: generated silent, the mouth will not match")
    elif wants_audio and not info.get("audio_reference", False):
        notes.append(f"wants audio but {model} takes no audio reference: generated silent")
    if with_audio and not src:
        notes.append(f"audio_ref {shot.get('audio_ref')!r} not found (plan 'stems' or a file path)")
    if not info:
        notes.append(f"{model} is not in model-routing.json: cost unknown, request fields guessed")
    if shot["end"] - shot["start"] > info.get("duration", [0, 999])[1] + 0.5:
        notes.append(f"slot {shot['end'] - shot['start']:.1f}s > model max {info['duration'][1]}s: cut will hold/loop")
    frame = pl.resolve_frame(shot, frames_dir)
    if frame is None:
        notes.append("keyframe missing")
    est = pl.estimate_cost(shot, info, res, dur, 1)
    prompt = (plan.get("style", "").strip() + " " + pl.apply_identities(shot["description"], plan.get("identities"))).strip()
    if with_audio and shot.get("sing"):
        prompt += SING_SUFFIX
    return {"id": shot["id"], "slug": shot["slug"], "model": model, "why": why, "duration": dur, "resolution": res,
            "audio": with_audio, "audio_src": src, "audio_start": src_start, "audio_ref": shot.get("audio_ref") or "mix",
            "frame": frame, "est": est, "prompt": prompt, "notes": notes,
            "start": shot["start"], "image_mode": info.get("image_mode", "first_frame"),
            "send_false": info.get("send_generate_audio_false", False), "slot": shot["end"] - shot["start"]}


def audio_source(plan: dict, shot: dict) -> tuple[str | None, float]:
    """(file, start seconds) for a shot's audio reference. Song or stem: sliced at the shot start. Other path: from 0."""
    ref = shot.get("audio_ref") or "mix"
    if ref == "mix":
        return pl.resolve_path(plan, plan.get("audio")), shot["start"]
    stems = plan.get("stems") or {}
    if ref in stems:
        return pl.resolve_path(plan, stems[ref]), shot["start"]
    if ref in ("vocals", "instrumental"):
        return None, shot["start"]  # a stem name the plan does not map
    p = pl.resolve_path(plan, ref)
    return (p if p and os.path.exists(p) else None), 0.0


def print_plan(jobs: list[dict], skipped: list[str], ceiling: float | None) -> float:
    print(f"{'shot':<6}{'model':<30}{'dur':>4} {'res':<6}{'mode':<12}{'est $':>8}  notes")
    total = 0.0
    for j in jobs:
        mode = (j["audio_ref"][:5] + "+frame") if j["audio"] else ("frame(ref)" if j["image_mode"] == "reference" else "first-frame")
        est = "?" if j["est"] is None else f"{j['est']:.2f}"
        total += j["est"] or 0.0
        print(f"{j['id']:<6}{j['model']:<30}{j['duration']:>3}s {str(j['resolution'] or 'auto'):<6}{mode:<12}{est:>8}  {'; '.join(j['notes'])}")
    if skipped:
        print(f"skipping {len(skipped)} shot(s) that already have a clip: {', '.join(skipped)} (use --force to redo)")
    ceil = f" (ceiling ${ceiling:.2f})" if ceiling is not None else ""
    print(f"ESTIMATED TOTAL ${total:.2f} for {len(jobs)} clip(s){ceil}. Estimates come from data/model-routing.json and drift; real cost is read from the API.")
    return total


def prep_image(path: str, aspect: str, out: str) -> str:
    w, h = (1280, 720) if aspect != "9:16" else (720, 1280)
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", path, "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}", "-frames:v", "1", "-q:v", "2", out], check=True)
    with open(out, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def upload_public(path: str) -> str:
    """Temp-upload to a public host. uguu.se first, litterbox (1h) second. PUBLIC: anyone with the URL can fetch it."""
    hosts = [
        (["curl", "-s", "-F", f"files[]=@{path}", "https://uguu.se/upload"], lambda o: json.loads(o)["files"][0]["url"]),
        (["curl", "-s", "-F", "reqtype=fileupload", "-F", "time=1h", "-F", f"fileToUpload=@{path}",
          "https://litterbox.catbox.moe/resources/internals/api.php"], lambda o: o.strip()),
    ]
    for attempt in range(3):
        for cmd, parse in hosts:
            try:
                url = parse(subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout)
                if url.startswith("https://"):
                    return url
            except Exception:
                pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("all temporary audio hosts failed")


class _NoKeyOffHost(urllib.request.HTTPRedirectHandler):
    """urllib copies every header, Authorization included, onto a redirect to ANY host. Drop it when the host changes."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            new.remove_header("Authorization")
        return new


_OPENER = urllib.request.build_opener(_NoKeyOffHost)


def api(key: str, url: str, body: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                                 method="POST" if body else "GET")
    with _OPENER.open(req, timeout=120) as r:
        return json.loads(r.read())


def run_job(j: dict, plan: dict, a, key: str, ledger: Ledger, work: str, clips: str):
    sid = j["id"]
    out = os.path.join(clips, f"{sid}-{j['slug']}.mp4")
    est = j["est"] or 0.0
    if not ledger.reserve(est):
        return sid, f"SKIPPED cost ceiling ${a.max_usd:.2f} would be exceeded", 0.0
    actual = 0.0
    try:
        img = {"type": "image_url", "image_url": {"url": prep_image(j["frame"], plan.get("aspect", "16:9"), os.path.join(work, f"{sid}.jpg"))}}
        body = {"model": j["model"], "prompt": j["prompt"], "duration": j["duration"], "aspect_ratio": plan.get("aspect", "16:9")}
        if j["resolution"]:
            body["resolution"] = j["resolution"]
        if j["audio"]:
            # audio only works with the keyframe as a reference; a pinned first frame silently drops it
            mp3 = os.path.join(work, f"{sid}.mp3")
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{j['audio_start']:.3f}", "-t", str(j["duration"]),
                            "-i", j["audio_src"], "-af", f"apad=whole_dur={j['duration']}", "-c:a", "libmp3lame", "-b:a", "160k", mp3], check=True)
            body["input_references"] = [img, {"type": "audio_url", "audio_url": {"url": upload_public(mp3)}}]
        elif j["image_mode"] == "reference":
            body["input_references"] = [img]
        else:
            body["frame_images"] = [{**img, "frame_type": "first_frame"}]
            if j["send_false"]:
                body["generate_audio"] = False
        pending = os.path.join(clips, f"{sid}-{j['slug']}.pending")
        if os.path.exists(pending):
            # a previous run submitted this shot and stopped polling; resume that job instead of paying twice
            jid = open(pending, encoding="utf-8").read().strip()
        else:
            try:
                job = api(key, API, body)
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:400]
                hint = (" -> face filter (free refusal): give this shot a 'model' override, e.g. minimax/hailuo-3-max (silent)"
                        " or minimax/hailuo-3; never edit the image to sneak it past" if "SensitiveContent" in msg else "")
                return sid, f"SUBMIT {e.code} {msg}{hint}", 0.0
            jid = job["id"]
            with open(pending, "w", encoding="utf-8") as f:
                f.write(jid)
        status, last = "pending", {}
        for _ in range(a.max_polls):
            time.sleep(a.poll_interval)
            try:
                last = api(key, f"{API}/{jid}")
            except urllib.error.HTTPError as e:
                if e.code in (401, 402, 403, 404):
                    return sid, f"POLL {e.code} (job {jid}); not retrying", actual
                continue  # 429/5xx: transient, keep polling
            except (urllib.error.URLError, TimeoutError):
                continue  # transient; keep polling
            status = last.get("status", "?")
            if status in ("completed", "failed", "cancelled", "expired"):
                break
        actual = float((last.get("usage") or {}).get("cost") or 0.0)
        if status != "completed":
            if status in ("failed", "cancelled", "expired"):
                os.remove(pending)  # terminal: a rerun may submit fresh
            else:
                status += f" (still running; rerun to resume job {jid}, it will not be resubmitted)"
            return sid, f"{status} {str(last.get('error'))[:300]} (job {jid})", actual
        req = urllib.request.Request(f"{API}/{jid}/content", headers={"Authorization": f"Bearer {key}"})
        with _OPENER.open(req, timeout=300) as r, open(out + ".part", "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(out + ".part", out)
        if os.path.exists(pending):
            os.remove(pending)
        with open(os.path.join(clips, f"{sid}-{j['slug']}.json"), "w", encoding="utf-8") as f:
            json.dump({"job": jid, "model": j["model"], "routed_by": j["why"], "prompt": j["prompt"], "duration": j["duration"],
                       "resolution": j["resolution"], "audio_ref": j["audio_ref"] if j["audio"] else None,
                       "audio_ref_start": j["audio_start"] if j["audio"] else None, "cost": actual, "plan_time": [j["start"], j["start"] + j["slot"]],
                       "made": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, f, indent=1)
        return sid, "ok", actual
    except Exception as e:  # one bad shot must not sink the batch
        return sid, f"ERROR {type(e).__name__}: {str(e)[:200]}", actual
    finally:
        ledger.settle(est, actual)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Animate shot-plan keyframes into video clips via OpenRouter /api/v1/videos.",
                                 epilog="--audio-refs uploads song slices to a PUBLIC temporary host (uguu.se / litterbox.catbox.moe). Off by default.")
    ap.add_argument("plan", help="shot-plan.json")
    ap.add_argument("--only", nargs="+", metavar="ID", help="only these shot ids")
    ap.add_argument("--frames-dir", help="keyframes (default: <plan dir>/frames)")
    ap.add_argument("--clips-dir", help="output clips (default: <plan dir>/clips)")
    ap.add_argument("--audio", help="song file (default: the plan's 'audio')")
    ap.add_argument("--routing", help="model routing JSON (default: bundled data/model-routing.json)")
    ap.add_argument("--model", help="force one model for every selected shot")
    ap.add_argument("--resolution", help="override the model's default resolution (e.g. 480p, 720p)")
    ap.add_argument("--audio-refs", action="store_true", help="send song slices for singing shots (uploads them to a public temp host)")
    ap.add_argument("--max-usd", type=float, help="cost ceiling: refuse the run if the estimate is over it, stop submitting if actual spend reaches it")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and estimated cost; no API calls, no key needed")
    ap.add_argument("--force", action="store_true", help="redo shots that already have a clip (old clip moved to clips/_old/)")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--poll-interval", type=float, default=10.0)
    ap.add_argument("--max-polls", type=int, default=90, help="polls per job before giving up (default 90 = 15 min at 10 s)")
    a = ap.parse_args(argv)

    try:
        plan = pl.load_plan(a.plan)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"cannot read plan: {e}", file=sys.stderr)
        return 2
    routing = pl.load_routing(a.routing)
    frames = a.frames_dir or os.path.join(plan["_dir"], "frames")
    clips = a.clips_dir or os.path.join(plan["_dir"], "clips")
    if a.audio:
        plan["audio"] = os.path.abspath(a.audio)
    shots = [s for s in plan["shots"] if not a.only or s["id"] in a.only]
    if a.only and len(shots) != len(set(a.only)):
        print(f"unknown shot id(s): {sorted(set(a.only) - {s['id'] for s in shots})}", file=sys.stderr)
        return 2

    jobs, skipped = [], []
    for s in shots:
        if os.path.exists(os.path.join(clips, f"{s['id']}-{s['slug']}.mp4")) and not a.force:
            skipped.append(s["id"])
        else:
            jobs.append(build_job(plan, s, routing, a.model, a.resolution, a.audio_refs, frames))
    print(f"routing table checked {routing.get('checked')}: video-model behaviour and prices drift, re-check before a big run.")
    total = print_plan(jobs, skipped, a.max_usd)
    if a.dry_run:
        if a.max_usd is not None and total > a.max_usd:
            print(f"A live run would be REFUSED: estimate ${total:.2f} is over --max-usd ${a.max_usd:.2f}.")
        print("DRY RUN: no API calls were made, nothing was uploaded.")
        return 0
    if not jobs:
        print("nothing to do.")
        return 0
    missing = [j["id"] for j in jobs if not j["frame"]]
    if missing:
        print(f"refusing to run: keyframe missing for {', '.join(missing)} (run plan_check.py)", file=sys.stderr)
        return 1
    if any(j["est"] is None for j in jobs) and a.max_usd is not None:
        print("refusing to run: some shots have no cost estimate, so --max-usd cannot be enforced", file=sys.stderr)
        return 1
    if a.max_usd is not None and total > a.max_usd:
        print(f"refusing to run: estimate ${total:.2f} is over --max-usd ${a.max_usd:.2f}", file=sys.stderr)
        return 1
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("OPENROUTER_API_KEY is not set in the environment.", file=sys.stderr)
        return 2
    if any(j["audio"] for j in jobs):
        bad = [j["id"] for j in jobs if j["audio"] and not (j["audio_src"] and os.path.exists(j["audio_src"]))]
        if bad:
            print(f"--audio-refs: audio reference file missing for {', '.join(bad)} (plan 'audio', 'stems', or the shot's audio_ref path).",
                  file=sys.stderr)
            return 2
        print("NOTICE: uploading song slices to a public temporary host (uguu.se / litterbox.catbox.moe).", file=sys.stderr)

    work = os.path.join(clips, "_work")
    os.makedirs(work, exist_ok=True)
    if a.force:
        os.makedirs(os.path.join(clips, "_old"), exist_ok=True)
        for j in jobs:
            for ext in (".mp4", ".json"):
                p = os.path.join(clips, f"{j['id']}-{j['slug']}{ext}")
                if os.path.exists(p):
                    shutil.move(p, os.path.join(clips, "_old", f"{int(time.time())}-{os.path.basename(p)}"))

    ledger, spent_total = Ledger(a.max_usd), 0.0
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for sid, status, cost in ex.map(lambda j: run_job(j, plan, a, key, ledger, work, clips), jobs):
            spent_total += cost
            print(f"{sid:>5} {status} ${cost:.3f}", flush=True)
    print(f"TOTAL ${spent_total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
