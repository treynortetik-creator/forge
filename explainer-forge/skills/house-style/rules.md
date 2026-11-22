# House rules for explainer videos

Every rule here comes from a real video: an owner asked for it on a cut, or approved a cut that did it. Each has one
line of why. "The owner" is the person who commissions the video and says ship. When a new rule fights an old one, the
newest approved cut wins, and the old one moves to **Superseded** at the bottom.

How to read it: rules apply to every video unless a profile in `${CLAUDE_PLUGIN_ROOT}/profiles/` says otherwise.
Your own overlay can add or replace rules (see the `house-style` skill). Rules marked *(generalised)* were said about
one video and widened by us.

## Writing

| # | Rule | Why |
|---|---|---|
| W1 | Write for a complete beginner. Replace every technical word, or explain it in plain speech. | Viewers stop following at the first word they don't know. |
| W2 | Define a word before the scene that uses it. Teach two or three words at most, the ones the story needs. | A term explained after its first use is a term not explained. |
| W3 | Clarity beats runtime. Take 5 minutes rather than leave a step confusing. | A shorter video that loses people is the longer one, because they watch it twice. |
| W4 | If the owner can't tell what a line means, cut or rewrite it. | If the person who knows the subject is lost, everyone else is too. |
| W5 | Cut a weak or confusing beat whole. Don't patch it. *(generalised)* | A patched beat stays weak and gets longer. |
| W6 | Say the problem, then the fix, in that order. *(generalised)* | A fix means nothing until the viewer feels the problem. |
| W7 | Never offer to walk the viewer through anything. | It is a tell of machine-written scripts. |
| W8 | No confessional stock phrases (a past mistake described as something biting the narrator). No other stock machine phrases. | Same reason. |
| W9 | Narrate in third person. | First person from a synthetic voice sounds false. |
| W10 | Refer to a person plainly: a name the owner agreed to, or "he" or "she" after one introduction. No code names. | Code names collide with other words on screen and feel odd. |
| W11 | Don't teach two words as the same thing if they are not. Use the plain word, and put the specialist word on a small on-screen tag. | Experts notice the mistake, and beginners don't need the second word. |
| W12 | No jokes in a story told straight. | They read as cringe in a sincere piece. |
| W13 | No swearing in anything coworkers will watch. | Work register. |
| W14 | A video posted in a chat ends with an invitation to drop questions in the thread. | It gives viewers a place to go next. |
| W15 | Turning a document into audio means rewriting it for the ear: diagrams, tables and layouts become sentences. | Read aloud, a table is noise. |
| W16 | Ease up on em-dashes in every piece of prose; aim for none in scripts and posts. | They are a telltale of machine writing. |
| W17 | Elaborate where the mechanism is hard; move fast everywhere else. | The hard step is the one people came for. |
| W18 | Split a dense scene in two. | One idea per scene is the only pace people follow. |

## Voice and pace

| # | Rule | Why |
|---|---|---|
| V1 | Record the whole script in ONE take. Never render scene by scene and stitch. | Viewers hear the tone change at every join. |
| V2 | Pace is a measured number: words per minute while speaking, pauses excluded. Start at 207 for the bundled baritone; the owner sets the final by ear. | A quarter more tempo came out a third faster on a new script. Percent of tempo is not percent of pace. |
| V3 | One uniform, pitch-preserving tempo over the whole take. Faster and slower are both allowed. | Per-line speed changes sound uneven. |
| V4 | Understated and conversational. Not intense, not dramatic, not a narrator-of-epics. | An intense house voice was rejected twice. |
| V5 | No stock preset voices. | They were rejected outright. |
| V6 | Design a synthetic voice from a written description, then clone that clip. Never clone a real person. | It gets the sound the owner wants, and nobody's voice is borrowed. |
| V7 | Audition three labelled candidates; the owner picks a letter. | Every voice that shipped was picked this way. |
| V8 | Offer a man's and a woman's voice when the format has no settled default. | Preference changed between videos; don't assume. |
| V9 | Use the engine's own direction tags for pauses and inflection, after reading its docs. | Guessing tags wastes takes. |
| V10 | Write "AI agents", never "AIs". Give the voice a spoken spelling ("A I") and keep the real spelling in captions. | The voice mangled the plural. |
| V11 | A small flaw in an otherwise good take is fine. List it; don't burn a re-take on it. | A stray pause was not noticeable, and one take means no splicing. |
| V12 | Some warmth: calm is not flat. | Dry narration was called out on long audio. |
| V13 | Write a voice spec before any paid audio. Accent is a choice; never default to British. | Money was spent on voices that were wrong on paper. |
| V14 | Anything paid is proposed with a cost first. | The local route is free and good enough for most. |

## Look

