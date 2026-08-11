#!/usr/bin/env python3
"""Manage the private, local Pastor Assistant OS with no third-party packages."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Iterator, List, Mapping, Optional


SCHEMA_VERSION = 1
PRODUCT_ID = "pastor-assistant-os"
VENDOR = "Valley Forge Baptist"
PRODUCT_FOLDER = "Pastor Assistant OS"
CREATE_CONSENT = "YES, CREATE PASTOR ASSISTANT OS"
SAVE_CONSENT = "YES, SAVE THIS RULE"
FORGET_CONSENT = "YES, FORGET THIS RULE"
PROPOSAL_CONSENT = "YES, PREPARE CHURCH RULE PROPOSAL"
CATEGORIES = ("layout", "imagery", "wording", "workflow", "privacy", "other")

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "workspace-template"

REQUIRED_FILES = (
    "AGENTS.md",
    "START-HERE.md",
    "state/os-state.json",
    "profile/church-profile.md",
    "profile/pastor-preferences.md",
    "learning/rules.json",
    "learning/approved-rules.md",
    "learning/promotion-candidates.json",
    "audit/rule-changes.jsonl",
)

SENSITIVE_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\bhttps?://", re.IGNORECASE),
    re.compile(r"\bwww\.", re.IGNORECASE),
    re.compile(r"(?:^|\s)[A-Za-z]:\\"),
    re.compile(r"(?:^|\s)/(?:Users|home|Volumes)/"),
    re.compile(r"\\\\[^\s]+\\"),
    re.compile(r"(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}"),
)

UNSAFE_PHRASES = (
    "ignore privacy",
    "bypass privacy",
    "skip approval",
    "without approval",
    "rewrite the sermon",
    "change scripture",
    "change the scripture",
    "change theology",
    "upload private",
    "publish private",
    "generate the real pastor",
    "generate a real church member",
    "remove the ai label",
)


class PastorOSError(RuntimeError):
    """A safe, user-facing Pastor Assistant OS error."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _windows_default_string(env: Mapping[str, str]) -> str:
    raw = (env.get("LOCALAPPDATA") or "").strip()
    if not raw:
        raise PastorOSError(
            "Windows LOCALAPPDATA is unavailable. No local OS folder was chosen."
        )
    base = PureWindowsPath(raw)
    if not base.is_absolute():
        raise PastorOSError(
            "Windows LOCALAPPDATA is not an absolute path. No files were changed."
        )
    return str(base / VENDOR / PRODUCT_FOLDER)


