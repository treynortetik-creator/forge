#!/usr/bin/env node
// copy-gate.js — deterministic slop gate. No model, no network, no cost.
//
// Catches the single most common failure of a model that read the brief but
// performed none of it: the page NARRATING ITS OWN CONCEPT to the visitor
// instead of just doing it. Real brands don't ship reading instructions.
// A site that says "HOW TO READ THIS PAGE — it is one continuous descent"
// has described the brief in place of building it.
//
// Also catches placeholder text and hand-drawn stand-ins for real brand logos.
//
//   node copy-gate.js <path-to-index.html> [more.html ...]
//
// Exit 0 = clean. Exit 1 = defects found (never publish).

const fs = require("node:fs");

const RULES = [
  // --- meta-narration: the page explaining itself ---
  [/how\s+to\s+read\s+this\s+(page|site)/i, "tells the visitor how to read the page"],
  [/\bas\s+you\s+scroll\b/i, "narrates the scroll instead of performing it"],
  [/\b(keep|continue)\s+scrolling\b/i, "instructs the visitor to scroll"],
  [/\bscroll\s+(down|on|further)\b/i, "instructs the visitor to scroll"],
  [/\bscroll\s+to\s+(begin|start|continue|explore)\b/i, "scroll-prompt copy"],
  [/this\s+(page|site|website)\s+(is|was|will|shows|explains|tells)/i, "page refers to itself"],
  [/\b(one\s+)?continuous\s+(descent|scroll|journey)\b/i, "describes the mechanic as copy"],

  // --- camera narration: the page describing the SHOT instead of selling ---
  // The world brief describes the film in vivid prose because it is production
  // guidance. That language must not be paraphrased into visitor-facing copy.
  // The visitor is then reading a shot list. Test: someone who cannot see the
  // film at all must still read every line as advertising for the product.
  [/\beverything\s+(before|after)\s+(this\s+)?(was|is)\s+\w+/i, "narrates the camera's arc"],
  [/\b(the\s+)?(pull[-\s]?back|push[-\s]?in|dolly|tilt|pan|crane|tracking\s+shot)\b/i,
   "names a camera move in visitor-facing copy"],
  [/\b(looking|gazing)\s+(up|down|through|inside)\b/i, "narrates where the camera points"],
  [/\b(past|through|into|inside)\s+the\s+(bubbles?|glass|liquid|frame|structure|interior)\b/i,
   "narrates what the camera passes"],
  [/\b(descent|ascent|retreat|reveal)\b(?![\w-])/i, "shot-list vocabulary as copy"],
  [/\bone\s+(continuous\s+)?(take|shot|move)\b/i, "describes the filmmaking"],
  [/\b(frame|camera|lens|shot)\s+(narrows|widens|holds|rests|settles|comes to rest)\b/i,
   "describes the frame instead of the brand"],

  // --- placeholder text ---
  [/lorem\s+ipsum/i, "lorem ipsum placeholder"],
  [/\b(placeholder|TODO|TBD|FIXME|XXX)\b/, "placeholder marker left in copy"],
  [/\byour\s+(headline|text|copy|tagline)\s+here\b/i, "template placeholder"],
];

// A real brand logo is fetched as SVG. A <svg> whose only child is a circle or
// a polygon, sitting next to a brand name, is a hand-drawn approximation.
const FAKE_LOGO = /<svg[^>]*>\s*<(circle|polygon|path\s+d="M\s*\d+\s*[,\s]\d+\s*L)[^>]*\/?>\s*<\/svg>/i;

// The film's own frames must never be re-served as static <img> in the content
// below it. The canvas already ends the scroll on the payoff frame; dropping the
// same frame in again as decorative section art shows the visitor one picture
// twice in a row and throws away the ending.
const REUSED_FRAME = /<img[^>]+src="[^"]*frames?\/f?_?\d{3,4}\.(jpg|jpeg|png|webp)"/i;

// Strip <script>/<style> so we only judge what a visitor can actually read.
const visibleText = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<!--[\s\S]*?-->/g, " ");

let failed = false;
const files = process.argv.slice(2);

if (!files.length) {
  console.error("usage: node copy-gate.js <path-to-index.html> [more.html ...]");
  process.exit(2);
}

for (const file of files) {
  let html;
  try {
    html = fs.readFileSync(file, "utf8");
  } catch (e) {
    console.error(`✗ ${file} — cannot read: ${e.message}`);
    failed = true;
    continue;
  }

  const text = visibleText(html);
  const hits = [];

  for (const [re, why] of RULES) {
    const m = re.exec(text);
    if (!m) continue;
    const line = text.slice(0, m.index).split("\n").length;
    const snippet = text
      .slice(Math.max(0, m.index - 40), m.index + m[0].length + 40)
      .replace(/<[^>]+>/g, "")
      .replace(/\s+/g, " ")
      .trim();
    hits.push(`  line ${line}: ${why}\n    …${snippet}…`);
  }

  if (FAKE_LOGO.test(html)) {
    hits.push("  hand-drawn <svg> stand-in where a real brand logo belongs");
  }

  const reused = REUSED_FRAME.exec(html);
  if (reused) {
    hits.push(
      `  a film frame is re-served as a static <img> below the film:\n    ${reused[0].slice(0, 100)}\n` +
        "    the scroll already ends on that frame — this shows it twice and kills the payoff",
    );
  }

  if (hits.length) {
    failed = true;
    console.error(`✗ ${file} — ${hits.length} copy defect(s)\n${hits.join("\n")}`);
  } else {
    console.log(`✓ ${file} — copy clean`);
  }
}

if (failed) {
  console.error(
    "\nFAIL. The page is describing itself instead of being itself.\n" +
      "Rewrite the copy to sell the brand. Do not add the mechanic as a label —\n" +
      "if the scroll works, the visitor does not need to be told it works.",
  );
  process.exit(1);
}
