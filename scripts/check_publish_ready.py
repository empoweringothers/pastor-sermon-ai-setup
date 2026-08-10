#!/usr/bin/env python3
"""Check whether the source repository can build a pastor release."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
from validate_package import validate as validate_package  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]


def problems() -> list[str]:
    found: list[str] = []
    if not (REPO_ROOT / "LICENSE").is_file():
        found.append("Choose and add LICENSE before public distribution.")
    template = REPO_ROOT / "PASTE-INTO-CHATGPT.txt"
    content = template.read_text(encoding="utf-8")
    for marker in (
        "{{GITHUB_RELEASE_URL}}",
        "{{GIT_COMMIT_SHA}}",
        "{{RELEASE_ZIP_SHA256}}",
    ):
        if marker not in content:
            found.append(f"Paste-message template is missing {marker}.")
    if not (REPO_ROOT / "scripts/build_release.py").is_file():
        found.append("Release builder is missing.")
    found.extend(validate_package())

    try:
        plugin = json.loads(
            (
                REPO_ROOT
                / "plugins/sermon-slide-builder/.codex-plugin/plugin.json"
            ).read_text(encoding="utf-8")
        )
        release = json.loads((REPO_ROOT / "RELEASE.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        found.append("Plugin or release identity JSON is missing or invalid.")
    else:
        version = str(plugin.get("version", ""))
        if release.get("package_version") != version:
            found.append("RELEASE.json package_version does not match plugin version.")
        if release.get("release_tag") != f"v{version}":
            found.append("RELEASE.json release_tag does not match plugin version.")

        config = (REPO_ROOT / "setup-ui/config.js").read_text(encoding="utf-8")
        fallback = (REPO_ROOT / "setup-ui/release-data.js").read_text(
            encoding="utf-8"
        )
        if not re.search(
            rf'pluginVersion:\s*"{re.escape(version)}"', config
        ):
            found.append("setup-ui/config.js pluginVersion does not match plugin version.")
        if f'packageVersion: "{version}"' not in fallback:
            found.append("setup-ui/release-data.js packageVersion does not match.")
        if f'releaseTag: "v{version}"' not in fallback:
            found.append("setup-ui/release-data.js releaseTag does not match.")
    return found


def main() -> None:
    found = problems()
    if found:
        print("SOURCE IS NOT READY FOR A PUBLIC RELEASE BUILD")
        for item in found:
            print(f"- {item}")
        raise SystemExit(1)
    print("SOURCE IS READY FOR THE RELEASE BUILDER")


if __name__ == "__main__":
    main()
