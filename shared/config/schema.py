from __future__ import annotations

from typing import Any

ALLOWED_GOALS = {"everyday", "ielts"}
ALLOWED_MODES = {"everyday", "ielts-writing", "ielts-speaking", "review"}
ALLOWED_STYLES = {"teaching", "concise", "translate"}
ALLOWED_RESPONSE_LANGUAGES = {"native", "target"}
ALLOWED_IELTS_FOCUS = {"writing", "speaking", "both"}
IELTS_MODES = {"ielts-writing", "ielts-speaking"}

LEGACY_KEY_MAP = {
    "native": "nativeLanguage",
    "target": "targetLanguage",
}

TARGET_OVERRIDE_KEYS = (
    "targetLanguage",
    "goal",
    "mode",
    "style",
    "responseLanguage",
    "ieltsFocus",
    "targetBand",
    "currentLevel",
)


def _normalize_goal_mode_fields(
    data: dict[str, Any], defaults: dict[str, Any]
) -> dict[str, Any]:
    if data["goal"] not in ALLOWED_GOALS:
        data["goal"] = defaults["goal"]
    if data["mode"] not in ALLOWED_MODES:
        data["mode"] = defaults["mode"]
    if data["style"] not in ALLOWED_STYLES:
        data["style"] = defaults["style"]
    if data["responseLanguage"] not in ALLOWED_RESPONSE_LANGUAGES:
        data["responseLanguage"] = defaults["responseLanguage"]
    if data["ieltsFocus"] not in ALLOWED_IELTS_FOCUS:
        data["ieltsFocus"] = defaults["ieltsFocus"]

    if data["mode"] in IELTS_MODES:
        data["goal"] = "ielts"

    if data["goal"] == "ielts" and data["mode"] == "everyday":
        data["mode"] = "ielts-writing"

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
    data["version"] = 1
    return data
