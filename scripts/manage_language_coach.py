from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.config.io import load_config, load_defaults, save_config
from shared.config.schema import (
    ALLOWED_GOALS,
    ALLOWED_IELTS_FOCUS,
    ALLOWED_MODES,
    ALLOWED_RESPONSE_LANGUAGES,
    ALLOWED_STYLES,
)
from shared.prompts.build_prompt import build_prompt
from platforms.codex.install_hooks import (
    HOOK_EVENT,
    install as install_codex_hook,
    is_managed_entry,
    load_payload as load_codex_hooks_payload,
    remove as remove_codex_hook,
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


def resolve_progress_path(platform: str) -> Path:
    home = Path.home()
    if platform == "codex":
        return home / ".codex" / "language-progress.json"
    if platform == "cursor":
        return home / ".cursor" / "language-progress.json"
    return home / ".claude" / "language-progress.json"


def resolve_shared_progress_path() -> Path:
    return Path.home() / ".prompt-language-coach" / "language-progress.json"


def resolve_all_progress_paths() -> list[Path]:
    return [
        resolve_shared_progress_path(),
        Path.home() / ".codex" / "language-progress.json",
        Path.home() / ".claude" / "language-progress.json",
        Path.home() / ".cursor" / "language-progress.json",
    ]


def resolve_codex_hooks_path() -> Path:
    return Path.home() / ".codex" / "hooks.json"


def codex_hook_installed(hooks_path: Path) -> bool:
    payload = load_codex_hooks_payload(hooks_path)
    hooks = payload.get("hooks", {})
    entries = hooks.get(HOOK_EVENT, [])
    if not isinstance(entries, list):
        return False
    return any(is_managed_entry(entry) for entry in entries)


def _load_progress(progress_path: Path) -> dict[str, Any]:
    if progress_path.exists():
        try:
            return json.loads(progress_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_progress(progress_path: Path, data: dict[str, Any]) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_record_band(args: argparse.Namespace) -> int:
    progress_path = resolve_shared_progress_path()
    data = _load_progress(progress_path)

    language = args.language
    band = args.band
    today = datetime.date.today().isoformat()

    entry = data.setdefault(language, {"estimates": [], "currentBand": None})
    estimates: list[dict[str, str]] = entry.get("estimates", [])

    # Build the record — include original text when provided
    text = getattr(args, "text", "") or ""
    record: dict[str, str] = {"date": today, "band": band}
    if text:
        record["text"] = text[:500]  # cap at 500 chars

    # Overwrite existing entry for the same date (idempotent)
    replaced = False
    for i, est in enumerate(estimates):
        if est.get("date") == today:
            estimates[i] = record
            replaced = True
            break
    if not replaced:
        estimates.append(record)

    entry["estimates"] = estimates
    entry["currentBand"] = band
    for path in resolve_all_progress_paths():
        _save_progress(path, data)
    print(f"Recorded: {language} band {band} on {today}")
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    progress_path = resolve_shared_progress_path()
    data = _load_progress(progress_path)
    if not data:
        data = _load_progress(resolve_progress_path(args.platform))

    filter_language = getattr(args, "language", None)
    languages = [filter_language] if filter_language else sorted(data.keys())

    if not languages or (filter_language and filter_language not in data):
        lang_label = filter_language or "any language"
        print(f"No progress data found for {lang_label}.")
        return 0

    for lang in languages:
        entry = data.get(lang, {})
        estimates: list[dict[str, str]] = entry.get("estimates", [])
        current_band = entry.get("currentBand")
        recent = estimates[-5:]
        print(f"{lang} progress (last {len(recent)} session{'s' if len(recent) != 1 else ''}):")
        if recent:
            for est in recent:
                print(f"  {est['date']}  {est['band']}")
        else:
            print("  (no data yet)")
        print(f"Current estimate: {current_band if current_band is not None else '-'}")
        print()
    return 0


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

    child = subparsers.add_parser("record-band", help="Record an IELTS band estimate for a language.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("band", help="Band score, e.g. 5.5")
    child.add_argument("--text", default="", help="The user's original message (optional, for history review)")

    child = subparsers.add_parser("progress", help="Show recent band history.")
    child.add_argument("language", nargs="?", default=None, help="Optional language to filter by")

    subparsers.add_parser("progress-path", help="Print the progress file path for the current platform.")
    for name in ("install-hook", "remove-hook", "hook-status"):
        subparsers.add_parser(name)

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
    target = load_defaults()
    target["targetLanguage"] = language
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

    lines = [
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
    ]
    if platform == "codex":
        hook_status = "installed" if codex_hook_installed(resolve_codex_hooks_path()) else "not installed"
        lines.append(f"Hook status:       {hook_status}")
    lines.append(f"Config file:       {path}")
    return "\n".join(lines)


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

    if args.command == "record-band":
        return cmd_record_band(args)
    if args.command == "progress":
        return cmd_progress(args)
    if args.command == "progress-path":
        print(resolve_progress_path(args.platform))
        return 0
    if args.command == "install-hook":
        hooks_path = resolve_codex_hooks_path()
        install_codex_hook(hooks_path, REPO_ROOT)
        print(f"Codex hook installed: {hooks_path}")
        return 0
    if args.command == "remove-hook":
        hooks_path = resolve_codex_hooks_path()
        remove_codex_hook(hooks_path)
        print(f"Codex hook removed: {hooks_path}")
        return 0
    if args.command == "hook-status":
        print("installed" if codex_hook_installed(resolve_codex_hooks_path()) else "not installed")
        return 0

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
