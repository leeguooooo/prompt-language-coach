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

    command = [
        "python3",
        str(REPO_ROOT / "scripts" / "render_coaching_context.py"),
        "--platform",
        "codex",
        "--config",
        str(config_path),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
