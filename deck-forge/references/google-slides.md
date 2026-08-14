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
| Slide transition | no | — | dropped |
| Embedded video | no | — | dropped |

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

## Sources

Practitioner documentation, consistent with each other and with direct testing:

- BrightCarbon, converting PowerPoint to Google Slides —
  <https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/>
- think-cell KB0224 —  <https://www.think-cell.com/en/resources/kb/0224>
- SlideModel, PowerPoint/Slides compatibility —
  <https://slidemodel.com/fix-compatibility-powerpoint-google-slides/>

Verified 2026-08-14. Re-check before treating any row as current; Google changes the
importer without announcement.
