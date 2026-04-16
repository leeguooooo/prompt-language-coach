import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from platforms.codex.hook_entry import main as run_hook_entry
from platforms.codex.install_hooks import build_hook_command


class CodexHookInstallTests(unittest.TestCase):
    def test_build_hook_command_is_guarded_when_python3_is_unavailable(self) -> None:
        command = build_hook_command(Path.cwd())

        self.assertIn("platforms/codex/hook_entry.py", command)
        self.assertIn("command -v python3", command)

    def test_installer_writes_user_prompt_submit_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            result = subprocess.run(
                [
                    "python3",
                    "platforms/codex/install_hooks.py",
                    "--hooks-path",
                    str(hooks_path),
                    "--repo-root",
                    str(Path.cwd()),
                    "install",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            command = payload["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            self.assertIn("platforms/codex/hook_entry.py", command)

    def test_install_preserves_unrelated_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            hooks_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 \"/tmp/other.py\"",
                                        }
                                    ]
                                }
                            ],
                            "UserPromptSubmit": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 \"/tmp/unrelated.py\"",
                                        }
                                    ]
                                }
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "platforms/codex/install_hooks.py",
                    "--hooks-path",
                    str(hooks_path),
                    "--repo-root",
                    str(Path.cwd()),
                    "install",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["hooks"]["SessionStart"]), 1)
            self.assertEqual(len(payload["hooks"]["UserPromptSubmit"]), 2)
            commands = [
                entry["hooks"][0]["command"]
                for entry in payload["hooks"]["UserPromptSubmit"]
            ]
            self.assertIn("python3 \"/tmp/unrelated.py\"", commands)
            self.assertTrue(
                any("platforms/codex/hook_entry.py" in command for command in commands)
            )

    def test_remove_only_deletes_managed_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            hooks_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "UserPromptSubmit": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": (
                                                "python3 "
                                                f"\"{Path.cwd() / 'platforms' / 'codex' / 'hook_entry.py'}\""
                                            ),
                                        }
                                    ]
                                },
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 \"/tmp/unrelated.py\"",
                                        }
                                    ]
                                },
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "platforms/codex/install_hooks.py",
                    "--hooks-path",
                    str(hooks_path),
                    "--repo-root",
                    str(Path.cwd()),
                    "remove",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            commands = [
                entry["hooks"][0]["command"]
                for entry in payload["hooks"]["UserPromptSubmit"]
            ]
            self.assertEqual(commands, ["python3 \"/tmp/unrelated.py\""])


class CodexHookEntryTests(unittest.TestCase):
    def test_hook_entry_reuses_current_interpreter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_path = home / ".codex" / "language-coach.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("{}", encoding="utf-8")

            with (
                mock.patch("platforms.codex.hook_entry.Path.home", return_value=home),
                mock.patch("platforms.codex.hook_entry.subprocess.call", return_value=0) as call_mock,
            ):
                result = run_hook_entry()

            self.assertEqual(result, 0)
            command = call_mock.call_args.args[0]
            self.assertEqual(command[0], sys.executable)
            self.assertEqual(command[1], str(Path.cwd() / "scripts" / "render_coaching_context.py"))

    def test_hook_entry_is_silent_when_renderer_cannot_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_path = home / ".codex" / "language-coach.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("{}", encoding="utf-8")

            with (
                mock.patch("platforms.codex.hook_entry.Path.home", return_value=home),
                mock.patch(
                    "platforms.codex.hook_entry.subprocess.call",
                    side_effect=FileNotFoundError,
                ),
            ):
                result = run_hook_entry()

            self.assertEqual(result, 0)

    def test_hook_entry_falls_back_to_existing_claude_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_path = home / ".claude" / "language-coach.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("{}", encoding="utf-8")

            with (
                mock.patch("platforms.codex.hook_entry.Path.home", return_value=home),
                mock.patch("platforms.codex.hook_entry.subprocess.call", return_value=0) as call_mock,
            ):
                result = run_hook_entry()

            self.assertEqual(result, 0)
            command = call_mock.call_args.args[0]
            self.assertIn("--config", command)
            self.assertEqual(command[-1], str(config_path))


if __name__ == "__main__":
    unittest.main()
