import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class CodexHookInstallTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
