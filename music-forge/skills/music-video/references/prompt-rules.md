# Prompt rules that cost money to learn (2026-10-14)

Each of these broke a real paid clip. Image-to-video models copy the first frame and take the prompt literally.

## Describe only what is in the first frame
- A wardrobe item named in the character's look string but absent from the keyframe (a choker) slid onto the character mid-shot. Keep a per-shot look: the look string must match that keyframe, not the character sheet.
- A prop the keyframe lacks gets invented (a microphone appeared in close-ups whose keyframe had none). Either put it in the keyframe or say it is not there.

## No size words in action prompts
- "towering", "huge", "looms over" in an action made a character double in size mid-clip. Describe the action only, and add "same size and proportions throughout; nobody changes size".
- Describing a creature as "huge" is fine in the still prompt; keep it out of the motion prompt.

## Looks, never names
Video models have never heard of your characters. Describe each by appearance every time (the plan's `identities` map does the swap). Name the role, not the person: "the pale vampire guitarist on the left", not a name.

## Count everything
- State the exact head count: "exactly four musicians; no extra people appear".
- State hands: "each character has exactly two arms and two hands". One take gave a guitarist a third hand.
- For multi-character wides, give each character a position and an action, including the ones doing nothing ("the bassist on the right stands with arms crossed, mouth closed").

## Check monster hands in every keyframe
The video model copies the frame. A werewolf drawn with one human hand kept it for the whole clip, so the fix was a keyframe edit, not a reprompt. Before generating, look at every non-human character's hands, ears and mouth in every still. Fix stills with an edit prompt that changes one thing and keeps the rest ("Edit this image. Change only X: <target>. Keep everything else exactly as it is."), saved as a new file.

## The perspective trap
A figure walking or running toward a far doorway shrinks: the model renders the distance as a child-sized adult. Use a tracking shot behind them, or have them take only a few steps away.

## Camera
- Lock the camera on wides ("locked-off, the camera does not pan or move"). Prompted sweeps were mostly ignored and moving cameras invite duplicate characters. Add the move in post (`post_sweep.py`).
- "One continuous shot, no cuts" when a model might jump to a close-up mid-clip.

## Never generate text
Signs, wedding programmes, tags, letters: generate them blank ("the blank areas stay blank; no letters or words appear") and set the type in post (ImageMagick for the artwork, tracked to the surface; see `post.md`).

## Story canon becomes prompt constraints
Keep a running canon list for the video and paste the relevant lines into every shot that involves those characters. Example from one project: "the creature is effortlessly strong; the creator is contemptuous but physically afraid of him". The viewer's notes on story and power dynamics (who looms, who flinches, who comforts whom) turned into canon lines, and every later shot had to obey them.

## Mouths
- Sung shot with several characters: name the singer(s), give every other character "mouth closed" explicitly.
- Mouths that are open in the keyframe stay open for the first second or so. Draw the keyframe with closed mouths, or trim the head of the clip.
