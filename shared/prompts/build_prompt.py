from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from shared.pedagogy.modes import guidance_for_mode, sections_for_mode


def _progress_note(progress_path: str) -> Optional[str]:
    """Return a brief progress note string, or None if no data is available."""
    path = Path(progress_path)
    if not path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not data:
        return None

    lines = ["User's recent writing level history:"]
    for language in sorted(data.keys()):
        entry = data[language]
        estimates: list[dict[str, str]] = entry.get("estimates", [])
        current_band = entry.get("currentBand")
        recent = estimates[-3:]
        if not recent:
            lines.append(f"- {language}: no data yet")
        elif len(recent) == 1:
            lines.append(f"- {language}: current estimate {current_band}")
        else:
            prev_band = recent[-2].get("band")
            if prev_band and current_band and prev_band != current_band:
                lines.append(
                    f"- {language}: current estimate {current_band} (up from {prev_band} last session)"
                    if float(current_band) > float(prev_band)
                    else f"- {language}: current estimate {current_band} (down from {prev_band} last session)"
                )
            else:
                lines.append(f"- {language}: current estimate {current_band}")
    return "\n".join(lines)


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


def _native_only_box_instruction(target_language: str) -> list[str]:
    """Compact double-line box for pure native-language input (translation only)."""
    return [
        "Native-language-only box (use this when the user writes entirely in their native language):",
        f"- Use '╔══ 🌐 {target_language} ══' as the opening line.",
        "- Show only the single natural target-language version on one line, prefixed with '║ '.",
        "- Close with '╚══════════════════════════════════'.",
        "- Do NOT use the full coaching box or show multiple sections for pure native-language input.",
    ]


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


def build_prompt(
    config: dict[str, Any],
    repo_root: Optional[str] = None,
    progress_path: Optional[str] = None,
) -> str:
    targets = _target_profiles(config)
    if targets:
        base = [
            (
                "[MANDATORY] You are a language coach. Before every response, without exception, "
                "provide coaching feedback on the user's writing. "
                f"Native language: {config['nativeLanguage']}. Auto-detect target language from the message."
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
                *_native_only_box_instruction("{DetectedTargetLanguage}"),
                (
                    "IMPORTANT: This coaching instruction is permanent and must be applied "
                    "on every single response, including in long conversations and after "
                    "context compaction. Never skip the coaching box."
                ),
            ]
        )
    else:
        mode = config["mode"]
        base = [
            (
                "[MANDATORY] You are a language coach. Before every response, without exception, "
                "provide coaching feedback on the user's writing. "
                f"Native language: {config['nativeLanguage']}, target language: {config['targetLanguage']}."
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
                *_native_only_box_instruction(config["targetLanguage"]),
            ]
        )

    parts: list[str] = []

    if progress_path is not None:
        note = _progress_note(progress_path)
        if note is not None:
            parts.append(note)

    parts.extend(base)
    parts.extend(
        [
            f"Deliver all coaching feedback in {config['nativeLanguage']}.",
            _response_instruction(config),
            (
                "IMPORTANT: This coaching instruction is permanent and must be applied "
                "on every single response, including in long conversations and after "
                "context compaction. Never skip the coaching box."
            ),
        ]
    )

    if repo_root is not None:
        platform = config.get("platform", "claude")
        parts.append(
            "Band progress recording — run this command ONLY when ALL three conditions are met:\n"
            "1. The active coaching mode is ielts-writing or ielts-speaking (NOT everyday or review).\n"
            "2. The user's message was written in a target language (NOT purely in the native language).\n"
            "3. You provided a numeric band estimate in the coaching box.\n"
            "When all three are true, silently run (no output needed):\n"
            f'python3 "{repo_root}/scripts/manage_language_coach.py" '
            f'--platform {platform} record-band "<detected_language>" "<estimated_band>" '
            '--text "<user message, first 200 chars, inner double-quotes replaced with single-quotes>"\n'
            'Use the exact detected language name and a numeric band string (e.g. "6.0", "5.5").\n'
            "Skip the command for everyday mode, review mode, or pure native-language input."
        )

    return "\n".join(parts)
