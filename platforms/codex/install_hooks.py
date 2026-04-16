from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any


HOOK_EVENT = "UserPromptSubmit"
HOOK_ENTRY_PATH = "platforms/codex/hook_entry.py"


def build_hook_command(repo_root: Path) -> str:
    hook_entry = shlex.quote(str(repo_root / "platforms" / "codex" / "hook_entry.py"))
    script_parts = []

    if sys.executable and Path(sys.executable).is_absolute():
        interpreter = shlex.quote(sys.executable)
        script_parts.append(f"if [ -x {interpreter} ]; then exec {interpreter} {hook_entry}; fi")

    script_parts.append(
        f"if command -v python3 >/dev/null 2>&1; then exec python3 {hook_entry}; fi"
    )
    script_parts.append("exit 0")

    return f"/bin/sh -lc {shlex.quote('; '.join(script_parts))}"


def build_managed_entry(repo_root: Path) -> dict[str, Any]:
    return {
        "hooks": [
            {
                "type": "command",
                "command": build_hook_command(repo_root),
            }
        ]
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
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return False
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        if hook.get("type") != "command":
            continue
        command = hook.get("command")
        if isinstance(command, str) and HOOK_ENTRY_PATH in command:
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
        "--hooks-path", default=str(Path.home() / ".codex" / "hooks.json")
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
