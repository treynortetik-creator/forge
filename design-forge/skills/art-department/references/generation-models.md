# Generation models — OpenRouter, verified live 2026-08-07 16:56 MST

Key in `.env` as `OPENROUTER_API_KEY`. Never echo it.

---

## 🖼️ Image — the `/api/v1/chat/completions` endpoint

Image models are normal chat models with `image` in `architecture.output_modalities`. **Nine of them
as of today.** Find them with:

```bash
curl -sS -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models \
 | python3 -c "import json,sys;[print(m['id'],'|',m['name']) for m in json.load(sys.stdin)['data'] if 'image' in (m.get('architecture',{}).get('output_modalities') or [])]"
```

| Model ID | Marketing name | $/image-output token | Use it for |
|---|---|---|---|
| `google/gemini-3-pro-image` | **Nano Banana Pro** | 0.00012 | **The quality tier.** Hero images, anything that carries a page |
| `google/gemini-3.1-flash-image` | **Nano Banana 2** | 0.00006 | **The workhorse.** Default choice |
| `google/gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | 0.00003 | Bulk, thumbnails, variations |
| `openai/gpt-5.4-image-2` | **GPT-5.4 Image 2** | 0.00003 | ⭐ **Best at text inside the image** and at following a long compositional prompt. This is what people usually mean by "ChatGPT Image 2" |
| `openai/gpt-5-image` / `-mini` | GPT-5 Image | 0.00004 / 0.000008 | Prior generation, cheaper |
| `google/gemini-2.5-flash-image` | Nano Banana (original) | 0.00003 | Superseded |

**Picking between the two families:** Gemini/Nano Banana is stronger on photographic realism, lighting
and material. GPT-5.4 Image 2 is stronger on **legible text in the image**, diagram-like layouts, and
obeying a precise multi-part instruction. If the image contains words, go OpenAI.

**Cost is negligible** — fractions of a cent. Generate 6 variations and pick, per Anti-Slop Rule 3
(AI for volume, human for judgment). Do not ask permission for image generation.

---

## 🎬 Video — the SEPARATE `/api/v1/videos` async API

🔴 **Video models are NOT in `/api/v1/models`.** That endpoint is text and image only. Grepping it
"proves" video does not exist and the proof is worthless. **That mistake is easy to make, and easy to repeat.**

```
GET  /api/v1/videos/models                      ← THE LIST. 21 models. Check HERE.
POST /api/v1/videos                             ← submit; returns {id, polling_url, status:"pending"}
GET  /api/v1/videos/{jobId}                     ← poll until status == "completed"
GET  /api/v1/videos/{jobId}/content?index=0     ← download the mp4
```
A GET on `/api/v1/videos` returns **404 — it is POST-only.** That 404 is what made it look absent.

### Live list, 21 models (verified with a cache-busted request, 2026-08-07 16:56 MST)

`bytedance/seedance-2.0` · `-2.0-fast` · `-1-5-pro` · `openai/sora-2-pro` · `google/veo-3.1` ·
`-3.1-fast` · `-3.1-lite` · `runway/gen-4.5` · `runway/aleph-2` · `kwaivgi/kling-v3.0-pro` ·
`-v3.0-std` · `kwaivgi/kling-video-o1` · `minimax/hailuo-3` · `minimax/hailuo-2.3` ·
`black-forest-labs/flux-3-video` · `x-ai/grok-imagine-video-1.5` · `x-ai/grok-imagine-video` ·
`alibaba/wan-2.7` · `-2.6` · `alibaba/happyhorse-1.1` · `-1.0`

### 🔴 CORRECTION — Seedance 2.5 is NOT on OpenRouter

On 2026-08-07 an assistant claimed `bytedance/seedance-2.5` had been added, and used that to argue
Higgsfield's early access was not a real differentiator. **That was wrong.** A cache-busted query of
`/api/v1/videos/models` on the same day returns 21 models and the only Seedance entries are
`2.0`, `2.0-fast`, and `1-5-pro`. Dated build strings confirm it: `seedance-2.0-20260414`.

**Consequence for the Higgsfield decision:** early access to 2.5 IS a real Higgsfield differentiator
today. The rest of the earlier comparison stands — `soul-id` character consistency, backend prompt
enhancement, the post-production chain — but the "no early-access moat" line was built on a bad fact.
**Re-check `/api/v1/videos/models` before repeating any version claim.**

### Working image-to-video request

```json
{ "model": "bytedance/seedance-2.0",
  "prompt": "…describe what should MOVE, not what the image contains…",
  "frame_images": [{ "type": "image_url", "frame_type": "first_frame",
                     "image_url": { "url": "data:image/jpeg;base64,…" } }],
  "duration": 5, "size": "1280x720", "generate_audio": false }
