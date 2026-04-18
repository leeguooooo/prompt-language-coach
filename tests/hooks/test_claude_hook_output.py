import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._subprocess_env import env_for_home


class ClaudeHookOutputTests(unittest.TestCase):
    def test_render_script_emits_user_prompt_submit_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/render_coaching_context.py",
                    "--platform",
                    "claude",
                    "--config",
                    "tests/fixtures/config_everyday.json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env_for_home(Path(tmp)),
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"],
            "UserPromptSubmit",
        )
        self.assertIn(
            "[MANDATORY]",
            payload["hookSpecificOutput"]["additionalContext"],
        )


if __name__ == "__main__":
    unittest.main()
