# Lessons, merged

Three sources: a run of narrated interactive HTML explainers for internal decision reviews (Nov 2026) and a product-demo
MP4 built on the same kit and approved on its second cut; plus a drawn character-animation story film (rules 27-44). Each line is a rule because a real cut was rejected or a
reviewer caught it.

## What the viewer and the owner want

1. **Short.** 3:00 to 3:30 is the target for a single-topic explainer; 5:00 is the hard cap. About 7 scenes. One idea
   per sentence; merge rather than repeat. A presentation someone delivers live: under 10 minutes, three ideas.
2. **Fast, calm voice, with the pace set by the owner's ear.** Two approved cuts measured about 180 and about 207
   speaking words per minute (pauses not counted); a first cut at about 120 was "a snail". These are measured results,
   not targets: pick a number, play 30 seconds, let the owner move it up or down. The calm comes from the voice, not
   from slowing it. See voice.md and lessons 45 and 46.
3. **No stock voices, no dramatic reads.** Presets had an accent the owner disliked; a cloned house voice was "overly
   intense". Plain, friendly sentences, not punchy one-liners.
4. **Light, warm, approachable look.** Off-white background, soft matte "clay" 3D or flat illustration, one or two
   accent colours, everyday metaphors. Dark neon "cyberpunk" vaults and glowing circuits were rejected. Approved from
   ONE sample image plus ONE rendered scene: make the style sample before building, every time a style is new.
5. **Show the real product, full screen.** Footage shrunk into fake browser cards was rejected. Edge-to-edge screen
   recordings; zoom only to make a number readable, then pull back.
6. **Pixel-exact callouts.** Rings a few pixels off read as sloppy. Place every ring from a box measured on the actual
   frame; screenshot each ring at its frame (`ring_check.mjs`).
7. **A detail pass is required.** A frame every 2 s, every sheet looked at. Found: a ring still on after its cut,
   crossfades overlapping, text overflowing a card, blank flash frames, captions over callouts.
8. **No real people.** No names, quotes or "X built Y" anywhere: narration, slides, notes, captions, footage. Use
   "someone in support". Grep before shipping (`name_check.py`).
9. **Current names and titles.** Teams rename roles; check every job title and product name with the owner.
10. **Fact-check the script against the source before recording.** A reviewer caught three overstatements in one
    draft ("checks every number" when only cited figures are checked; "download" when only PDF export existed).
11. **State facts only.** Leave out an "open questions" slide unless the audience needs it to decide.

## Build rules

12. **Timeline time is narration time.** Every animation is placed from the cue times (`T`, `E`) or the moment a word
    is spoken (`W`), never typed seconds, so a re-voiced line carries its animation with it.
13. **Know where your cue times come from.** With one clip per line, stitching clips with fixed gaps makes the cue times
    sums, exact to the sample; no alignment step. With one take for the whole script (lesson 44) the cues are
    alignments of whisper word times to the script and carry a real error: measure it (lesson 50) instead of assuming
    it away. Word timing from whisper alone drifted about 0.4 s on an earlier per-clip deck.
14. **Render frame by frame, never screen-record.** Seek the paused timeline and every video per frame. Real-time
    capture drops frames.
15. **Re-encode footage with a short GOP** (6 frames, no B-frames) so every seek lands on the exact frame.
16. **One command rebuilds everything**, with a visual-only switch (`SKIP_AUDIO=1`).
17. **Vendor every library** (GSAP, three.js) so the output works offline and renders do not depend on a CDN.
18. **Image backgrounds never match the page exactly.** Sample the page colour from the images and feather each
    image's edge with a radial mask.
19. **3D labels projected onto the page** must hide when they fall into the text column and be clamped inside the
    frame, or they clip at the edge.
20. **Phone layout is its own layout.** No stage scaling on a phone: the visual in a band on top, the text reflowed
    below, short labels, tiny SVG text hidden.
21. **Give the speed control to the viewer** on interactive explainers: 1x to 2x, pitch preserved, the animation
    timeline scaled to match, remembered locally. Prove sync at 1x and at the top speed.
22. **A big inlined audio file can show 0:00 duration for a few seconds** while it decodes. It fills in on its own.

## Process rules

23. **Design and editing go to the strongest model; capture, TTS setup, file reading and fact-checks go to a cheaper
    one.**
24. **Spend plan before any paid call** (image-to-3D, image models, cloud TTS): per item, cost, retries, acceptance
    check, and a cap. On the reference run, six image-to-3D props cost $2.40 against a $3.00 cap; the product demo
    spent nothing (all graphics drawn in SVG, CSS and GSAP).
25. **Drafts go to the owner first.** The owner posts; the agent never sends to the audience.
26. **Label every proof image** you send for review with what it shows (scene, before/after).

## Drawn character animation

From a 2-minute clay-style story film (7 scenes, about 300 generated drawings, three overnight passes). The first cut
shipped half its scenes on reused art with code-only motion; the owner called the two key actions "flimsy".

27. **Lock script, voice and storyboard before any drawing.** Narration and captions then stay frozen: check the
    decoded-audio hash and the frame count of every scene after each rebuild, so redraws never move sync.
