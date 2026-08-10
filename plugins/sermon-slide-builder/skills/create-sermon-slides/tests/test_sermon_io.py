#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit_slide_fidelity import (  # noqa: E402
    align_cues_to_slides,
    attach_continuation_slides,
    classify_fidelity_status,
    match_metrics,
)
from sermon_io import (  # noqa: E402
    MARKER_RE,
    classify_cue,
    extract_cues_from_text,
    pptx_metadata,
)


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

    def test_extracts_full_records_from_pasted_sl_and_slide_markers(self) -> None:
        sermon = "\n".join(
            (
                "Opening context",
                "SL: First Point",
                "First-point context",
                "Slide: Second Point",
                "(Slide — map of a traditional site)",
            )
        )

        result = extract_cues_from_text(sermon)

        self.assertEqual(result["source_file"], "[pasted text]")
        self.assertEqual(result["paragraph_count"], 5)
        self.assertEqual(result["cue_count"], 3)
        cues = result["cues"]
        self.assertEqual(
            [cue["source_marker"] for cue in cues],
            ["SL", "Slide", "Slide"],
        )
        self.assertEqual(
            [cue["paragraph_number"] for cue in cues],
            [2, 4, 5],
        )
        self.assertEqual(
            [cue["visible_text_candidate"] for cue in cues],
            ["First Point", "Second Point", "map of a traditional site"],
        )
        self.assertEqual(cues[0]["context_before"], ["Opening context"])
        self.assertEqual(cues[0]["context_after"], ["First-point context"])
        self.assertEqual(cues[2]["site_identification_status"], "traditional")
        self.assertEqual(
            cues[2]["visible_uncertainty_label"], "Traditional site"
        )


class CueClassificationTests(unittest.TestCase):
    def test_exposes_each_stable_visual_route_hint(self) -> None:
        cases = (
            (
                "AI realistic image of the empty tomb",
                "ai_illustration",
            ),
            (
                "Use an actual archival photograph of the Garden Tomb",
                "authentic_sourced_image",
            ),
            (
                "Google real images of possible historic tomb locations",
                "authentic_sourced_image",
            ),
            (
                "Use the attached baptism photo",
                "pastor_provided_asset",
            ),
            (
                "Pastor will add the baptism photo later",
                "pastor_supplied_placeholder",
            ),
            (
                "realistic picture of a shepherd beside a lake",
                "automatic",
            ),
        )
        for cue, expected_route in cases:
            with self.subTest(cue=cue):
                result = classify_cue(cue, 2)
                self.assertEqual(result["visual_route_hint"], expected_route)
                self.assertFalse(result["visual_route_conflict_review"])

    def test_realistic_ai_language_remains_one_ai_route(self) -> None:
        for cue in (
            "AI realistic image of a possible location of Jesus' tomb",
            "AI realistic Peter beside Galilee",
        ):
            with self.subTest(cue=cue):
                result = classify_cue(cue, 2)
                self.assertEqual(result["visual_route_hint"], "ai_illustration")
                self.assertFalse(result["visual_route_conflict_review"])
                self.assertTrue(result["contains_media_direction"])

    def test_distinguishes_received_asset_and_future_placeholder(self) -> None:
        received = classify_cue("Use the attached baptism photo", 2)
        needed = classify_cue("Pastor will add the baptism photo later", 2)
        church_needed = classify_cue(
            "Pastor will add the church photo later", 2
        )

        self.assertEqual(received["visual_route_hint"], "pastor_provided_asset")
        self.assertEqual(received["placeholder_status"], "received")
        self.assertEqual(
            needed["visual_route_hint"], "pastor_supplied_placeholder"
        )
        self.assertEqual(needed["placeholder_status"], "needed")
        self.assertEqual(
            church_needed["visual_route_hint"], "pastor_supplied_placeholder"
        )
        self.assertFalse(church_needed["visual_route_conflict_review"])
        self.assertEqual(church_needed["placeholder_status"], "needed")

    def test_exposes_completed_placeholder_states_without_requesting_one(self) -> None:
        replaced = classify_cue("IMAGE NEEDED placeholder replaced", 2)
        waived = classify_cue("No image needed", 2)

        self.assertEqual(replaced["placeholder_status"], "replaced")
        self.assertEqual(replaced["visual_route_hint"], "automatic")
        self.assertEqual(waived["placeholder_status"], "waived")
        self.assertEqual(waived["visual_route_hint"], "automatic")

    def test_returns_conflict_review_for_multiple_explicit_route_families(self) -> None:
        for cue in (
            "Use a real archival photo; AI only if unavailable",
            "AI edit of my church photo",
        ):
            with self.subTest(cue=cue):
                result = classify_cue(cue, 2)
                self.assertEqual(result["visual_route_hint"], "conflict_review")
                self.assertTrue(result["visual_route_conflict_review"])

    def test_exposes_site_status_and_visible_uncertainty_label(self) -> None:
        for cue, expected_status, expected_label in (
            ("photo of a possible tomb site", "possible", "Possible site"),
            (
                "photo of the traditional upper-room site",
                "traditional",
                "Traditional site",
            ),
            ("map of a proposed Mount Sinai site", "proposed", "Proposed site"),
            ("photo of the disputed tomb location", "disputed", "Disputed site"),
        ):
            with self.subTest(cue=cue):
                result = classify_cue(cue, 2)
                self.assertEqual(
                    result["site_identification_status"], expected_status
                )
                self.assertEqual(
                    result["visible_uncertainty_label"], expected_label
                )
                self.assertTrue(
                    result["historical_certainty_review_recommended"]
                )
                self.assertTrue(result["research_review_recommended"])

    def test_infers_authentic_route_for_site_photos_and_maps(self) -> None:
        for cue in (
            "photo of a possible tomb site",
            "map of a proposed Exodus route",
        ):
            with self.subTest(cue=cue):
                result = classify_cue(cue, 2)
                self.assertEqual(
                    result["visual_route_hint"], "authentic_sourced_image"
                )
                self.assertFalse(result["visual_route_conflict_review"])

    def test_exposes_remaining_site_identification_states(self) -> None:
        established = classify_cue("verified location of the tomb", 2)
        unknown = classify_cue("photo of the archaeological site", 2)
        unknown_tomb = classify_cue("photo of the archaeological tomb", 2)
        unrelated = classify_cue("Grace changes everything", 2)

        self.assertEqual(established["site_identification_status"], "established")
        self.assertIsNone(established["visible_uncertainty_label"])
        self.assertEqual(unknown["site_identification_status"], "unknown")
        self.assertIsNone(unknown["visible_uncertainty_label"])
        self.assertEqual(unknown_tomb["site_identification_status"], "unknown")
        self.assertIsNone(unknown_tomb["visible_uncertainty_label"])
        self.assertEqual(
            unrelated["site_identification_status"], "not_applicable"
        )

    def test_realistic_style_is_not_an_authentic_source_request(self) -> None:
        result = classify_cue("realistic picture of a shepherd", 2)
        self.assertEqual(result["visual_route_hint"], "automatic")
        self.assertFalse(result["historical_certainty_review_recommended"])

    def test_does_not_treat_ai_as_an_image_route_when_ai_is_the_topic(self) -> None:
        result = classify_cue("The rise of AI in modern life", 2)
        self.assertEqual(result["visual_route_hint"], "automatic")


