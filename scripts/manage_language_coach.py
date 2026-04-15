from __future__ import annotations

import argparse
import sys
from pathlib import Path


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


def resolve_default_config(platform: str) -> Path:
    home = Path.home()
    if platform == "codex":
        return home / ".codex" / "language-coach.json"
    return home / ".claude" / "language-coach.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage language coach config for Claude or Codex."
    )
    parser.add_argument("--platform", choices=("claude", "codex"), default="claude")
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


def apply_command(config: dict[str, object], args: argparse.Namespace) -> str | None:
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
            f"Status:            {status}",
            f"Config file:       {path}",
        ]
    )


def main() -> int:
    args = parse_args()
    path = Path(args.config).expanduser() if args.config else resolve_default_config(args.platform)
    configured = path.exists()
    config = load_config(path)

    if args.command == "status":
        print(format_status(config, path, args.platform, configured))
        return 0

    message = apply_command(config, args)
    save_config(path, config)
    if message is not None:
        print(message)
    print(f"Config file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
