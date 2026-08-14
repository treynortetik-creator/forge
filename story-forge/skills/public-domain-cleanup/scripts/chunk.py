#!/usr/bin/env python3
"""
chunk.py -- Split public-domain text files into ~N-word chunks for multi-pass cleanup.

Adapted from story-forge/skills/de-sloppifier/scripts/chunk.py.
Default target is 1000 words (matching the original n8n automation).

MODES
-----
split      Split a text file into chunks on paragraph boundaries.
           Never cuts mid-sentence. Writes numbered chunk files OR prints
           them with delimiter markers.

reassemble Stitch numbered chunk files back into a single output file.

USAGE
-----
Split to files:
    python3 chunk.py split source.txt --output-dir ./chunks/

Split and print with delimiters (useful for piping):
    python3 chunk.py split source.txt --print

Custom chunk size:
    python3 chunk.py split source.txt --words 1200 --output-dir ./chunks/

Reassemble:
    python3 chunk.py reassemble ./chunks-cleaned/ --output cleaned.md
    python3 chunk.py reassemble ./chunks-cleaned/ --print

CHUNK BOUNDARIES
----------------
The chunker splits on paragraph boundaries (double newlines). When a
paragraph pushes the current chunk past the target word count, it closes
the current chunk at that boundary and starts a new one. Chunks may run
slightly over or under the target -- a complete paragraph is always kept
together.

If a single paragraph exceeds the target word count (rare in prose), it is
kept in one chunk rather than split mid-paragraph.
"""

import argparse
import os
import re
import sys
from pathlib import Path


CHUNK_DELIMITER = "--- CHUNK {index} ({words} words) ---"
CHUNK_FILE_PATTERN = "chunk_{index:03d}.md"


def count_words(text: str) -> int:
    """Count whitespace-separated words in a string."""
    return len(text.split())


def split_into_paragraphs(text: str) -> list:
    """
    Split text into paragraphs on double-newline boundaries.
    Returns a list of strings including the separator tokens so the text
    can be reconstructed exactly.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"(\n\s*\n)", text)
    return parts


def build_chunks(text: str, target_words: int = 1000) -> list:
    """
    Split text into chunks of approximately target_words words.
    Splits on paragraph boundaries only -- never mid-sentence or mid-paragraph.

    Returns a list of dicts with keys:
        index  (int, 1-based)
        text   (str)
        words  (int)
    """
    parts = split_into_paragraphs(text)

    chunks = []
    current_parts = []
    current_words = 0
    chunk_index = 1

    for part in parts:
        # Blank-line separators: collect but do not count toward word total.
        if re.match(r"^\n\s*\n$", part):
            current_parts.append(part)
            continue

        part_words = count_words(part)
        current_parts.append(part)
        current_words += part_words

        # When we hit or exceed the target, close this chunk.
        if current_words >= target_words:
            chunk_text = "".join(current_parts).strip()
            chunks.append({
                "index": chunk_index,
                "text": chunk_text,
                "words": count_words(chunk_text),
            })
            chunk_index += 1
            current_parts = []
            current_words = 0

    # Remaining content becomes the final chunk.
    if current_parts:
        leftover = "".join(current_parts).strip()
        if leftover:
            chunks.append({
                "index": chunk_index,
                "text": leftover,
                "words": count_words(leftover),
            })

    return chunks


def cmd_split(args: argparse.Namespace) -> None:
    """Handle the 'split' subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    chunks = build_chunks(text, target_words=args.words)

    if not chunks:
        print("WARNING: no content found in input file.", file=sys.stderr)
        return

    if args.print:
        for chunk in chunks:
            header = CHUNK_DELIMITER.format(index=chunk["index"], words=chunk["words"])
            print(f"\n{header}\n")
            print(chunk["text"])
        print()
    else:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for chunk in chunks:
            filename = CHUNK_FILE_PATTERN.format(index=chunk["index"])
            out_path = output_dir / filename
            out_path.write_text(chunk["text"] + "\n", encoding="utf-8")
            print(f"Wrote {out_path}  ({chunk['words']} words)")
        print(f"\n{len(chunks)} chunk(s) written to {output_dir}/")


def cmd_reassemble(args: argparse.Namespace) -> None:
    """Handle the 'reassemble' subcommand."""
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"ERROR: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    chunk_files = sorted(
        [f for f in source_dir.iterdir() if re.match(r"chunk_\d+\.", f.name)],
        key=lambda f: int(re.match(r"chunk_(\d+)\.", f.name).group(1)),
    )

    if not chunk_files:
        print(f"ERROR: no chunk files found in {source_dir}", file=sys.stderr)
        sys.exit(1)

    parts = []
    for cf in chunk_files:
        content = cf.read_text(encoding="utf-8").rstrip()
        parts.append(content)

    assembled = "\n\n".join(parts) + "\n"

    if args.print:
        print(assembled)
    else:
        output_path = Path(args.output)
        output_path.write_text(assembled, encoding="utf-8")
        print(f"Reassembled {len(chunk_files)} chunk(s) -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split public-domain text into ~N-word chunks for cleanup, or reassemble them.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # split subcommand
    split_parser = subparsers.add_parser(
        "split",
        help="Split a text file into chunks on paragraph boundaries.",
    )
    split_parser.add_argument("input", help="Path to the input text or Markdown file.")
    split_parser.add_argument(
        "--words",
        type=int,
        default=1000,
        metavar="N",
        help="Target words per chunk (default: 1000). Chunks may run slightly over.",
    )

    split_output = split_parser.add_mutually_exclusive_group(required=True)
    split_output.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Directory to write numbered chunk files (chunk_001.md, etc.).",
    )
    split_output.add_argument(
        "--print",
        action="store_true",
        help="Print chunks to stdout with delimiter markers instead of writing files.",
    )

    # reassemble subcommand
    reassemble_parser = subparsers.add_parser(
        "reassemble",
        help="Stitch numbered chunk files back into a single output.",
    )
    reassemble_parser.add_argument(
        "source_dir",
        help="Directory containing chunk_NNN.md files.",
    )

    reassemble_output = reassemble_parser.add_mutually_exclusive_group(required=True)
    reassemble_output.add_argument(
        "--output",
        metavar="FILE",
        help="Path to write the reassembled output file.",
    )
    reassemble_output.add_argument(
        "--print",
        action="store_true",
        help="Print reassembled output to stdout.",
    )

    args = parser.parse_args()

    if args.command == "split":
        cmd_split(args)
    elif args.command == "reassemble":
        cmd_reassemble(args)


if __name__ == "__main__":
    main()
