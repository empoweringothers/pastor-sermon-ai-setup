#!/usr/bin/env python3
"""Verify every distributed setup file against the release hash manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "FILE-SHA256SUMS.json"
IGNORED_NAMES = {".DS_Store", "setup-state.local.json"}
IGNORED_PARTS = {".git", "__pycache__"}


def included_files() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path == MANIFEST_PATH:
            continue
        relative = path.relative_to(REPO_ROOT)
        if path.name in IGNORED_NAMES or path.suffix == ".pyc":
            continue
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        result[relative.as_posix()] = path
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify() -> tuple[bool, list[str]]:
    if not MANIFEST_PATH.is_file():
        return False, ["The release hash manifest is missing."]
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, ["The release hash manifest is not valid JSON."]
    expected = manifest.get("files")
    if manifest.get("algorithm") != "sha256" or not isinstance(expected, dict):
        return False, ["The release hash manifest has an unsupported format."]

    actual = included_files()
    errors: list[str] = []
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing:
        errors.append(f"Missing distributed files: {', '.join(missing)}")
    if unexpected:
        errors.append(f"Unlisted distributed files: {', '.join(unexpected)}")
    for relative in sorted(set(expected) & set(actual)):
        if sha256(actual[relative]) != expected[relative]:
            errors.append(f"Hash mismatch: {relative}")
    return not errors, errors


def main() -> None:
    passed, errors = verify()
    if not passed:
        print("RELEASE VERIFICATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("RELEASE VERIFIED")
    print("All distributed files match FILE-SHA256SUMS.json.")


if __name__ == "__main__":
    main()
