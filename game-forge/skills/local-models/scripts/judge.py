"""Local image judge: scores two images against a prompt. Run via img_judge.sh.

Model: CodeGoat24/UnifiedReward-2.0-qwen3vl-8b (MIT), via mlx-vlm. The two prompts are the
official ones from github.com/CodeGoat24/UnifiedReward (inference_qwen/UnifiedReward-2.0-inference),
MIT licensed; scoring Alignment / Coherence / Style.
Runs pairwise in BOTH orders (position bias is real) and averages, plus a pointwise 1-5 per image.
Use it to RANK best-of-N, not for absolute grades (calibration unverified; deltas are small).
Env: JUDGE_MODEL overrides the model id; JUDGE_RAW=1 prints the raw model output as JSON.
"""
import sys, json, time, resource, os, re, tempfile
from PIL import Image
prompt, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
MID = os.environ.get("JUDGE_MODEL", "CodeGoat24/UnifiedReward-2.0-qwen3vl-8b")
t0 = time.time()
model, proc = load(MID); cfg = load_config(MID)
tl = time.time() - t0
TMP = tempfile.mkdtemp(prefix="judge_")
def jpg(p):
    out = os.path.join(TMP, os.path.basename(p) + ".jpg")
    Image.open(p).convert("RGB").resize((768, 768)).save(out, quality=95); return out
PAIR = ("You are presented with two generated images (Image 1 and Image 2) along with a shared text caption. "
 "Your task is to comparatively evaluate the two images across three specific dimensions:\n\n"
 "- Alignment Score: How well each image matches the caption in terms of content.\n"
 "- Coherence Score: How logically consistent and visually coherent each image is (absence of visual glitches, distorted objects, etc.).\n"
 "- Style Score: How aesthetically appealing each image is, regardless of caption accuracy.\n\n"
 "For each dimension, you must assign a relative score to Image 1 and Image 2, such that:\n"
 "- Each score is a float between 0 and 1 (inclusive).\n"
 "- The scores for Image 1 and Image 2 must sum to exactly 1.0 for each dimension.\n"
 "- The higher the score, the better that image is in the corresponding dimension *relative to the other*.\n\n"
 "This format emphasizes comparative quality rather than absolute evaluation.\n\n"
 "Please provide your evaluation in the format below:\n\nAlignment Score:\n Image 1: X\n Image 2: Y\n\n"
 "Coherence Score:\n Image 1: X\n Image 2: Y\n\nStyle Score:\n Image 1: X\n Image 2: Y\n\n"
 "Your task is provided as follows:\nText Caption: [%s]")
POINT = ("You are presented with a generated image and its associated text caption. "
 "Your task is to analyze the image across multiple dimensions in relation to the caption. Specifically:\n"
 "Provide overall assessments for the image along the following axes (each rated from 1 to 5):\n"
 "- Alignment Score: How well the image matches the caption in terms of content.\n"
 "- Coherence Score: How logically consistent the image is (absence of visual glitches, object distortions, etc.).\n"
 "- Style Score: How aesthetically appealing the image looks, regardless of caption accuracy.\n\n"
 "Output your evaluation using the format below:\n\nAlignment Score (1-5): X\nCoherence Score (1-5): Y\nStyle Score (1-5): Z\n\n"
 "Your task is provided as follows:\nText Caption: [%s]")
def run(text, imgs):
    t = time.time()
    p = apply_chat_template(proc, cfg, text, num_images=len(imgs))
    r = generate(model, proc, p, image=imgs, max_tokens=220, temperature=0.0, verbose=False)
    return (r.text if hasattr(r, "text") else r), time.time() - t
A, B = jpg(a), jpg(b)
res = {"load_s": round(tl, 1)}
for name, txt, im in [("pair_ab", PAIR % prompt, [A, B]), ("pair_ba", PAIR % prompt, [B, A]),
                      ("point_a", POINT % prompt, [A]), ("point_b", POINT % prompt, [B])]:
    o, s = run(txt, im); res[name] = {"out": o.strip(), "s": round(s, 1)}
res["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2)
if os.environ.get("JUDGE_RAW"): print("JUDGE_JSON", json.dumps(res))
def nums(t): return [float(x) for x in re.findall(r"(?<![\d.])(\d\.\d+)", t)]
ab, ba = nums(res["pair_ab"]["out"]), nums(res["pair_ba"]["out"])
if len(ab) >= 6 and len(ba) >= 6:
    a_s = [(ab[i*2] + ba[i*2+1]) / 2 for i in range(3)]
    print("PAIR (avg both orders, A vs B) align/coher/style:", " ".join(f"{x:.2f}/{1-x:.2f}" for x in a_s))
    print("WINNER:", "A" if sum(a_s) > 1.5 else "B")
pa, pb = nums(res["point_a"]["out"]), nums(res["point_b"]["out"])
print("POINT A (align,coher,style):", pa, " B:", pb)
print(f"load {res['load_s']}s, total {sum(res[k]['s'] for k in ('pair_ab','pair_ba','point_a','point_b')):.0f}s, peak RSS {res['peak_rss_gb']} GB")
