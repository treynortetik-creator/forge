# Style header

`prompt-header.txt` holds the same words for `sprite_prompts.py --header`. Paste it first, unchanged, then the item lines (`items.md`, or `items.json` for the script). Attach the files in `../refs/`. Tested with a command-line
image tool (OpenAI Codex CLI built-in image tool, 2026-11): expect one to three tries for awkward objects.

```text
Use your built-in image generation tool (do not write code to draw anything). STYLE: match style-reference and
station-example exactly: matte soft 3D modelling-clay / plasticine look, chunky rounded forms, visible soft clay
texture with tiny fingerprint-like surface variation, warm palette (cream, terracotta coral, mustard, slate blue, sage,
teal), soft studio light from top-left. Each image is ONE object (or one small group), centered, complete and not
cropped. NO text, letters, numbers or logos anywhere. NO ground shadow and no floor. BACKGROUND: fully transparent
alpha PNG. Generate each image separately at the highest quality and save each as a PNG in the current folder with
exactly the file name given. Do not stop until every file exists. When finished, list the files.
```

If the tool can't do transparency: ask for a perfectly flat pure magenta background (`#FF00FF`, no gradient, no shadow,
no pink in the object) and key it out. We have no script for that; the reference cut never needed it.

Extra lines we add when they apply:

- For buildings and stations: `CAMERA: straight-on front view from slightly above. Fill about 80% of a square frame.`
- For workers: `Robots are small friendly clay worker robots: rounded slate-blue and cream bodies, a rounded screen-face
  with two simple dot eyes, mustard antenna, stubby clay arms with round mitten hands. They are NOT humans.`
- For the guide character: the block in `../../../mascots/ember/MASCOT.md`.
