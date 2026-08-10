#!/usr/bin/env python3
"""Dependency-free validation for this repository's plugin and skill package."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins/sermon-slide-builder"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def validate() -> list[str]:
    errors: list[str] = []
    manifest_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["Plugin manifest is missing or invalid JSON."]
    for key in ("name", "version", "description", "author", "interface"):
        if key not in manifest:
            errors.append(f"Plugin manifest is missing {key}.")
    if manifest.get("name") != "sermon-slide-builder":
        errors.append("Plugin name must be sermon-slide-builder.")
    if not isinstance(manifest.get("version"), str) or not SEMVER.fullmatch(
        manifest.get("version", "")
    ):
        errors.append("Plugin version must be strict major.minor.patch semver.")
    if manifest.get("skills") != "./skills/":
        errors.append("Plugin skills path must be ./skills/.")

    interface = manifest.get("interface", {})
    expected_caps = {"Interactive", "Write"}
    if set(interface.get("capabilities", [])) != expected_caps:
        errors.append("Plugin capabilities must be Interactive and Write.")
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("interface.defaultPrompt must contain one to three prompts.")
    elif not all(isinstance(item, str) and 0 < len(item) <= 128 for item in prompts):
        errors.append("Each default prompt must be a non-empty string of at most 128 characters.")

    skill = PLUGIN_ROOT / "skills/create-sermon-slides/SKILL.md"
    if not skill.is_file():
        errors.append("Bundled create-sermon-slides SKILL.md is missing.")
    else:
        content = skill.read_text(encoding="utf-8")
        frontmatter = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter:
            errors.append("Skill YAML frontmatter is missing.")
        else:
            header = frontmatter.group(1)
            if not re.search(r"^name:\s*create-sermon-slides\s*$", header, re.MULTILINE):
                errors.append("Skill name is invalid.")
            if not re.search(r"^description:\s*\S", header, re.MULTILINE):
                errors.append("Skill description is missing.")
        if "Never place sermon words on top of" not in content:
            errors.append("The no-text-over-images layout rule is missing.")

    marketplace_path = REPO_ROOT / ".agents/plugins/marketplace.json"
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append("Repository marketplace is missing or invalid.")
    else:
        entries = [
            item
            for item in marketplace.get("plugins", [])
            if isinstance(item, dict) and item.get("name") == "sermon-slide-builder"
        ]
        if len(entries) != 1:
            errors.append("Marketplace must contain exactly one sermon-slide-builder entry.")
        elif entries[0].get("source", {}).get("path") != "./plugins/sermon-slide-builder":
            errors.append("Marketplace plugin path is invalid.")

    unwanted = [
        path
        for path in REPO_ROOT.rglob("*")
        if (path.is_dir() and path.name == "__pycache__")
        or (path.is_file() and (path.suffix == ".pyc" or path.name == ".DS_Store"))
    ]
    if unwanted:
        errors.append("Generated cache or desktop metadata files are present.")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("PACKAGE VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("PACKAGE VALIDATION PASSED")


if __name__ == "__main__":
    main()
