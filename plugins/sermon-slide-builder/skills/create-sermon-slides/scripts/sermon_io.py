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


def read_note_paragraphs(path_value: str | os.PathLike[str]) -> list[str]:
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


def classify_cue(cue: str, cue_number: int) -> dict[str, object]:
    lower = cue.casefold()
    if "video" in lower or "clip" in lower:
        cue_type = "video"
    elif re.search(r"\b(pic|picture|photo|image|map|graphic|screenshot)\b", lower):
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
        re.search(
            r"\b(video|clip|pic|picture|photo|image|map|graphic|screenshot)\b",
            lower,
        )
    )
    current_terms = bool(
        re.search(
            r"\b(news|today|yesterday|current|latest|world cup|election|"
            r"president|prime minister|survey|statistics?|report)\b",
            lower,
        )
    )
    return {
        "cue_type": cue_type,
        "contains_media_direction": media_terms,
        "research_review_recommended": media_terms or current_terms,
    }


def extract_cues(path_value: str | os.PathLike[str]) -> dict[str, object]:
    path = Path(path_value).expanduser().resolve()
    paragraphs = read_note_paragraphs(path)
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
        "source_file": str(path),
        "paragraph_count": len(paragraphs),
        "cue_count": len(cues),
        "cues": cues,
    }


def _slide_number(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def extract_pptx_slides(path_value: str | os.PathLike[str]) -> list[dict[str, object]]:
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


def pptx_metadata(path_value: str | os.PathLike[str]) -> dict[str, object]:
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
            "faithway_2560x704_like": abs(ratio - (2560 / 704)) < 0.01,
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


def write_json(data: object, output: str | os.PathLike[str] | None) -> None:
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        output_path = Path(output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
