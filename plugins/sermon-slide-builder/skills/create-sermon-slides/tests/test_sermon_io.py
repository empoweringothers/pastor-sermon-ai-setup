#!/usr/bin/env python3

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit_slide_fidelity import (  # noqa: E402
    align_cues_to_slides,
    attach_continuation_slides,
    classify_fidelity_status,
    match_metrics,
)
from sermon_io import MARKER_RE  # noqa: E402


class MarkerTests(unittest.TestCase):
    def test_recognizes_known_marker_variants(self) -> None:
        for value in (
            "SL - Main Point",
            "Sl – Main Point",
            "sl: Main Point",
            "Slide — Main Point",
            "3Sl – I Cor. 3:10-15",
            "(SL – 2 Peter theme slide)",
        ):
            with self.subTest(value=value):
                self.assertIsNotNone(MARKER_RE.match(value))

    def test_does_not_treat_prose_beginning_with_si_as_a_marker(self) -> None:
        self.assertIsNone(
            MARKER_RE.match("Since the church is simply a body of believers")
        )


class AlignmentTests(unittest.TestCase):
    def test_keeps_matches_in_order_and_leaves_graphic_opener_unmatched(self) -> None:
        cues = [
            {
                "visible_text_candidate": "First point",
                "contains_media_direction": False,
            },
            {
                "visible_text_candidate": "Second point",
                "contains_media_direction": False,
            },
        ]
        slides = [
            {"slide_number": 1, "text": ""},
            {"slide_number": 2, "text": "First point"},
            {"slide_number": 3, "text": "Second point"},
        ]
        aligned, unmatched = align_cues_to_slides(cues, slides)
        self.assertEqual([(item[0], item[1]) for item in aligned], [(0, 1), (1, 2)])
        self.assertEqual(unmatched, [0])

    def test_attaches_a_split_scripture_continuation(self) -> None:
        cues = [
            {
                "visible_text_candidate": (
                    "In the beginning was the Word and the Word was with God "
                    "and the Word was God the same was in the beginning with God"
                ),
                "contains_media_direction": False,
                "cue_type": "scripture",
            }
        ]
        slides = [
            {
                "slide_number": 1,
                "text": "In the beginning was the Word and the Word was with God",
            },
            {
                "slide_number": 2,
                "text": "and the Word was God the same was in the beginning with God",
            },
        ]
        aligned = [(0, 0, 0.5)]
        continuations, unmatched = attach_continuation_slides(
            cues, slides, aligned, [1]
        )
        self.assertEqual(continuations, {0: [1]})
        self.assertEqual(unmatched, [])


class FidelityStatusTests(unittest.TestCase):
    def test_flags_body_copy_added_beyond_the_slide_cue(self) -> None:
        metrics = match_metrics(
            "Our King has Power.",
            "Our King has Power. Jesus has power to rise from the dead.",
        )
        status = classify_fidelity_status(
            media_only=False,
            cue_type="outline",
            score=float(metrics["score"]),
            metrics=metrics,
            extra_source_fraction=1.0,
        )
        self.assertEqual(status, "source-context-additions-review")


if __name__ == "__main__":
    unittest.main()
