import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._subprocess_env import env_for_home


class CodexHookOutputTests(unittest.TestCase):
    def _run_render(self, home: Path, config_path: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                "scripts/render_coaching_context.py",
                "--platform",
                "codex",
                "--config",
                str(config_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env_for_home(home),
        )

    def test_render_emits_only_progress_note_in_additional_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".codex").mkdir()
            config_path = home / ".codex" / "language-coach.json"
            config_path.write_text(
                Path("tests/fixtures/config_everyday.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = self._run_render(home, config_path)
            self.assertEqual(result.returncode, 0, result.stderr)

            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("[MANDATORY]", context)
            self.assertNotIn("Box framing", context)
            self.assertLess(len(context), 500, "context should be tiny in Codex")

    def test_render_writes_static_prompt_into_agents_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".codex").mkdir()
            config_path = home / ".codex" / "language-coach.json"
            config_path.write_text(
                Path("tests/fixtures/config_everyday.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = self._run_render(home, config_path)
            self.assertEqual(result.returncode, 0, result.stderr)

            agents_md = home / ".codex" / "AGENTS.md"
            self.assertTrue(agents_md.exists())
            text = agents_md.read_text(encoding="utf-8")
            self.assertIn("<!-- prompt-language-coach:start -->", text)
            self.assertIn("[MANDATORY]", text)
            self.assertIn("<!-- prompt-language-coach:end -->", text)

    def test_render_removes_block_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".codex").mkdir()
            config_path = home / ".codex" / "language-coach.json"
            config_data = json.loads(
                Path("tests/fixtures/config_everyday.json").read_text(encoding="utf-8")
            )
            config_data["enabled"] = False
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            agents_md = home / ".codex" / "AGENTS.md"
            agents_md.write_text(
                "# User note\n"
                "<!-- prompt-language-coach:start -->\nold block\n<!-- prompt-language-coach:end -->\n",
                encoding="utf-8",
            )

            result = self._run_render(home, config_path)
            self.assertEqual(result.returncode, 0, result.stderr)

            text = agents_md.read_text(encoding="utf-8")
            self.assertNotIn("old block", text)
            self.assertIn("# User note", text)

    def test_remove_hook_clears_agents_md_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".codex").mkdir()
            agents_md = home / ".codex" / "AGENTS.md"
            agents_md.write_text(
                "# Keep\n"
                "<!-- prompt-language-coach:start -->\ncoach\n<!-- prompt-language-coach:end -->\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/manage_language_coach.py",
                    "--platform",
                    "codex",
                    "remove-hook",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env_for_home(home),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = agents_md.read_text(encoding="utf-8")
            self.assertNotIn("coach", text)
            self.assertIn("# Keep", text)


if __name__ == "__main__":
    unittest.main()
