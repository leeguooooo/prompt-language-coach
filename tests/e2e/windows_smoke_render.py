"""Windows encoding smoke test for render_coaching_context.

Pre-0.12.1, the render hook crashed with UnicodeEncodeError on Windows
PowerShell because `print(json.dumps(..., ensure_ascii=False))` used the
default stdout encoding (GBK / cp1252 / cp936) which cannot encode 📚
(U+1F4DA) in coaching box titles.

This script runs the render hook as a child process inheriting the current
(Windows default) stdout encoding, then asserts:
  1. Exit code is 0 (no crash)
  2. Output is valid UTF-8
  3. The 📚 emoji is present in the emitted JSON

Run locally with `PYTHONIOENCODING=gbk:strict python tests/e2e/windows_smoke_render.py`
to exercise the same path without a Windows runner.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BOOK_EMOJI = "\U0001f4da"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".cursor").mkdir()
        shared = home / ".prompt-language-coach"
        shared.mkdir()
        (shared / "language-coach.json").write_text(
            json.dumps(
                {
                    "nativeLanguage": "Chinese",
                    "targetLanguage": "English",
                    "goal": "everyday",
                    "mode": "everyday",
                    "style": "teaching",
                    "responseLanguage": "native",
                    "enabled": True,
                    "targets": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "render_coaching_context.py"), "--platform", "cursor"],
            env=env,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            sys.stderr.buffer.write(b"render exited non-zero\n")
            sys.stderr.buffer.write(result.stderr)
            return 1

        try:
            text = result.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            sys.stderr.write(f"render output was not valid UTF-8: {exc}\n")
            return 1

        if BOOK_EMOJI not in text:
            sys.stderr.write("render output did not contain 📚 (coaching box emoji)\n")
            sys.stderr.write(f"output head: {text[:200]}\n")
            return 1

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"render output was not valid JSON: {exc}\n")
            return 1

        if "additional_context" not in payload:
            sys.stderr.write("render output missing additional_context key\n")
            return 1

        print("Windows UTF-8 render smoke test OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