| # | Rule | Why |
|---|---|---|
| L1 | Light, warm, approachable clay. Never dark neon, circuits, vaults or cyberpunk. | The dark look was rejected the first time and every time after. |
| L2 | Clay everywhere, start to finish. Titles, numbers, cards and the close all live in the clay world. | Dropping into flat interface cards broke the spell. |
| L3 | Clay factory is the house style until the owner says otherwise. | The owner chose the reference cut as the style to keep. |
| L4 | No engineer flowcharts (boxes and arrows). Show the thing moving through the real places. | Rejected as unattractive, and beginners can't read them. |
| L5 | Don't copy somebody else's diagram style. | The house style is the point. |
| L6 | Every video has one wow moment. Usually it is the whole system moving end to end. | A cut without one was sent back for it. |
| L7 | Show the system actually working, step to step. | A picture of a process is not the process. |
| L8 | Put the wow scene in the middle, after the basic words are taught. | Earlier, nobody can read it. |
| L9 | Show the real mark (actual logo file) for a product, company or operating system. Ask whether the icon or the wordmark is meant. | Lookalikes and icon fonts were caught immediately. |
| L10 | When several computers appear, each carries its system's mark. | It makes the fleet readable at a glance. |
| L11 | Motion needs enough frames: no jerky walks, no slides passed off as actions. | Jerky motion was the first thing seen. |
| L12 | Key actions need weight: wind-up, action, settle. | Without it, the action looks weightless. |
| L13 | Slightly glossy clay beats dull clay when you can choose. | The owner preferred it side by side. |
| L14 | Reuse the generated sprites across a video and between videos. | Consistency is what makes it a world. |
| L15 | 3D objects, shifting and floating, are welcome where they help. | Approved and asked for. |
| L16 | Interactive pages: plenty to click, small portions, nothing to study. | The page has to earn its form. |
| L17 | Nothing generic: things move with a purpose, and a slop check runs before anyone sees it. | Generic decks were sent back. |
| L18 | Product demos show the real product full screen. No fake browser cards; callout rings pixel-exact. | Both were rejected on sight. |
| L19 | Image models can write text in images. Use that for a post image; keep text out of sprites. | Sprites get reused; text in them can't be edited. |
| L20 | Image tool: the best app for shipped hero art and GIFs, the command-line tool for straight images. Put references in a folder with a short instruction file. | Better finish where it shows, less hand work elsewhere. |

## Mascot

| # | Rule | Why |
|---|---|---|
| M1 | Use a recurring character as the guide, on-model every time. | Viewers recognised it and liked it. |
| M2 | Keep it an unofficial guide. It sits beside a brand's logo and never replaces it. | It is a character, not the brand. |
| M3 | Friendly and approachable is the point: neutral or happy face, never an angry brow. | A focused pose once read as angry. |
| M4 | Put the character image in decks and posts too. | Asked for. |
| M5 | A product's own story uses that product's own mascot. | Two mascots in one story confuse. |

## On-screen text and captions

| # | Rule | Why |
|---|---|---|
| C1 | Teach the few words the story needs in the narration (W2). Any further specialist word is a small tag only. | Beginners follow; experts are satisfied. |
| C2 | Cut any on-screen text nobody outside the team understands. | Status jargon was called out twice. |
| C3 | Label every image you send the owner for review. | Otherwise notes can't name what they mean. |
| C4 | Text style fits the piece. *(generalised)* | Off-tone lettering looked corny. |

Caption size, place and style have never had a direct owner note. The numbers in
`styles/clay-factory/STYLE.md` are ours: they shipped without complaint.

## Structure and length

| # | Rule | Why |
|---|---|---|
| T1 | Teaching a concept: as long as clarity needs, about 5 minutes. | See W3. |
| T2 | A low-risk review explainer or a product demo: 3:00 to 3:30, never over 5:00. Other formats follow their profile (concept video about 4:00 to 5:00, story film about 2:00). | The owner set both numbers for reviews and demos only. |
| T3 | Combine, tighten and cut freely to hit the cap. | Length is the owner's number; how is yours. |
| T4 | Cut what the organisation already handles, and skip an open-questions slide on low-risk reviews. | It invites debate nobody needs. |
| T5 | Review explainers get more data-flow pictures, not fewer. | The flow is what reviewers judge. |
| T6 | Start from the last approved build's folder, not from a written recipe. | Recipes drift; the last build is what was approved. |
| T7 | No dead air and no jumps. No gap over 1.2 seconds anywhere. | A long pause before a scene reads as broken. |
| T8 | A talk someone delivers live: under 10 minutes, one to three slides. | It stays a conversation. |
| T9 | A voiced deck ships with its audio inside, without being asked. | The owner had to ask once. |
| T10 | Interactive players: F for full screen and a speed control (both asked for), plus a progress bar (ours). | Viewers want their own pace and a full picture. |
| T11 | A recurring series keeps one written standard: slide count, synced audio, effort level, and a research round first (a deep pass plus what people said in the last month). | Each week starts at the level of the best one. |

## Facts and privacy

