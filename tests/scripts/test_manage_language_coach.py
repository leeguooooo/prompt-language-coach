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
            "scoringFocus": "both",
            "targetEstimate": "",
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

    def test_claude_setup_like_update_mirrors_config_to_all_platform_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "claude",
                    "target",
                    "Japanese",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for config_path in (
                home / ".claude" / "language-coach.json",
                home / ".codex" / "language-coach.json",
                home / ".cursor" / "language-coach.json",
                home / ".prompt-language-coach" / "language-coach.json",
            ):
                self.assertTrue(config_path.exists(), str(config_path))
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
                        "scoringFocus": "both",
                        "targetEstimate": "",
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
            self.assertEqual(updated["mode"], "scored-writing")
            self.assertEqual(updated["goal"], "scored")

    def test_estimate_command_updates_target_estimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "Japanese",
                        "goal": "scored",
                        "mode": "scored-writing",
                        "style": "teaching",
                        "responseLanguage": "target",
                        "enabled": True,
                        "scoringFocus": "writing",
                        "targetEstimate": "N4",
                        "currentLevel": "N5",
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
                    "estimate",
                    "N3",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["targetEstimate"], "N3")

    def test_target_add_reloads_current_config_but_starts_new_language_conservatively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "scored",
                        "mode": "ielts-writing",
                        "style": "teaching",
                        "responseLanguage": "target",
                        "enabled": True,
                        "scoringFocus": "writing",
                        "targetEstimate": "7.0",
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
                "scoringFocus": "both",
                "targetEstimate": "",
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
            self.assertEqual(japanese_target["scoringFocus"], "both")
            self.assertEqual(japanese_target["targetEstimate"], "")
            self.assertEqual(japanese_target["currentLevel"], "")
            self.assertEqual(japanese_target["responseLanguage"], "target")

    def test_status_uses_scored_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".codex"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "language-coach.json").write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "Japanese",
                        "goal": "scored",
                        "mode": "scored-writing",
                        "style": "teaching",
                        "responseLanguage": "target",
                        "enabled": True,
                        "scoringFocus": "writing",
                        "targetEstimate": "N3",
                        "currentLevel": "N5",
                    }
                ),
                encoding="utf-8",
            )

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
            self.assertIn("Goal:              scored", result.stdout)
            self.assertIn("Scoring focus:     writing", result.stdout)
            self.assertIn("Target estimate:   N3", result.stdout)

    def test_practice_focus_alias_updates_scoring_focus(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "scored",
                        "mode": "scored-writing",
                        "style": "teaching",
                        "responseLanguage": "target",
                        "enabled": True,
                        "scoringFocus": "writing",
                        "targetEstimate": "6.5",
                        "currentLevel": "5.5",
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
                    "practice-focus",
                    "speaking",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["scoringFocus"], "speaking")
            self.assertEqual(updated["mode"], "scored-speaking")

    def test_track_estimate_merges_progress_across_platforms_into_shared_file(self) -> None:
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
                        "track-estimate",
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
            self.assertEqual(shared["English"]["currentEstimate"], "6.0")
            self.assertEqual(shared["English"]["estimates"][-1]["estimate"], "6.0")
            self.assertNotIn("band", shared["English"]["estimates"][-1])

            for legacy_path in (
                home / ".codex" / "language-progress.json",
                home / ".claude" / "language-progress.json",
                home / ".cursor" / "language-progress.json",
            ):
                self.assertTrue(legacy_path.exists())
                mirrored = json.loads(legacy_path.read_text(encoding="utf-8"))
                self.assertEqual(mirrored["English"]["currentEstimate"], "6.0")

    def test_progress_loader_migrates_legacy_band_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            legacy_path = home / ".claude" / "language-progress.json"
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text(
                json.dumps(
                    {
                        "English": {
                            "currentBand": "5.5",
                            "estimates": [
                                {"date": "2026-04-01", "band": "5.5"},
                            ],
                            "scale": "ielts",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "claude",
                    "progress",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = json.loads((home / ".prompt-language-coach" / "language-progress.json").read_text(encoding="utf-8"))
            self.assertEqual(migrated["English"]["currentEstimate"], "5.5")
            self.assertEqual(migrated["English"]["estimates"][0]["estimate"], "5.5")

    def test_track_vocab_gap_mirrors_across_platform_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "track-vocab",
                    "English",
                    "gap",
                    "--native",
                    "吐槽",
                    "--target",
                    "vent",
                    "--context",
                    "I want to 吐槽 this bug",
                    "--note",
                    "vent = express frustration",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for vocab_path in (
                home / ".prompt-language-coach" / "vocab-focus.json",
                home / ".codex" / "vocab-focus.json",
                home / ".claude" / "vocab-focus.json",
                home / ".cursor" / "vocab-focus.json",
            ):
                self.assertTrue(vocab_path.exists(), str(vocab_path))
                payload = json.loads(vocab_path.read_text(encoding="utf-8"))
                entry = payload["English"]["entries"][0]
                self.assertEqual(entry["type"], "gap")
                self.assertEqual(entry["native"], "吐槽")
                self.assertEqual(entry["target"], "vent")
                self.assertEqual(entry["masteredHits"], 0)

    def test_track_vocab_caps_active_entries_at_twenty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            for index in range(21):
                result = subprocess.run(
                    [
                        "python3",
                        "scripts/manage_language_coach.py",
                        "--platform",
                        "codex",
                        "track-vocab",
                        "English",
                        "correction",
                        "--wrong",
                        f"wrong-{index}",
                        "--right",
                        f"right-{index}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"HOME": str(home)},
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            payload = json.loads(
                (home / ".prompt-language-coach" / "vocab-focus.json").read_text(
                    encoding="utf-8"
                )
            )
            entries = payload["English"]["entries"]
            self.assertEqual(len(entries), 20)
            rights = [entry["right"] for entry in entries]
            self.assertNotIn("right-0", rights)
            self.assertEqual(rights[-1], "right-20")

    def test_mark_vocab_mastered_moves_entry_after_three_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            seed = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "track-vocab",
                    "English",
                    "upgrade",
                    "--from",
                    "good",
                    "--to",
                    "compelling",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )
            self.assertEqual(seed.returncode, 0, seed.stderr)

            for hit in range(3):
                result = subprocess.run(
                    [
                        "python3",
                        "scripts/manage_language_coach.py",
                        "--platform",
                        "codex",
                        "mark-vocab-mastered",
                        "English",
                        "compelling",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={"HOME": str(home)},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(
                    (home / ".prompt-language-coach" / "vocab-focus.json").read_text(
                        encoding="utf-8"
                    )
                )
                if hit < 2:
                    self.assertEqual(payload["English"]["entries"][0]["masteredHits"], hit + 1)
                else:
                    self.assertEqual(payload["English"]["entries"], [])
                    self.assertEqual(payload["English"]["mastered"][0]["to"], "compelling")
                    self.assertEqual(payload["English"]["mastered"][0]["masteredHits"], 3)

    def test_vocab_command_prints_entries_and_toggles_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            seed = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "track-vocab",
                    "English",
                    "correction",
                    "--wrong",
                    "effect",
                    "--right",
                    "affect",
                    "--note",
                    "affect = verb",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )
            self.assertEqual(seed.returncode, 0, seed.stderr)

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "vocab",
                    "English",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("English vocab focus", result.stdout)
            self.assertIn("effect -> affect", result.stdout)

            toggle = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "vocab",
                    "on",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home)},
            )
            self.assertEqual(toggle.returncode, 0, toggle.stderr)

            config = json.loads(
                (home / ".prompt-language-coach" / "language-coach.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(config["vocabFocus"])


if __name__ == "__main__":
    unittest.main()
