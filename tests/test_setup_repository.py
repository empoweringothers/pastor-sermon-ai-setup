from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SetupRepositoryTests(unittest.TestCase):
    def test_manifests_point_to_the_bundled_plugin(self) -> None:
        plugin_manifest = json.loads(
            (
                REPO_ROOT / "plugins/sermon-slide-builder/.codex-plugin/plugin.json"
            ).read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (REPO_ROOT / ".agents/plugins/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(plugin_manifest["name"], "sermon-slide-builder")
        self.assertEqual(plugin_manifest["skills"], "./skills/")
        self.assertEqual(plugin_manifest["interface"]["capabilities"], ["Interactive", "Write"])
        prompts = plugin_manifest["interface"]["defaultPrompt"]
        self.assertIsInstance(prompts, list)
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(0 < len(prompt) <= 128 for prompt in prompts))
        entries = [
            item
            for item in marketplace["plugins"]
            if item["name"] == "sermon-slide-builder"
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"]["path"], "./plugins/sermon-slide-builder")

    def test_setup_contract_separates_questions_actions_and_permission(self) -> None:
        protocol = (REPO_ROOT / "SETUP-ASSISTANT.md").read_text(encoding="utf-8")
        self.assertIn("one question, one permission request, or one action", protocol)
        self.assertIn("A reply of `DONE` is never permission", protocol)
        self.assertIn("Reply exactly: YES, <SPECIFIC CHANGE>", protocol)
        self.assertIn("Do not teach prompting", protocol)
        self.assertIn("Do not install Java", protocol)

    def test_paste_message_contains_local_safety_rules_and_release_pins(self) -> None:
        message = (REPO_ROOT / "PASTE-INTO-CHATGPT.txt").read_text(encoding="utf-8")
        self.assertIn("{{GITHUB_RELEASE_URL}}", message)
        self.assertIn("{{GIT_COMMIT_SHA}}", message)
        self.assertIn("{{RELEASE_ZIP_SHA256}}", message)
        self.assertIn("DONE never gives permission", message)
        self.assertIn(
            "Do not disable my security settings", " ".join(message.split())
        )

    def test_public_package_has_no_absolute_private_paths(self) -> None:
        private_path_patterns = (
            re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
            re.compile(r"/Volumes/[A-Za-z0-9_. -]+/"),
        )
        text_extensions = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".css", ".html"}
        for path in REPO_ROOT.rglob("*"):
            if path.is_file() and path.suffix in text_extensions:
                content = path.read_text(encoding="utf-8", errors="replace")
                for pattern in private_path_patterns:
                    self.assertIsNone(pattern.search(content), str(path))

    def test_environment_report_is_private_and_presence_only_by_default(self) -> None:
        checker = load_script("check_environment")
        report = checker.build_report()
        self.assertTrue(report["privacy"]["paths_redacted"])
        self.assertFalse(report["privacy"]["versions_executed"])
        self.assertFalse(report["conditional"]["java"]["required"])
        self.assertFalse(report["conditional"]["node"]["required"])
        self.assertFalse(report["conditional"]["git"]["required"])
        self.assertNotIn(str(Path.home()), json.dumps(report))
        self.assertEqual(report["required"]["repository"]["status"], "pass")

    def test_preparer_backup_remove_and_restore(self) -> None:
        preparer = load_script("prepare_plugin")
        with tempfile.TemporaryDirectory(prefix="sermon-plugin-test-") as value:
            home = Path(value)
            first = preparer.prepare(home, show_paths=True)
            self.assertTrue(first["source_registered"])
            self.assertTrue(first["target_matches_source"])
            self.assertTrue(first["plugins_directory_action_required"])

            second = preparer.prepare(home, show_paths=True)
            backup = Path(second["backup_bundle"])
            self.assertTrue(backup.is_dir())

            removed = preparer.remove_source(home, show_paths=True)
            self.assertFalse(removed["source_registered"])
            self.assertTrue(removed["uninstall_in_plugins_directory_still_required"])

            restored = preparer.restore(home, backup, show_paths=True)
            self.assertTrue(restored["source_registered"])
            marketplace = json.loads(
                (home / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
            )
            entries = [
                item
                for item in marketplace["plugins"]
                if item["name"] == "sermon-slide-builder"
            ]
            self.assertEqual(len(entries), 1)

            invalid = home / "invalid-backup"
            invalid.mkdir()
            (invalid / "metadata.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "plugin_name": "sermon-slide-builder",
                        "target_existed": True,
                        "marketplace_existed": False,
                    }
                ),
                encoding="utf-8",
            )
            before = preparer.check(home, show_paths=True)
            with self.assertRaises(ValueError):
                preparer.restore(home, invalid, show_paths=True)
            after = preparer.check(home, show_paths=True)
            self.assertEqual(before["target_matches_source"], after["target_matches_source"])
            self.assertEqual(before["source_registered"], after["source_registered"])

    def test_slide_layout_rule_separates_text_and_images(self) -> None:
        skill_root = REPO_ROOT / "plugins/sermon-slide-builder/skills/create-sermon-slides"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        profile = (skill_root / "references/church-style-profile.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Never place sermon words on top of", skill)
        self.assertIn("recent pastor-approved sermon PowerPoint", skill)
        self.assertIn("Never place sermon words over", profile)

    def test_biblical_images_have_scoped_generation_and_character_continuity(self) -> None:
        skill_root = REPO_ROOT / "plugins/sermon-slide-builder/skills/create-sermon-slides"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            skill_root / "references/biblical-photorealistic-image-set.md"
        ).read_text(encoding="utf-8")
        self.assertIn("point and first-level lettered subpoint only", skill)
        self.assertIn("Peter must look like the same Peter", skill)
        self.assertIn("character-continuity.md", reference)
        self.assertIn("The first eligible sermon image becomes the visual", reference)
        self.assertIn("Do not add a separate character portrait", reference)
        self.assertIn("All sermon text stays in the PowerPoint's separate text region", reference)
        image_policy = (skill_root / "references/image-research-policy.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("negative space for the sermon copy", image_policy)
        self.assertIn("reference-image and character", image_policy)
        self.assertIn("eligible-heading count equals the generated-image count", skill)

    def test_release_builder_stages_a_self_verifying_package(self) -> None:
        builder = load_script("build_release")
        with tempfile.TemporaryDirectory(prefix="sermon-release-test-") as value:
            root = Path(value)
            source = root / "source"
            shutil.copytree(REPO_ROOT, source)
            (source / "LICENSE").write_text("Temporary test license\n", encoding="utf-8")
            builder.REPO_ROOT = source
            builder.PLUGIN_MANIFEST = (
                source / "plugins/sermon-slide-builder/.codex-plugin/plugin.json"
            )
            release_url = "https://github.com/example/example/releases/tag/v0.1.0"
            commit = "a" * 40
            builder.validate_inputs(release_url, commit)
            with self.assertRaises(ValueError):
                builder.validate_inputs(
                    "https://github.com/example/example/releases/tag/v9.9.9",
                    commit,
                )

            prior_output = source / "release"
            prior_output.mkdir()
            (prior_output / "old-release.zip").write_bytes(b"old release")

            stage = root / "stage"
            stage.mkdir()
            builder.copy_release_tree(
                stage,
                release_url,
                commit,
                excluded_roots=(prior_output,),
            )
            builder.write_file_manifest(stage, "0.1.0", commit)
            builder.verify_staged_tree(stage)
            archive = root / "release.zip"
            builder.write_zip(stage, archive)
            self.assertTrue(archive.is_file())
            self.assertEqual(len(builder.file_sha256(archive)), 64)
            self.assertFalse((stage / "PASTE-INTO-CHATGPT.txt").exists())
            self.assertFalse((stage / "release").exists())
            self.assertFalse((stage / "RELEASE-README.md").exists())
            staged_readme = (stage / "README.md").read_text(encoding="utf-8")
            self.assertIn("Start with the separate setup message", staged_readme)
            self.assertNotIn("scripts/build_release.py", staged_readme)
            release = json.loads((stage / "RELEASE.json").read_text(encoding="utf-8"))
            self.assertEqual(release["release_url"], release_url)
            self.assertEqual(release["git_commit"], commit)
            release_data = (stage / "setup-ui/release-data.js").read_text(
                encoding="utf-8"
            )
            self.assertIn("window.PASTOR_SERMON_RELEASE", release_data)
            self.assertIn('"messageTemplate"', release_data)
            self.assertIn("{{RELEASE_ZIP_SHA256}}", release_data)
            self.assertIn('"packageVersion": "0.1.0"', release_data)
            self.assertIn('"releaseTag": "v0.1.0"', release_data)

    def test_release_builder_requires_clean_tagged_git_head(self) -> None:
        builder = load_script("build_release")
        with tempfile.TemporaryDirectory(prefix="sermon-git-release-test-") as value:
            source = Path(value) / "source"
            shutil.copytree(REPO_ROOT, source)
            (source / "LICENSE").write_text("Temporary test license\n", encoding="utf-8")
            commands = [
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Release Test"],
                ["git", "add", "."],
                ["git", "commit", "-m", "test release"],
                ["git", "tag", "v0.1.0"],
                ["git", "remote", "add", "origin", "https://github.com/example/example.git"],
            ]
            for command in commands:
                subprocess.run(command, cwd=source, check=True, capture_output=True)

            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            builder.REPO_ROOT = source
            builder.PLUGIN_MANIFEST = (
                source / "plugins/sermon-slide-builder/.codex-plugin/plugin.json"
            )
            release_url = "https://github.com/example/example/releases/tag/v0.1.0"
            builder.validate_git_state(release_url, commit, "v0.1.0")

            (source / "README.md").write_text("dirty\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                builder.validate_git_state(release_url, commit, "v0.1.0")

    def test_setup_ui_never_persists_clipboard_readiness(self) -> None:
        app = (REPO_ROOT / "setup-ui/app.js").read_text(encoding="utf-8")
        html = (REPO_ROOT / "setup-ui/index.html").read_text(encoding="utf-8")
        self.assertIn('normalized.stage === "open-chatgpt"', app)
        self.assertIn('normalized.stage === "confirm-chatgpt"', app)
        self.assertIn('normalized.stage === "paste-message"', app)
        self.assertIn("clipboard state are never", app)
        self.assertIn("The full setup message does not match", app)
        self.assertIn("The ZIP itself is not verified yet", app)
        self.assertEqual(html.count('data-status="'), 1)
        self.assertIn("Copy help prompt", html)
        self.assertNotIn("Copy help prompt &amp; open ChatGPT", html)
        self.assertIn('aria-label="Ask Setup Help"', html)
        self.assertIn("Reset this launcher", html)
        self.assertIn("Something else", app)
        self.assertIn("I don\\'t know", app)


if __name__ == "__main__":
    unittest.main()
