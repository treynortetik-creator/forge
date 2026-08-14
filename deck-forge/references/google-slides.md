# What survives a PowerPoint → Google Slides import

Google **rebuilds** the slide rather than copying it. PowerPoint and Slides store slides
differently, so anything Slides cannot represent is approximated or dropped. That single
mechanism explains every row below.

| Element | Survives | Editable after | Note |
|---|---|---|---|
| Rectangle, rounded rectangle, oval | yes | yes | the safe vocabulary |
| Text box | yes | yes | text stays real text |
| Table | yes | yes | including cell fills |
| Group | yes | yes | ungroups cleanly |
| PNG / JPG image | yes | as an image | no surprises |
| Speaker notes | yes | yes | |
| Hyperlink | yes | yes | |
| **Native chart** | **as a picture** | **no** | the reason this plugin exists |
| Font Google lacks | substituted | yes | metrics shift, layout moves |
| Transition, supported | yes | yes | Dissolve, Fade, Slide L/R, Flip, Cube, Gallery |
| Transition, unsupported | **no** | — | removed with **no substitute**. Morph does not survive |
| Animation, unsupported | **substituted** | yes | usually replaced with Fade |
| Embedded video | ⚠️ unverified | ⚠️ | see the caveat below — do not assert this either way |

## Why the chart cannot be saved

Slides keeps a chart live **only** when it is linked to a Google Sheet, created via
Insert → Chart → From Sheets inside Slides. That creates a Drive-side link between two
Drive objects. An uploaded `.pptx` has no Drive-side link and cannot contain one, so there
is no file you can author that imports as a live chart. It is not a fidelity bug to be
worked around; the target format has no representation for what you are sending.

**Therefore building from shapes is not a stylistic preference. It is the only path to an
editable deck.**

## The trade-off to state out loud

Shape bars are not data-driven. Changing a value means resizing a rectangle and editing its
label. Tell the recipient once, so they come back to you instead of typing over a number
and leaving a bar at the wrong height.

## Two rows that are easy to get wrong

**Transitions and animations follow opposite rules.** An unsupported transition is *removed*;
an unsupported animation is *substituted*. A single "breaks on import" line is wrong about one
of them no matter which behaviour it picks. An earlier version of this file had exactly that.

⚠️ **This topic has a contaminated search surface.** Several well-ranking pages invent Google
Slides transition names that do not exist ("Bounce", "Turn on a Cube", "Whip", "Zoom",
"Glitch", "Ripple"), and at least one search summariser asserts Push and Wipe support, which
is false. Google does not publish the transition list itself. Treat any transition claim
without a first-hand observation as unreliable — including the one above.

⚠️ **The embedded-video row is NOT verified.** The structural argument is that Slides' `Video`
element accepts only `YOUTUBE` and `DRIVE` sources, so a package-embedded mp4 has nowhere to
land. That is a good argument, not an observation, and it is passed through here as such.

⚠️ **Uploading via Drive is not a safe "lossless" path.** think-cell KB0224 records that the
issues occur "both in opening files in Google directly, and in saving the file in the Google
format", and documents irreversible destruction on that path. Opening a `.pptx` in Slides is
not a read-only operation.

**The cheap way to close all of this** is about ten minutes of empirical testing: build a
one-slide-per-feature `.pptx` (Fade, Push, Wipe, Morph, Dissolve, Cube; plus a native chart,
an embedded video, a group, and a table with cell fills), upload it both ways, read the
Transition panel per slide, and click the chart and video to see what they became. **Nobody
has run it.** Until someone does, the ⚠️ rows stay marked.

## Sources

**Primary, for the chart row:** the Slides API `presentations.pages` reference, which
documents that there is no native chart `PageElement` type and that unlinked charts are
represented as images — <https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations.pages>
(page last updated 2026-02-24, so this describes the current data model, not an archival one).

Corroborating practitioner sources, demoted from primary:

- BrightCarbon, converting PowerPoint to Google Slides —
  <https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/>
  (publication date reported inconsistently as 2021 and 2023; either way it predates this
  file's verification stamp by years)
- think-cell KB0224 —  <https://www.think-cell.com/en/resources/kb/0224>
- SlideModel, PowerPoint/Slides compatibility —
  <https://slidemodel.com/fix-compatibility-powerpoint-google-slides/>

Chart row verified 2026-08-14 against the primary source above. **The transition, animation
and video rows are NOT equally verified** — the ⚠️ marks are load-bearing, and a single
"Verified" stamp across the whole table would overstate what is actually known. Re-check
before treating any row as current; Google changes the importer without announcement.
