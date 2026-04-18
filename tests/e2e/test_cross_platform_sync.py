"""End-to-end tests that run the CLI as a subprocess against a mocked HOME.

These cover cross-platform behavior that unit tests with mocked helpers miss:
- A config change from one platform must refresh the other platforms' static
  prompt files (Claude @-import target, Codex AGENTS.md marker block).
- The render hook must emit valid UTF-8 JSON even when stdout is forced to a
  non-UTF-8 encoding (simulates Windows PowerShell GBK default).
- Multi-target `targets[]` must stay in lockstep with top-level after any
  mode / style / goal / response / estimate / focus / level / vocab command.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests._subprocess_env import env_for_home

REPO_ROOT = Path(__file__).resolve().parents[2]
MANAGE = str(REPO_ROOT / "scripts" / "manage_language_coach.py")
RENDER = str(REPO_ROOT / "scripts" / "render_coaching_context.py")

# Emoji U+1F4DA (📚) appears in every coaching box title — the canary we use
# to prove non-ASCII content survives the render hook end-to-end.
BOOK_EMOJI = "\U0001f4da"
BOOK_EMOJI_UTF8 = BOOK_EMOJI.encode("utf-8")


def _run(cmd: list[str], home: Path, *, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = env_for_home(home)
    env["PYTHONPATH"] = str(REPO_ROOT)
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, *cmd], env=env, capture_output=True, text=True, check=False)


def _seed_config(home: Path, config: dict) -> Path:
    shared = home / ".prompt-language-coach" / "language-coach.json"
    shared.parent.mkdir(parents=True, exist_ok=True)
    shared.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    return shared


class CrossPlatformSyncTests(unittest.TestCase):
    def test_codex_mode_change_refreshes_claude_external_coaching_file(self) -> None:
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".claude").mkdir()
            (home / ".codex").mkdir()
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [],
            })

            r = _run([MANAGE, "--platform", "codex", "mode", "scored-writing"], home)
            self.assertEqual(r.returncode, 0, r.stderr)

            external = home / ".prompt-language-coach" / "claude-coaching.md"
            self.assertTrue(external.exists(), "claude-coaching.md should be refreshed by a codex-triggered config change")
            text = external.read_text(encoding="utf-8")
            # Top-level single-target prompt renders "Goal: scored." +
            # "Scored Writing Coaching" box title when mode=scored-writing.
            self.assertIn("Goal: scored", text)
            self.assertIn("Scored Writing Coaching", text)

            claude_md = home / ".claude" / "CLAUDE.md"
            self.assertTrue(claude_md.exists())
            self.assertIn("@", claude_md.read_text(encoding="utf-8"))
            self.assertIn(str(external), claude_md.read_text(encoding="utf-8"))

    def test_render_cursor_emits_utf8_under_gbk_stdout(self) -> None:
        """Simulates Windows PowerShell (GBK stdout). Must not crash, and output
        must be valid UTF-8 JSON containing the coaching emoji."""
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".cursor").mkdir()
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [],
            })

            env = env_for_home(home)
            env["PYTHONPATH"] = str(REPO_ROOT)
            env["PYTHONIOENCODING"] = "gbk:strict"
            r = subprocess.run(
                [sys.executable, RENDER, "--platform", "cursor"],
                env=env,
                capture_output=True,
                text=False,  # bytes — we're checking encoding explicitly
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", errors="replace"))
            self.assertIn(BOOK_EMOJI_UTF8, r.stdout, "render output should contain UTF-8 emoji bytes")
            payload = json.loads(r.stdout.decode("utf-8"))
            self.assertIn("additional_context", payload)
            self.assertIn(BOOK_EMOJI, payload["additional_context"])

    def test_render_claude_short_path_when_marker_present(self) -> None:
        """When ~/.claude/CLAUDE.md has the marker block, the hook emits only
        the ~25-token progress note (not the full 750-token prompt)."""
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir()
            (claude_dir / "CLAUDE.md").write_text(
                "some unrelated content\n"
                "<!-- language-coach:start -->\n"
                "@/somewhere/claude-coaching.md\n"
                "<!-- language-coach:end -->\n",
                encoding="utf-8",
            )
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [],
            })
            # Need a progress file so progress note emits something meaningful
            progress = home / ".prompt-language-coach" / "language-progress.json"
            progress.write_text(
                json.dumps({"English": {"estimates": [{"date": "2026-04-18", "estimate": "B1"}], "currentEstimate": "B1", "scale": "cefr"}}),
                encoding="utf-8",
            )

            r = _run([RENDER, "--platform", "claude"], home)
            self.assertEqual(r.returncode, 0, r.stderr)
            payload = json.loads(r.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            # Progress note should be present …
            self.assertIn("English", context)
            # … but the full coaching prompt (containing MANDATORY + box title)
            # should NOT be re-emitted per turn because CLAUDE.md already has it.
            self.assertNotIn("MANDATORY", context)
            self.assertNotIn(BOOK_EMOJI, context)

    def test_multi_target_propagation_through_mode_command(self) -> None:
        """A `mode scored-writing` command must flip every target to
        scored-writing, not just top-level."""
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            # Seed a legacy config with stale per-target fields (the pre-0.12.1
            # shape that ignored top-level). Pick two targets with different
            # scales so we also cover the fix #6 scope (IELTS vs JLPT).
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [
                    {"targetLanguage": "English", "goal": "everyday", "mode": "everyday", "style": "teaching"},
                    {"targetLanguage": "Japanese", "goal": "everyday", "mode": "everyday", "style": "teaching"},
                ],
            })

            r = _run([MANAGE, "--platform", "claude", "mode", "scored-writing"], home)
            self.assertEqual(r.returncode, 0, r.stderr)

            config = json.loads((home / ".prompt-language-coach" / "language-coach.json").read_text(encoding="utf-8"))
            for target in config["targets"]:
                self.assertEqual(target["mode"], "scored-writing", target)
                self.assertEqual(target["goal"], "scored", target)

    def test_target_command_promotes_matching_profile_to_primary(self) -> None:
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [
                    {"targetLanguage": "English", "goal": "everyday", "mode": "everyday", "style": "teaching"},
                    {"targetLanguage": "Japanese", "goal": "everyday", "mode": "everyday", "style": "teaching"},
                ],
            })

            r = _run([MANAGE, "--platform", "claude", "target", "Japanese"], home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Primary target set to: Japanese", r.stdout)

            config = json.loads((home / ".prompt-language-coach" / "language-coach.json").read_text(encoding="utf-8"))
            self.assertEqual(config["targets"][0]["targetLanguage"], "Japanese")
            self.assertEqual(config["targetLanguage"], "Japanese")

    def test_target_command_warns_when_language_not_in_profiles(self) -> None:
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            _seed_config(home, {
                "nativeLanguage": "Chinese",
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
                "responseLanguage": "native",
                "enabled": True,
                "targets": [
                    {"targetLanguage": "English", "goal": "everyday", "mode": "everyday", "style": "teaching"},
                ],
            })
            r = _run([MANAGE, "--platform", "claude", "target", "Korean"], home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("fallback", r.stdout)
            self.assertIn("target-add Korean", r.stdout)

            config = json.loads((home / ".prompt-language-coach" / "language-coach.json").read_text(encoding="utf-8"))
            self.assertEqual(config["targetLanguage"], "Korean")
            # targets[] unchanged
            self.assertEqual([t["targetLanguage"] for t in config["targets"]], ["English"])


if __name__ == "__main__":
    unittest.main()
