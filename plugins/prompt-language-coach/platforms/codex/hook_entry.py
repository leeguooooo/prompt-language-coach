from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    config_path = Path.home() / ".codex" / "language-coach.json"
    if not config_path.exists():
        return 0

    python_executable = sys.executable or "python3"
    command = [
        python_executable,
        str(REPO_ROOT / "scripts" / "render_coaching_context.py"),
        "--platform",
        "codex",
        "--config",
        str(config_path),
    ]
    try:
        return subprocess.call(command)
    except OSError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
