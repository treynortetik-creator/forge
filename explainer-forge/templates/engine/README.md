# Engine

One 1920x1080 stage, one paused GSAP timeline, a list of per-frame updaters. Everything on screen is a function of the
AUDIO time, so live playback, scrubbing, stills and the frame-by-frame render agree.

| File | What |
|---|---|
| `page.html` | the shell with placeholders; `scripts/build_explainer.py` fills it |
| `engine.css` | stage, plaque, pill tags, caption bar with safe areas (`--safe-x`, `--safe-top`, `--cap-bottom`), player bar, `?render` mode. Neutral light palette in tokens |
| `filters.svg.html` | `grain` (paper tooth), `clay` (soft surface noise), `emboss`, `soft` |
| `engine.js` | helpers and the player (API in its header comment) |

API in one table (all in `engine.js`):

| Group | Names |
|---|---|
| time | `S(id)` `E(id)` `SC(n)` `SE(n)` `DUR`, `tl` (GSAP timeline), `UPD.push(t => ...)` per-frame updater |
| sprites | `sprite(parent, name, x, y, h, opts)` centre-x, bottom-y; `el`, `svgAbs`, `mark` |
| motion | `pop` `fade` `swap` `squash` `popIn` `hideAt` `show` `hide` `tagAt` + `tagPop` |
| belt | `track(path)`, `belt(parent, tracks, opts)` returns `t => ...` for `UPD` |
| token | `Tok(parent, kind, scale, {bad})`: `.ride` `.hop` `.loop` `.key` `.posAt` |
| camera | `cam(t, dur, zoom, x, y, follow?)` on `#world`, `worldOn(a, b)` |
| captions | `capHigh(a, b)` lifts the bar; `guardEdges(() => elements)` hides labels the frame cuts off |
| output | `window.__ready` `__total` `__seek(t)` `__cues` `__hero(t?)`; `?render` bare stage; `#t=42` park |

Scene markup is one `<section class="scene" id="scN">` per cue scene (crossfaded automatically; set
`window.EF_NO_AUTOFADE = true` first to do it yourself). Put a persistent camera set in `<div id="world">`.
Do not edit the engine per project: theme through `theme.css`, behaviour through your `scenes.js`.
