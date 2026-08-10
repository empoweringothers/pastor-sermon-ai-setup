#!/usr/bin/env python3
"""Extract SL/Sl slide cues and nearby context from sermon notes."""

from __future__ import annotations

import argparse

from sermon_io import extract_cues, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract case-insensitive SL slide cues from a sermon note."
    )
    parser.add_argument("note", help="Path to .docx, .doc, .txt, .md, or .pdf note")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    result = extract_cues(args.note)
    if result["cue_count"] == 0:
        raise SystemExit("No SL/Sl slide cues found.")
    write_json(result, args.out)
    if args.out:
        print(f"Extracted {result['cue_count']} slide cues to {args.out}")


if __name__ == "__main__":
    main()