```
`frame_type` is **required** per frame image: `first_frame` | `last_frame`. Durations 4-15s. Sizes
480x480 → 5040x2160. `seed` and `generate_audio` supported.

⚠️ **POST with `curl -d @file`.** A base64 image inline blows the argv limit
(`OSError: [Errno 7] Argument list too long`).
⚠️ **`/chat/completions` does NOT work for video** — returns a bare `500`, which reads like an outage
and is actually the wrong endpoint.

### 💰 Real cost, not the sticker

The `/videos/models` response carries an **empty `pricing` object** — the API will not tell you.
Observed billing: a **5-second 1280x720 Seedance 2.0 clip cost $0.756** against an advertised
$0.06726/sec (which implies $0.34).

**Budget 2× the advertised per-second price.** Four clips ≈ $3, over the $1 dry-run threshold.
**Quote the real number and ask before submitting.**

### When video is the wrong tool

Blender 2.5D displacement moves a **camera** over static geometry. Real parallax, but **the content
does not animate** — a clock rendered that way does not tick. Called correctly at the time:

> *"You didn't really animate the image. You just did a zoom-in/zoom-out feature."*

**Camera moves → Blender, free. Subject moves → Seedance, $0.75.** Do not sell the former as the
latter.

---

## Text-to-3D, inside the `blender-assets` MCP

- **Hyper3D / Rodin** — ships a free-trial key (`vibecoding`), rate-limited
- **Hunyuan3D** — Tencent, text-to-3D
- **Sketchfab** — needs an API key, **not configured**
- **PolyHaven** — the default, CC0, no key

---

## Model routing note

Rauch's rule, which applies here: *"If I'm talking to an agent interactively, I want fast. If the
agent is doing an asynchronous job, I want accuracy."* Interactive iteration on a look → Nano Banana 2
Lite, 6 cheap variations. The final hero asset that ships → Nano Banana Pro or GPT-5.4 Image 2, once.

---

## 🔴 Deprecations — verified at the vendors' own docs, 2026-08-13

**Do not build on these. Both were checked by fetching the vendor deprecation tables directly.**

| Model | Shutdown | Replacement |
|---|---|---|
| `imagen-4.0-generate-001`, `-ultra-`, `-fast-` | **2026-08-17** | `gemini-3.1-flash-image` |
| `sora-2`, `sora-2-pro`, and the OpenAI **Videos API** itself | **2026-09-24** | **none — the column is `---`** |

**Imagen 4** was verified by me at `ai.google.dev/gemini-api/docs/deprecations`; the table lists all
three IDs shutting down 2026-08-17 with `gemini-3.1-flash-image` as the replacement. *(A research
agent initially reported this as independently double-verified when it was not. It is verified — at
the primary source, by the main session. Recording that because laundered corroboration is worse than
an honest single source.)* **Nothing in this repo referenced Imagen**, so nothing broke.

**Sora** is the one that affects this file: `openai/sora-2-pro` is listed above and is live on
OpenRouter today, but OpenAI is exiting video generation on 2026-09-24 **with no successor named** —
the recommended-replacement column is literally `---` for every row including the API itself. Treat
that line as dead on arrival for anything built after today.

Also current as of this check: there is **no Runway Gen-5 and no Veo 4**. Latest are `gen4.5` and
`veo-3.1-*`; Luma is `ray-3.2`; `aleph` is now `aleph2`. Veo 3.1 preview has no announced shutdown.

### Routing note
Aggregators were price-checked against direct vendors on both modalities and **there is no markup** —
Kling 3.0 1080p $0.112/s, MiniMax H3 2K $0.13/s, Veo 3.1 w/ audio $0.40/s, Recraft V4.1 $0.035, FLUX.2
pro $0.03/MP all identical direct vs fal vs OpenRouter. So route through an aggregator: going direct
buys nothing and costs you Kling's expiring prepaid units (30-180 days, no rollover) and Alibaba's
region-locked hosts. ⚠️ **Ideogram is absent from OpenRouter entirely** (0 of 43 image models); fal
carries 34. If typography or design-decomposition matters, OpenRouter alone will not cover it.

⚠️ **Recraft brand styles are V2/V3 only.** Verbatim from their docs: *"Styles are not supported on V4
and V4.1 models... The `style` and `style_id` parameters only apply to V2 and V3 models."* Only
`recraftv2`, `recraftv2_vector`, `recraftv3`, `recraftv3_vector` accept a custom `style_id`. So
brand-locked vector means `recraftv3_vector` at $0.08/image, and **you cannot combine V4.1 quality
with a custom brand style.** That is an architecture fork, not a footnote.
