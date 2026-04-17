import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from platforms.cursor import install_hooks
from platforms.cursor.install_hooks import (
    HOOK_EVENT,
    build_hook_command,
    install,
    is_managed_entry,
    remove,
)


class CursorHookInstallTests(unittest.TestCase):
    def test_build_hook_command_points_at_sh_script(self) -> None:
        command = build_hook_command(Path.cwd())
        self.assertIn("hooks/cursor-language-coach.sh", command)
        self.assertTrue(command.startswith("bash "))

    def test_build_hook_command_on_windows_uses_python_direct(self) -> None:
        with mock.patch.object(install_hooks, "_is_windows", return_value=True):
            command = build_hook_command(Path("C:/Users/Administrator/.cursor/plugins/lc"))
        self.assertIn("render_coaching_context.py", command)
        self.assertIn("--platform cursor", command)
        self.assertNotIn("bash ", command)
        self.assertNotIn(".sh", command)

    def test_is_managed_entry_matches_both_posix_and_windows(self) -> None:
        posix_entry = {"type": "command", "command": "bash /x/hooks/cursor-language-coach.sh"}
        windows_entry = {
            "type": "command",
            "command": '"C:/Python/python.exe" "C:/x/scripts/render_coaching_context.py" --platform cursor',
        }
        unrelated = {"type": "command", "command": "echo hi"}
        render_non_cursor = {
            "type": "command",
            "command": "python render_coaching_context.py --platform claude",
        }
        self.assertTrue(is_managed_entry(posix_entry))
        self.assertTrue(is_managed_entry(windows_entry))
        self.assertFalse(is_managed_entry(unrelated))
        self.assertFalse(is_managed_entry(render_non_cursor))

    def test_installer_writes_session_start_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            install(hooks_path, Path.cwd())

            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            entries = payload["hooks"][HOOK_EVENT]
            self.assertEqual(len(entries), 1)
            self.assertIn("cursor-language-coach.sh", entries[0]["command"])
            self.assertEqual(entries[0]["type"], "command")

    def test_install_preserves_unrelated_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            hooks_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "sessionStart": [
                                {
                                    "type": "command",
                                    "command": "echo unrelated",
                                }
                            ],
                            "beforeSubmitPrompt": [
                                {"type": "command", "command": "echo other"}
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )

            install(hooks_path, Path.cwd())

            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            sess = payload["hooks"]["sessionStart"]
            commands = [entry["command"] for entry in sess]
            self.assertIn("echo unrelated", commands)
            self.assertTrue(any("cursor-language-coach.sh" in c for c in commands))
            self.assertEqual(
                payload["hooks"]["beforeSubmitPrompt"],
                [{"type": "command", "command": "echo other"}],
            )

    def test_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            install(hooks_path, Path.cwd())
            install(hooks_path, Path.cwd())
            install(hooks_path, Path.cwd())

            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            entries = payload["hooks"][HOOK_EVENT]
            managed = [e for e in entries if is_managed_entry(e)]
            self.assertEqual(len(managed), 1)

    def test_remove_only_deletes_managed_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            hooks_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "sessionStart": [
                                {"type": "command", "command": "echo unrelated"},
                                {
                                    "type": "command",
                                    "command": f"bash {Path.cwd()}/hooks/cursor-language-coach.sh",
                                },
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            remove(hooks_path)

            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            entries = payload["hooks"]["sessionStart"]
            self.assertEqual(entries, [{"type": "command", "command": "echo unrelated"}])

    def test_install_hook_command_via_manage_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            hooks_path = home / ".cursor" / "hooks.json"

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "cursor",
                    "install-hook",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(hooks_path.exists())
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            entries = payload["hooks"]["sessionStart"]
            self.assertTrue(any("cursor-language-coach.sh" in e["command"] for e in entries))
            self.assertIn("Cursor hook installed:", result.stdout)


if __name__ == "__main__":
    unittest.main()
