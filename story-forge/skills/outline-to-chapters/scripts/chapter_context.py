#!/usr/bin/env python3
"""
chapter_context.py — Context slicing and wordcount estimation for outline-to-chapters.

MODES
-----
last-words   Extract the last N words from a draft file. Preserves word
             boundaries. Useful for feeding continuity context to the chapter
             generation pipeline (2,000-word or 20,000-word rolling windows).

estimate     Suggest a per-chapter word count target based on scene type, with
             the 1.25x inflation already applied. Scene type is a rough heuristic
             — override with the LLM's Step 4 output if they diverge.

USAGE
-----
Extract last 2,000 words:
    python3 chapter_context.py last-words draft.md --words 2000

Extract last 20,000 words:
    python3 chapter_context.py last-words draft.md --words 20000

Get a heuristic word count target (action scene):
    python3 chapter_context.py estimate --scene-type action

Supported scene types: action, quiet, establishment, climax, dialogue

WORD COUNT INFLATION
--------------------
The pipeline inflates the raw word count target by 1.25 before passing it to
the First Draft step, capped at 6,000. AI models consistently undershoot targets;
the inflation is a systematic correction, not padding. This script returns the
inflated number so the output can feed directly into the prompt.
"""

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Baseline targets (pre-inflation) by scene type.
# These reflect the automation's 1,000-5,000 word range guidance:
# climax and action are punchier; establishment and quiet are expansive.
# ---------------------------------------------------------------------------
_SCENE_BASELINES: dict[str, int] = {
    "action": 1800,
    "climax": 1600,
    "dialogue": 2000,
    "quiet": 2500,
    "establishment": 2800,
}

_INFLATION_FACTOR = 1.25
_INFLATION_CAP = 6000
_ABSOLUTE_MIN = 1000
_ABSOLUTE_MAX = 5000


def apply_inflation(base: int) -> int:
    """Apply the 1.25x inflation and cap at 6,000."""
    raw = base * _INFLATION_FACTOR
    return min(int(raw), _INFLATION_CAP)


def count_words(text: str) -> int:
    """Count whitespace-separated tokens."""
    return len(text.split())


# ---------------------------------------------------------------------------
# last-words command
# ---------------------------------------------------------------------------


def cmd_last_words(args: argparse.Namespace) -> None:
    """Extract the last N words from a draft file and print to stdout."""
    path = Path(args.file)
    if not path.exists():
        # Chapter 1 has no draft file yet -- the skill's own contract says "empty
        # string if this is chapter 1", so absence is a valid state, not an error.
        # Exiting 1 here broke the FIRST command the drafting engine ever runs.
        return

    text = path.read_text(encoding="utf-8")
    normalized = " ".join(text.split())  # collapse all whitespace

    if not normalized:
        # Empty draft: first chapter, no continuity context needed.
        print("")
        return

    words = normalized.split()
    n = args.words
    if n >= len(words):
        # Entire draft is shorter than the window — return everything.
        print(normalized)
        return

    window = " ".join(words[-n:])
    print(window)


# ---------------------------------------------------------------------------
# estimate command
# ---------------------------------------------------------------------------


def cmd_estimate(args: argparse.Namespace) -> None:
    """Print an inflated word count target for a given scene type."""
    scene_type = args.scene_type.lower()
    if scene_type not in _SCENE_BASELINES:
        valid = ", ".join(sorted(_SCENE_BASELINES))
        print(
            f"ERROR: unknown scene type '{scene_type}'. Valid types: {valid}",
            file=sys.stderr,
        )
        sys.exit(1)

    base = _SCENE_BASELINES[scene_type]
    inflated = apply_inflation(base)
    print(
        f"Scene type : {scene_type}\n"
        f"Base target: {base} words  (within the 1,000-5,000 range)\n"
        f"After 1.25x: {inflated} words  (use this as the draft target; capped at {_INFLATION_CAP})"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Context slicing and wordcount estimation for the outline-to-chapters pipeline."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- last-words ---
    lw = subparsers.add_parser(
        "last-words",
        help="Extract the last N words from a draft file (stdout).",
    )
    lw.add_argument("file", help="Path to the draft markdown file.")
    lw.add_argument(
        "--words",
        type=int,
        default=2000,
        metavar="N",
        help="Number of words to return (default: 2000). Use 20000 for the post-draft chronology check.",
    )

    # --- estimate ---
    est = subparsers.add_parser(
        "estimate",
        help="Suggest an inflated word count target for a scene type.",
    )
    est.add_argument(
        "--scene-type",
        required=True,
        metavar="TYPE",
        help=f"Scene type. One of: {', '.join(sorted(_SCENE_BASELINES))}.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "last-words":
        cmd_last_words(args)
    elif args.command == "estimate":
        cmd_estimate(args)


if __name__ == "__main__":
    main()
