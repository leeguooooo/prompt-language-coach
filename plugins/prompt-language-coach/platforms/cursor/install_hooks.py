"""Install a top-level ~/.cursor/hooks.json entry for prompt-language-coach.

Plugin-manifest hooks declared via ``.cursor-plugin/plugin.json -> hooks``
are unreliable on current Cursor releases: ``${CURSOR_PLUGIN_ROOT}`` does
not always expand, and the plugin manifest is sometimes not reloaded after
edits. The top-level ``~/.cursor/hooks.json`` location is documented and
fires consistently, so we mirror the codex installer and register our
sessionStart entry there with an absolute path.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


HOOK_EVENT = "sessionStart"
HOOK_SCRIPT_REL = "hooks/cursor-language-coach.sh"
HOOK_RENDER_SIGNATURE = "render_coaching_context.py"


def _is_windows() -> bool:
    return os.name == "nt"


def build_hook_command(repo_root: Path) -> str:
    if _is_windows():
        python_exec = sys.executable if sys.executable and Path(sys.executable).is_absolute() else "python"
        render_script = str(repo_root / "scripts" / "render_coaching_context.py")
        return f'"{python_exec}" "{render_script}" --platform cursor'
    hook_script = shlex.quote(str(repo_root / "hooks" / "cursor-language-coach.sh"))
    return f"bash {hook_script}"


def build_managed_entry(repo_root: Path) -> dict[str, Any]:
    return {
        "type": "command",
        "command": build_hook_command(repo_root),
    }


def load_payload(hooks_path: Path) -> dict[str, Any]:
    if not hooks_path.exists():
        return {"hooks": {}}

    payload = json.loads(hooks_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"hooks": {}}
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        payload["hooks"] = {}
    return payload


def is_managed_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    command = entry.get("command")
    if not isinstance(command, str):
        return False
    if HOOK_SCRIPT_REL in command:
        return True
    if HOOK_RENDER_SIGNATURE in command and "--platform cursor" in command:
        return True
    return False


def write_payload(hooks_path: Path, payload: dict[str, Any]) -> None:
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def install(hooks_path: Path, repo_root: Path) -> None:
    payload = load_payload(hooks_path)
    hooks = payload.setdefault("hooks", {})
    existing_entries = hooks.get(HOOK_EVENT, [])
    if not isinstance(existing_entries, list):
        existing_entries = []

    preserved_entries = [
        entry for entry in existing_entries if not is_managed_entry(entry)
    ]
    preserved_entries.append(build_managed_entry(repo_root))
    hooks[HOOK_EVENT] = preserved_entries
    write_payload(hooks_path, payload)


def remove(hooks_path: Path) -> None:
    payload = load_payload(hooks_path)
    hooks = payload.get("hooks", {})
    existing_entries = hooks.get(HOOK_EVENT, [])
    if not isinstance(existing_entries, list):
        existing_entries = []

    preserved_entries = [
        entry for entry in existing_entries if not is_managed_entry(entry)
    ]
    if preserved_entries:
        hooks[HOOK_EVENT] = preserved_entries
    else:
        hooks.pop(HOOK_EVENT, None)
    write_payload(hooks_path, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hooks-path", default=str(Path.home() / ".cursor" / "hooks.json")
    )
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("command", choices={"install", "remove"})
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hooks_path = Path(args.hooks_path).expanduser()
    repo_root = Path(args.repo_root).resolve()
    if args.command == "install":
        install(hooks_path, repo_root)
    else:
        remove(hooks_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