class PowerPointMetadataTests(unittest.TestCase):
    @staticmethod
    def _write_minimal_pptx(path: Path, width_emu: int, height_emu: int) -> None:
        presentation_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:p="'
            'http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:sldSz cx="{}" cy="{}"/>'
            '</p:presentation>'
        ).format(width_emu, height_emu)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("ppt/presentation.xml", presentation_xml)

    def test_recognizes_32_by_9_without_changing_exact_dimensions(self) -> None:
        width_emu = 32 * 914400
        height_emu = 9 * 914400
        with tempfile.TemporaryDirectory() as temp_dir:
            deck_path = Path(temp_dir) / "ultrawide.pptx"
            self._write_minimal_pptx(deck_path, width_emu, height_emu)
            metadata = pptx_metadata(deck_path)

        self.assertTrue(metadata["ultrawide_32x9_like"])
        self.assertFalse(metadata["widescreen_16x9_like"])
        self.assertFalse(metadata["faithway_2560x704_like"])
        self.assertFalse(metadata["vf_sanctuary_2560x704_like"])
        self.assertEqual(metadata["width_emu"], width_emu)
        self.assertEqual(metadata["height_emu"], height_emu)

    def test_preserves_nonstandard_template_ratio_as_faithway_like(self) -> None:
        width_emu = 2560 * 10000
        height_emu = 704 * 10000
        with tempfile.TemporaryDirectory() as temp_dir:
            deck_path = Path(temp_dir) / "exact-template.pptx"
            self._write_minimal_pptx(deck_path, width_emu, height_emu)
            metadata = pptx_metadata(deck_path)

        self.assertTrue(metadata["faithway_2560x704_like"])
        self.assertTrue(metadata["vf_sanctuary_2560x704_like"])
        self.assertEqual(
            metadata["faithway_2560x704_like"],
            metadata["vf_sanctuary_2560x704_like"],
        )
        self.assertFalse(metadata["ultrawide_32x9_like"])
        self.assertEqual(metadata["width_emu"], width_emu)
        self.assertEqual(metadata["height_emu"], height_emu)


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
