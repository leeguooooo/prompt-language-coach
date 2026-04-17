from __future__ import annotations

from typing import Any

CANONICAL_GOALS = {"everyday", "scored"}
LEGACY_GOAL_ALIASES = {
    "ielts": "scored",
}
ALLOWED_GOALS = CANONICAL_GOALS | set(LEGACY_GOAL_ALIASES)
CANONICAL_MODES = {"everyday", "scored-writing", "scored-speaking", "review"}
LEGACY_MODE_ALIASES = {
    "ielts-writing": "scored-writing",
    "ielts-speaking": "scored-speaking",
}
ALLOWED_MODES = CANONICAL_MODES | set(LEGACY_MODE_ALIASES)
ALLOWED_STYLES = {"teaching", "concise", "translate"}
ALLOWED_RESPONSE_LANGUAGES = {"native", "target"}
ALLOWED_IELTS_FOCUS = {"writing", "speaking", "both"}
IELTS_MODES = {"scored-writing", "scored-speaking"}

LEGACY_KEY_MAP = {
    "native": "nativeLanguage",
    "target": "targetLanguage",
    "ieltsFocus": "scoringFocus",
    "targetBand": "targetEstimate",
}

TARGET_OVERRIDE_KEYS = (
    "targetLanguage",
    "goal",
    "mode",
    "style",
    "responseLanguage",
    "vocabFocus",
    "scoringFocus",
    "targetEstimate",
    "currentLevel",
)


def canonicalize_goal(goal: str | None, *, default: str) -> str:
    if not goal:
        return default
    normalized = LEGACY_GOAL_ALIASES.get(goal, goal)
    return normalized if normalized in CANONICAL_GOALS else default


def canonicalize_mode(mode: str | None, *, default: str) -> str:
    if not mode:
        return default
    normalized = LEGACY_MODE_ALIASES.get(mode, mode)
    return normalized if normalized in CANONICAL_MODES else default


def _normalize_goal_mode_fields(
    data: dict[str, Any], defaults: dict[str, Any]
) -> dict[str, Any]:
    data["goal"] = canonicalize_goal(data.get("goal"), default=defaults["goal"])
    data["mode"] = canonicalize_mode(data.get("mode"), default=defaults["mode"])
    if data["style"] not in ALLOWED_STYLES:
        data["style"] = defaults["style"]
    if data["responseLanguage"] not in ALLOWED_RESPONSE_LANGUAGES:
        data["responseLanguage"] = defaults["responseLanguage"]
    if data["scoringFocus"] not in ALLOWED_IELTS_FOCUS:
        data["scoringFocus"] = defaults["scoringFocus"]

    if data["mode"] in IELTS_MODES:
        data["goal"] = "scored"

    if data["goal"] == "scored" and data["mode"] == "everyday":
        data["mode"] = "scored-writing"

    return data


def _normalize_targets(
    raw_targets: Any, config_defaults: dict[str, Any], defaults: dict[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(raw_targets, list):
        return []

    targets: list[dict[str, Any]] = []
    base = {key: config_defaults[key] for key in TARGET_OVERRIDE_KEYS if key != "targetLanguage"}

    for raw_target in raw_targets:
        if not isinstance(raw_target, dict):
            continue

        target = dict(base)
        if "targetLanguage" in raw_target:
            target["targetLanguage"] = raw_target["targetLanguage"]
        elif "target" in raw_target:
            target["targetLanguage"] = raw_target["target"]
        else:
            continue

        for key in TARGET_OVERRIDE_KEYS:
            if key in {"targetLanguage"}:
                continue
            if raw_target.get(key) is not None:
                target[key] = raw_target[key]

        normalized = _normalize_goal_mode_fields(target, defaults)
        targets.append(normalized)

    return targets


def normalize_config(raw: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    data = dict(defaults)
    migrated = dict(raw)

    for legacy_key, new_key in LEGACY_KEY_MAP.items():
        if legacy_key in migrated and new_key not in migrated:
            migrated[new_key] = migrated[legacy_key]

    data.update({key: value for key, value in migrated.items() if value is not None})
    data = _normalize_goal_mode_fields(data, defaults)
    data["targets"] = _normalize_targets(migrated.get("targets"), data, defaults)
    data["enabled"] = bool(data["enabled"])
    data["vocabFocus"] = bool(data["vocabFocus"])
    data["version"] = 1
    return data
