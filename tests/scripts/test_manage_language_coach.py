import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.manage_language_coach import add_target, list_targets, remove_target


class ManageLanguageCoachTests(unittest.TestCase):
    def test_target_management_helpers(self) -> None:
        config = {
            "nativeLanguage": "Chinese",
            "targetLanguage": "English",
            "goal": "everyday",
            "mode": "everyday",
            "style": "teaching",
            "responseLanguage": "native",
            "enabled": True,
            "ieltsFocus": "both",
            "targetBand": "",
            "currentLevel": "",
            "targets": [],
            "version": 1,
        }

        add_target(config, "Japanese")
        self.assertEqual(list_targets(config), ["English", "Japanese"])

        remove_target(config, "English")
        self.assertEqual(list_targets(config), ["Japanese"])
        self.assertEqual(config["targets"][0]["targetLanguage"], "Japanese")

    def test_status_reports_missing_config_as_not_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_path = home / ".codex" / "language-coach.json"

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "status",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(config_path.exists())
            self.assertIn("Status:            not configured", result.stdout)

    def test_platform_default_path_writes_codex_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_path = home / ".codex" / "language-coach.json"

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "target",
                    "Japanese",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(config_path.exists())
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["targetLanguage"], "Japanese")

    def test_set_mode_updates_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "everyday",
                        "mode": "everyday",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                        "ieltsFocus": "both",
                        "targetBand": "",
                        "currentLevel": "",
                        "version": 1,
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--config",
                    str(config_path),
                    "mode",
                    "ielts-writing",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["mode"], "ielts-writing")
            self.assertEqual(updated["goal"], "ielts")


if __name__ == "__main__":
    unittest.main()