28. **Build a shared kit first, then one builder per scene.** Cast reference sheets (turnaround, expressions), a scale
    chart, motion helpers, one render script, padded audio per scene. Attach the cast sheets to every image prompt.
29. **Write the character's fixed facts as rules every builder gets**: expression, which side a one-sided detail is on,
    "never mirror this character". Mirroring a drawing silently moves an asymmetric detail to the wrong side.
30. **Put recurring props on the scale chart, not only characters.** A prop drawn by two builders came back at two
    sizes and the mismatch was the first thing a reviewer saw.
31. **State the screen direction of every action in the shot list.** Shots drawn in isolation flipped a fall from
    rightward to leftward across one cut.
32. **An action needs drawn poses.** Rotating, sliding or gliding one drawing reads as flimsy however it is eased.
    Aim for a new drawing every 2 to 3 frames at 30 fps during action; hold only on stillness. A figure frozen while a
    prop moves is the same fault.
33. **Give weight three beats**: anticipation, the action, follow-through and settle. A thrown object keeps its held
    size for the first frames of flight; an effect (splash, dust) is drawn in stages sized to what caused it.
34. **Machine interpolation is a bonus, not the plan.** It only works between near-identical drawings and ghosts on
    limbs and fingers. Budget for drawn in-betweens and reject any interpolated frame you would not draw.
35. **One fresh image session per drawing.** Long resumed sessions stalled. Look at every image as it lands and
    regenerate off-model ones at once.
36. **Find the usage limit of the image tool before fanning out**, order the work so the most-watched shots are drawn
    first, and tell builders to stop cleanly at a limit and list the missing images with their prompt paths.
37. **Prompts, raw art and every assembly command live in the project folder**, never a temp folder. A final encode
    whose command was not saved had to be rediscovered by trial on the next pass.
38. **Keep every previous cut and scene file under a pass name.** Rollback is then one rename, and before/after proof
    is free.
39. **Proof for motion you cannot watch**: a strip of every 2nd or 3rd frame per action, a frame every 4 s for the
    film, the frame pair at every join. Then a separate reviewer on the strongest model returns SHIP or FIX FIRST with
    at most 8 ranked findings, each with a fix that needs only a few drawings.
40. **The owner's first viewing is the real motion review.** Send the cut as soon as it exists with the known flaws
    listed first; two notes from a viewing steered the next pass better than eight findings from stills.
41. **Stop at SHIP.** List the remaining polish with its likely gain and let the owner decide; for a teaser the last
    10 to 15 percent was not worth another pass.
42. **Test the image route on one frame, side by side, before the build.** The same prompt and references through two
    routes of the same provider differed visibly in finish; switching mid-film would have split the look.
43. **A logo is a file, not a font rendering.** Ask which mark is meant (icon or wordmark) when both exist, use the
    exact file, and check its real pixel size first: canvas metadata can be wrong and crop it silently.

44. **Record story narration in one take, not scene by scene.** Clips generated separately drift in tone and the
    viewer hears it at the scene changes. Generate the whole script in one request, put pauses and delivery notes in
    the text with the model's own inline direction tags (look up the tag syntax and the length limit first), then cut
    scenes from that single take by word timings. Re-record everything, not one scene, when a line changes. The tag
    syntax, limits and timestamp call for one cloud voice are in `cloud-voice.md`.

## One take and a sprite world (generic)

From a 4-minute narrated explainer made of transparent clay-style sprites on a paused timeline, one local voice take for
the whole script, three cuts. Each rule is here because a cut was flagged or a check caught it.

45. **Pace has two numbers: speaking pace and overall pace.** Speaking pace is words divided by the summed time
    spent speaking (pauses between scenes not counted); overall is words divided by the runtime. Quote both, and say
    which one a target means. The newest approved cut measured 207 speaking and 201 overall; an earlier approved cut
    about 188 speaking and 165 overall.
46. **One uniform tempo on the whole take, never per scene, either direction.** The take is measured, one
    pitch-preserving tempo moves it to the target, and a tempo outside about 0.8 to 1.25 gets flagged for a listen.
    Speeding up and slowing down are both legitimate; the owner's ear decides which. A first cut that was 15 percent
    too fast was fixed by one tempo, not by re-voicing.
47. **Pauses only between scenes, each capped.** Cut the take mid-gap between scenes, keep a short pad of its own edge
    silence, insert a measured scene gap, and cap every audible gap at 1.2 seconds. Long holds of 2 to 2.6 seconds were
    flagged as dead air; a deliberate held beat is a short extra gap before one named scene, not a long tail.
    Default head 0.8 s and tail 0.8 s (the 0.35 s of silence kept after the last word counts toward the cap, so a 0.95 s tail needs `--max-gap 1.3`). Pauses INSIDE a scene count too: the build shortens them, and the cap is measured on the finished audio.
48. **Cut the take at the last script word.** A voice model can make up a closing sentence. End the audio a third of a
    second after the last scripted word and the invented tail is gone without a re-render.
