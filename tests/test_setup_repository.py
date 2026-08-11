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
        self.assertEqual(plugin_manifest["version"], "0.2.0")
        self.assertEqual(plugin_manifest["skills"], "./skills/")
        self.assertEqual(
            plugin_manifest["interface"]["displayName"],
            "Pastor Assistant Agent OS",
        )
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
        self.assertFalse(report["conditional"]["python"]["required"])
        self.assertFalse(report["pastor_assistant_os"]["rule_contents_in_report"])
        self.assertNotIn(str(Path.home()), json.dumps(report))
        self.assertEqual(report["required"]["repository"]["status"], "pass")

    def test_pastor_assistant_os_has_private_approved_learning_loop(self) -> None:
        plugin_root = REPO_ROOT / "plugins/sermon-slide-builder"
        os_root = plugin_root / "skills/pastor-assistant-os"
        os_skill = (os_root / "SKILL.md").read_text(encoding="utf-8")
        learn_skill = (
            plugin_root / "skills/learn-pastor-corrections/SKILL.md"
        ).read_text(encoding="utf-8")
        review_skill = (
            plugin_root / "skills/review-pastor-work/SKILL.md"
        ).read_text(encoding="utf-8")
        setup = (REPO_ROOT / "SETUP-ASSISTANT.md").read_text(encoding="utf-8")
        state = json.loads(
            (REPO_ROOT / "setup-state.example.json").read_text(encoding="utf-8")
        )

        self.assertIn("YES, CREATE PASTOR ASSISTANT OS", os_skill)
        self.assertIn("YES, SAVE THIS RULE", os_skill)
        self.assertIn("Do not install Python merely to use this OS", os_skill)
        self.assertIn("do not interrupt the fix for OS setup", os_skill)
        self.assertIn("Fix the current deliverable first", learn_skill)
        self.assertIn("never a reason to delay the current fix", learn_skill)
        self.assertIn("Never edit the installed skill", learn_skill)
        self.assertIn("fresh reviewer subagent", review_skill)
        self.assertIn("local application-data", setup)
        self.assertIn("python-free-fallback.md", setup)
        self.assertEqual(state["schema_version"], 2)
        self.assertIn("pastor_assistant_os_initialized", state)
        self.assertTrue(
            (os_root / "assets/workspace-template/AGENTS.md").is_file()
        )
        self.assertTrue((os_root / "scripts/pastor_os.py").is_file())

    def test_preparer_backup_remove_and_restore(self) -> None:
        preparer = load_script("prepare_plugin")
        with tempfile.TemporaryDirectory(prefix="sermon-plugin-test-") as value:
            home = Path(value)
            first = preparer.prepare(home, show_paths=True)
            self.assertTrue(first["source_registered"])
            self.assertTrue(first["target_matches_source"])
            self.assertTrue(first["plugins_directory_action_required"])

            local_os = (
                home
                / "Library/Application Support/Valley Forge Baptist/Pastor Assistant OS"
            )
            local_os.mkdir(parents=True)
            local_rule = local_os / "approved-rule-test.txt"
            local_rule.write_text("preserve local pastor rule", encoding="utf-8")

            second = preparer.prepare(home, show_paths=True)
            backup = Path(second["backup_bundle"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(
                local_rule.read_text(encoding="utf-8"),
                "preserve local pastor rule",
            )

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
            self.assertEqual(
                local_rule.read_text(encoding="utf-8"),
                "preserve local pastor rule",
            )

    def test_slide_layout_rule_separates_text_and_images(self) -> None:
        skill_root = REPO_ROOT / "plugins/sermon-slide-builder/skills/create-sermon-slides"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        profile = (skill_root / "references/church-style-profile.md").read_text(
            encoding="utf-8"
        )
        vf_patterns = (
            skill_root / "references/vf-service-deck-patterns.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Never place sermon words on top of", skill)
        self.assertIn("recent pastor-approved sermon PowerPoint", skill)
        self.assertIn("Never place sermon words over", profile)
        self.assertIn("approximately `2560 × 704`", vf_patterns)
        self.assertIn("text on the left and one picture on the right", vf_patterns)
        self.assertIn("Sermon text never goes over a topical", vf_patterns)
        self.assertIn("legacy", vf_patterns)

    def test_biblical_images_have_scoped_generation_and_character_continuity(self) -> None:
        skill_root = REPO_ROOT / "plugins/sermon-slide-builder/skills/create-sermon-slides"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            skill_root / "references/biblical-photorealistic-image-set.md"
        ).read_text(encoding="utf-8")
        self.assertIn("first-level lettered subpoint routed to AI", skill)
        self.assertIn("Peter must look like the same Peter", skill)
        self.assertIn("character-continuity.md", reference)
        self.assertIn("The first eligible sermon image becomes the visual", reference)
        self.assertIn("Do not add a separate character portrait", reference)
        self.assertIn("clear production direction as a recorded", reference)
        self.assertIn("All sermon text stays in the PowerPoint's separate text region", reference)
        image_policy = (skill_root / "references/image-research-policy.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("negative space for the sermon copy", image_policy)
        self.assertIn("reference-image and character", image_policy)
        self.assertIn("approved for AI generation equal the", skill)
        self.assertIn("does not also receive an AI", reference)

    def test_skill_routes_pasted_sermons_canvases_and_real_media(self) -> None:
        skill_root = REPO_ROOT / "plugins/sermon-slide-builder/skills/create-sermon-slides"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        fidelity = (skill_root / "references/wording-fidelity.md").read_text(
            encoding="utf-8"
        )
        image_policy = (skill_root / "references/image-research-policy.md").read_text(
            encoding="utf-8"
        )
        profile = (skill_root / "references/church-style-profile.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("pasted directly into chat", skill)
        self.assertIn("`SL` or full `Slide` marker", fidelity)
        self.assertIn("**Sermon plus PPTX:**", skill)
        self.assertIn("never edit the supplied source in place", skill)
        self.assertIn("Never infer the canvas from filename", skill)
        self.assertIn("16 by 4.5 inches", skill)
        self.assertIn("separate PPTX files", skill)
        self.assertIn("possible tomb location", skill)
        self.assertIn("`conflict_review`", skill)
        self.assertIn("`pastor_provided_asset`", skill)
        self.assertIn("`pastor_supplied_placeholder`", skill)
        self.assertIn("Possible site — identification disputed", skill)
        self.assertIn("tracked `IMAGE NEEDED` placeholder", skill)
        self.assertIn("search-result thumbnail", image_policy)
        self.assertIn("IMAGE NEEDED: <description>", image_policy)
        self.assertIn("Conflicting Visual Directions", image_policy)
        self.assertIn("true 32:9 canvas", profile)
        self.assertIn("separate decks", profile)

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
            release_url = "https://github.com/example/example/releases/tag/v0.2.0"
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
            builder.write_file_manifest(stage, "0.2.0", commit)
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
            self.assertTrue(
                (
                    stage
                    / "plugins/sermon-slide-builder/skills/pastor-assistant-os/SKILL.md"
                ).is_file()
            )
            self.assertFalse(
                (
                    stage
                    / "plugins/sermon-slide-builder/skills/pastor-assistant-os/tests"
                ).exists()
            )
            release = json.loads((stage / "RELEASE.json").read_text(encoding="utf-8"))
            self.assertEqual(release["release_url"], release_url)
            self.assertEqual(release["git_commit"], commit)
            release_data = (stage / "setup-ui/release-data.js").read_text(
                encoding="utf-8"
            )
            self.assertIn("window.PASTOR_SERMON_RELEASE", release_data)
            self.assertIn('"messageTemplate"', release_data)
            self.assertIn("{{RELEASE_ZIP_SHA256}}", release_data)
            self.assertIn('"packageVersion": "0.2.0"', release_data)
            self.assertIn('"releaseTag": "v0.2.0"', release_data)

    def test_release_builder_requires_clean_tagged_git_head(self) -> None:
        builder = load_script("build_release")
        with tempfile.TemporaryDirectory(prefix="sermon-git-release-test-") as value:
            source = Path(value) / "source"
            shutil.copytree(
                REPO_ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "release",
                    "__pycache__",
                    "*.pyc",
                ),
            )
            (source / "LICENSE").write_text("Temporary test license\n", encoding="utf-8")
            commands = [
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Release Test"],
                ["git", "add", "."],
                ["git", "commit", "-m", "test release"],
                ["git", "tag", "v0.2.0"],
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
            release_url = "https://github.com/example/example/releases/tag/v0.2.0"
            builder.validate_git_state(release_url, commit, "v0.2.0")

            (source / "README.md").write_text("dirty\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                builder.validate_git_state(release_url, commit, "v0.2.0")

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
