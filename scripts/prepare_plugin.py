#!/usr/bin/env python3
"""Prepare, inspect, remove, or restore a personal plugin source safely.

This script does not claim that ChatGPT installed or loaded the plugin. It only
copies a trusted source into the personal plugin folder and registers that source
in the personal marketplace. Installation is completed in the Plugins Directory
and verified in a fresh Work or Codex chat.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "sermon-slide-builder"
SOURCE_PLUGIN = REPO_ROOT / "plugins" / PLUGIN_NAME
EXPECTED_SOURCE_PATH = f"./.codex/plugins/{PLUGIN_NAME}"


def _digest(root: Path) -> Optional[str]:
    if not root.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _read_manifest(root: Path) -> Optional[dict[str, Any]]:
    path = root / ".codex-plugin/plugin.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("name") != PLUGIN_NAME or not isinstance(data.get("version"), str):
        return None
    return data


def _load_marketplace(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": "personal",
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("plugins", []), list):
        raise ValueError(f"Unsupported marketplace format: {path}")
    data.setdefault("plugins", [])
    return data


def _entry() -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": EXPECTED_SOURCE_PATH},
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def _paths(home: Path) -> tuple[Path, Path, Path]:
    target = home / ".codex/plugins" / PLUGIN_NAME
    marketplace = home / ".agents/plugins/marketplace.json"
    backups = home / ".codex/plugin-backups"
    return target, marketplace, backups


def _safe_display(path: Path, home: Path, show_paths: bool) -> str:
    if show_paths:
        return str(path)
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return f"<repository>/{path.name}"


def _marketplace_entry(marketplace: dict[str, Any]) -> Optional[dict[str, Any]]:
    for item in marketplace.get("plugins", []):
        if isinstance(item, dict) and item.get("name") == PLUGIN_NAME:
            return item
    return None


def _cache_manifests(home: Path, version: Optional[str]) -> list[Path]:
    if not version:
        return []
    root = home / ".codex/plugins/cache"
    if not root.is_dir():
        return []
    matches: list[Path] = []
    for path in root.glob(f"*/{PLUGIN_NAME}/{version}/.codex-plugin/plugin.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("name") == PLUGIN_NAME and data.get("version") == version:
            matches.append(path)
    return matches


def check(home: Path, *, show_paths: bool = False) -> dict[str, Any]:
    target, marketplace_path, _ = _paths(home)
    source_manifest = _read_manifest(SOURCE_PLUGIN)
    target_manifest = _read_manifest(target)
    source_digest = _digest(SOURCE_PLUGIN)
    target_digest = _digest(target)
    marketplace_entry: Optional[dict[str, Any]] = None
    marketplace_error = None
    if marketplace_path.exists():
        try:
            marketplace_entry = _marketplace_entry(_load_marketplace(marketplace_path))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            marketplace_error = str(exc)

    entry_matches = marketplace_entry == _entry()
    target_matches = bool(
        source_manifest
        and target_manifest
        and source_manifest.get("version") == target_manifest.get("version")
        and source_digest
        and source_digest == target_digest
    )
    cache_manifests = _cache_manifests(
        home, source_manifest.get("version") if source_manifest else None
    )
    source_registered = bool(target_matches and entry_matches)
    return {
        "source_valid": bool(source_manifest and source_digest),
        "source_version": source_manifest.get("version") if source_manifest else None,
        "target": _safe_display(target, home, show_paths),
        "target_found": target.is_dir(),
        "target_manifest_valid": bool(target_manifest),
        "target_matches_source": target_matches,
        "marketplace": _safe_display(marketplace_path, home, show_paths),
        "marketplace_entry_found": marketplace_entry is not None,
        "marketplace_entry_matches": entry_matches,
        "marketplace_error": marketplace_error,
        "source_registered": source_registered,
        "installed_cache_detected": bool(cache_manifests),
        "fresh_chat_verification_required": True,
        "note": (
            "source_registered only means the plugin is available to the Plugins "
            "Directory. Install or enable it there, then verify it in a fresh "
            "Work or Codex chat."
        ),
    }


def _unique_backup_dir(backup_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = backup_root / f"{PLUGIN_NAME}-{timestamp}"
    counter = 1
    while candidate.exists():
        candidate = backup_root / f"{PLUGIN_NAME}-{timestamp}-{counter}"
        counter += 1
    candidate.mkdir(parents=True)
    return candidate


def _backup_current(home: Path) -> Path:
    target, marketplace_path, backup_root = _paths(home)
    backup_root.mkdir(parents=True, exist_ok=True)
    bundle = _unique_backup_dir(backup_root)
    metadata = {
        "schema_version": 1,
        "plugin_name": PLUGIN_NAME,
        "target_existed": target.is_dir(),
        "marketplace_existed": marketplace_path.is_file(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    if target.is_dir():
        shutil.copytree(target, bundle / "plugin")
    if marketplace_path.is_file():
        shutil.copy2(marketplace_path, bundle / "marketplace.json")
    (bundle / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return bundle


def _write_marketplace(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.new")
    try:
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_bundle(
    bundle: Path,
) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
    metadata_path = bundle / "metadata.json"
    if not metadata_path.is_file():
        raise ValueError(f"Backup metadata is missing: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("plugin_name") != PLUGIN_NAME:
        raise ValueError("Backup is for a different plugin.")
    if not isinstance(metadata.get("target_existed"), bool) or not isinstance(
        metadata.get("marketplace_existed"), bool
    ):
        raise ValueError("Backup metadata is incomplete.")
    if metadata["target_existed"] and not (bundle / "plugin").is_dir():
        raise ValueError("Backup plugin folder is missing.")

    previous_entry = None
    if metadata["marketplace_existed"]:
        backup_marketplace = bundle / "marketplace.json"
        if not backup_marketplace.is_file():
            raise ValueError("Backup marketplace file is missing.")
        previous_entry = _marketplace_entry(_load_marketplace(backup_marketplace))
    return metadata, previous_entry


def _restore_bundle(home: Path, bundle: Path) -> None:
    metadata, previous_entry = _validate_bundle(bundle)

    target, marketplace_path, _ = _paths(home)
    current = _load_marketplace(marketplace_path)
    current["plugins"] = [
        item
        for item in current["plugins"]
        if not (isinstance(item, dict) and item.get("name") == PLUGIN_NAME)
    ]
    if previous_entry:
        current["plugins"].append(previous_entry)

    staged_plugin = None
    staging = None
    if metadata["target_existed"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{PLUGIN_NAME}-restore-", dir=target.parent))
        staged_plugin = staging / PLUGIN_NAME
        shutil.copytree(bundle / "plugin", staged_plugin)

    try:
        if target.exists():
            shutil.rmtree(target)
        if staged_plugin is not None:
            os.replace(staged_plugin, target)

        if current["plugins"] or marketplace_path.exists() or metadata[
            "marketplace_existed"
        ]:
            _write_marketplace(marketplace_path, current)
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)


def prepare(home: Path, *, show_paths: bool = False) -> dict[str, Any]:
    manifest = _read_manifest(SOURCE_PLUGIN)
    if not manifest:
        raise ValueError("The bundled plugin manifest is missing or invalid.")

    target, marketplace_path, _ = _paths(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    backup_bundle = _backup_current(home)

    marketplace = _load_marketplace(marketplace_path)
    marketplace["plugins"] = [
        item
        for item in marketplace["plugins"]
        if not (isinstance(item, dict) and item.get("name") == PLUGIN_NAME)
    ]
    marketplace["plugins"].append(_entry())

    staging = Path(tempfile.mkdtemp(prefix=f".{PLUGIN_NAME}-", dir=target.parent))
    staged_plugin = staging / PLUGIN_NAME
    try:
        shutil.copytree(SOURCE_PLUGIN, staged_plugin)
        if target.exists():
            shutil.rmtree(target)
        os.replace(staged_plugin, target)
        _write_marketplace(marketplace_path, marketplace)
    except Exception:
        _restore_bundle(home, backup_bundle)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    result = check(home, show_paths=show_paths)
    result["backup_bundle"] = _safe_display(backup_bundle, home, show_paths)
    result["plugins_directory_action_required"] = True
    return result


def restore(home: Path, bundle: Path, *, show_paths: bool = False) -> dict[str, Any]:
    resolved_bundle = bundle.resolve()
    _validate_bundle(resolved_bundle)
    recovery_backup = _backup_current(home)
    try:
        _restore_bundle(home, resolved_bundle)
    except Exception as restore_error:
        try:
            _restore_bundle(home, recovery_backup)
        except Exception as rollback_error:
            raise RuntimeError(
                f"Restore failed and automatic rollback also failed: {rollback_error}"
            ) from restore_error
        raise
    result = check(home, show_paths=show_paths)
    result["restored_from"] = _safe_display(resolved_bundle, home, show_paths)
    result["recovery_backup"] = _safe_display(recovery_backup, home, show_paths)
    result["plugins_directory_review_required"] = True
    return result


def remove_source(home: Path, *, show_paths: bool = False) -> dict[str, Any]:
    target, marketplace_path, _ = _paths(home)
    recovery_backup = _backup_current(home)
    marketplace = _load_marketplace(marketplace_path)
    marketplace["plugins"] = [
        item
        for item in marketplace["plugins"]
        if not (isinstance(item, dict) and item.get("name") == PLUGIN_NAME)
    ]
    try:
        if target.exists():
            shutil.rmtree(target)
        _write_marketplace(marketplace_path, marketplace)
    except Exception:
        _restore_bundle(home, recovery_backup)
        raise
    result = check(home, show_paths=show_paths)
    result["recovery_backup"] = _safe_display(recovery_backup, home, show_paths)
    result["uninstall_in_plugins_directory_still_required"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Only inspect status")
    action.add_argument(
        "--prepare",
        action="store_true",
        help="Back up and register the bundled source in the personal marketplace",
    )
    action.add_argument(
        "--restore",
        type=Path,
        metavar="BACKUP_BUNDLE",
        help="Restore the plugin source and its prior marketplace entry",
    )
    action.add_argument(
        "--remove-source",
        action="store_true",
        help="Back up and remove the personal source registration",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Override the home directory (primarily for testing)",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Include full local paths in the report",
    )
    args = parser.parse_args()
    home = args.home.resolve()
    if args.prepare:
        result = prepare(home, show_paths=args.show_paths)
    elif args.restore:
        result = restore(home, args.restore, show_paths=args.show_paths)
    elif args.remove_source:
        result = remove_source(home, show_paths=args.show_paths)
    else:
        result = check(home, show_paths=args.show_paths)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