| # | Rule | Why |
|---|---|---|
| P1 | No real people: no names, quotes, faces or examples drawn from someone's work. The owner's own name is fine if they choose it. | Hard rule. |
| P2 | No AI source older than about 90 days without a date or a re-check. | In this field, months old is old. |
| P3 | No third-party opinion that undercuts the subject unless it is needed. *(generalised)* | It moves the argument somewhere else. |
| P4 | Re-count every number on the day. Never round up: 4,873 is "almost 4,900". | Old counts and round-ups were caught. |
| P5 | A number has to measure what the line says it measures. *(generalised)* | A long broken stretch is not one long fix. |
| P6 | Say only what is in the source. Quote a primary page word for word or don't quote it. | Two misquotes were caught in one script. |
| P7 | Extra paperwork rides beside the video, never inside it, and adds no work for reviewers. | Reviewers barely have time for the video. |
| P8 | Source the script from the owner's own documents first. | That is where the facts and the wording live. |
| P9 | Fake demo data: check it yourself instead of asking the owner whether it is fake. | Asking wastes their time. |
| P10 | Nothing personal, no employer and no customer in anything public. | Public means public. |
| P11 | A coined term needs no credit line in the narration, unless the owner wants one. *(generalised)* | Crediting a common term reads as fussy. |

## Process and delivery

| # | Rule | Why |
|---|---|---|
| D1 | The owner approves the script before anything is built or bought. Story films add the storyboard, unless the owner hands that to a reviewer. | A bad script wastes everything after it. |
| D2 | Big edit list: state it back and wait for go. | Misread edits cost a rebuild. |
| D3 | Batch the edits. Don't rebuild on the first note. | More notes are always coming. |
| D4 | Small test first: one style frame, then one scene, then the rest. Show frames as they land so the owner can steer. | Steering early is cheap. |
| D5 | One independent cold read of the script, and one independent review of the cut, by someone who did not make them. | The maker can't see what the viewer misses. |
| D6 | Owner rulings outrank the reviewer. Give the reviewer the list of cuts. | Reviewers re-suggested lines the owner had cut. |
| D7 | A teaser is done once it does its job. Stop there. | The last 10 percent was not worth another pass. |
| D8 | "Full send" means use every tool: research, images, 3D, motion, music, agents. | The ask is for ambition. |
| D9 | Sync is tight and visuals never lag the voice. Fire a build about 0.3 s early. | Late animations were noticed at once. |
| D10 | Deliver one file that opens on a double-click, named with its real extension. Decks carry their audio inside. | A download once opened as a wall of code. |
| D11 | Keep files small: about 35 MB for chat, 720p when in doubt. | Huge files were sent back. |
| D12 | The owner posts. Draft the post for them, with an image. | It goes out under their name. |
| D13 | The post teases and never retells: one line on what it is, light emojis, plain words, clear topic. | A post that tells the story replaces the video. |
| D14 | Read the vendor's docs before testing a limit by hand. | Testing without reading wasted a run. |
| D15 | Use a second machine for rendering when one is available. | Frees the owner's machine. |
| D16 | Write down every lesson, and put the general ones in this plugin. | Each video should start where the last one ended. |
| D17 | Best available model on script and motion; cheaper ones on capture, setup and checks. | Craft is where it shows. |
| D18 | Everything lives in the project folder, and every step is a script. | A lost encode command cost a pass. |

## From our own reviews (not owner notes)

Findings that cost us a pass, kept because they repeat: stale takes of an old script get reused (rename them); the raw
take can end with invented words (diff the whole take against the script); labels orphaned at camera moves (check
frames from the final file at every move); a state flips back before the cut (hold it to the crossfade); captions over
the art; a blank first frame (first object within about 1 second); small grey labels (full strength on the active
row, judged at phone size); reviewers can't hear or see motion (send early, with known flaws listed first).

## Superseded

| Was | Now |
|---|---|
| A fixed percent speed-up (half again, later a quarter) | V2: a measured pace, 207 words per minute while speaking, set by ear |
| No slowing allowed (our own rule, never an owner note) | V3: both directions are allowed |
| About 180 words per minute as the one target | V2: 188 speaking was approved on a product demo, 207 on a concept video. Depends on the format |
| Stock preset voice as the default | V5 and V6 |
| House clone as the narrator | V4 and V6 |
| Softer female voice by default | V7 and V8: the owner picks; the newest approved narrator is a baritone |
| First-person narration | W9 |
| A code name for the person | W10 |
| Everything must be under 5:00 | T1 and T2: length follows the format |
| Teach every engineering word first | W2 and C1: teach the few the story needs, tag the rest |
| One clip per line, stitched, as the default | V1: one take is the default; per-line stays a named fallback when exact cues matter more than continuity |
| Cue times are sums of clip lengths as the only method | One take means cues are alignments of word times; measure them with `sync_check.py` (they are sums only in the per-line fallback) |
| 2.6 second holds or tails between scenes | T7: cap every audible gap at 1.2 seconds, measured on the finished file |
| Dark 3D look | L1 |
