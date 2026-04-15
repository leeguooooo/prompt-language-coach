from __future__ import annotations

from typing import Any

from shared.pedagogy.modes import guidance_for_mode, sections_for_mode


def _response_instruction(config: dict[str, Any]) -> str:
    target = config["targetLanguage"]
    native = config["nativeLanguage"]
    response_language = target if config["responseLanguage"] == "target" else native
    return f"After coaching, answer the actual request in {response_language}."


def build_prompt(config: dict[str, Any]) -> str:
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

    return "\n".join(
        base
        + [
            "Coaching guidance:",
            guidance_text,
            "Feedback sections to include before the actual answer:",
            section_text,
            _response_instruction(config),
        ]
    )
