from __future__ import annotations

from typing import Any

from shared.pedagogy.modes import guidance_for_mode, sections_for_mode


def _box_title_for_mode(mode: str, detected_language: str | None = None) -> str:
    if detected_language is not None:
        if mode == "ielts-writing":
            return f"📚 {detected_language} · IELTS Writing"
        return f"📚 {detected_language} Coaching"
    if mode == "ielts-writing":
        return "📚 IELTS Writing Coaching"
    if mode == "ielts-speaking":
        return "📚 IELTS Speaking Coaching"
    if mode == "review":
        return "📚 Review Session"
    return "📚 Language Coaching"


def _box_instruction(mode: str, detected_language: str | None = None) -> list[str]:
    title = _box_title_for_mode(mode, detected_language)
    opening_line = (
        f"Substitute the detected language name into the box title and use '╭─ {title} ─' as the opening line."
        if detected_language is not None
        else f"Use '╭─ {title} ─' as the opening line."
    )
    return [
        "Box framing for the coaching feedback:",
        f"- {opening_line}",
        "- Prefix every coaching line with '│ '.",
        "- Close with '╰─────────────────────────────────────' before giving the actual answer.",
    ]


def _response_instruction(config: dict[str, Any]) -> str:
    native = config["nativeLanguage"]
    if _target_profiles(config) and config["responseLanguage"] == "target":
        return "After coaching, answer the actual request in the matched target language."
    target = config["targetLanguage"]
    response_language = target if config["responseLanguage"] == "target" else native
    return f"After coaching, answer the actual request in {response_language}."


def _target_profiles(config: dict[str, Any]) -> list[dict[str, Any]]:
    targets = config.get("targets")
    if not isinstance(targets, list):
        return []
    return [target for target in targets if isinstance(target, dict) and target.get("targetLanguage")]


def _target_summary(
    target: dict[str, Any], *, detected_language: str | None = None
) -> list[str]:
    lines = [
        (
            f"- {target['targetLanguage']}: goal={target['goal']}, "
            f"mode={target['mode']}, style={target['style']}."
        )
    ]
    if target.get("targetBand"):
        lines.append(f"  Target band: {target['targetBand']}.")
    if target.get("currentLevel"):
        lines.append(f"  Current level: {target['currentLevel']}.")
    if target.get("responseLanguage"):
        lines.append(f"  Response language: {target['responseLanguage']}.")
    lines.append("  Coaching guidance:")
    lines.extend(f"  - {line}" for line in guidance_for_mode(target["mode"]))
    lines.append("  Feedback sections:")
    lines.extend(f"  - {section}" for section in sections_for_mode(target["mode"]))
    lines.append("  Box framing:")
    lines.extend(
        f"  - {line}"
        for line in _box_instruction(target["mode"], detected_language)
    )
    return lines


def build_prompt(config: dict[str, Any]) -> str:
    targets = _target_profiles(config)
    if targets:
        base = [
            (
                "Language coaching preference "
                f"(native: {config['nativeLanguage']} -> auto-detect target language)."
            ),
            "Target language profiles:",
        ]
        for target in targets:
            base.extend(_target_summary(target, detected_language="{DetectedLanguage}"))
        base.extend(
            [
                (
                    "Detect which target language the user is currently writing in "
                    "based on the message content."
                ),
                (
                    "Apply the coaching config for that detected language before coaching."
                ),
                (
                    "If the user's language is ambiguous or does not match a configured "
                    f"target, fall back to the legacy single-target settings for {config['targetLanguage']}."
                ),
                "Legacy single-target box framing:",
                *_box_instruction(config["mode"]),
            ]
        )
    else:
        mode = config["mode"]
        base = [
            (
                "Language coaching preference "
                f"(native: {config['nativeLanguage']} -> target: {config['targetLanguage']})."
            ),
            f"Goal: {config['goal']}.",
            f"Style: {config['style']}.",
        ]

        if config["goal"] == "ielts":
            if config.get("targetBand"):
                base.append(f"Target band: {config['targetBand']}.")
            if config.get("currentLevel"):
                base.append(f"Current level: {config['currentLevel']}.")

        guidance_text = "\n".join(f"- {line}" for line in guidance_for_mode(mode))
        section_text = "\n".join(f"- {section}" for section in sections_for_mode(mode))
        base.extend(
            [
                "Coaching guidance:",
                guidance_text,
                "Feedback sections to include before the actual answer:",
                section_text,
                *_box_instruction(mode),
            ]
        )

    return "\n".join(
        base
        + [
            f"Deliver all coaching feedback in {config['nativeLanguage']}.",
            _response_instruction(config),
        ]
    )
