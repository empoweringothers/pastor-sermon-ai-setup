#!/usr/bin/env python3
"""Dependency-free readers for sermon notes and PowerPoint text."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Optional, Union
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

MARKER_RE = re.compile(
    r"^\s*(?P<outer_open>\()?\s*"
    r"(?:(?P<numeric_prefix>\d{1,2})\s*)?"
    r"(?P<marker>s[l1i]|slide)(?=\s|[-–—:]|$)"
    r"\s*(?:[-–—:]+\s*)?(?P<cue>.*)$",
    re.IGNORECASE,
)

VISUAL_ROUTE_AI_ILLUSTRATION = "ai_illustration"
VISUAL_ROUTE_AUTHENTIC_SOURCED_IMAGE = "authentic_sourced_image"
VISUAL_ROUTE_PASTOR_PROVIDED_ASSET = "pastor_provided_asset"
VISUAL_ROUTE_PASTOR_SUPPLIED_PLACEHOLDER = "pastor_supplied_placeholder"
VISUAL_ROUTE_AUTOMATIC = "automatic"
VISUAL_ROUTE_CONFLICT_REVIEW = "conflict_review"

PLACEHOLDER_STATUS_NEEDED = "needed"
PLACEHOLDER_STATUS_RECEIVED = "received"
PLACEHOLDER_STATUS_REPLACED = "replaced"
PLACEHOLDER_STATUS_WAIVED = "waived"
PLACEHOLDER_STATUS_NOT_APPLICABLE = "not_applicable"

VISUAL_NOUN_PATTERN = (
    r"(?:images?|pictures?|photos?|photographs?|illustrations?|art|artworks?|"
    r"visuals?|maps?|graphics?|screenshots?|videos?|clips?)"
)
HISTORICAL_LOCATION_PATTERN = (
    r"(?:sites?|locations?|places?|routes?|tombs?|caves?)"
)
AI_TERM_PATTERN = r"(?:\bai\b|\ba\.i\.(?=\s|$)|\bartificial intelligence\b)"

AI_VISUAL_RE = re.compile(
    AI_TERM_PATTERN
    + r".{0,40}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b|\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,40}"
    + AI_TERM_PATTERN
    + r"|(?:\b(?:generate|generated|generative|create)\b.{0,40}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,40}\b(?:generate|generated)\b)|(?:"
    + AI_TERM_PATTERN
    + r".{0,24}\b(?:realistic|photorealistic|cinematic|illustrated?|"
    r"rendered?|scene|portrait|depiction|reconstruction)\b)",
    re.IGNORECASE | re.DOTALL,
)

PASTOR_PROVIDED_ASSET_RE = re.compile(
    r"(?:\b(?:attached|uploaded|supplied|provided)\b.{0,40}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,40}\b(?:attached|uploaded|supplied|provided)\b)|"
    r"(?:\b(?:my|our)(?:\s+[a-z0-9'-]+){0,3}\s+"
    + VISUAL_NOUN_PATTERN
    + r"\b)",
    re.IGNORECASE | re.DOTALL,
)

PASTOR_SUPPLIED_PLACEHOLDER_RE = re.compile(
    r"(?:\b(?:pastor|i|we)\b.{0,30}\b"
    r"(?:add|provide|insert|supply|upload)\b.{0,30}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,30}\b(?:pastor|i|we)\b.{0,30}\b"
    r"(?:add|provide|insert|supply|upload)\b)|"
    r"(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,30}\b(?:will\s+be|to\s+be)\s+"
    r"(?:added|provided|inserted|supplied|uploaded)\b)|"
    r"(?:\b(?:leave|keep)\b.{0,30}\b(?:blank|empty)\b)|"
    r"(?:\b(?:blank|empty)\b.{0,30}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\s+(?:needed|required|tbd)\b)|\bplaceholder\b",
    re.IGNORECASE | re.DOTALL,
)

AUTHENTIC_VISUAL_RE = re.compile(
    r"(?:\b(?:real|actual|authentic|archival|archive|documentary)\b.{0,40}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,40}\b(?:real|actual|authentic|archival|archive|documentary)\b)|"
    r"(?:\b(?:historical|historic)\s+(?:photo|photograph|image|map|"
    r"document|artifact)\b)|"
    r"(?:\b(?:google|search|find|source)\b.{0,40}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b)|(?:\b(?:real|actual|authentic)\b.{0,40}\b"
    + HISTORICAL_LOCATION_PATTERN
    + r"\b)|(?:\b"
    + HISTORICAL_LOCATION_PATTERN
    + r"\b.{0,40}\b(?:real|actual|authentic)\b)",
    re.IGNORECASE | re.DOTALL,
)

PLACEHOLDER_REPLACED_RE = re.compile(
    r"\bplaceholder\b.{0,30}\b(?:replaced|filled|resolved)\b|"
    r"\b(?:replaced|filled|resolved)\b.{0,30}\bplaceholder\b",
    re.IGNORECASE | re.DOTALL,
)
PLACEHOLDER_WAIVED_RE = re.compile(
    r"\b(?:no|without)\b.{0,20}\b"
    + VISUAL_NOUN_PATTERN
    + r"\b.{0,20}\b(?:needed|required)\b|"
    r"\b(?:waive|waived)\b.{0,30}\b(?:image|media|placeholder)\b",
    re.IGNORECASE | re.DOTALL,
)


def _compile_site_status_re(terms: str) -> re.Pattern:
    return re.compile(
        r"(?:\b(?:"
        + terms
        + r")\b.{0,50}\b"
        + HISTORICAL_LOCATION_PATTERN
        + r"\b)|(?:\b"
        + HISTORICAL_LOCATION_PATTERN
        + r"\b.{0,50}\b(?:"
        + terms
        + r")\b)",
        re.IGNORECASE | re.DOTALL,
    )


SITE_REFERENCE_RE = re.compile(
    r"\b(?:sites?|locations?|places?|routes?|tombs?|caves?)\b",
    re.IGNORECASE,
)
SITE_DISPUTED_RE = _compile_site_status_re(r"disputed|contested|uncertain")
SITE_POSSIBLE_RE = _compile_site_status_re(r"possible|possibly|perhaps")
SITE_PROPOSED_RE = _compile_site_status_re(r"proposed|suggested|candidate")
SITE_TRADITIONAL_RE = _compile_site_status_re(
    r"traditional|traditionally|believed"
)
SITE_ESTABLISHED_RE = _compile_site_status_re(
    r"established|confirmed|verified"
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_text_in_order(element: ET.Element) -> str:
    parts: list[str] = []
    for child in element.iter():
        name = _local_name(child.tag)
        if name == "t" and child.text:
            parts.append(child.text)
        elif name == "tab":
            parts.append("\t")
        elif name in {"br", "cr"}:
            parts.append("\n")
    return "".join(parts).replace("\u00a0", " ").strip()


def _read_docx(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    return [_element_text_in_order(p) for p in root.findall(f".//{{{W_NS}}}p")]


def _run_text_converter(path: Path) -> str:
    textutil = Path("/usr/bin/textutil")
    if platform.system() == "Darwin" and textutil.exists():
        result = subprocess.run(
            [str(textutil), "-convert", "txt", "-stdout", str(path)],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode("utf-8", errors="replace")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            f"Cannot read legacy {path.suffix} file: install LibreOffice or "
            "convert the note to .docx."
        )
    with tempfile.TemporaryDirectory(prefix="sermon-note-") as temp_dir:
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "txt:Text",
                "--outdir",
                temp_dir,
                str(path),
            ],
            check=True,
            capture_output=True,
        )
        converted = Path(temp_dir) / f"{path.stem}.txt"
        return converted.read_text(encoding="utf-8", errors="replace")


def read_note_paragraphs(
    path_value: Union[str, os.PathLike[str]],
) -> list[str]:
    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _read_docx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    if suffix == ".doc":
        return _run_text_converter(path).splitlines()
    if suffix == ".pdf":
        pdftotext = shutil.which("pdftotext")
        if not pdftotext:
            raise RuntimeError("Install pdftotext or convert the PDF note to .docx.")
        result = subprocess.run(
            [pdftotext, "-layout", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.splitlines()
    raise ValueError(f"Unsupported note type: {suffix}")


def _nearest_context(
    paragraphs: list[str], index: int, direction: int, limit: int = 2
) -> list[str]:
    result: list[str] = []
    cursor = index + direction
    while 0 <= cursor < len(paragraphs) and len(result) < limit:
        value = paragraphs[cursor].strip()
        if value and MARKER_RE.match(value):
            break
        if value:
            if direction < 0:
                result.insert(0, value)
            else:
                result.append(value)
        cursor += direction
    return result


def _visual_route(cue: str) -> tuple[str, bool]:
    """Return the requested visual route and whether its directions conflict.

    ``realistic`` is only a style word, so an ``AI realistic image`` has one
    route. In contrast, explicit combinations such as ``real archival photo;
    AI only if unavailable`` retain the ambiguity for human review.
    """

    explicit_routes: list[str] = []
    inactive_placeholder = bool(
        PLACEHOLDER_REPLACED_RE.search(cue) or PLACEHOLDER_WAIVED_RE.search(cue)
    )
    for pattern, route in (
        (AI_VISUAL_RE, VISUAL_ROUTE_AI_ILLUSTRATION),
        (AUTHENTIC_VISUAL_RE, VISUAL_ROUTE_AUTHENTIC_SOURCED_IMAGE),
        (PASTOR_PROVIDED_ASSET_RE, VISUAL_ROUTE_PASTOR_PROVIDED_ASSET),
        (
            PASTOR_SUPPLIED_PLACEHOLDER_RE,
            VISUAL_ROUTE_PASTOR_SUPPLIED_PLACEHOLDER,
        ),
    ):
        if route == VISUAL_ROUTE_PASTOR_SUPPLIED_PLACEHOLDER and inactive_placeholder:
            continue
        if pattern.search(cue):
            explicit_routes.append(route)

    if len(explicit_routes) > 1:
        return VISUAL_ROUTE_CONFLICT_REVIEW, True
    if explicit_routes:
        return explicit_routes[0], False
    if SITE_REFERENCE_RE.search(cue) and re.search(
        r"\b(?:photos?|photographs?|maps?|documents?|artifacts?|screenshots?)\b",
        cue,
        re.IGNORECASE,
    ):
        return VISUAL_ROUTE_AUTHENTIC_SOURCED_IMAGE, False
    return VISUAL_ROUTE_AUTOMATIC, False


def _site_identification(cue: str) -> tuple[str, Optional[str]]:
    for pattern, status, label in (
        (SITE_DISPUTED_RE, "disputed", "Disputed site"),
        (SITE_POSSIBLE_RE, "possible", "Possible site"),
        (SITE_PROPOSED_RE, "proposed", "Proposed site"),
        (SITE_TRADITIONAL_RE, "traditional", "Traditional site"),
        (SITE_ESTABLISHED_RE, "established", None),
    ):
        if pattern.search(cue):
            return status, label
    if SITE_REFERENCE_RE.search(cue):
        return "unknown", None
    return "not_applicable", None


def _placeholder_status(cue: str) -> str:
    if PLACEHOLDER_REPLACED_RE.search(cue):
        return PLACEHOLDER_STATUS_REPLACED
    if PLACEHOLDER_WAIVED_RE.search(cue):
        return PLACEHOLDER_STATUS_WAIVED
    if PASTOR_SUPPLIED_PLACEHOLDER_RE.search(cue):
        return PLACEHOLDER_STATUS_NEEDED
    if PASTOR_PROVIDED_ASSET_RE.search(cue):
        return PLACEHOLDER_STATUS_RECEIVED
    return PLACEHOLDER_STATUS_NOT_APPLICABLE


def classify_cue(cue: str, cue_number: int) -> dict[str, object]:
    lower = cue.casefold()
    if "video" in lower or "clip" in lower:
        cue_type = "video"
    elif re.search(r"\b" + VISUAL_NOUN_PATTERN + r"\b", lower):
        cue_type = "image"
    elif re.search(r"\b[a-z]{2,}\.?\s+\d{1,3}:\d{1,3}", lower):
        cue_type = "scripture"
    elif cue_number == 1 or "theme slide" in lower or "title slide" in lower:
        cue_type = "title"
    elif re.match(r"^\s*\d+[.)-]?\s+", cue):
        cue_type = "outline"
    elif "“" in cue or '"' in cue or "quote" in lower:
        cue_type = "quotation"
    else:
        cue_type = "text"

    media_terms = bool(
        re.search(r"\b" + VISUAL_NOUN_PATTERN + r"\b", lower)
    )
    current_terms = bool(
        re.search(
            r"\b(news|today|yesterday|current|latest|world cup|election|"
            r"president|prime minister|survey|statistics?|report)\b",
            lower,
        )
    )
    visual_route, visual_route_conflict = _visual_route(cue)
    site_status, uncertainty_label = _site_identification(cue)
    historical_certainty_review = site_status in {
        "traditional",
        "proposed",
        "possible",
        "disputed",
    }
    return {
        "cue_type": cue_type,
        "contains_media_direction": (
            media_terms or visual_route != VISUAL_ROUTE_AUTOMATIC
        ),
        "visual_route_hint": visual_route,
        "visual_route_conflict_review": visual_route_conflict,
        "site_identification_status": site_status,
        "visible_uncertainty_label": uncertainty_label,
        "placeholder_status": _placeholder_status(cue),
        "historical_certainty_review_recommended": historical_certainty_review,
        "research_review_recommended": (
            media_terms
            or current_terms
            or historical_certainty_review
            or visual_route != VISUAL_ROUTE_AUTOMATIC
        ),
    }


def _extract_cues_from_paragraphs(
    paragraphs: list[str], source_label: str
) -> dict[str, object]:
    cues: list[dict[str, object]] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        match = MARKER_RE.match(paragraph)
        if not match:
            continue
        cue_text = match.group("cue").strip()
        if match.group("outer_open") and paragraph.rstrip().endswith(")"):
            cue_text = cue_text[:-1].rstrip()
        cue_number = len(cues) + 1
        cue_record: dict[str, object] = {
            "cue_number": cue_number,
            "paragraph_number": paragraph_index + 1,
            "source_marker": match.group("marker"),
            "numeric_prefix": match.group("numeric_prefix"),
            "source_line": paragraph,
            "visible_text_candidate": cue_text,
            "context_before": _nearest_context(paragraphs, paragraph_index, -1),
            "context_after": _nearest_context(paragraphs, paragraph_index, 1),
        }
        cue_record.update(classify_cue(cue_text, cue_number))
        cues.append(cue_record)
    return {
        "source_file": source_label,
        "paragraph_count": len(paragraphs),
        "cue_count": len(cues),
        "cues": cues,
    }


def extract_cues_from_text(
    text: str, source_label: str = "[pasted text]"
) -> dict[str, object]:
    """Extract complete cue records directly from pasted sermon text."""

    return _extract_cues_from_paragraphs(text.splitlines(), source_label)


def extract_cues(path_value: Union[str, os.PathLike[str]]) -> dict[str, object]:
    path = Path(path_value).expanduser().resolve()
    paragraphs = read_note_paragraphs(path)
    return _extract_cues_from_paragraphs(paragraphs, str(path))


def _slide_number(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def extract_pptx_slides(
    path_value: Union[str, os.PathLike[str]],
) -> list[dict[str, object]]:
    path = Path(path_value).expanduser().resolve()
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            (
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=_slide_number,
        )
        slides: list[dict[str, object]] = []
        for name in slide_names:
            root = ET.fromstring(archive.read(name))
            fragments = [
                node.text or "" for node in root.findall(f".//{{{A_NS}}}t")
            ]
            slides.append(
                {
                    "slide_number": _slide_number(name),
                    "text": " ".join(part.strip() for part in fragments if part.strip()),
                    "text_fragments": fragments,
                }
            )
    return slides


def pptx_metadata(path_value: Union[str, os.PathLike[str]]) -> dict[str, object]:
    path = Path(path_value).expanduser().resolve()
    with zipfile.ZipFile(path) as archive:
        archive_names = archive.namelist()
        root = ET.fromstring(archive.read("ppt/presentation.xml"))
        size = root.find(f".//{{{P_NS}}}sldSz")
        if size is None:
            return {}
        width_emu = int(size.attrib["cx"])
        height_emu = int(size.attrib["cy"])
        ratio = width_emu / height_emu
        vf_sanctuary_like = abs(ratio - (2560 / 704)) < 0.01
        notes_names = sorted(
            name
            for name in archive_names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        )
        notes_with_sources = 0
        for name in notes_names:
            notes_root = ET.fromstring(archive.read(name))
            notes_text = " ".join(
                node.text or "" for node in notes_root.findall(f".//{{{A_NS}}}t")
            )
            if "[sources]" in notes_text.casefold():
                notes_with_sources += 1
        return {
            "width_emu": width_emu,
            "height_emu": height_emu,
            "width_inches": round(width_emu / 914400, 4),
            "height_inches": round(height_emu / 914400, 4),
            "aspect_ratio": round(ratio, 5),
            "faithway_2560x704_like": vf_sanctuary_like,
            "vf_sanctuary_2560x704_like": vf_sanctuary_like,
            "ultrawide_32x9_like": abs(ratio - (32 / 9)) < 0.01,
            "widescreen_16x9_like": abs(ratio - (16 / 9)) < 0.01,
            "media_file_count": sum(
                1
                for name in archive_names
                if name.startswith("ppt/media/") and not name.endswith("/")
            ),
            "speaker_notes_slide_count": len(notes_names),
            "speaker_notes_with_sources_count": notes_with_sources,
            "source_notes_complete_for_all_slides": (
                bool(notes_names) and notes_with_sources == len(notes_names)
            ),
        }


def normalize_for_match(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = value.casefold()
    value = re.sub(r"\b(slide|s[l1i])\b", " ", value)
    value = re.sub(
        r"\b(pic|picture|photo|image|video|clip|map|graphic|screenshot)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def write_json(
    data: object,
    output: Optional[Union[str, os.PathLike[str]]],
) -> None:
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        output_path = Path(output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
