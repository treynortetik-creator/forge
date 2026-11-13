# Shipping: desktop wrapper, Steam scoping, AI disclosure, web deploy

**Everything dated here was checked on the stated day against the platform's own pages. Store rules and prices change: re-verify the day you act.**
Valve's times are Pacific. Sources at the end.

## 1. Pick the platform before you pick the caps

The roguelite started as "a browser game on itch.io and CrazyGames, wrap for Steam later" (2026-10-15) and became "Steam first, port everywhere after 1.0" (2026-10-19).
For about a week the web caps (itch 1,000 files, CrazyGames 1,500, 20 MB first play, 900 KB JS gzip) kept failing builds for a platform nobody was shipping to. See `SKILL.md` section 9: web limits became warnings; Steam Deck gates became the real ones.
Our recommendation for a Hades-like: skip itch, put up a Steam store page early, ship a free demo into a Next Fest, then Early Access. That is the path the leader took (Epic Early Access 2018-12-06, Steam Early Access 2019-12-10 at $24.99, 1.0 on 2020-09-17).

## 2. Desktop wrapper: Electron

| Option | Verdict (2026-10-19) |
|---|---|
| **Electron** (44.9.0 published 2026-10-17) | Pick this. Spiked on 2026-10-15 with 44.7.2 plus electron-builder: it launched, the canvas rendered, saves persisted. Same Chromium the game is tuned on, so gamepads and performance match what you test. Big download (393 MB mac arm64 unsigned app) but Steam players do not care |
| Tauri (2.12.3) | Small app but each OS's own webview: three engines, three sets of controller bugs. Steam hookup means Rust. No |
| NW.js (0.118.0) | Works (a famous survivor-like shipped on a web engine) but a smaller ecosystem. No reason to switch |

