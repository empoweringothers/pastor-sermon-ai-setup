#!/usr/bin/env python3
"""Read-only readiness check for the Pastor Sermon AI setup repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "sermon-slide-builder"
REQUIRED_REPO_FILES = (
    "SETUP-ASSISTANT.md",
    ".agents/plugins/marketplace.json",
    "plugins/sermon-slide-builder/.codex-plugin/plugin.json",
    "plugins/sermon-slide-builder/skills/create-sermon-slides/SKILL.md",
)


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _safe_path(path: Path | None, *, show_paths: bool) -> str | None:
    if path is None:
        return None
    if show_paths:
        return str(path)
    try:
        return "<repository>/" + path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return f"<system>/{path.name}"


def _command(
    name: str,
    version_args: list[str] | None = None,
    *,
    include_versions: bool = False,
    show_paths: bool = False,
) -> dict[str, Any]:
    path_value = shutil.which(name)
    path = Path(path_value) if path_value else None
    result: dict[str, Any] = {
        "found": bool(path),
        "command": name,
        "path": _safe_path(path, show_paths=show_paths),
    }
    if not path or not include_versions or not version_args:
        return result
    try:
        completed = subprocess.run(
            [str(path), *version_args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        version = (completed.stdout or completed.stderr).strip().splitlines()
        result["version"] = version[0] if version else ""
    except (OSError, subprocess.SubprocessError) as exc:
        result["version_error"] = str(exc)
    return result


def _app_checks(*, show_paths: bool) -> dict[str, dict[str, Any]]:
    system = platform.system()
    user_home = Path.home()

    if system == "Darwin":
        chatgpt = _first_existing(
            [Path("/Applications/ChatGPT.app"), user_home / "Applications/ChatGPT.app"]
        )
        powerpoint = _first_existing(
            [
                Path("/Applications/Microsoft PowerPoint.app"),
                user_home / "Applications/Microsoft PowerPoint.app",
            ]
        )
        word = _first_existing(
            [
                Path("/Applications/Microsoft Word.app"),
                user_home / "Applications/Microsoft Word.app",
            ]
        )
        return {
            "chatgpt_desktop": {
                "status": "pass" if chatgpt else "fail",
                "path": _safe_path(chatgpt, show_paths=show_paths),
                "note": "Sign-in and Plugins Directory still need manual confirmation.",
            },
            "powerpoint": {
                "status": "pass" if powerpoint else "fail",
                "path": _safe_path(powerpoint, show_paths=show_paths),
                "note": "Launch, license, open, and save checks are still required.",
            },
            "word": {
                "found": bool(word),
                "path": _safe_path(word, show_paths=show_paths),
                "required": False,
                "when_needed": "Native review of a requested Word handout.",
            },
        }

    if system == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        program_files = [
            Path(value)
            for value in (
                os.environ.get("PROGRAMFILES"),
                os.environ.get("PROGRAMFILES(X86)"),
            )
            if value
        ]
        chatgpt_candidates = [
            local / "Programs/ChatGPT/ChatGPT.exe",
            local / "Programs/OpenAI/ChatGPT/ChatGPT.exe",
        ]
        powerpoint_candidates: list[Path] = []
        word_candidates: list[Path] = []
        for root in program_files:
            powerpoint_candidates.extend(
                [
                    root / "Microsoft Office/root/Office16/POWERPNT.EXE",
                    root / "Microsoft Office/Office16/POWERPNT.EXE",
                ]
            )
            word_candidates.extend(
                [
                    root / "Microsoft Office/root/Office16/WINWORD.EXE",
                    root / "Microsoft Office/Office16/WINWORD.EXE",
                ]
            )
        chatgpt = _first_existing(chatgpt_candidates)
        powerpoint = _first_existing(powerpoint_candidates)
        word = _first_existing(word_candidates)
        return {
            "chatgpt_desktop": {
                "status": "pass" if chatgpt else "unknown",
                "path": _safe_path(chatgpt, show_paths=show_paths),
                "note": "Store apps may require manual confirmation.",
            },
            "powerpoint": {
                "status": "pass" if powerpoint else "unknown",
                "path": _safe_path(powerpoint, show_paths=show_paths),
                "note": "Store installs may require manual launch and license checks.",
            },
            "word": {
                "found": bool(word),
                "path": _safe_path(word, show_paths=show_paths),
                "required": False,
                "when_needed": "Native review of a requested Word handout.",
            },
        }

    return {
        "chatgpt_desktop": {
            "status": "unsupported",
            "path": None,
            "note": "This setup package supports macOS and Windows only.",
        },
        "powerpoint": {
            "status": "unsupported",
            "path": None,
            "note": "This setup package supports macOS and Windows only.",
        },
        "word": {
            "found": False,
            "path": None,
            "required": False,
            "when_needed": "This setup package supports macOS and Windows only.",
        },
    }


def _repo_check(*, show_paths: bool) -> dict[str, Any]:
    files = {
        relative: (REPO_ROOT / relative).is_file() for relative in REQUIRED_REPO_FILES
    }
    return {
        "status": "pass" if all(files.values()) else "fail",
        "root": _safe_path(REPO_ROOT, show_paths=show_paths),
        "files": files,
    }


def _digest(root: Path) -> str | None:
    if not root.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _plugin_check(*, show_paths: bool) -> dict[str, Any]:
    source = REPO_ROOT / "plugins" / PLUGIN_NAME
    source_manifest_path = source / ".codex-plugin/plugin.json"
    source_manifest: dict[str, Any] | None = None
    if source_manifest_path.is_file():
        try:
            value = json.loads(source_manifest_path.read_text(encoding="utf-8"))
            if value.get("name") == PLUGIN_NAME:
                source_manifest = value
        except (OSError, json.JSONDecodeError):
            pass
    version = source_manifest.get("version") if source_manifest else None

    personal_source = Path.home() / ".codex/plugins" / PLUGIN_NAME
    personal_manifest = personal_source / ".codex-plugin/plugin.json"
    target_manifest_matches = False
    if personal_manifest.is_file() and source_manifest:
        try:
            target_value = json.loads(personal_manifest.read_text(encoding="utf-8"))
            target_manifest_matches = (
                target_value.get("name") == PLUGIN_NAME
                and target_value.get("version") == version
            )
        except (OSError, json.JSONDecodeError):
            pass
    digest_matches = bool(
        _digest(source)
        and _digest(personal_source)
        and _digest(source) == _digest(personal_source)
    )

    marketplace_path = Path.home() / ".agents/plugins/marketplace.json"
    expected_path = f"./.codex/plugins/{PLUGIN_NAME}"
    entry_matches = False
    marketplace_error = None
    if marketplace_path.is_file():
        try:
            data = json.loads(marketplace_path.read_text(encoding="utf-8"))
            for item in data.get("plugins", []):
                if not isinstance(item, dict) or item.get("name") != PLUGIN_NAME:
                    continue
                source_value = item.get("source", {})
                entry_matches = (
                    source_value.get("source") == "local"
                    and source_value.get("path") == expected_path
                )
                break
        except (OSError, json.JSONDecodeError) as exc:
            marketplace_error = str(exc)

    cache_manifests: list[Path] = []
    cache_root = Path.home() / ".codex/plugins/cache"
    if version and cache_root.is_dir():
        cache_manifests = list(
            cache_root.glob(
                f"*/{PLUGIN_NAME}/{version}/.codex-plugin/plugin.json"
            )
        )
    source_registered = bool(target_manifest_matches and digest_matches and entry_matches)
    status = (
        "installed-cache-detected"
        if cache_manifests
        else "source-registered"
        if source_registered
        else "not-prepared"
    )
    return {
        "status": status,
        "version": version,
        "personal_source": _safe_path(personal_source, show_paths=show_paths),
        "source_registered": source_registered,
        "target_manifest_matches": target_manifest_matches,
        "target_digest_matches": digest_matches,
        "marketplace": _safe_path(marketplace_path, show_paths=show_paths),
        "marketplace_entry_matches": entry_matches,
        "marketplace_error": marketplace_error,
        "installed_cache_detected": bool(cache_manifests),
        "fresh_chat_verification_required": True,
        "note": (
            "A source registration or cache folder is not proof that the plugin "
            "loaded. Verify it in the Plugins Directory and a fresh Work or Codex chat."
        ),
    }


def build_report(
    *, show_paths: bool = False, include_versions: bool = False
) -> dict[str, Any]:
    app_checks = _app_checks(show_paths=show_paths)
    python_supported = sys.version_info >= (3, 9)
    required = {
        "repository": _repo_check(show_paths=show_paths),
        "chatgpt_desktop": app_checks["chatgpt_desktop"],
        "powerpoint": app_checks["powerpoint"],
    }
    conditional = {
        "python": {
            "status": "available" if python_supported else "unsupported",
            "version": platform.python_version(),
            "executable": _safe_path(Path(sys.executable), show_paths=show_paths),
            "note": "Python 3.9 or newer; no pip packages are needed.",
        },
        "word": app_checks["word"],
        "libreoffice": {
            **_command(
                "soffice",
                ["--version"],
                include_versions=include_versions,
                show_paths=show_paths,
            ),
            "required": False,
            "when_needed": "Legacy .doc conversion off macOS or fallback rendering.",
        },
        "pdftotext": {
            **_command(
                "pdftotext",
                ["-v"],
                include_versions=include_versions,
                show_paths=show_paths,
            ),
            "required": False,
            "when_needed": "Local extraction from PDF sermon notes.",
        },
        "git": {
            **_command(
                "git",
                ["--version"],
                include_versions=include_versions,
                show_paths=show_paths,
            ),
            "required": False,
            "when_needed": "Optional updates; ZIP download does not need Git.",
        },
        "java": {
            **_command(
                "java",
                ["-version"],
                include_versions=include_versions,
                show_paths=show_paths,
            ),
            "required": False,
            "when_needed": "Not used by this repository.",
        },
        "node": {
            **_command(
                "node",
                ["--version"],
                include_versions=include_versions,
                show_paths=show_paths,
            ),
            "required": False,
            "when_needed": "Not used by this repository.",
        },
    }
    statuses = [item["status"] for item in required.values()]
    return {
        "schema_version": 2,
        "privacy": {
            "paths_redacted": not show_paths,
            "versions_executed": include_versions,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "required": required,
        "plugin": _plugin_check(show_paths=show_paths),
        "conditional": conditional,
        "summary": {
            "required_failures": statuses.count("fail")
            + statuses.count("unsupported"),
            "manual_confirmations": statuses.count("unknown"),
            "note": (
                "Resolve one required failure at a time. Optional tools are not "
                "setup failures. Account, license, and fresh-chat checks remain manual."
            ),
        },
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"System: {report['platform']['system']} {report['platform']['release']}")
    for name, item in report["required"].items():
        print(f"Required - {name}: {item['status']}")
    print(f"Plugin source: {report['plugin']['status']}")
    for name, item in report["conditional"].items():
        if name == "python":
            value = item["version"]
        else:
            value = "available" if item.get("found") else "not found"
        print(f"Optional - {name}: {value}")
    print(report["summary"]["note"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Include full local paths instead of redacted paths",
    )
    parser.add_argument(
        "--versions",
        action="store_true",
        help="Run optional tools to collect version strings",
    )
    args = parser.parse_args()
    report = build_report(
        show_paths=args.show_paths, include_versions=args.versions
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