49. **Check the take before building on it.** Diff what whisper heard against what the voice was asked to say. An
    insert at the end is a made-up tail; a replace or delete in the middle is a misread line, and one take can only be
    fixed by re-rendering it (another seed) or rewording the line. Spelled-out letters ("Q R") come back from whisper
    as one word, so expect a harmless mismatch there.
50. **Measure the sync of the file people actually hear.** Re-transcribe the FINAL audio, find each chunk's first word,
    compare with the cue sheet. On a 70-chunk take: mean 0.12 s, median 0.06 s, worst 1.5 s, 20 chunks over 150 ms.
    Whisper reports the first word of a file at 0.0 whatever comes before it. Promise 150 ms, not 50, for a one-take
    voice; if exact cues matter, use a voice service that returns timestamps (cloud-voice.md).
51. **Two texts per sentence: what the viewer reads and what the voice says.** Captions keep the real spelling; the
    spoken form carries respellings, spelled-out acronyms and numbers and clock times as words. Keep the map in a file,
    not in code, so a new script does not mean editing a script. Quotation marks are never spoken.
52. **One caption splitter, one width.** The cue sheet, the SRT, the page and the proof all use the same function
    (clauses first, then balanced wraps, at most about 70 characters, timed by character share inside a chunk). Two
    copies with different widths drifted apart.
53. **Audit text size after the camera scale.** A label that is 28 px on the stage is 17 px when the camera pulls back.
    Measure the drawn size of every visible text at every proof still; 24 px is a workable floor for a 1080p explainer
    that is watched on a laptop or a phone, bigger for the line the viewer must read.
54. **Hide a label that the frame cuts off.** In a close-up a label half outside the frame reads as a bug; the engine
    hides any label that touches the frame edge and shows it again when the camera moves.
55. **One shared sprite set and a camera, not a new drawing per shot.** Build one world, move a camera over it with a
    queue of eased moves that can follow a token, and size every sprite to its largest on-screen height times the
    largest zoom. Place sprites by centre x and bottom y after trimming to the alpha box.
56. **Attach references and restate the character in words.** For a recurring character, attach the approved sheet
    to every image request and also write the character out in the prompt: references carry pose, words carry identity.
    Keep every prompt in the project so one sprite can be redone later with the same words.
57. **Never hard-code the machine.** A render script that names one person's Playwright folder and one Chrome path
    works once. Look up Playwright from an argument, an environment variable or the usual module paths, and the
    browser from an argument, a variable or the usual install locations.
58. **Keep the frames of a long render, and keep the final encode command.** A resumable render (skip frames that
    exist) survives an interruption; the mux command goes in the project, because a final encode whose command was
    not saved had to be rediscovered. Prefer PNG frames, or JPEG at 92 or higher: a JPEG at 90 is lossy before the
    encoder even starts.
59. **One page, three outputs.** The same page, driven by time, makes the interactive file, the frames for the MP4 and
    a hero still for a post card. Keep the hero a function of the page (park at a chosen time, enlarge the labels), never
    a separate drawing that can fall out of date.
60. **Read the narration cold before you build to it.** A reviewer who sees only the narration text, with no visuals,
    finds the term used before it was defined and the claim the picture was quietly carrying.
61. **Never assume the sample rate of a supplied take.** A wav read as 24 kHz that is really 48 kHz plays an octave low
    and twice as long, yet its pace, duration and cues all look plausible. Read the rate from the file and resample, or
    refuse; test with the same take at two rates.
62. **A check that uses the same model as the build cannot see that model's bias.** Whisper word times lead the real
    sound after a long silence by 0.1 to 0.5 s, and a second whisper pass agrees with the first. Measure the scene
    openings, which animation hangs on, against speech onsets from silence detection, and snap the cue to them.
63. **A cap is only real when it is measured on the finished file.** A planned gap says nothing about a pause the voice
    made inside a scene, or about the silence a cut keeps after the last word. Shorten inner pauses, count kept pads, and
    read the longest silence off the final audio.
64. **A resumable render needs a fingerprint.** Frames from an older page, another frame rate or an interrupted write
    must never be reused or swept into the encode: write each frame under a temporary name, stamp the folder with the
    page hash and settings, limit the encode to the wanted frame count and check the count afterwards.
65. **Straight lines lose filter effects that use a percentage region.** A filter region measured against the bounding box
    of a perfectly horizontal line has zero height and draws nothing. Give shared filters a fixed user-space region.
66. **A privacy check that skips part of a line is not a check.** Generated pages put a whole cue sheet on one line: scan
    every line in full (dropping only base64 payloads) and fail when there is no names list to check against.

## Time, from the two runs

| Step | Time |
|---|---|
| Voice setup + 3 candidates | about 10 min |
| 33 lines rendered | about 3 min |
| Interactive explainer, first run (incl. two style resets) | about 40 min; a repeat 25-35 min |
| App capture, first round | about 70 min (a second round of 9 flows took longer) |
| Design + edit by the strongest model | about 30-35 min per cut |
| Frame render, about 2:45 at 1080p30, 10 workers | about 6 min; full rebuild about 10 min |
