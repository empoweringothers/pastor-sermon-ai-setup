#!/usr/bin/env python3
"""Compare sermon SL cues with visible text in a PowerPoint deck."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
from pathlib import Path
import sys
from typing import Any

from sermon_io import (
    extract_cues,
    extract_pptx_slides,
    normalize_for_match,
    pptx_metadata,
    read_note_paragraphs,
    write_json,
)


def match_metrics(cue_text: str, slide_text: str) -> dict[str, float | int]:
    cue = normalize_for_match(cue_text)
    slide = normalize_for_match(slide_text)
    if not cue or not slide:
        return {
            "score": 0.0,
            "sequence_similarity": 0.0,
            "cue_coverage": 0.0,
            "slide_extra_token_count": 0,
            "slide_extra_token_ratio": 0.0,
        }
    sequence = SequenceMatcher(None, cue, slide).ratio()
    cue_tokens = set(cue.split())
    slide_tokens = set(slide.split())
    containment = len(cue_tokens & slide_tokens) / max(1, len(cue_tokens))
    extra_count = len(slide_tokens - cue_tokens)
    return {
        "score": max(sequence, containment),
        "sequence_similarity": sequence,
        "cue_coverage": containment,
        "slide_extra_token_count": extra_count,
        "slide_extra_token_ratio": extra_count / max(1, len(cue_tokens)),
    }


def similarity(cue_text: str, slide_text: str) -> float:
    return float(match_metrics(cue_text, slide_text)["score"])


def classify_fidelity_status(
    *,
    media_only: bool,
    cue_type: str,
    score: float,
    metrics: dict[str, float | int],
    extra_source_fraction: float,
) -> str:
    substantial_additions = (
        int(metrics["slide_extra_token_count"]) >= 4
        and float(metrics["slide_extra_token_ratio"]) >= 0.6
        and float(metrics["cue_coverage"]) >= 0.6
    )

    if media_only and score < 0.45:
        return "media-only-review"
    if cue_type == "scripture" and (score < 0.9 or substantial_additions):
        return "scripture-review"
    if substantial_additions and extra_source_fraction >= 0.65:
        return "source-context-additions-review"
    if substantial_additions:
        return "unattributed-additions-review"
    if score >= 0.72:
        return "strong"
    if score >= 0.45:
        return "review"
    return "missing-or-rewritten"


def align_cues_to_slides(
    cues: list[dict[str, Any]], slides: list[dict[str, Any]]
) -> tuple[list[tuple[int, int | None, float]], list[int]]:
    """Order-preserving alignment with room for extra or missing slides."""

    cue_count = len(cues)
    slide_count = len(slides)
    skip_cue_penalty = -0.12
    skip_slide_penalty = -0.08
    scores = [
        [
            similarity(
                str(cue["visible_text_candidate"]),
                str(slide["text"]),
            )
            for slide in slides
        ]
        for cue in cues
    ]

    dp = [[float("-inf")] * (slide_count + 1) for _ in range(cue_count + 1)]
    back: list[list[str | None]] = [
        [None] * (slide_count + 1) for _ in range(cue_count + 1)
    ]
    dp[0][0] = 0.0
    for cue_index in range(1, cue_count + 1):
        dp[cue_index][0] = cue_index * skip_cue_penalty
        back[cue_index][0] = "skip-cue"
    for slide_index in range(1, slide_count + 1):
        dp[0][slide_index] = slide_index * skip_slide_penalty
        back[0][slide_index] = "skip-slide"

    for cue_index in range(1, cue_count + 1):
        cue = cues[cue_index - 1]
        normalized_tokens = normalize_for_match(
            str(cue["visible_text_candidate"])
        ).split()
        media_only = bool(cue["contains_media_direction"]) and len(
            normalized_tokens
        ) <= 4
        for slide_index in range(1, slide_count + 1):
            raw_score = scores[cue_index - 1][slide_index - 1]
            media_bonus = 0.22 if media_only and raw_score < 0.45 else 0.0
            choices = {
                "match": dp[cue_index - 1][slide_index - 1]
                + raw_score
                - 0.35
                + media_bonus,
                "skip-cue": dp[cue_index - 1][slide_index] + skip_cue_penalty,
                "skip-slide": dp[cue_index][slide_index - 1]
                + skip_slide_penalty,
            }
            operation = max(choices, key=choices.get)
            dp[cue_index][slide_index] = choices[operation]
            back[cue_index][slide_index] = operation

    aligned: list[tuple[int, int | None, float]] = []
    unmatched_slides: list[int] = []
    cue_index = cue_count
    slide_index = slide_count
    while cue_index > 0 or slide_index > 0:
        operation = back[cue_index][slide_index]
        if operation == "match":
            aligned.append(
                (
                    cue_index - 1,
                    slide_index - 1,
                    scores[cue_index - 1][slide_index - 1],
                )
            )
            cue_index -= 1
            slide_index -= 1
        elif operation == "skip-cue":
            aligned.append((cue_index - 1, None, 0.0))
            cue_index -= 1
        elif operation == "skip-slide":
            unmatched_slides.append(slide_index - 1)
            slide_index -= 1
        else:
            break

    aligned.reverse()
    unmatched_slides.reverse()
    return aligned, unmatched_slides


def attach_continuation_slides(
    cues: list[dict[str, Any]],
    slides: list[dict[str, Any]],
    aligned: list[tuple[int, int | None, float]],
    unmatched_slide_indexes: list[int],
) -> tuple[dict[int, list[int]], list[int]]:
    """Attach approved-looking split continuations to long or Scripture cues.

    The primary alignment remains one cue to one anchor slide. This pass accepts
    only contiguous unmatched slides after that anchor when their combined text
    materially improves coverage of the same cue.
    """

    unmatched = set(unmatched_slide_indexes)
    continuations: dict[int, list[int]] = {}
    matched_indexes = [item[1] for item in aligned]
    for position, (cue_index, slide_index, _) in enumerate(aligned):
        if slide_index is None:
            continue
        cue_text = str(cues[cue_index]["visible_text_candidate"])
        cue_tokens = normalize_for_match(cue_text).split()
        cue_type = str(cues[cue_index].get("cue_type", ""))
        if cue_type != "scripture" and len(cue_tokens) < 18:
            continue

        next_anchor = len(slides)
        for later_index in matched_indexes[position + 1 :]:
            if later_index is not None:
                next_anchor = later_index
                break

        candidates: list[int] = []
        cursor = slide_index + 1
        while cursor < next_anchor and cursor in unmatched and len(candidates) < 5:
            candidates.append(cursor)
            cursor += 1
        if not candidates:
            continue

        base_text = str(slides[slide_index]["text"])
        base_metrics = match_metrics(cue_text, base_text)
        base_score = float(base_metrics["score"])
        base_coverage = float(base_metrics["cue_coverage"])
        best: list[int] = []
        best_score = base_score
        best_coverage = base_coverage
        for length in range(1, len(candidates) + 1):
            selected = candidates[:length]
            combined = " ".join(
                [base_text, *(str(slides[index]["text"]) for index in selected)]
            )
            metrics = match_metrics(cue_text, combined)
            score = float(metrics["score"])
            coverage = float(metrics["cue_coverage"])
            materially_better = (
                coverage >= base_coverage + 0.15
                or score >= base_score + 0.08
                or (coverage >= 0.9 and coverage > base_coverage)
            )
            if materially_better and (coverage, score) > (best_coverage, best_score):
                best = selected
                best_score = score
                best_coverage = coverage
        if best:
            continuations[cue_index] = best
            unmatched.difference_update(best)

    return continuations, sorted(unmatched)


def audit(note: str, deck: str) -> dict[str, object]:
    extracted = extract_cues(note)
    cues = extracted["cues"]
    note_paragraphs = read_note_paragraphs(note)
    slides = extract_pptx_slides(deck)
    aligned, unmatched_slide_indexes = align_cues_to_slides(cues, slides)
    continuation_map, unmatched_slide_indexes = attach_continuation_slides(
        cues, slides, aligned, unmatched_slide_indexes
    )
    matches: list[dict[str, object]] = []

    for cue_index, slide_index, score in aligned:
        cue = cues[cue_index]
        media_only = bool(cue["contains_media_direction"]) and len(
            normalize_for_match(str(cue["visible_text_candidate"])).split()
        ) <= 4

        continuation_indexes = continuation_map.get(cue_index, [])
        if slide_index is not None:
            slide = slides[slide_index]
            matched_slide_indexes = [slide_index, *continuation_indexes]
            combined_slide_text = " ".join(
                str(slides[index]["text"]) for index in matched_slide_indexes
            )
        else:
            slide = {"slide_number": None, "text": ""}
            matched_slide_indexes = []
            combined_slide_text = ""

        metrics = match_metrics(
            str(cue["visible_text_candidate"]), combined_slide_text
        )
        score = float(metrics["score"])
        next_paragraph_number = (
            int(cues[cue_index + 1]["paragraph_number"])
            if cue_index + 1 < len(cues)
            else len(note_paragraphs) + 1
        )
        source_block = " ".join(
            note_paragraphs[
                int(cue["paragraph_number"]) : next_paragraph_number - 1
            ]
        )
        cue_tokens = set(
            normalize_for_match(str(cue["visible_text_candidate"])).split()
        )
        slide_tokens = set(normalize_for_match(combined_slide_text).split())
        source_block_tokens = set(normalize_for_match(source_block).split())
        extra_tokens = slide_tokens - cue_tokens
        extra_source_fraction = (
            len(extra_tokens & source_block_tokens) / len(extra_tokens)
            if extra_tokens
            else 1.0
        )
        status = classify_fidelity_status(
            media_only=media_only,
            cue_type=str(cue["cue_type"]),
            score=score,
            metrics=metrics,
            extra_source_fraction=extra_source_fraction,
        )

        matches.append(
            {
                "cue_number": cue["cue_number"],
                "paragraph_number": cue["paragraph_number"],
                "source_line": cue["source_line"],
                "matched_slide": slide["slide_number"],
                "matched_slides": [
                    slides[index]["slide_number"] for index in matched_slide_indexes
                ],
                "continuation_slides": [
                    slides[index]["slide_number"] for index in continuation_indexes
                ],
                "slide_text": combined_slide_text,
                "similarity": round(score, 3),
                "sequence_similarity": round(
                    float(metrics["sequence_similarity"]), 3
                ),
                "cue_coverage": round(float(metrics["cue_coverage"]), 3),
                "slide_extra_token_count": metrics["slide_extra_token_count"],
                "extra_tokens_from_source_context": round(
                    extra_source_fraction, 3
                ),
                "status": status,
            }
        )

    status_counts: dict[str, int] = {}
    for match in matches:
        status = str(match["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "note": str(Path(note).expanduser().resolve()),
        "deck": str(Path(deck).expanduser().resolve()),
        "cue_count": len(cues),
        "slide_count": len(slides),
        "deck_metadata": pptx_metadata(deck),
        "status_counts": status_counts,
        "unmatched_deck_slides": [
            slides[index]["slide_number"] for index in unmatched_slide_indexes
        ],
        "matches": matches,
        "interpretation": (
            "Review every non-strong result manually. Source-context additions "
            "may be faithful but were not present in the SL cue. Visual-only cues "
            "may have little text. Contiguous split slides are grouped only when "
            "their combined text materially improves cue coverage. No score "
            "verifies the image or factual source."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit visible PowerPoint text against sermon SL cues."
    )
    parser.add_argument("note", help="Path to sermon note")
    parser.add_argument("deck", help="Path to .pptx")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    result = audit(args.note, args.deck)
    write_json(result, args.out)
    counts = result["status_counts"]
    summary = (
        "Fidelity audit: "
        f"{result['cue_count']} cues / {result['slide_count']} slides; "
        + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    )
    print(summary, file=sys.stdout if args.out else sys.stderr)
    if args.out:
        print(f"Report written to {args.out}")


if __name__ == "__main__":
    main()
