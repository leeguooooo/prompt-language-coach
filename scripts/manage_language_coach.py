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

from shared.codex.agents_md import remove_block as remove_codex_agents_md_block
from shared.codex.agents_md import upsert_block as upsert_codex_agents_md_block
from shared.config.io import load_config, load_defaults, save_config
from shared.config.schema import (
    ALLOWED_GOALS,
    ALLOWED_IELTS_FOCUS,
    ALLOWED_MODES,
    ALLOWED_RESPONSE_LANGUAGES,
    ALLOWED_STYLES,
    canonicalize_goal,
    canonicalize_mode,
)
from shared.proficiency import normalize_estimate, scale_for_language
from shared.prompts.build_prompt import build_prompt, build_static_prompt
from platforms.codex.install_hooks import (
    HOOK_EVENT,
    install as install_codex_hook,
    is_managed_entry,
    load_payload as load_codex_hooks_payload,
    remove as remove_codex_hook,
)
from platforms.cursor.install_hooks import (
    HOOK_EVENT as CURSOR_HOOK_EVENT,
    install as install_cursor_hook,
    is_managed_entry as is_cursor_managed_entry,
    load_payload as load_cursor_hooks_payload,
    remove as remove_cursor_hook,
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


def resolve_shared_config_path() -> Path:
    return Path.home() / ".prompt-language-coach" / "language-coach.json"


def resolve_all_config_paths() -> list[Path]:
    return [
        resolve_shared_config_path(),
        Path.home() / ".claude" / "language-coach.json",
        Path.home() / ".codex" / "language-coach.json",
        Path.home() / ".cursor" / "language-coach.json",
    ]


def resolve_effective_config_path(platform: str) -> Path | None:
    # Shared path is canonical; per-platform mirrors are fallbacks for legacy installs.
    preferred = [
        resolve_shared_config_path(),
        resolve_default_config(platform),
    ]
    fallbacks = [
        path
        for path in resolve_all_config_paths()
        if path not in preferred
    ]
    for candidate in preferred + fallbacks:
        if candidate.exists():
            return candidate
    return None


def _migrate_config_to_shared() -> None:
    """One-time migration: promote the first existing per-platform config to shared."""
    shared = resolve_shared_config_path()
    if shared.exists():
        return
    for platform in ("claude", "codex", "cursor"):
        candidate = resolve_default_config(platform)
        if candidate.exists():
            try:
                shared.parent.mkdir(parents=True, exist_ok=True)
                shared.write_text(candidate.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError:
                pass
            return


def resolve_progress_path(platform: str) -> Path:
    del platform
    return resolve_shared_progress_path()


def resolve_shared_progress_path() -> Path:
    return Path.home() / ".prompt-language-coach" / "language-progress.json"


def resolve_all_progress_paths() -> list[Path]:
    return [
        resolve_shared_progress_path(),
        Path.home() / ".codex" / "language-progress.json",
        Path.home() / ".claude" / "language-progress.json",
        Path.home() / ".cursor" / "language-progress.json",
    ]


def resolve_vocab_path(platform: str) -> Path:
    del platform
    return resolve_shared_vocab_path()


def resolve_shared_vocab_path() -> Path:
    return Path.home() / ".prompt-language-coach" / "vocab-focus.json"


def resolve_all_vocab_paths() -> list[Path]:
    return [
        resolve_shared_vocab_path(),
        Path.home() / ".codex" / "vocab-focus.json",
        Path.home() / ".claude" / "vocab-focus.json",
        Path.home() / ".cursor" / "vocab-focus.json",
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


def resolve_cursor_hooks_path() -> Path:
    return Path.home() / ".cursor" / "hooks.json"


def cursor_hook_installed(hooks_path: Path) -> bool:
    payload = load_cursor_hooks_payload(hooks_path)
    hooks = payload.get("hooks", {})
    entries = hooks.get(CURSOR_HOOK_EVENT, [])
    if not isinstance(entries, list):
        return False
    return any(is_cursor_managed_entry(entry) for entry in entries)


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


def _merge_estimates(
    current: list[dict[str, str]], incoming: list[dict[str, str]]
) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}

    for record in current + incoming:
        date_key = record.get("date", "")
        if not date_key:
            continue
        estimate_value = record.get("estimate")
        if estimate_value is None:
            estimate_value = record.get("band")
        normalized_record = {"date": date_key}
        if estimate_value is not None:
            normalized_record["estimate"] = estimate_value
        if record.get("text"):
            normalized_record["text"] = record["text"]
        existing = merged.get(date_key)
        if existing is None:
            merged[date_key] = normalized_record
            continue
        if normalized_record.get("text") and not existing.get("text"):
            merged[date_key] = normalized_record

    return [merged[key] for key in sorted(merged.keys())]


def load_progress_data(platform: str) -> dict[str, Any]:
    del platform
    merged: dict[str, Any] = {}

    for path in resolve_all_progress_paths():
        payload = _load_progress(path)
        for language, incoming_entry in payload.items():
            if not isinstance(incoming_entry, dict):
                continue
            entry = merged.setdefault(
                language,
                {
                    "estimates": [],
                    "currentEstimate": None,
                    "scale": scale_for_language(language).key,
                },
            )
            entry["scale"] = (
                incoming_entry.get("scale")
                or entry.get("scale")
                or scale_for_language(language).key
            )
            entry["estimates"] = _merge_estimates(
                entry.get("estimates", []),
                incoming_entry.get("estimates", []),
            )
            if entry["estimates"]:
                entry["currentEstimate"] = entry["estimates"][-1].get("estimate")
            elif incoming_entry.get("currentEstimate") is not None:
                entry["currentEstimate"] = incoming_entry.get("currentEstimate")
            elif incoming_entry.get("currentBand") is not None:
                entry["currentEstimate"] = incoming_entry.get("currentBand")

    return merged


def save_progress_data(platform: str, data: dict[str, Any]) -> None:
    del platform
    for path in resolve_all_progress_paths():
        _save_progress(path, data)


def ensure_progress_snapshot(platform: str) -> dict[str, Any]:
    data = load_progress_data(platform)
    if data:
        save_progress_data(platform, data)
    return data


def _vocab_signature(entry: dict[str, Any]) -> tuple[str, str, str, str]:
    entry_type = str(entry.get("type", ""))
    if entry_type == "gap":
        return (
            entry_type,
            str(entry.get("native", "")),
            str(entry.get("target", "")),
            str(entry.get("context", "")),
        )
    if entry_type == "correction":
        return (
            entry_type,
            str(entry.get("wrong", "")),
            str(entry.get("right", "")),
            str(entry.get("context", "")),
        )
    return (
        entry_type,
        str(entry.get("from", "")),
        str(entry.get("to", "")),
        str(entry.get("context", "")),
    )


def _normalize_vocab_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    normalized["masteredHits"] = max(0, min(3, int(normalized.get("masteredHits", 0) or 0)))
    return normalized


def _merge_vocab_records(
    current: list[dict[str, Any]], incoming: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in current + incoming:
        if not isinstance(record, dict):
            continue
        normalized = _normalize_vocab_entry(record)
        merged[_vocab_signature(normalized)] = normalized
    return list(merged.values())


def _trim_active_vocab(entry: dict[str, Any]) -> None:
    active = [
        _normalize_vocab_entry(item)
        for item in entry.get("entries", [])
        if isinstance(item, dict)
    ]
    mastered = [
        _normalize_vocab_entry(item)
        for item in entry.get("mastered", [])
        if isinstance(item, dict)
    ]
    entry["entries"] = active[-20:]
    entry["mastered"] = mastered


def load_vocab_data(platform: str) -> dict[str, Any]:
    del platform
    merged: dict[str, Any] = {}
    for path in resolve_all_vocab_paths():
        payload = _load_progress(path)
        for language, incoming_entry in payload.items():
            if not isinstance(incoming_entry, dict):
                continue
            entry = merged.setdefault(language, {"entries": [], "mastered": []})
            entry["entries"] = _merge_vocab_records(
                entry.get("entries", []),
                incoming_entry.get("entries", []),
            )
            entry["mastered"] = _merge_vocab_records(
                entry.get("mastered", []),
                incoming_entry.get("mastered", []),
            )
            _trim_active_vocab(entry)
    return merged


def save_vocab_data(platform: str, data: dict[str, Any]) -> None:
    del platform
    for path in resolve_all_vocab_paths():
        _save_progress(path, data)


def ensure_vocab_snapshot(platform: str) -> dict[str, Any]:
    data = load_vocab_data(platform)
    if data:
        save_vocab_data(platform, data)
    return data


def save_config_data(platform: str, config: dict[str, Any]) -> None:
    del platform
    for path in resolve_all_config_paths():
        save_config(path, config)


def cmd_record_estimate(args: argparse.Namespace) -> int:
    data = load_progress_data(args.platform)

    language = args.language
    scale = scale_for_language(language)
    estimate = normalize_estimate(args.band, scale=scale) or args.band
    today = datetime.date.today().isoformat()

    entry = data.setdefault(
        language,
        {"estimates": [], "currentEstimate": None, "scale": scale.key},
    )
    estimates: list[dict[str, str]] = entry.get("estimates", [])

    # Build the record — include original text when provided
    text = getattr(args, "text", "") or ""
    record: dict[str, str] = {"date": today, "estimate": estimate}
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
    entry["currentEstimate"] = estimate
    entry["scale"] = scale.key
    save_progress_data(args.platform, data)
    print(f"Recorded: {language} estimate {estimate} on {today}")
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    data = ensure_progress_snapshot(args.platform)

    filter_language = getattr(args, "language", None)
    languages = [filter_language] if filter_language else sorted(data.keys())

    if not languages or (filter_language and filter_language not in data):
        lang_label = filter_language or "any language"
        print(f"No progress data found for {lang_label}.")
        return 0

    for lang in languages:
        entry = data.get(lang, {})
        estimates: list[dict[str, str]] = entry.get("estimates", [])
        current_estimate = entry.get("currentEstimate")
        recent = estimates[-5:]
        print(f"{lang} progress (last {len(recent)} session{'s' if len(recent) != 1 else ''}):")
        if recent:
            for est in recent:
                estimate_value = est.get("estimate")
                if estimate_value is None:
                    estimate_value = est.get("band")
                print(f"  {est['date']}  {estimate_value}")
        else:
            print("  (no data yet)")
        print(f"Current estimate: {current_estimate if current_estimate is not None else '-'}")
        print()
    return 0


def _build_vocab_record(args: argparse.Namespace, today: str) -> tuple[dict[str, Any], str]:
    context = getattr(args, "context", "") or ""
    note = getattr(args, "note", "") or ""
    if args.entry_type == "gap":
        record = {
            "date": today,
            "type": "gap",
            "native": args.native,
            "target": args.target,
            "masteredHits": 0,
        }
        label = f"{args.native} -> {args.target}"
    elif args.entry_type == "correction":
        record = {
            "date": today,
            "type": "correction",
            "wrong": args.wrong,
            "right": args.right,
            "masteredHits": 0,
        }
        label = f"{args.wrong} -> {args.right}"
    else:
        record = {
            "date": today,
            "type": "upgrade",
            "from": args.from_word,
            "to": args.to_word,
            "masteredHits": 0,
        }
        label = f"{args.from_word} -> {args.to_word}"
    if context:
        record["context"] = context
    if note:
        record["note"] = note
    return record, label


def cmd_track_vocab(args: argparse.Namespace) -> int:
    data = load_vocab_data(args.platform)
    today = datetime.date.today().isoformat()
    entry = data.setdefault(args.language, {"entries": [], "mastered": []})
    record, label = _build_vocab_record(args, today)
    entry["entries"].append(record)
    _trim_active_vocab(entry)
    save_vocab_data(args.platform, data)
    print(f"Recorded: {args.language} {args.entry_type} {label} on {today}")
    return 0


def _entry_identifier(entry: dict[str, Any]) -> str:
    if entry.get("type") == "gap":
        return str(entry.get("target", ""))
    if entry.get("type") == "correction":
        return str(entry.get("right", ""))
    return str(entry.get("to", ""))


def cmd_mark_vocab_mastered(args: argparse.Namespace) -> int:
    data = load_vocab_data(args.platform)
    entry = data.get(args.language)
    if not isinstance(entry, dict):
        print(f"No active vocab focus found for {args.language}.")
        return 0

    active = [
        _normalize_vocab_entry(item)
        for item in entry.get("entries", [])
        if isinstance(item, dict)
    ]
    for index in range(len(active) - 1, -1, -1):
        item = active[index]
        if _entry_identifier(item) != args.identifier:
            continue
        item["masteredHits"] = min(3, item.get("masteredHits", 0) + 1)
        if item["masteredHits"] >= 3:
            active.pop(index)
            mastered = [
                _normalize_vocab_entry(existing)
                for existing in entry.get("mastered", [])
                if isinstance(existing, dict)
            ]
            mastered.append(item)
            entry["mastered"] = mastered
            entry["entries"] = active
            save_vocab_data(args.platform, data)
            print(f"Mastered: {args.language} {args.identifier}")
            return 0
        active[index] = item
        entry["entries"] = active
        save_vocab_data(args.platform, data)
        print(f"Mastered hit: {args.language} {args.identifier} ({item['masteredHits']}/3)")
        return 0

    print(f"No active vocab focus found for {args.language}: {args.identifier}")
    return 0


def _format_vocab_pair(entry: dict[str, Any]) -> str:
    entry_type = entry.get("type")
    if entry_type == "gap":
        return f"{entry.get('native', '-')} -> {entry.get('target', '-')}"
    if entry_type == "correction":
        return f"{entry.get('wrong', '-')} -> {entry.get('right', '-')}"
    return f"{entry.get('from', '-')} -> {entry.get('to', '-')}"


def cmd_vocab(args: argparse.Namespace) -> int:
    data = ensure_vocab_snapshot(args.platform)
    filter_language = getattr(args, "value", None)
    languages = [filter_language] if filter_language else sorted(data.keys())
    if not languages or (filter_language and filter_language not in data):
        lang_label = filter_language or "any language"
        print(f"No vocab focus data found for {lang_label}.")
        return 0

    for language in languages:
        entry = data.get(language, {})
        active = entry.get("entries", [])
        print(
            f"{language} vocab focus (active {len(active)} entr{'y' if len(active) == 1 else 'ies'}):"
        )
        if active:
            for item in active[-5:]:
                note = f"  [{item['note']}]" if item.get("note") else ""
                print(f"  {item['date']}  {item['type']}  {_format_vocab_pair(item)}{note}")
        else:
            print("  (no active entries)")
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
        "estimate": None,
        "focus": sorted(ALLOWED_IELTS_FOCUS),
        "practice-focus": sorted(ALLOWED_IELTS_FOCUS),
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

    child = subparsers.add_parser("track-estimate", help="Record a proficiency estimate for a language.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("band", help="Estimate value, e.g. 5.5 or N4")
    child.add_argument("--text", default="", help="The user's original message (optional, for history review)")

    child = subparsers.add_parser("record-estimate", help="Legacy alias for track-estimate.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("band", help="Estimate value, e.g. 5.5 or N4")
    child.add_argument("--text", default="", help="The user's original message (optional, for history review)")

    child = subparsers.add_parser("record-band", help="Legacy alias for record-estimate.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("band", help="Estimate value, e.g. 5.5 or N4")
    child.add_argument("--text", default="", help="The user's original message (optional, for history review)")

    child = subparsers.add_parser("progress", help="Show recent estimate history.")
    child.add_argument("language", nargs="?", default=None, help="Optional language to filter by")

    child = subparsers.add_parser("track-vocab", help="Record a vocab focus entry.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("entry_type", choices=("gap", "correction", "upgrade"))
    child.add_argument("--native")
    child.add_argument("--target")
    child.add_argument("--wrong")
    child.add_argument("--right")
    child.add_argument("--from", dest="from_word")
    child.add_argument("--to", dest="to_word")
    child.add_argument("--context", default="")
    child.add_argument("--note", default="")

    child = subparsers.add_parser("mark-vocab-mastered", help="Advance mastery for one vocab focus entry.")
    child.add_argument("language", help="Language name, e.g. English")
    child.add_argument("identifier", help="target/right/to value")

    child = subparsers.add_parser("vocab", help="Show active vocab focus or toggle vocab focus.")
    child.add_argument("value", nargs="?", default=None, help="Optional language, or on/off to toggle the feature")

    subparsers.add_parser("progress-path", help="Print the progress file path for the current platform.")
    for name in ("install-hook", "remove-hook", "hook-status"):
        subparsers.add_parser(name)

    return parser.parse_args()


def normalize_goal_state(config: dict[str, object]) -> None:
    goal = canonicalize_goal(config.get("goal"), default="everyday")
    mode = canonicalize_mode(config.get("mode"), default="everyday")
    focus = config.get("scoringFocus")
    config["goal"] = goal
    config["mode"] = mode

    if goal == "everyday":
        config["mode"] = "everyday"
        return

    if goal == "scored" and mode == "everyday":
        config["mode"] = "scored-speaking" if focus == "speaking" else "scored-writing"


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
    target["goal"] = "everyday"
    target["mode"] = "everyday"
    target["scoringFocus"] = "both"
    target["targetEstimate"] = ""
    target["currentLevel"] = ""
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
        config["goal"] = canonicalize_goal(args.value, default="everyday")
        normalize_goal_state(config)
        return f"Goal updated to: {config['goal']}"
    if args.command == "mode":
        mode = canonicalize_mode(args.value, default="everyday")
        config["mode"] = mode
        if mode in {"scored-writing", "scored-speaking"}:
            config["goal"] = "scored"
        elif mode == "everyday":
            config["goal"] = "everyday"
        return f"Mode updated to: {mode}"
    if args.command in {"band", "estimate"}:
        config["targetEstimate"] = args.value
        return f"Target estimate updated to: {args.value}"
    if args.command in {"focus", "practice-focus"}:
        config["scoringFocus"] = args.value
        if config.get("goal") == "scored" and config.get("mode") in {
            "scored-speaking",
            "scored-writing",
        }:
            if args.value == "speaking":
                config["mode"] = "scored-speaking"
            elif args.value == "writing":
                config["mode"] = "scored-writing"
        return f"Scoring focus updated to: {args.value}"
    if args.command == "level":
        config["currentLevel"] = args.value
        return f"Current level updated to: {args.value}"
    if args.command == "vocab" and args.value in {"on", "off"}:
        config["vocabFocus"] = args.value == "on"
        return f"Vocab focus {'enabled' if config['vocabFocus'] else 'disabled'}."
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
        f"Vocab focus:       {'on' if config['vocabFocus'] else 'off'}",
        f"Scoring focus:     {config['scoringFocus']}",
        f"Target estimate:   {config['targetEstimate'] or '-'}",
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
        build_static_prompt(config),
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


def sync_codex_agents_md(config: dict[str, Any]) -> None:
    codex_home = Path.home() / ".codex"
    if not codex_home.exists():
        return
    if not config.get("enabled", True):
        remove_codex_agents_md_block()
        return
    static_text = build_static_prompt(
        config,
        repo_root=str(REPO_ROOT),
        vocab_path=str(resolve_vocab_path("codex")),
    )
    upsert_codex_agents_md_block(static_text)


def _should_sync_runtime_files(args: argparse.Namespace, path: Path) -> bool:
    if not args.config:
        return True
    expected = {
        resolve_default_config(args.platform).expanduser(),
        resolve_shared_config_path().expanduser(),
    }
    return path.expanduser() in expected


def main() -> int:
    args = parse_args()
    _migrate_config_to_shared()

    if args.command in {"record-band", "record-estimate", "track-estimate"}:
        return cmd_record_estimate(args)
    if args.command == "track-vocab":
        return cmd_track_vocab(args)
    if args.command == "mark-vocab-mastered":
        return cmd_mark_vocab_mastered(args)
    if args.command == "progress":
        return cmd_progress(args)
    if args.command == "vocab" and getattr(args, "value", None) not in {"on", "off"}:
        return cmd_vocab(args)
    if args.command == "progress-path":
        print(resolve_progress_path(args.platform))
        return 0
    if args.command == "install-hook":
        if args.platform == "cursor":
            hooks_path = resolve_cursor_hooks_path()
            install_cursor_hook(hooks_path, REPO_ROOT)
            print(f"Cursor hook installed: {hooks_path}")
        else:
            hooks_path = resolve_codex_hooks_path()
            install_codex_hook(hooks_path, REPO_ROOT)
            effective_config = resolve_effective_config_path("codex")
            if effective_config is not None:
                sync_codex_agents_md(load_config(effective_config))
            print(f"Codex hook installed: {hooks_path}")
        return 0
    if args.command == "remove-hook":
        if args.platform == "cursor":
            hooks_path = resolve_cursor_hooks_path()
            remove_cursor_hook(hooks_path)
            print(f"Cursor hook removed: {hooks_path}")
        else:
            hooks_path = resolve_codex_hooks_path()
            remove_codex_hook(hooks_path)
            remove_codex_agents_md_block()
            print(f"Codex hook removed: {hooks_path}")
        return 0
    if args.command == "hook-status":
        if args.platform == "cursor":
            print(
                "installed"
                if cursor_hook_installed(resolve_cursor_hooks_path())
                else "not installed"
            )
        else:
            print(
                "installed"
                if codex_hook_installed(resolve_codex_hooks_path())
                else "not installed"
            )
        return 0

    if args.config:
        path = Path(args.config).expanduser()
        configured = path.exists()
    else:
        effective_path = resolve_effective_config_path(args.platform)
        path = effective_path or resolve_default_config(args.platform)
        configured = effective_path is not None
    config = load_config(path)

    if args.command == "status":
        print(format_status(config, path, args.platform, configured))
        return 0

    message = apply_command(config, args, path)
    if args.config:
        save_config(path, config)
    else:
        save_config_data(args.platform, config)
    if _should_sync_runtime_files(args, path):
        sync_claude_md(config, args.platform)
        sync_codex_agents_md(config)
    if message is not None:
        print(message)
    print(f"Config file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
