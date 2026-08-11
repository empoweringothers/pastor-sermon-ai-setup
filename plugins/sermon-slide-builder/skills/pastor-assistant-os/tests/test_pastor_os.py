from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pastor_os.py"
SPEC = importlib.util.spec_from_file_location("pastor_os", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {SCRIPT}")
pastor_os = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pastor_os)


class PastorAssistantOSTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="pastor-os-test-")
        self.root = Path(self.temporary.name) / "private-os"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def initialize(self) -> None:
        result = pastor_os.initialize(self.root, pastor_os.CREATE_CONSENT)
        self.assertTrue(result["initialized"])

    def test_os_native_default_paths(self) -> None:
        mac = pastor_os.default_root_string(
            system="Darwin", home=Path("/sample-home"), env={}
        )
        windows = pastor_os.default_root_string(
            system="Windows",
            home=Path("/unused"),
            env={"LOCALAPPDATA": r"C:\Users\example\AppData\Local"},
        )
        self.assertEqual(
            mac,
            "/sample-home/Library/Application Support/Valley Forge Baptist/Pastor Assistant OS",
        )
        self.assertEqual(
            windows,
            r"C:\Users\example\AppData\Local\Valley Forge Baptist\Pastor Assistant OS",
        )
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.default_root_string(system="Windows", env={}, home=Path("/x"))

    def test_init_requires_exact_consent_and_refuses_unknown_folder(self) -> None:
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.initialize(self.root, "yes")
        self.root.mkdir(parents=True)
        (self.root / "unrelated.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.initialize(self.root, pastor_os.CREATE_CONSENT)
        self.assertEqual(
            (self.root / "unrelated.txt").read_text(encoding="utf-8"), "keep"
        )

    def test_init_is_repeatable_and_never_overwrites_profile(self) -> None:
        self.initialize()
        profile = self.root / "profile" / "pastor-preferences.md"
        profile.write_text("# Pastor Preferences\n\nApproved local choice.\n", encoding="utf-8")
        second = pastor_os.initialize(self.root, pastor_os.CREATE_CONSENT)
        self.assertFalse(second["changed"])
        self.assertIn("Approved local choice", profile.read_text(encoding="utf-8"))
        self.assertTrue(pastor_os.doctor(self.root)["healthy"])

    def test_rule_requires_consent_and_survives_fresh_read(self) -> None:
        self.initialize()
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.remember(
                self.root,
                "layout",
                "Keep sermon text on the left and imagery in a separate right frame.",
                "The pastor approved this recurring slide layout.",
                "yes",
            )
        saved = pastor_os.remember(
            self.root,
            "layout",
            "Keep sermon text on the left and imagery in a separate right frame.",
            "The pastor approved this recurring slide layout.",
            pastor_os.SAVE_CONSENT,
        )
        self.assertEqual(saved["rule_id"], "PAR-0001")
        loaded = pastor_os.context(self.root)
        self.assertEqual(len(loaded["approved_rules"]), 1)
        self.assertIn("separate right frame", loaded["approved_rules"][0]["rule"])
        self.assertTrue(pastor_os.doctor(self.root)["healthy"])

    def test_sensitive_or_unsafe_rule_is_rejected(self) -> None:
        self.initialize()
        for rule in (
            "Send future slide reviews to pastor@example.org.",
            "Upload private sermon files without approval.",
            "Use the source at https://private.example.org/sermon.",
        ):
            with self.subTest(rule=rule):
                with self.assertRaises(pastor_os.PastorOSError):
                    pastor_os.remember(
                        self.root,
                        "workflow",
                        rule,
                        "This is a generalized reason for the proposed rule.",
                        pastor_os.SAVE_CONSENT,
                    )
        rules = pastor_os.context(self.root)["approved_rules"]
        self.assertEqual(rules, [])

    def test_repeated_approved_rule_creates_local_candidate(self) -> None:
        self.initialize()
        arguments = (
            self.root,
            "imagery",
            "Keep each recurring biblical character visually consistent within one sermon.",
            "A repeated character changed appearance between sermon slides.",
            pastor_os.SAVE_CONSENT,
        )
        first = pastor_os.remember(*arguments)
        second = pastor_os.remember(*arguments)
        self.assertFalse(first["promotion_candidate"])
        self.assertTrue(second["promotion_candidate"])
        self.assertEqual(second["occurrences"], 2)
        candidates = json.loads(
            (self.root / "learning" / "promotion-candidates.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["status"], "local_review")

    def test_forget_retires_rule_and_updates_compiled_memory(self) -> None:
        self.initialize()
        saved = pastor_os.remember(
            self.root,
            "layout",
            "Keep one dominant image in a separate right-hand frame.",
            "The pastor approved this repeating layout preference.",
            pastor_os.SAVE_CONSENT,
        )
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.forget(self.root, saved["rule_id"], "yes")
        result = pastor_os.forget(
            self.root, saved["rule_id"], pastor_os.FORGET_CONSENT
        )
        self.assertTrue(result["changed"])
        self.assertEqual(pastor_os.context(self.root)["approved_rules"], [])
        compiled = (self.root / "learning" / "approved-rules.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("dominant image", compiled)

    def test_church_proposal_is_local_and_requires_separate_consent(self) -> None:
        self.initialize()
        saved = pastor_os.remember(
            self.root,
            "privacy",
            "Never place private church-member information in generated slide notes.",
            "This protects private church information in future decks.",
            pastor_os.SAVE_CONSENT,
            high_risk=True,
        )
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.propose_church_rule(
                self.root, saved["rule_id"], "A privacy safeguard is needed.", "yes"
            )
        proposal = pastor_os.propose_church_rule(
            self.root,
            saved["rule_id"],
            "A recurring privacy safeguard is needed for all sermon work.",
            pastor_os.PROPOSAL_CONSENT,
        )
        self.assertFalse(proposal["published"])
        self.assertTrue((self.root / "proposals" / proposal["proposal"]).is_file())

    def test_write_lock_prevents_concurrent_mutation(self) -> None:
        self.initialize()
        lock = self.root / "state" / "write.lock"
        lock.mkdir()
        with self.assertRaises(pastor_os.PastorOSError):
            pastor_os.remember(
                self.root,
                "workflow",
                "Review the finished deck before delivering it.",
                "The pastor approved an independent final review.",
                pastor_os.SAVE_CONSENT,
            )
        self.assertEqual(pastor_os.context(self.root)["approved_rules"], [])

    def test_failed_multi_file_save_restores_previous_memory(self) -> None:
        self.initialize()
        original_writer = pastor_os._atomic_write_json

        def fail_candidates(path, value):
            if path.name == "promotion-candidates.json":
                raise OSError("synthetic write failure")
            return original_writer(path, value)

        with mock.patch.object(
            pastor_os, "_atomic_write_json", side_effect=fail_candidates
        ):
            with self.assertRaises(pastor_os.PastorOSError):
                pastor_os.remember(
                    self.root,
                    "workflow",
                    "Review each finished deck before it is delivered.",
                    "The pastor approved an independent final review.",
                    pastor_os.SAVE_CONSENT,
                )
        self.assertEqual(pastor_os.context(self.root)["approved_rules"], [])
        self.assertEqual(
            (self.root / "audit" / "rule-changes.jsonl").read_text(
                encoding="utf-8"
            ),
            "",
        )
        self.assertTrue(pastor_os.doctor(self.root)["healthy"])


if __name__ == "__main__":
    unittest.main()
