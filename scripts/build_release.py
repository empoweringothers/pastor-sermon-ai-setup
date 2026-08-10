#!/usr/bin/env python3
"""Build a pinned pastor release ZIP and external ChatGPT paste message."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MANIFEST = (
    REPO_ROOT / "plugins/sermon-slide-builder/.codex-plugin/plugin.json"
)
EXCLUDED_NAMES = {
    ".DS_Store",
    "FILE-SHA256SUMS.json",
    "PASTE-INTO-CHATGPT.txt",
    "PUBLISHING-CHECKLIST.md",
    "RELEASE-README.md",
    "TESTING.md",
    "setup-state.local.json",
}
EXCLUDED_PARTS = {".git", "__pycache__"}
EXCLUDED_SOURCE_PATHS = {
    "scripts/build_release.py",
    "scripts/check_publish_ready.py",
    "tests/test_setup_repository.py",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included(relative: Path) -> bool:
    if relative.name in EXCLUDED_NAMES or relative.suffix == ".pyc":
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    return relative.as_posix() not in EXCLUDED_SOURCE_PATHS


def release_identity() -> tuple[str, str]:
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    release = json.loads((REPO_ROOT / "RELEASE.json").read_text(encoding="utf-8"))
    version = str(plugin["version"])
    expected_tag = f"v{version}"
    if str(release.get("package_version")) != version:
        raise ValueError("RELEASE.json package_version must match plugin.json version.")
    if str(release.get("release_tag")) != expected_tag:
        raise ValueError("RELEASE.json release_tag must be v<plugin version>.")
    return version, expected_tag


def github_release_identity(release_url: str) -> tuple[str, str, str]:
    parsed = urlparse(release_url)
    parts = [unquote(part) for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or len(parts) != 5
        or parts[2:4] != ["releases", "tag"]
    ):
        raise ValueError("Use an https://github.com/OWNER/REPO/releases/tag/TAG URL.")
    return parts[0], parts[1].removesuffix(".git"), parts[4]


def validate_inputs(release_url: str, commit: str) -> None:
    _, expected_tag = release_identity()
    _, _, supplied_tag = github_release_identity(release_url)
    if supplied_tag != expected_tag:
        raise ValueError(f"Release URL tag must be {expected_tag}.")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("Commit must be a full 40-character hexadecimal SHA.")
    if not (REPO_ROOT / "LICENSE").is_file():
        raise ValueError("Choose and add LICENSE before building a public release.")
    template = (REPO_ROOT / "PASTE-INTO-CHATGPT.txt").read_text(encoding="utf-8")
    for marker in (
        "{{GITHUB_RELEASE_URL}}",
        "{{GIT_COMMIT_SHA}}",
        "{{RELEASE_ZIP_SHA256}}",
    ):
        if marker not in template:
            raise ValueError(f"Paste-message template is missing {marker}.")


def run_git(*arguments: str) -> str:
    git = shutil.which("git")
    if not git:
        raise ValueError("Git is required only for the publisher's release build.")
    completed = subprocess.run(
        [git, "-C", str(REPO_ROOT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Git command failed."
        raise ValueError(detail)
    return completed.stdout.strip()


def normalize_github_remote(value: str) -> str:
    remote = value.strip()
    if remote.startswith("git@github.com:"):
        path = remote.split(":", 1)[1]
    else:
        parsed = urlparse(remote)
        if parsed.hostname != "github.com":
            return ""
        path = parsed.path.lstrip("/")
    return path.removesuffix(".git").strip("/").lower()


def validate_git_state(release_url: str, commit: str, expected_tag: str) -> None:
    repository_root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    if repository_root != REPO_ROOT.resolve():
        raise ValueError("Build from the root of the Git repository being released.")
    head = run_git("rev-parse", "HEAD").lower()
    if head != commit.lower():
        raise ValueError("The supplied commit must equal the repository's current HEAD.")
    tagged_commit = run_git(
        "rev-parse", f"refs/tags/{expected_tag}^{{commit}}"
    ).lower()
    if tagged_commit != commit.lower():
        raise ValueError(f"Tag {expected_tag} must point to the supplied commit.")
    if run_git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("The repository must be clean before building a release.")

    owner, repository, _ = github_release_identity(release_url)
    expected_remote = f"{owner}/{repository}".lower()
    actual_remote = normalize_github_remote(run_git("remote", "get-url", "origin"))
    if actual_remote != expected_remote:
        raise ValueError("The Git origin must match the repository in the release URL.")


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def copy_release_tree(
    destination: Path,
    release_url: str,
    commit: str,
    excluded_roots: tuple[Path, ...] = (),
) -> None:
    for source in REPO_ROOT.rglob("*"):
        if not source.is_file():
            continue
        if any(path_is_within(source, root) for root in excluded_roots):
            continue
        relative = source.relative_to(REPO_ROOT)
        if not included(relative):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    shutil.copy2(REPO_ROOT / "RELEASE-README.md", destination / "README.md")

    release_path = destination / "RELEASE.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    release["release_url"] = release_url
    release["git_commit"] = commit.lower()
    release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

    fallback_path = destination / "setup-ui/release-data.js"
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback = {
        "publisher": release["publisher"],
        "releaseUrl": release["release_url"],
        "gitCommit": release["git_commit"],
        "packageVersion": release["package_version"],
        "releaseTag": release["release_tag"],
        "messageTemplate": (
            REPO_ROOT / "PASTE-INTO-CHATGPT.txt"
        ).read_text(encoding="utf-8"),
    }
    fallback_path.write_text(
        "window.PASTOR_SERMON_RELEASE = "
        + json.dumps(fallback, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def write_file_manifest(root: Path, version: str, commit: str) -> Path:
    files: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "FILE-SHA256SUMS.json":
            continue
        files[path.relative_to(root).as_posix()] = file_sha256(path)
    manifest = {
        "schema_version": 1,
        "package_version": version,
        "git_commit": commit.lower(),
        "algorithm": "sha256",
        "files": files,
    }
    path = root / "FILE-SHA256SUMS.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_staged_tree(root: Path) -> None:
    manifest = json.loads((root / "FILE-SHA256SUMS.json").read_text(encoding="utf-8"))
    expected = manifest["files"]
    actual = {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in root.rglob("*")
        if path.is_file() and path.name != "FILE-SHA256SUMS.json"
    }
    if expected != actual:
        raise RuntimeError("Staged release failed its file-integrity self-check.")
    release_text = (root / "RELEASE.json").read_text(encoding="utf-8")
    if "{{GITHUB_" in release_text or "{{GIT_" in release_text:
        raise RuntimeError("Staged RELEASE.json still contains placeholders.")


def write_zip(root: Path, output: Path) -> None:
    folder_name = "pastor-sermon-ai-setup"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            archive.write(path, f"{folder_name}/{path.relative_to(root).as_posix()}")


def atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_name(path.name + ".new")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-url", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    validate_inputs(args.release_url, args.commit)

    version, expected_tag = release_identity()
    validate_git_state(args.release_url, args.commit, expected_tag)

    output_root = args.out.expanduser().resolve()
    repository_root = REPO_ROOT.resolve()
    if output_root == repository_root or path_is_within(repository_root, output_root):
        raise ValueError("--out cannot be the repository root or one of its parent folders.")

    output_root.mkdir(parents=True, exist_ok=True)
    zip_path = output_root / f"pastor-sermon-ai-setup-v{version}.zip"

    with tempfile.TemporaryDirectory(prefix="pastor-sermon-ai-release-") as value:
        stage = Path(value) / "pastor-sermon-ai-setup"
        stage.mkdir()
        copy_release_tree(
            stage,
            args.release_url,
            args.commit,
            excluded_roots=(output_root,),
        )
        write_file_manifest(stage, version, args.commit)
        verify_staged_tree(stage)
        temporary_zip = zip_path.with_name(zip_path.name + ".new")
        try:
            write_zip(stage, temporary_zip)
            os.replace(temporary_zip, zip_path)
        finally:
            if temporary_zip.exists():
                temporary_zip.unlink()

    zip_digest = file_sha256(zip_path)
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    atomic_write_text(checksum_path, f"{zip_digest}  {zip_path.name}\n")

    message = (REPO_ROOT / "PASTE-INTO-CHATGPT.txt").read_text(encoding="utf-8")
    message = message.replace("{{GITHUB_RELEASE_URL}}", args.release_url)
    message = message.replace("{{GIT_COMMIT_SHA}}", args.commit.lower())
    message = message.replace("{{RELEASE_ZIP_SHA256}}", zip_digest)
    message_path = output_root / "PASTOR-SETUP-MESSAGE.txt"
    atomic_write_text(message_path, message)

    print(f"Release ZIP: {zip_path}")
    print(f"Checksum: {checksum_path}")
    print(f"Pastor message: {message_path}")


if __name__ == "__main__":
    main()
