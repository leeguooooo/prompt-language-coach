import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import manage_language_coach
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

    def test_codex_install_hook_command_writes_hooks_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            hooks_path = home / ".codex" / "hooks.json"

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "install-hook",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(hooks_path.exists())
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            command = payload["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            self.assertIn("platforms/codex/hook_entry.py", command)
            self.assertIn("Codex hook installed:", result.stdout)

    def test_codex_status_reports_hook_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".codex"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "language-coach.json").write_text("{}", encoding="utf-8")

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
            self.assertIn("Hook status:       not installed", result.stdout)

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

    def test_target_add_reloads_current_config_but_starts_new_language_conservatively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "ielts",
                        "mode": "ielts-writing",
                        "style": "teaching",
                        "responseLanguage": "target",
                        "enabled": True,
                        "ieltsFocus": "writing",
                        "targetBand": "7.0",
                        "currentLevel": "6.0",
                        "version": 1,
                    }
                ),
                encoding="utf-8",
            )
            stale_loaded_config = {
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
            disk_loaded_config = json.loads(config_path.read_text(encoding="utf-8"))
            saved_config: dict[str, object] = {}

            def capture_save(path: Path, config: dict[str, object]) -> None:
                self.assertEqual(path, config_path)
                saved_config.clear()
                saved_config.update(json.loads(json.dumps(config)))

            with (
                mock.patch(
                    "scripts.manage_language_coach.load_config",
                    side_effect=[stale_loaded_config, disk_loaded_config],
                ),
                mock.patch("scripts.manage_language_coach.save_config", side_effect=capture_save),
                mock.patch(
                    "sys.argv",
                    [
                        "manage_language_coach.py",
                        "--config",
                        str(config_path),
                        "target-add",
                        "Japanese",
                    ],
                ),
            ):
                exit_code = manage_language_coach.main()

            self.assertEqual(exit_code, 0)
            japanese_target = next(
                target
                for target in saved_config["targets"]
                if target["targetLanguage"] == "Japanese"
            )
            self.assertEqual(japanese_target["goal"], "everyday")
            self.assertEqual(japanese_target["mode"], "everyday")
            self.assertEqual(japanese_target["ieltsFocus"], "both")
            self.assertEqual(japanese_target["targetBand"], "")
            self.assertEqual(japanese_target["currentLevel"], "")
            self.assertEqual(japanese_target["responseLanguage"], "target")

    def test_record_band_merges_progress_across_platforms_into_shared_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            shared_path = home / ".prompt-language-coach" / "language-progress.json"

            for platform, band in (("codex", "5.0"), ("claude", "5.5"), ("cursor", "6.0")):
                result = subprocess.run(
                    [
                        "python3",
                        "scripts/manage_language_coach.py",
                        "--platform",
                        platform,
                        "record-band",
                        "English",
                        band,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"HOME": str(home)},
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            self.assertTrue(shared_path.exists())
            shared = json.loads(shared_path.read_text(encoding="utf-8"))
            self.assertEqual(shared["English"]["currentBand"], "6.0")

            for legacy_path in (
                home / ".codex" / "language-progress.json",
                home / ".claude" / "language-progress.json",
                home / ".cursor" / "language-progress.json",
            ):
                self.assertTrue(legacy_path.exists())
                mirrored = json.loads(legacy_path.read_text(encoding="utf-8"))
                self.assertEqual(mirrored["English"]["currentBand"], "6.0")


if __name__ == "__main__":
    unittest.main()