def default_root_string(
    system: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> str:
    """Return the OS-native local application-data location as a string."""

    system_name = system or platform.system()
    environment = env if env is not None else os.environ
    user_home = home or Path.home()
    if system_name == "Darwin":
        return str(
            user_home
            / "Library"
            / "Application Support"
            / VENDOR
            / PRODUCT_FOLDER
        )
    if system_name == "Windows":
        return _windows_default_string(environment)
    raise PastorOSError(
        "Pastor Assistant OS setup supports macOS and Windows only."
    )


def default_root() -> Path:
    return Path(default_root_string())


def _root(value: Optional[str]) -> Path:
    if value:
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise PastorOSError("The selected OS folder must use an absolute path.")
        return path
    return default_root()


def _display_path(path: Path, show_paths: bool = False) -> str:
    if show_paths:
        return str(path)
    try:
        relative = path.relative_to(Path.home())
        return "~/" + relative.as_posix()
    except ValueError:
        return "<local application data>/" + path.name


def _secure_directory(path: Path) -> None:
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _secure_file(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _secure_directory(path.parent)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=".pastor-os-",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _secure_file(temporary)
        os.replace(str(temporary), str(path))
        _secure_file(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, value: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PastorOSError(f"Required local OS file is missing: {path.name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PastorOSError(f"Local OS file is unreadable: {path.name}") from exc
    if not isinstance(value, dict):
        raise PastorOSError(f"Local OS file has the wrong format: {path.name}")
    return value


def _recognized(root: Path) -> bool:
    state_path = root / "state" / "os-state.json"
    if not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        isinstance(state, dict)
        and state.get("product") == PRODUCT_ID
        and state.get("schema_version") == SCHEMA_VERSION
    )


def _require_initialized(root: Path) -> None:
    if not _recognized(root):
        raise PastorOSError(
            "The Pastor Assistant OS is not initialized at the selected local path."
        )


@contextmanager
def _write_lock(root: Path) -> Iterator[None]:
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    _secure_directory(state_dir)
    lock = state_dir / "write.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        try:
            age = time.time() - lock.stat().st_mtime
        except OSError:
            age = 0
        if age > 300:
            raise PastorOSError(
                "A stale write lock was found. Ask the setup owner to inspect it; "
                "no files were changed."
            ) from exc
        raise PastorOSError(
            "Another Pastor Assistant task is saving a rule. Wait for it to finish."
        ) from exc
    try:
        yield
    finally:
        try:
            lock.rmdir()
        except OSError:
            pass


def _copy_template_missing(root: Path) -> List[str]:
    if not TEMPLATE_ROOT.is_dir():
        raise PastorOSError("The bundled Pastor Assistant OS template is missing.")
    created: List[str] = []
    for source in sorted(TEMPLATE_ROOT.rglob("*")):
        relative = source.relative_to(TEMPLATE_ROOT)
        target = root / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            _secure_directory(target)
            continue
        if target.exists():
            continue
        _atomic_write_text(target, source.read_text(encoding="utf-8"))
        created.append(relative.as_posix())
    return created


def _initial_state() -> Dict[str, Any]:
    timestamp = _now()
    return {
        "schema_version": SCHEMA_VERSION,
        "product": PRODUCT_ID,
        "created_at": timestamp,
        "updated_at": timestamp,
        "memory_policy": "explicit-approved-rules-only",
    }


def _empty_audit(root: Path) -> None:
    path = root / "audit" / "rule-changes.jsonl"
    if not path.exists():
        _atomic_write_text(path, "")


def plan(root: Path, show_paths: bool = False) -> Dict[str, Any]:
    return {
        "supported": True,
        "initialized": _recognized(root),
        "target": _display_path(root, show_paths=show_paths),
        "storage": "local application data",
        "cloud_sync_requested": False,
        "change_requires": CREATE_CONSENT,
    }


def initialize(root: Path, consent: str) -> Dict[str, Any]:
    if consent != CREATE_CONSENT:
        raise PastorOSError(
            f"Creation requires the exact permission: {CREATE_CONSENT}"
        )
    if root.exists() and not root.is_dir():
        raise PastorOSError("The selected OS location is not a folder.")
    if root.is_dir() and any(root.iterdir()) and not _recognized(root):
        raise PastorOSError(
            "The selected folder already contains unrelated files. Choose another local folder."
        )
    root.mkdir(parents=True, exist_ok=True)
    _secure_directory(root)
    with _write_lock(root):
        created = _copy_template_missing(root)
        state_path = root / "state" / "os-state.json"
        if not state_path.exists():
            _atomic_write_json(state_path, _initial_state())
            created.append("state/os-state.json")
        _empty_audit(root)
        if "learning/approved-rules.md" in created:
            rules_document = _load_rules(root)
            _atomic_write_text(
                root / "learning" / "approved-rules.md",
                _compiled_rules(rules_document["rules"]),
            )
        for name in ("backups", "proposals", "projects", "reviews"):
            directory = root / name
            directory.mkdir(parents=True, exist_ok=True)
            _secure_directory(directory)
    result = status(root)
    result.update({"created": sorted(created), "changed": bool(created)})
    return result


def _validate_rules_document(value: Dict[str, Any]) -> List[Dict[str, Any]]:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise PastorOSError("The local rules schema is unsupported.")
    rules = value.get("rules")
    if not isinstance(rules, list):
        raise PastorOSError("The local rules list has the wrong format.")
    for item in rules:
        if not isinstance(item, dict):
            raise PastorOSError("A local rule has the wrong format.")
        required = {
            "id",
            "status",
            "scope",
            "category",
            "rule",
            "reason",
            "created_at",
            "updated_at",
            "occurrences",
        }
        if not required.issubset(item):
            raise PastorOSError("A local rule is missing required fields.")
        if item.get("scope") != "this_pastor":
            raise PastorOSError("A local rule has an unsupported scope.")
        if item.get("status") not in {"approved", "retired"}:
            raise PastorOSError("A local rule has an unsupported status.")
        if item.get("category") not in CATEGORIES:
            raise PastorOSError("A local rule has an unsupported category.")
        if not isinstance(item.get("occurrences"), int) or item["occurrences"] < 1:
            raise PastorOSError("A local rule has an invalid occurrence count.")
    return rules


def _load_rules(root: Path) -> Dict[str, Any]:
    value = _read_json(root / "learning" / "rules.json")
    _validate_rules_document(value)
    return value


def _load_candidates(root: Path) -> Dict[str, Any]:
    value = _read_json(root / "learning" / "promotion-candidates.json")
    if value.get("schema_version") != SCHEMA_VERSION or not isinstance(
        value.get("candidates"), list
    ):
        raise PastorOSError("The promotion-candidate file has the wrong format.")
    return value


def _compiled_rules(rules: List[Dict[str, Any]]) -> str:
    approved = [item for item in rules if item.get("status") == "approved"]
    lines = [
        "# Approved Personal Rules",
        "",
        "This file is generated from `rules.json`. Built-in safety, privacy,",
        "authenticity, theology, and sermon-fidelity rules always take priority.",
        "",
    ]
    if not approved:
        lines.extend(["No approved personal rules yet.", ""])
        return "\n".join(lines)
    for category in CATEGORIES:
        items = [item for item in approved if item["category"] == category]
        if not items:
            continue
        lines.extend([f"## {category.title()}", ""])
        for item in items:
            lines.append(f"- [{item['id']}] {item['rule']}")
        lines.append("")
    return "\n".join(lines)


def _normalize_text(value: str, label: str, maximum: int = 500) -> str:
    text = " ".join((value or "").split()).strip()
    if len(text) < 5:
        raise PastorOSError(f"The {label} is too short to be useful.")
    if len(text) > maximum:
        raise PastorOSError(f"The {label} is too long for private rule memory.")
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise PastorOSError(
                f"The {label} appears to contain private contact, link, or path data."
            )
    return text


def _enforce_safety(rule: str) -> None:
    lowered = rule.casefold()
    safe_negative = lowered.startswith(("never ", "do not ", "don't "))
    for phrase in UNSAFE_PHRASES:
        if phrase in lowered and not safe_negative:
            raise PastorOSError(
                "The proposed rule could weaken a core safety or fidelity rule."
            )


def _next_rule_id(rules: List[Dict[str, Any]]) -> str:
    numbers: List[int] = []
    for item in rules:
        match = re.fullmatch(r"PAR-(\d{4})", str(item.get("id", "")))
        if match:
            numbers.append(int(match.group(1)))
    return f"PAR-{max(numbers, default=0) + 1:04d}"


def _backup(root: Path, names: List[str]) -> Optional[str]:
    existing = [root / name for name in names if (root / name).is_file()]
    if not existing:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / "backups" / stamp
    suffix = 1
    while base.exists():
        base = root / "backups" / f"{stamp}-{suffix}"
        suffix += 1
    base.mkdir(parents=True)
    _secure_directory(base)
    for source in existing:
        target = base / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        _secure_file(target)
    return base.name


def _append_audit(root: Path, event: Dict[str, Any]) -> None:
    path = root / "audit" / "rule-changes.jsonl"
    event_value = {"timestamp": _now(), **event}
    line = json.dumps(event_value, ensure_ascii=False, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_write_text(path, previous + line)


def _save_learning_documents(
    root: Path,
    rules_document: Dict[str, Any],
    candidates_document: Dict[str, Any],
    audit_event: Dict[str, Any],
) -> None:
    rules = _validate_rules_document(rules_document)
    approved_text = _compiled_rules(rules)
    paths = (
        root / "learning" / "rules.json",
        root / "learning" / "approved-rules.md",
        root / "learning" / "promotion-candidates.json",
        root / "audit" / "rule-changes.jsonl",
    )
    previous: Dict[Path, Optional[str]] = {}
    for path in paths:
        previous[path] = path.read_text(encoding="utf-8") if path.exists() else None
    try:
        _atomic_write_json(paths[0], rules_document)
        _atomic_write_text(paths[1], approved_text)
        _atomic_write_json(paths[2], candidates_document)
        _append_audit(root, audit_event)
    except Exception as exc:
        restore_errors: List[str] = []
        for path, content in previous.items():
            try:
                if content is None:
                    if path.exists():
                        path.unlink()
                else:
                    _atomic_write_text(path, content)
            except OSError:
                restore_errors.append(path.name)
        if restore_errors:
            raise PastorOSError(
                "Learning save failed and its local rollback needs administrator review."
            ) from exc
        raise PastorOSError(
            "Learning save failed; the previous approved rules were restored."
        ) from exc


def _ensure_candidate(
    candidates: List[Dict[str, Any]], rule: Dict[str, Any], trigger: str
) -> bool:
    for item in candidates:
        if item.get("rule_id") == rule["id"] and item.get("status") == "local_review":
            item["occurrences"] = rule["occurrences"]
            item["updated_at"] = _now()
            return False
    timestamp = _now()
    candidates.append(
        {
            "rule_id": rule["id"],
            "status": "local_review",
            "trigger": trigger,
            "occurrences": rule["occurrences"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    return True


def remember(
    root: Path,
    category: str,
    rule_text: str,
    reason_text: str,
    consent: str,
    high_risk: bool = False,
) -> Dict[str, Any]:
    _require_initialized(root)
    if consent != SAVE_CONSENT:
        raise PastorOSError(f"Saving requires the exact permission: {SAVE_CONSENT}")
    if category not in CATEGORIES:
        raise PastorOSError("The selected rule category is not supported.")
    rule = _normalize_text(rule_text, "rule")
    reason = _normalize_text(reason_text, "reason", maximum=240)
    _enforce_safety(rule)

    with _write_lock(root):
        rules_document = _load_rules(root)
        candidates_document = _load_candidates(root)
        rules = rules_document["rules"]
        duplicate = next(
            (
                item
                for item in rules
                if item.get("status") == "approved"
                and str(item.get("rule", "")).casefold() == rule.casefold()
            ),
            None,
        )
        timestamp = _now()
        if duplicate:
            duplicate["occurrences"] += 1
            duplicate["updated_at"] = timestamp
            saved_rule = duplicate
            event_name = "rule_confirmed_again"
        else:
            saved_rule = {
                "id": _next_rule_id(rules),
                "status": "approved",
                "scope": "this_pastor",
                "category": category,
                "rule": rule,
                "reason": reason,
                "created_at": timestamp,
                "updated_at": timestamp,
                "occurrences": 1,
            }
            rules.append(saved_rule)
            event_name = "rule_approved"

        candidate_added = False
        trigger = ""
        if saved_rule["occurrences"] >= 2:
            trigger = "repeated_approved_correction"
        elif high_risk:
            trigger = "approved_high_risk_correction"
        if trigger:
            candidate_added = _ensure_candidate(
                candidates_document["candidates"], saved_rule, trigger
            )

        backup = _backup(
            root,
            [
                "learning/rules.json",
                "learning/approved-rules.md",
                "learning/promotion-candidates.json",
            ],
        )
        _save_learning_documents(
            root,
            rules_document,
            candidates_document,
            {
                "event": event_name,
                "rule_id": saved_rule["id"],
                "category": saved_rule["category"],
                "occurrences": saved_rule["occurrences"],
            },
        )
    return {
        "saved": True,
        "rule_id": saved_rule["id"],
        "scope": "this_pastor",
        "occurrences": saved_rule["occurrences"],
        "promotion_candidate": bool(trigger),
        "promotion_candidate_added": candidate_added,
        "backup": backup,
    }


def forget(root: Path, rule_id: str, consent: str) -> Dict[str, Any]:
    _require_initialized(root)
    if consent != FORGET_CONSENT:
        raise PastorOSError(f"Forgetting requires the exact permission: {FORGET_CONSENT}")
    with _write_lock(root):
        rules_document = _load_rules(root)
        candidates_document = _load_candidates(root)
        target = next(
            (item for item in rules_document["rules"] if item.get("id") == rule_id),
            None,
        )
        if not target:
            raise PastorOSError("The requested local rule was not found.")
        if target.get("status") == "retired":
            return {"forgotten": True, "rule_id": rule_id, "changed": False}
        backup = _backup(
            root,
            [
                "learning/rules.json",
                "learning/approved-rules.md",
                "learning/promotion-candidates.json",
            ],
        )
        target["status"] = "retired"
        target["updated_at"] = _now()
        for candidate in candidates_document["candidates"]:
            if candidate.get("rule_id") == rule_id:
                candidate["status"] = "closed_rule_retired"
                candidate["updated_at"] = _now()
        _save_learning_documents(
            root,
            rules_document,
            candidates_document,
            {"event": "rule_retired", "rule_id": rule_id},
        )
    return {
        "forgotten": True,
        "rule_id": rule_id,
        "changed": True,
        "backup": backup,
    }


def propose_church_rule(
    root: Path, rule_id: str, reason_text: str, consent: str
) -> Dict[str, Any]:
    _require_initialized(root)
    if consent != PROPOSAL_CONSENT:
        raise PastorOSError(
            f"A church proposal requires the exact permission: {PROPOSAL_CONSENT}"
        )
    reason = _normalize_text(reason_text, "proposal reason", maximum=240)
    with _write_lock(root):
        rules_document = _load_rules(root)
        rule = next(
            (
                item
                for item in rules_document["rules"]
                if item.get("id") == rule_id and item.get("status") == "approved"
            ),
            None,
        )
        if not rule:
            raise PastorOSError("Only an active approved rule can become a proposal.")
        target = root / "proposals" / f"{rule_id.lower()}-church-rule.json"
        if target.exists():
            raise PastorOSError(
                "A local church-rule proposal already exists for this rule."
            )
        proposal = {
            "schema_version": SCHEMA_VERSION,
            "status": "administrator_review_required",
            "rule_id": rule_id,
            "category": rule["category"],
            "proposed_rule": rule["rule"],
            "generalized_reason": reason,
            "occurrences": rule["occurrences"],
            "created_at": _now(),
            "automatic_publish": False,
        }
        _atomic_write_json(target, proposal)
        _append_audit(
            root, {"event": "church_rule_proposal_created", "rule_id": rule_id}
        )
    return {
        "created": True,
        "rule_id": rule_id,
        "proposal": target.name,
        "administrator_review_required": True,
        "published": False,
    }


def status(root: Path, show_paths: bool = False) -> Dict[str, Any]:
    initialized = _recognized(root)
    result: Dict[str, Any] = {
        "initialized": initialized,
        "root": _display_path(root, show_paths=show_paths),
        "storage": "local application data",
    }
    if not initialized:
        result.update(
            {
                "approved_rules": 0,
                "promotion_candidates": 0,
                "doctor_required": True,
            }
        )
        return result
    try:
        rules = _validate_rules_document(
            _read_json(root / "learning" / "rules.json")
        )
        candidates = _load_candidates(root)["candidates"]
        result.update(
            {
                "approved_rules": sum(
                    1 for item in rules if item.get("status") == "approved"
                ),
                "retired_rules": sum(
                    1 for item in rules if item.get("status") == "retired"
                ),
                "promotion_candidates": sum(
                    1 for item in candidates if item.get("status") == "local_review"
                ),
                "doctor_required": False,
            }
        )
    except PastorOSError:
        result.update(
            {
                "approved_rules": 0,
                "promotion_candidates": 0,
                "doctor_required": True,
            }
        )
    return result


def context(root: Path) -> Dict[str, Any]:
    _require_initialized(root)
    rules = _validate_rules_document(_read_json(root / "learning" / "rules.json"))
    return {
        "approved_rules": [
            {
                "id": item["id"],
                "category": item["category"],
                "rule": item["rule"],
                "occurrences": item["occurrences"],
            }
            for item in rules
            if item.get("status") == "approved"
        ],
        "church_profile": (root / "profile" / "church-profile.md").read_text(
            encoding="utf-8"
        ),
        "pastor_preferences": (
            root / "profile" / "pastor-preferences.md"
        ).read_text(encoding="utf-8"),
        "privacy_note": "Use locally for this task; do not paste or publish wholesale.",
    }


def doctor(root: Path, show_paths: bool = False) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if not _recognized(root):
        errors.append("not_initialized")
        return {
            "healthy": False,
            "root": _display_path(root, show_paths=show_paths),
            "errors": errors,
            "warnings": warnings,
        }
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        errors.extend(f"missing:{name}" for name in missing)
    try:
        rules = _validate_rules_document(
            _read_json(root / "learning" / "rules.json")
        )
        candidates = _load_candidates(root)["candidates"]
        expected = _compiled_rules(rules)
        actual = (root / "learning" / "approved-rules.md").read_text(
            encoding="utf-8"
        )
        if actual != expected:
            errors.append("compiled_rules_out_of_sync")
        active = sum(1 for item in rules if item.get("status") == "approved")
        candidate_count = sum(
            1 for item in candidates if item.get("status") == "local_review"
        )
    except (PastorOSError, OSError):
        errors.append("learning_files_invalid")
        active = 0
        candidate_count = 0
    lock = root / "state" / "write.lock"
    if lock.exists():
        warnings.append("write_in_progress_or_stale_lock")
    if os.name != "nt":
        for name in REQUIRED_FILES:
            path = root / name
            if path.is_file() and path.stat().st_mode & 0o077:
                warnings.append(f"permissions:{name}")
    return {
        "healthy": not errors,
        "root": _display_path(root, show_paths=show_paths),
        "approved_rules": active,
        "promotion_candidates": candidate_count,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "contains_rule_text": False,
    }


def _add_common(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--root", help="Approved alternate absolute local OS path")
    subparser.add_argument("--json", action="store_true", help="Print JSON output")
    subparser.add_argument(
        "--show-paths", action="store_true", help="Show the full local path"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "status", "context", "doctor"):
        command = commands.add_parser(name)
        _add_common(command)
    init_parser = commands.add_parser("init")
    _add_common(init_parser)
    init_parser.add_argument("--consent", required=True)

    remember_parser = commands.add_parser("remember")
    _add_common(remember_parser)
    remember_parser.add_argument("--category", required=True, choices=CATEGORIES)
    remember_parser.add_argument("--rule", required=True)
    remember_parser.add_argument("--reason", required=True)
    remember_parser.add_argument("--consent", required=True)
    remember_parser.add_argument("--high-risk", action="store_true")

    forget_parser = commands.add_parser("forget")
    _add_common(forget_parser)
    forget_parser.add_argument("--id", required=True)
    forget_parser.add_argument("--consent", required=True)

    proposal_parser = commands.add_parser("propose-church-rule")
    _add_common(proposal_parser)
    proposal_parser.add_argument("--id", required=True)
    proposal_parser.add_argument("--reason", required=True)
    proposal_parser.add_argument("--consent", required=True)
    return parser


def _print(value: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return
    for key, item in value.items():
        print(f"{key}: {item}")


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = _root(args.root)
        if args.command == "plan":
            result = plan(root, show_paths=args.show_paths)
        elif args.command == "init":
            result = initialize(root, args.consent)
        elif args.command == "status":
            result = status(root, show_paths=args.show_paths)
        elif args.command == "context":
            result = context(root)
        elif args.command == "doctor":
            result = doctor(root, show_paths=args.show_paths)
        elif args.command == "remember":
            result = remember(
                root,
                args.category,
                args.rule,
                args.reason,
                args.consent,
                high_risk=args.high_risk,
            )
        elif args.command == "forget":
            result = forget(root, args.id, args.consent)
        elif args.command == "propose-church-rule":
            result = propose_church_rule(root, args.id, args.reason, args.consent)
        else:
            raise PastorOSError("Unknown Pastor Assistant OS command.")
        _print(result, args.json)
        if args.command == "doctor" and not result.get("healthy"):
            return 1
        return 0
    except PastorOSError as exc:
        error = {"ok": False, "error": str(exc), "changed": False}
        _print(error, getattr(args, "json", False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
