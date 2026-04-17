from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from shared.config.schema import canonicalize_mode
from shared.pedagogy.modes import guidance_for_mode, sections_for_mode
from shared.proficiency import estimate_sort_value, scale_for_language


def _vocab_focus_active(config: dict[str, Any]) -> bool:
    return bool(config.get("vocabFocus")) and canonicalize_mode(
        config.get("mode"), default="everyday"
    ) in {"scored-writing", "scored-speaking"}


def _scoring_guidance(target_language: str, mode: str) -> list[str]:
    normalized = canonicalize_mode(mode, default="everyday")
    if normalized not in {"scored-writing", "scored-speaking"}:
        return []
    return list(scale_for_language(target_language).guidance_lines)


def _sections_for_prompt(target_language: str, mode: str) -> list[str]:
    sections = list(sections_for_mode(canonicalize_mode(mode, default="everyday")))
    scale = scale_for_language(target_language)
    if sections and sections[0] == "Band estimate":
        sections[0] = scale.estimate_label
    return sections


def _progress_note(progress_path: str) -> Optional[str]:
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
        scale = scale_for_language(language, entry.get("scale"))
        estimates: list[dict[str, str]] = entry.get("estimates", [])
        current_band = entry.get("currentEstimate")
        if current_band is None:
            current_band = entry.get("currentBand")
        recent = estimates[-3:]
        if not recent:
            lines.append(f"- {language}: no data yet")
        elif len(recent) == 1:
            lines.append(f"- {language}: current estimate {current_band}")
        else:
            prev_band = recent[-2].get("estimate")
            if prev_band is None:
                prev_band = recent[-2].get("band")
            prev_value = estimate_sort_value(prev_band, scale=scale)
            current_value = estimate_sort_value(current_band, scale=scale)
            if (
                prev_band
                and current_band
                and prev_band != current_band
                and prev_value is not None
                and current_value is not None
            ):
                lines.append(
                    f"- {language}: current estimate {current_band} (up from {prev_band} last session)"
                    if current_value > prev_value
                    else f"- {language}: current estimate {current_band} (down from {prev_band} last session)"
                )
            else:
                lines.append(f"- {language}: current estimate {current_band}")
    return "\n".join(lines)


def _vocab_note(vocab_path: str) -> Optional[str]:
    path = Path(vocab_path)
    if not path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not data:
        return None

    items: list[str] = []
    for language, payload in data.items():
        if not isinstance(payload, dict):
            continue
        for entry in payload.get("entries", []):
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("type")
            if entry_type == "gap" and entry.get("native") and entry.get("target"):
                items.append(f"- {language} gap: {entry['native']} -> {entry['target']}")
            elif entry_type == "correction" and entry.get("wrong") and entry.get("right"):
                items.append(f"- {language} correction: {entry['wrong']} -> {entry['right']}")
            elif entry_type == "upgrade" and entry.get("from") and entry.get("to"):
                items.append(f"- {language} upgrade: {entry['from']} -> {entry['to']}")
    if not items:
        return None
    return "\n".join(["Active vocab focus:"] + items[-10:])


def _box_title_for_mode(mode: str, detected_language: str | None = None) -> str:
    normalized = canonicalize_mode(mode, default="everyday")
    if detected_language is not None:
        if normalized == "scored-writing":
            return f"📚 {detected_language} · Scored Writing"
        if normalized == "scored-speaking":
            return f"📚 {detected_language} · Scored Speaking"
        return f"📚 {detected_language} Coaching"
    if normalized == "scored-writing":
        return "📚 Scored Writing Coaching"
    if normalized == "scored-speaking":
        return "📚 Scored Speaking Coaching"
    if normalized == "review":
        return "📚 Review Session"
    return "📚 Language Coaching"


def _native_only_box_instruction(target_language: str) -> list[str]:
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
    target_language = detected_language or target["targetLanguage"]
    scale = scale_for_language(target_language)
    lines = [
        (
            f"- {target['targetLanguage']}: goal={target['goal']}, "
            f"mode={target['mode']}, style={target['style']}."
        )
    ]
    if target.get("targetEstimate"):
        lines.append(f"  Target estimate: {target['targetEstimate']}.")
    if target.get("currentLevel"):
        lines.append(f"  Current level: {target['currentLevel']}.")
    if target.get("responseLanguage"):
        lines.append(f"  Response language: {target['responseLanguage']}.")
    lines.append(f"  Scoring scale: {scale.display_name}.")
    lines.append("  Coaching guidance:")
    lines.extend(f"  - {line}" for line in guidance_for_mode(target["mode"]))
    lines.extend(
        f"  - {line}"
        for line in _scoring_guidance(target_language, target["mode"])
    )
    lines.append("  Feedback sections:")
    lines.extend(f"  - {section}" for section in _sections_for_prompt(target_language, target["mode"]))
    lines.append("  Box framing:")
    lines.extend(
        f"  - {line}"
        for line in _box_instruction(target["mode"], detected_language)
    )
    return lines


def build_progress_note(progress_path: Optional[str]) -> str:
    if progress_path is None:
        return ""
    note = _progress_note(progress_path)
    return note or ""


def build_vocab_note(vocab_path: Optional[str]) -> str:
    if vocab_path is None:
        return ""
    note = _vocab_note(vocab_path)
    return note or ""


