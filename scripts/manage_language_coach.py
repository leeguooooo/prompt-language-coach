from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.config.io import load_config, save_config
from shared.config.schema import (
    ALLOWED_GOALS,
    ALLOWED_IELTS_FOCUS,
    ALLOWED_MODES,
    ALLOWED_RESPONSE_LANGUAGES,
    ALLOWED_STYLES,
)
from shared.prompts.build_prompt import build_prompt

TARGET_INHERIT_KEYS = (
    "goal",
    "mode",
    "ieltsFocus",
    "targetBand",
    "currentLevel",
)
TARGET_FALLBACK_KEYS = (
    "style",
    "responseLanguage",
)


def resolve_default_config(platform: str) -> Path:
    home = Path.home()
    if platform == "codex":
        return home / ".codex" / "language-coach.json"
    if platform == "cursor":
        return home / ".cursor" / "language-coach.json"
    return home / ".claude" / "language-coach.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage language coach config for Claude or Codex."
    )
    parser.add_argument("--platform", choices=("claude", "codex", "cursor"), default="claude")
    parser.add_argument(
        "--config",
        help="Optional explicit config path. Defaults to the platform-specific location.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("status", "on", "off"):
        subparsers.add_parser(name)

    value_commands = {
        "native": None,
        "target": None,
        "style": sorted(ALLOWED_STYLES),
        "response": sorted(ALLOWED_RESPONSE_LANGUAGES),
        "goal": sorted(ALLOWED_GOALS),
        "mode": sorted(ALLOWED_MODES),
        "band": None,
        "focus": sorted(ALLOWED_IELTS_FOCUS),
        "level": None,
    }
    for name, choices in value_commands.items():
        child = subparsers.add_parser(name)
        child.add_argument("value", choices=choices)

    child = subparsers.add_parser("target-add")
    child.add_argument("value")

    child = subparsers.add_parser("target-remove")
    child.add_argument("value")

    subparsers.add_parser("target-list")

    return parser.parse_args()


def normalize_goal_state(config: dict[str, object]) -> None:
    goal = config.get("goal")
    mode = config.get("mode")
    focus = config.get("ieltsFocus")

    if goal == "everyday":
        config["mode"] = "everyday"
        return

    if goal == "ielts" and mode == "everyday":
        config["mode"] = "ielts-speaking" if focus == "speaking" else "ielts-writing"


def list_targets(config: dict[str, Any]) -> list[str]:
    raw_targets = config.get("targets")
    if isinstance(raw_targets, list):
        return [
            target["targetLanguage"]
            for target in raw_targets
            if isinstance(target, dict) and target.get("targetLanguage")
        ]

    target_language = config.get("targetLanguage")
    if isinstance(target_language, str) and target_language:
        return [target_language]
    return []


def _target_defaults(config: dict[str, Any], language: str) -> dict[str, Any]:
    target = {"targetLanguage": language}
    for key in TARGET_INHERIT_KEYS:
        target[key] = config.get(key)
    for key in TARGET_FALLBACK_KEYS:
        target[key] = config.get(key)
    return target


def add_target(config: dict[str, Any], language: str) -> bool:
    current_targets = [
        target
        for target in config.get("targets", [])
        if isinstance(target, dict) and target.get("targetLanguage")
    ]

    if not current_targets and config.get("targetLanguage"):
        current_targets.append(_target_defaults(config, str(config["targetLanguage"])))

    existing = {
        str(target["targetLanguage"]).casefold()
        for target in current_targets
        if target.get("targetLanguage")
    }
    if language.casefold() in existing:
        config["targets"] = current_targets
        return False

    current_targets.append(_target_defaults(config, language))
    config["targets"] = current_targets
    return True


def remove_target(config: dict[str, Any], language: str) -> bool:
    raw_targets = config.get("targets", [])
    if not isinstance(raw_targets, list):
        return False

    remaining = [
        target
        for target in raw_targets
        if not (
            isinstance(target, dict)
            and str(target.get("targetLanguage", "")).casefold() == language.casefold()
        )
    ]
    removed = len(remaining) != len(raw_targets)
    config["targets"] = remaining
    if remaining and isinstance(remaining[0], dict) and remaining[0].get("targetLanguage"):
        config["targetLanguage"] = remaining[0]["targetLanguage"]
    return removed


def apply_command(
    config: dict[str, object], args: argparse.Namespace, path: Path | None = None
) -> str | None:
    if args.command == "native":
        config["nativeLanguage"] = args.value
        return f"Native language updated to: {args.value}"
    if args.command == "target":
        config["targetLanguage"] = args.value
        return f"Target language updated to: {args.value}"
    if args.command == "style":
        config["style"] = args.value
        return f"Style updated to: {args.value}"
    if args.command == "response":
        config["responseLanguage"] = args.value
        return f"Responses will use: {args.value}"
    if args.command == "goal":
        config["goal"] = args.value
        normalize_goal_state(config)
        return f"Goal updated to: {args.value}"
    if args.command == "mode":
        config["mode"] = args.value
        if args.value.startswith("ielts"):
            config["goal"] = "ielts"
        elif args.value == "everyday":
            config["goal"] = "everyday"
        return f"Mode updated to: {args.value}"
    if args.command == "band":
        config["targetBand"] = args.value
        return f"Target band updated to: {args.value}"
    if args.command == "focus":
        config["ieltsFocus"] = args.value
        if config.get("goal") == "ielts" and config.get("mode") in {
            "ielts-speaking",
            "ielts-writing",
        }:
            if args.value == "speaking":
                config["mode"] = "ielts-speaking"
            elif args.value == "writing":
                config["mode"] = "ielts-writing"
        return f"IELTS focus updated to: {args.value}"
    if args.command == "level":
        config["currentLevel"] = args.value
        return f"Current level updated to: {args.value}"
    if args.command == "target-add":
        if path is not None:
            current_config = load_config(path)
            config.clear()
            config.update(current_config)
        added = add_target(config, args.value)
        if added:
            return f"Target added: {args.value}"
        return f"Target already exists: {args.value}"
    if args.command == "target-remove":
        removed = remove_target(config, args.value)
        if removed:
            return f"Target removed: {args.value}"
        return f"Target not found: {args.value}"
    if args.command == "target-list":
        targets = list_targets(config)
        if targets:
            return "\n".join(targets)
        return "(no configured targets)"
    if args.command == "on":
        config["enabled"] = True
        return "Language coach active."
    if args.command == "off":
        config["enabled"] = False
        return "Language coach paused."
    return None


def format_status(
    config: dict[str, object], path: Path, platform: str, configured: bool
) -> str:
    status = "on" if config["enabled"] else "off"
    if not configured:
        status = "not configured"

    return "\n".join(
        [
            f"Platform:          {platform}",
            f"Native language:   {config['nativeLanguage']}",
            f"Target language:   {config['targetLanguage']}",
            f"Goal:              {config['goal']}",
            f"Mode:              {config['mode']}",
            f"Style:             {config['style']}",
            f"Response in:       {config['responseLanguage']}",
            f"IELTS focus:       {config['ieltsFocus']}",
            f"Target band:       {config['targetBand'] or '-'}",
            f"Current level:     {config['currentLevel'] or '-'}",
            f"Targets:           {', '.join(list_targets(config)) or '-'}",
            f"Status:            {status}",
            f"Config file:       {path}",
        ]
    )


_MARKER_START = "<!-- language-coach:start -->"
_MARKER_END = "<!-- language-coach:end -->"


def _platform_claude_md(platform: str) -> Path | None:
    """Return the CLAUDE.md path for platforms that support it, or None."""
    if platform == "claude":
        return Path.home() / ".claude" / "CLAUDE.md"
    return None


def sync_claude_md(config: dict[str, Any], platform: str) -> None:
    """Upsert the coaching instruction block in the platform CLAUDE.md."""
    md_path = _platform_claude_md(platform)
    if md_path is None:
        return

    if not config.get("enabled", True):
        # Remove the block when coaching is disabled
        if not md_path.exists():
            return
        text = md_path.read_text(encoding="utf-8")
        start = text.find(_MARKER_START)
        end = text.find(_MARKER_END)
        if start == -1 or end == -1:
            return
        before = text[:start].rstrip("\n")
        after = text[end + len(_MARKER_END):].lstrip("\n")
        new_text = (before + "\n" + after).strip()
        md_path.write_text(new_text + "\n" if new_text else "", encoding="utf-8")
        return

    coaching_block = "\n".join([
        _MARKER_START,
        build_prompt(config),
        _MARKER_END,
    ])

    if not md_path.exists():
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(coaching_block + "\n", encoding="utf-8")
        return

    text = md_path.read_text(encoding="utf-8")
    start = text.find(_MARKER_START)
    end = text.find(_MARKER_END)

    if start != -1 and end != -1:
        new_text = text[:start] + coaching_block + text[end + len(_MARKER_END):]
    else:
        separator = "\n\n" if text.strip() else ""
        new_text = text.rstrip("\n") + separator + coaching_block + "\n"

    md_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    path = Path(args.config).expanduser() if args.config else resolve_default_config(args.platform)
    configured = path.exists()
    config = load_config(path)

    if args.command == "status":
        print(format_status(config, path, args.platform, configured))
        return 0

    message = apply_command(config, args, path)
    save_config(path, config)
    sync_claude_md(config, args.platform)
    if message is not None:
        print(message)
    print(f"Config file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