Facts from the spike and the Windows build:
- **Saves must be files for Steam Auto-Cloud** (you tell Steam which folder to sync; no code). Write saves to a JSON file with a `localStorage` mirror. In Electron, `localStorage` flushes on clean quit only.
- **Bundle fonts.** Google Fonts links break offline play; self-host them (also a boot win).
- **A platform adapter layer** (one small module: local / web portal / Steam) lets achievements, saves, "demo mode" and store links plug in once. Ours: `src/platform/` with Electron JSON saves and a localStorage mirror; a demo flag (hero fixed, run ends at the first boss); end-card store and feedback URLs configured in one file (they were empty strings, so both buttons toasted "Coming soon" until someone filled them).
- **Windows build from a Mac:** a Windows x64 zip (338 MB) cross-built with electron-builder, **never run on Windows**. The audit three days later said that is not a build. Add a CI job on `windows-latest` that launches the exe with a `--smoke` flag, waits for a boot line, writes and reads a save, captures a screenshot artifact and fails on any console error. (Proposed, not yet built when the reconcile was written.)
- **Linux/Deck:** an AppImage built the same day; the Linux depot was dropped. Valve tests Deck compatibility and uses whichever of the Linux or Windows build runs better. Skip Mac at launch: signing needs Apple's $99/yr program.
- **Steam Deck Verified needs (from Valve's review page):** works with the default controller layout; button icons match the pad in use; text readable at 1280x800 at arm's length; 30 fps at 800p (as our scope notes recorded Valve's page); no launcher. Our pad glyph module (`scripts/gamepad-detect.ts`) and a 28 px text floor were aimed at this.
  The 2026-10-23 reconcile still listed "no Steam Input config, no Deck glyphs, no fullscreen option in Settings (F11/Alt+Enter only)" as open: a pad-only or Deck player could not leave windowed mode.
- **Steam library bake-off:** `steamworks.js` 0.4.0 (last npm release 2024-08-06, 635 stars, has an Electron overlay helper) versus `steamworks-ffi-node` 0.11.3 (2026-09-24, 86 stars). Verdict at medium confidence: `steamworks.js`, fallback ffi. Overlay and achievements were never exercised (no Steam client on the build Mac); test both against the Spacewar test app (id 480) on a machine with Steam before committing.

## 3. Steam scope (checked live 2026-10-19)

| Item | Rule |
|---|---|
| Steam Direct fee | **$100 per game**, no refund, but recouped once the game reaches **$1,000** adjusted gross revenue |
| Paperwork | legal name (a sole proprietor is fine), bank account whose name matches, a US tax form, an identity check, e-sign the NDA and distribution agreement |
| Tax check | outside service; **up to 30 days**, may ask for more documents |
| Wait after paying | **21 days** from paying before that game can be released (Valve's onboarding page; some blogs say 30 and are wrong) |
| Coming Soon page | public for **at least 2 weeks** before release |
| Reviews | store page and build each usually 3-5 business days; **plan 7** |
| Demo | a **separate free app** tied to the game; a button on the store page; the "demo is out" notification to wishlisters goes **once, only within 14 days of the demo's first release**; Valve advises turning achievements off in demos |
| Next Fest | **one per game, ever.** The store page must be public; the demo live by the start; the game cannot release before the fest ends |
| Early Access | must be playable and unfinished; no specific promises of future features; no permanent discounts; leaving EA is one-way |

**Next Fest (verified 2026-10-19):** Feb 22 - Mar 1, 2027 (sign-up by Sun Jan 10, 11:59pm PST); June 14-21, 2027 (sign-up by Sun Apr 25, 11:59pm PDT); an October 2027 edition not announced (pattern, not fact: Feb, June, October).
We recommended June 2027 over February so the one shot lands on a polished slice. The owner later chose an earlier demo anyway, to beat a wave of AI-made games; see section 6 for how the plan fared.

**Store assets (Valve rules in force since 2022-09-01):**

| Asset | Size (px) | Notes |
|---|---|---|
| Header capsule | 920 x 430 | art + title only |
| Small capsule | 462 x 174 | logo nearly fills it |
| Main capsule | 1232 x 706 | |
| Vertical capsule | 748 x 896 | |
| Library capsule | 600 x 900 | logo plus optional subtitle |
| Library hero | 3840 x 1240 | **no text at all**; keep key content in the central 860 x 380 |
| Library logo | 1280 wide and/or 720 tall | transparent PNG |
| Page background | 1438 x 810 | optional, quiet |
| Screenshots | 1920 x 1080 min, 16:9, at least 5 | gameplay only; **mark 4+ as all-ages** or lose placements |
| Trailer | up to 1920x1080, 30/60 fps, H.264 .mp4, 5,000+ kbps, AAC 44.1/48 kHz | mostly gameplay with HUD |

Text banned on every capsule: review scores, awards, "X% off", calls to action ("Wishlist now"), other products, any other words. Art must be PG-13. The client app icon size was not verified.
We commissioned ten Steam-size images in one batch from an image model plus a 4K master, then checked the sizes with a script. Plan a **store capture harness** (a `?capture=1` mode with no dev overlays, a HUD toggle key, fixed seeds, 1920x1080, then PNG frame-step plus ffmpeg or a CDP screencast): 5 screenshots and a trailer are due before the page can be reviewed.

**Early Access price comps (US store prices, fetched 2026-10-19):** two big Hades titles $24.99 and $29.99; a Hades-like in EA $24.99; other EA roguelites $9.99 and $6.99; solo first games with an AI label sit better at $14.99 EA then $19.99 at 1.0 (raising at 1.0 is allowed). Recommendation, not a fact.

## 4. AI disclosure and licence checks (read 2026-10-20, not legal advice)

Steam's Content Survey has a Generative AI section with two kinds: **pre-generated** (made during development, ships fixed) and **live-generated** (made while the game runs; requires a guardrail description). Both ask you to describe the implementation.
Valve's rewrite (2026-01, per secondary coverage; Valve's own post was not found) exempts development efficiency tools such as coding assistants from disclosure.

| Service | Finding on 2026-10-20 |
|---|---|
| **Voice and SFX generator (ElevenLabs)** | Not cleared on our account: `GET /v1/user/subscription` returned `tier: payg`; pay-as-you-go is a feature of self-serve plans including free, and the free plan "does not include a commercial license". Anything already generated stays uncleared. **Subscribe to a paid plan, then regenerate everything that ships**; log the date; use your own designed voices or premade ones, not Voice Library or clones |
| **Music (Google Lyria 3 via OpenRouter)** | Conditional yes: no explicit grant and no prohibition ("cleared in practice, not in writing"); the Gemini API terms say Google "won't claim ownership". Accept the risk knowingly or swap for licensed tracks for the trailer; keep the files, model id and date |
| **Image generation (OpenAI via OpenRouter and apps)** | Provisional yes: OpenAI's pages returned HTTP 403 to automated fetches, so only secondary evidence was read. The owner must open the terms in a browser |
| **3D generation (Tripo)** | Provisional yes for **paid-credit output only**; free-tier output is retained by the vendor. Same 403 problem. Keep only models made with paid credits and your own input images |
| **Local TTS (Kokoro-82M)** | Yes: weights and code Apache-2.0; six voices built on CC BY data need attribution |
| **Valve/Steamworks** | Compliant if you disclose; nothing live-generated |

Rules from this pass:
- **Re-read the live terms the day you submit.** Keep a checklist with initials and dates.
- Disclose plainly in the survey (art, 3D, music, voice, some text; "all pre-generated; nothing is generated while you play; the game does not connect to any AI service"). Never market the game as "the AI game".
- **Perception data (secondary, reported in our 2026-10-20 research notes, not re-verified):** a 2026 survey had 52% of developers negative on AI; one gamer survey had 63% "very negative"; one analysis found AI-disclosed Steam games with about 52.6% fewer first-month reviews. A demo for a Next Fest was cancelled by another developer over fear of AI cloning. Disclose honestly, lead with direction and craft, consider a human paint-over of capsule art as optional insurance.
- Keep prompts free of living artists' and other games' names. Do a lookalike pass on key art for studio designs.
- Check a title for conflicts: a name search on the store (zero results on 2026-10-19) plus a free trademark search before paying for anything with the name on it.

## 5. Web deploy (what failed and what worked)

- **Deploy from version control.** The first host recipe was "build locally, stage a small directory, upload with the CLI". It worked for a 38 MB build. For a 127 MB `dist/` over a 10.7 Mbps uplink it timed out, then failed with HTTP 524; later, uploads produced six FAILED deployments in one night.
  The fix: push the repo (51 minutes for 1.8 GB the first time) and connect the host's service to a `deploy` branch, then main. Pushes auto-deploy; no dashboard click needed (it was done from the CLI).
- A staging directory must be **linked to the right project before the first upload**; an unlinked upload created a stray empty project.
- **Verify after every deploy:** the new `assets/index-*.js` name in the live HTML; the health endpoint; and the **content-type** of assets, because a SPA fallback answers any missing file with 200 and `text/html`.
- A host-wide outage ("new builds paused for all workspaces") blocked a deploy for an afternoon; a retry loop every 10 minutes for 3 hours was the workaround. Do not make a deploy the critical path of a feeling.
- **Secret scan the build output** before upload (keys, absolute paths, account names, internal hostnames). One scan pattern for `sk_` false-matched a CC0 asset named `asterisk_...`; use token-boundary patterns.
- A small account/save server (only `pg`) was added later: the staging directory contained `dist/`, `server/`, a trimmed `package.json` and a lockfile. `DATABASE_URL` is a **reference** to the database service, not a literal; the database had no public endpoint (the TCP proxy was removed after use). For one-off DB work, run node inside the service.

## 6. Planning a Steam demo with agents: what the reconcile found

A 19-sprint plan (198 tasks, demo on 2026-12-08, Next Fest Feb 22 - Mar 1 2027, EA proposed 2027-05-13) was reconciled against reality 2026-10-23:
- The code side was ahead of plan; **the Steam side was stuck**: no evidence the $100 fee was paid, no app ids. Nothing could be uploaded; the plan's latest day for the fee had arrived. Make owner-blocked steps the top line of every status.
- **Art drift:** 59 of 61 non-merge commits in two days were art, FX or look work. Script v2, settings display options, a hero feel pass, the feedback form and screenshot capture had barely moved. A plan needs a counter on non-art work.
- Nothing was deployed or backed up: 83 commits unpushed; the production build was a week old and still carried the old title; the Windows exe had never launched on Windows.
- Of 48 agent tasks in the first three sprints: 26 done, 11 partial, 10 not started, 1 n/a; 2 of the 10 were blocked on the owner.
- The opening scene shipped 3 of 6 stills; the end-card buttons toasted "Coming soon"; one memento ran an old effect that contradicted canon. **Run the built demo end to end after every merge** (title to end card, zero console errors, a screenshot per beat) and fix display strings last, on the built game.
- A hard plan should show real deadlines, not sprint ends: store page to Valve about 3 weeks before the demo; demo build about 2 weeks before; a Thanksgiving week in the window; a fallback date pair.
- The situation changed again on 2026-11-06: the hosted builds were deleted and the game went local-dev only while another project took priority. Plans are hypotheses; keep the project doc authoritative.

## 7. Open-sourcing a game repo

For the tower-defense game: the local `.git` was 747 MB (art alone 634 MB). Publish a clean snapshot (a fresh repo, one commit) with no raw renders or drafts (94 MB, no file over 5 MB).
Steps that held: an **independent audit agent** with fresh context; a secret scanner (gitleaks 8.30.1: no leaks) plus a hand grep for absolute paths, assistant paths, account wording, a time zone string, email, family names and employer names (0 hits after fixes);
remove cost logs (they exposed an image API balance and a voice API usage count); add MIT LICENSE, README and OFL font texts; **squash history before going public** (PR refs keep old commits forever: recreate instead); an export script (`tools/export-oss.sh`) so the next release is repeatable.

## 8. Sources (all read on the stated dates)

- Steam Direct fee, onboarding, Coming Soon, review process, store and library assets, asset rules, trailers, demos, Next Fest rules, event calendar, Early Access, Deck compatibility, Auto-Cloud, Content Survey: `partner.steamgames.com/doc/...` (2026-10-19 and 2026-10-20).
- ElevenLabs terms, help pages, billing and pricing; Gemini API terms; OpenRouter terms; Kokoro model card: primary pages (2026-10-20). OpenAI and Tripo: not readable by automated fetch (HTTP 403).
- Electron, Tauri, NW.js, steamworks.js, steamworks-ffi-node versions: `npm view` on 2026-10-19.
- Early Access history and prices: the leader's studio posts, game-news coverage, and Steam's store API (cc=us), 2026-10-19.
