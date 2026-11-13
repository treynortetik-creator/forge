# Cost plan, ledger, commercial terms

The rule behind this file: think about how the audio should sound and what it will cost before any
paid API call. Voice was cast "by convenience" once and re-recorded; music had a hard cap and a
ledger from the first call. The second approach cost less and surprised nobody.

## 1. Cost-plan template (write before the first paid call)

One row per item:

| Item | Value to the player | Cheapest model/setting that meets the bar | Calls (planned / expected / max incl. retries) | Cost exp / max | Accept check (before retry and before moving on) |
|---|---|---|---|---|---|

Then: total expected and worst case against the cap, the working hard stop (leave headroom for the
owner's call after listening), the prerequisite free work (tools and gates that must exist first), and
a cut list of low-value items. Report actual spend after.

Real example (music plan, 23 items): planned $3.60 (45 calls), expected $4.08, worst case $5.44
against an $8.00 cap with a $6.00 working stop. Actual: 34 calls, $2.72. The plan's key insight was
that money was not the binding limit: the seam bug (any new loop would sound broken), listening time,
disk (one raw WAV about 23 MB) and code risk in files other work was editing were. So free fixes
(loop cutter, gapless looping, routing, loudness trims) were scheduled before any paid cue, and "max
it" was treated as a ceiling, not a target.

Ledger rules:
- One line per call: time, key, take, model, cost from the response (`usage.cost` for music,
  `character-cost` header for voice), running total, gate result.
- Machine-readable total (JSON) plus a readable log. The generator script refuses to start a call
  when total + estimated cost would pass the stop (exit code 9 in `musicgen.py`).
- The ElevenLabs account counter lags and may be shared; the per-call header is the record.
- Never print the key; scripts read an env var or a `.env` file.

Voice example: audition spend 747 of a 3,000 credit cap (45 calls, 3,389 characters, billed about
0.22 credits per character against a list assumption of 1.0). A required recast set of about 3.4k
characters came to about 0.8k credits.

SFX example: 17 generated clips (12 spot sounds, 5 ambience beds) cost 1,122 real credits (counter
17,884 to 19,006) against a conservative estimate of 960 + 3,600; the estimate (about 40 credits per
generated second) was several times too high, so check estimates against a real run.

## 2. Commercial terms by tool (checked at the date shown; re-check before shipping)

| Tool | What was found | Date | Action |
|---|---|---|---|
| ElevenLabs, pay-as-you-go plan | Runs on the free plan's terms: no commercial licence, and content made before upgrading cannot be used commercially (official pages) | 2026-10-20 | Anything that ships (voice, SFX) must be generated on a paid plan (Starter or higher) at generation time. Upgrade first, then regenerate |
| ElevenLabs re-licence mechanics | An upgrade on 2026-10-21 meant re-rendering every shipped SFX with the same prompts, durations and influence into a staging directory, raw takes cached, a request-id ledger, a hard stop when the account counter passed a set value, and a swap step that copies only passing files into the shipped folder | 2026-10-21 | Pattern worth copying: never write into the shipped folder until a staged file passes |
| Google Lyria 3 (via OpenRouter) | Gemini API terms (updated 2026-04-28) say Google "won't claim ownership" and list no commercial restriction. The model is Preview and was bought through a reseller, so check the reseller's terms too. Pure-AI music likely cannot be copyrighted, so others could reuse it | 2026-10 | Generate final music on a paid route, keep receipts, decide to accept the residual risk or buy licensed tracks. In the roguelite this was still open |
| ACE-Step 1.5 (local, open weights) | Repo licence MIT (LICENSE file, copyright line), weights card `license: mit`, README says trained on licensed, royalty-free and synthetic data. Ran on a 32 GB Mac via the official turbo 2B build at a 39 GB peak (leans on swap). A different MLX XL Turbo build was not tried | 2026-10-22 | Free local generation for stingers and beds. Re-read the licence of the exact weights you download |
| Suno (sung songs) | Plan note only, unverified: commercial rights only while subscribed (about $10 a month Pro, third-party price mid-2026) | 2026-10 | Check Suno's terms yourself before relying on this |
| Local TTS (Kokoro-82M) | Free, local, used for placeholder narration | n/a | Placeholder only, replace with real performances by clip id |

Rules:
- Terms change. Record the date and the official page you read next to each decision.
- A model's licence is not the plan's licence: a free open-weights model can still have a "research
  only" build (a local image model in this project carried a research licence and was kept out of
  shipped assets). Read the licence on the exact files you use.
- Never let an unchecked licence guess be why you do not try something, and never let one be why you
  ship.

## 3. Steam AI disclosure (the form fields, as read from the store dashboard instructions)

- Pre-Generated: content made with AI tools during development that ships and players consume. It
  is judged "the same way all non-AI content" is. The game must not include illegal or infringing
  content.
- Live-Generated: made while the game runs, needs a guardrail description.
- The roguelite answered Pre-Generated yes for art, 3D models, music, voice and some text, and
  Live-Generated no. If you cut ElevenLabs lines or Lyria music, delete that word from the disclosure
  text and untick it in the survey together. Do not write "voice acting" on the page until
  regeneration under the paid plan is confirmed.
- Use a dedicated support address in the disclosure, not a personal one.

## 4. Free-first routing

Order of attempts for any audio need: free local (Kokoro placeholders, a local music model, ffmpeg
processing) before paid API; paid API only after the casting/plan step; anything over a few dollars
gets an explicit confirm from the owner. Free fixes (loop cutter, loudness match, pitch/tempo with
ffmpeg) before any regeneration.
