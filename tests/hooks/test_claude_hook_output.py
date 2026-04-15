import json
import subprocess
import unittest


class ClaudeHookOutputTests(unittest.TestCase):
    def test_render_script_emits_user_prompt_submit_payload(self) -> None:
        result = subprocess.run(
            [
                "python3",
                "scripts/render_coaching_context.py",
                "--platform",
                "claude",
                "--config",
                "tests/fixtures/config_everyday.json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"],
            "UserPromptSubmit",
        )
        self.assertIn(
            "Language coaching preference",
            payload["hookSpecificOutput"]["additionalContext"],
        )


if __name__ == "__main__":
    unittest.main()
