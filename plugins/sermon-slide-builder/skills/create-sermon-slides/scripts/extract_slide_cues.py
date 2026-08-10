#!/usr/bin/env python3
"""Extract SL/Slide cues and nearby context from sermon notes or stdin."""

from __future__ import annotations

import argparse
import sys

from sermon_io import extract_cues, extract_cues_from_text, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract case-insensitive SL/Slide cues from a sermon note."
    )
    parser.add_argument(
        "note",
        nargs="?",
        default="-",
        help="Path to .docx, .doc, .txt, .md, or .pdf; use - for pasted stdin",
    )
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    if args.note == "-":
        result = extract_cues_from_text(sys.stdin.read(), "[stdin pasted text]")
    else:
        result = extract_cues(args.note)
    if result["cue_count"] == 0:
        raise SystemExit("No SL/Slide cues found.")
    write_json(result, args.out)
    if args.out:
        print(f"Extracted {result['cue_count']} slide cues to {args.out}")


if __name__ == "__main__":
    main()