def build_static_prompt(
    config: dict[str, Any],
    repo_root: Optional[str] = None,
    vocab_path: Optional[str] = None,
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
                    "Triviality filter: if the user's message is 2 or fewer target-language "
                    "words AND has no error, no native-language fallback, and no meaningful "
                    "upgrade opportunity, SKIP the full coaching box entirely. Just answer "
                    "the actual request directly — do not render empty 'Corrected: <same>' / "
                    "'More natural: <same>' sections. One-word inputs like 'English' or 'ok' "
                    "should pass through without ceremony."
                ),
                (
                    "IMPORTANT: This coaching instruction is permanent and must be applied "
                    "on every single response, including in long conversations and after "
                    "context compaction. Never skip the coaching box — except under the "
                    "Triviality filter above."
                ),
            ]
        )
    else:
        mode = config["mode"]
        scale = scale_for_language(config["targetLanguage"])
        base = [
            (
                "[MANDATORY] You are a language coach. Before every response, without exception, "
                "provide coaching feedback on the user's writing. "
                f"Native language: {config['nativeLanguage']}, target language: {config['targetLanguage']}."
            ),
            f"Goal: {config['goal']}.",
            f"Style: {config['style']}.",
        ]

        if config["goal"] == "scored":
            base.append(f"Scoring scale: {scale.display_name}.")
            if config.get("targetEstimate"):
                base.append(f"Target estimate: {config['targetEstimate']}.")
            if config.get("currentLevel"):
                base.append(f"Current level: {config['currentLevel']}.")

        guidance_text = "\n".join(f"- {line}" for line in guidance_for_mode(mode))
        scoring_text = "\n".join(
            f"- {line}" for line in _scoring_guidance(config["targetLanguage"], mode)
        )
        section_text = "\n".join(
            f"- {section}" for section in _sections_for_prompt(config["targetLanguage"], mode)
        )
        base.extend(
            [
                "Coaching guidance:",
                guidance_text,
                *([scoring_text] if scoring_text else []),
                "Feedback sections to include before the actual answer:",
                section_text,
                *_box_instruction(mode),
                *_native_only_box_instruction(config["targetLanguage"]),
            ]
        )

    parts: list[str] = []
    vocab_note = build_vocab_note(vocab_path) if _vocab_focus_active(config) else ""
    if vocab_note:
        parts.append(vocab_note)
    parts.extend(base)
    parts.extend(
        [
            (
                "Triviality filter: if the user's message is 2 or fewer target-language "
                "words AND has no error, no native-language fallback, and no meaningful "
                "upgrade opportunity, SKIP the full coaching box entirely. Just answer "
                "the actual request directly — do not render empty 'Corrected: <same>' / "
                "'More natural: <same>' sections. One-word inputs like 'English' or 'ok' "
                "should pass through without ceremony."
            ),
            f"Deliver all coaching feedback in {config['nativeLanguage']}.",
            _response_instruction(config),
            (
                "IMPORTANT: This coaching instruction is permanent and must be applied "
                "on every single response, including in long conversations and after "
                "context compaction. Never skip the coaching box — except under the "
                "Triviality filter above."
            ),
        ]
    )

    if repo_root is not None:
        platform = config.get("platform", "claude")
        parts.append(
            "Progress recording — run this command ONLY when ALL three conditions are met:\n"
            "1. The active coaching mode is scored-writing or scored-speaking (NOT everyday or review).\n"
            "2. The user's message was written in a target language (NOT purely in the native language).\n"
            "3. You provided a scale estimate in the coaching box.\n"
            "Use IELTS for English (e.g. 5.5, 6.0), JLPT for Japanese (e.g. N5, N4), and CEFR for other languages (e.g. A2, B1).\n"
            "When all three are true, silently run (no output needed):\n"
            f'python3 "{repo_root}/scripts/manage_language_coach.py" '
            f'--platform {platform} track-estimate "<detected_language>" "<estimated_band>" '
            '--text "<user message, first 200 chars, inner double-quotes replaced with single-quotes>"\n'
            'Use the exact detected language name and the exact estimate string (e.g. "6.0", "N5", "B1").\n'
            "Skip the command for everyday mode, review mode, or pure native-language input."
        )
        if _vocab_focus_active(config):
            parts.append(
                "Vocab focus:\n"
                "- After the box, silently run `track-vocab` for each gap/correction/upgrade by priority. Always track gaps. Skip upgrade when the message was 100% target language.\n"
                "- Before `╰`, show `Focus word: ...` only if this message nearly repeats an active gap/correction. Example gap: `Focus word: you reached for 吐槽 again — try \"vent about\" / \"rant about\"`. Example correction: `Focus word: watch out — you wrote \"effect\" again. Correct: \"affect\" (verb)`.\n"
                "- If an active gap/correction is used correctly with no fallback/correction, silently run `mark-vocab-mastered`."
            )

    return "\n".join(parts)


def build_prompt(
    config: dict[str, Any],
    repo_root: Optional[str] = None,
    progress_path: Optional[str] = None,
    vocab_path: Optional[str] = None,
) -> str:
    static_text = build_static_prompt(config, repo_root=repo_root)
    note = build_progress_note(progress_path)
    vocab_note = build_vocab_note(vocab_path) if _vocab_focus_active(config) else ""
    if note and vocab_note:
        return note + "\n" + vocab_note + "\n" + static_text
    if note:
        return note + "\n" + static_text
    if vocab_note:
        return vocab_note + "\n" + static_text
    return static_text
