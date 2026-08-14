#!/usr/bin/env python3
"""
parse_chapters.py — Split a manuscript into chapters for the book-summarizer skill.

Accepts a manuscript file (Markdown, plain text, or HTML) and outputs a JSON array
of chapter objects: [{"title": "Chapter 1", "content": "..."}]

Supports three split strategies (tried in order):
  1. Markdown H1 headers:  # Chapter Title
  2. HTML <h1> tags:       <h1>Chapter Title</h1>
  3. Bare "Chapter N" lines: Chapter 1, Chapter One, CHAPTER 1, etc.

Usage:
  python3 parse_chapters.py manuscript.md
  python3 parse_chapters.py manuscript.html --output chapters.json
  python3 parse_chapters.py manuscript.txt --strategy html

Arguments:
  file         Path to the manuscript file.
  --output     Write JSON to this path instead of stdout.
  --strategy   Force a split strategy: auto (default), markdown, html, bare.
  --min-chars  Minimum content length to include a chapter (default: 100).
"""

import argparse
import json
import re
import sys
from pathlib import Path


def split_markdown(text: str) -> list[dict]:
    """Split on Markdown H1 lines (# Title)."""
    pattern = re.compile(r"^#{1,6}[ \t]+(.+)$", re.MULTILINE)
    return _split_by_matches(text, pattern)


def split_html(text: str) -> list[dict]:
    """Split on <h1>...</h1> tags (strips inner HTML)."""
    # Normalize HTML entities first
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    pattern = re.compile(r"<h1\b[^>]*>([\s\S]*?)<\/h1>", re.IGNORECASE)

    def clean_title(raw: str) -> str:
        return re.sub(r"<[^>]+>", "", raw).strip()

    matches = list(pattern.finditer(text))
    if not matches:
        return []

    chapters = []
    for i, match in enumerate(matches):
        title = clean_title(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw_content = text[start:end]
        # Strip HTML tags from body
        content = re.sub(r"<[^>]+>", " ", raw_content)
        content = re.sub(r"\s+", " ", content).strip()
        chapters.append({"title": title, "content": content})
    return chapters


def split_bare(text: str) -> list[dict]:
    """Split on bare 'Chapter N' / 'Chapter One' lines."""
    pattern = re.compile(
        r"^#{0,6}[ \t]*(chapter[ \t]+(?:\d+|[a-z]+(?:[ \t]+[a-z]+)?))[ \t]*.*$",
        re.IGNORECASE | re.MULTILINE,
    )
    return _split_by_matches(text, pattern)


def _split_by_matches(text: str, pattern: re.Pattern) -> list[dict]:
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    chapters = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        chapters.append({"title": title, "content": content})
    return chapters


def detect_strategy(text: str) -> str:
    if re.search(r"^#{1,6}[ \t]+\S", text, re.MULTILINE):
        return "markdown"
    if re.search(r"<h1\b", text, re.IGNORECASE):
        return "html"
    if re.search(r"^chapter\s+[\d\w]", text, re.IGNORECASE | re.MULTILINE):
        return "bare"
    return "markdown"  # fallback: try markdown (will return [] if nothing found)


def _pos(v, name):
    n = int(v)
    if n <= 0:
        raise SystemExit(f"ERROR: --{name} must be a positive integer (got {n})")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a manuscript into chapters as JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", type=Path, help="Path to the manuscript file.")
    parser.add_argument(
        "--output", type=Path, default=None, help="Write JSON to this path (default: stdout)."
    )
    parser.add_argument(
        "--strategy",
        choices=["auto", "markdown", "html", "bare"],
        default="auto",
        help="Chapter-split strategy (default: auto-detect).",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=100,
        help="Minimum content character count to include a chapter (default: 100).",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    text = args.file.read_text(encoding="utf-8", errors="replace")

    strategy = args.strategy if args.strategy != "auto" else detect_strategy(text)

    splitters = {"markdown": split_markdown, "html": split_html, "bare": split_bare}
    chapters = splitters[strategy](text)

    if not chapters and args.strategy in (None, 'auto'):
        # If primary strategy found nothing, try the others in order
        for name, fn in splitters.items():
            if name == strategy:
                continue
            chapters = fn(text)
            if chapters:
                break

    # Filter short chapters
    chapters = [c for c in chapters if len(c["content"]) >= args.min_chars]

    if not chapters:
        print("ERROR: no chapters found. Check file format or try --strategy.", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(chapters, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote {len(chapters)} chapter(s) to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
