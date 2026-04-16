from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProficiencyScale:
    key: str
    display_name: str
    estimate_label: str
    unit_label: str
    record_examples: tuple[str, ...]
    guidance_lines: tuple[str, ...]


IELTS = ProficiencyScale(
    key="ielts",
    display_name="IELTS",
    estimate_label="Estimate",
    unit_label="band",
    record_examples=("5.0", "5.5", "6.0"),
    guidance_lines=(
        "Estimate using IELTS bands in 0.5 increments.",
        "Prefer a rough range when the evidence is thin.",
        "Do not start above 5.5 on a first scored sample unless the writing clearly shows sustained band-6+ control.",
    ),
)

JLPT = ProficiencyScale(
    key="jlpt",
    display_name="JLPT",
    estimate_label="Estimate",
    unit_label="level",
    record_examples=("N5", "N4", "N3"),
    guidance_lines=(
        "Estimate using JLPT levels (N5, N4, N3, N2, N1).",
        "Default to N5 on a first scored sample unless the message clearly sustains N4 or above.",
        "Do not jump to N3 or above from one short prompt.",
    ),
)

CEFR = ProficiencyScale(
    key="cefr",
    display_name="CEFR",
    estimate_label="Estimate",
    unit_label="level",
    record_examples=("A1", "A2", "B1"),
    guidance_lines=(
        "Estimate using CEFR levels (A1, A2, B1, B2, C1, C2).",
        "Stay conservative on a first scored sample unless there is clear evidence for a higher level.",
    ),
)

SCALES = {
    IELTS.key: IELTS,
    JLPT.key: JLPT,
    CEFR.key: CEFR,
}

_LANGUAGE_SCALE_MAP = {
    "english": IELTS.key,
    "en": IELTS.key,
    "japanese": JLPT.key,
    "ja": JLPT.key,
    "nihongo": JLPT.key,
    "日本語": JLPT.key,
}

_JLPT_ORDER = {"N5": 1.0, "N4": 2.0, "N3": 3.0, "N2": 4.0, "N1": 5.0}
_CEFR_ORDER = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}


def scale_by_name(name: str | None) -> ProficiencyScale:
    if not name:
        return CEFR
    return SCALES.get(name.casefold(), CEFR)


def scale_for_language(language: str | None, explicit_scale: str | None = None) -> ProficiencyScale:
    if explicit_scale:
        return scale_by_name(explicit_scale)
    if not language:
        return CEFR
    normalized = language.strip().casefold()
    return scale_by_name(_LANGUAGE_SCALE_MAP.get(normalized))


def normalize_estimate(raw: str | None, *, scale: ProficiencyScale) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None

    if scale.key == IELTS.key:
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return None

    normalized = value.upper()
    if scale.key == JLPT.key:
        return normalized if normalized in _JLPT_ORDER else None
    if scale.key == CEFR.key:
        return normalized if normalized in _CEFR_ORDER else None
    return value


def estimate_sort_value(raw: str | None, *, scale: ProficiencyScale) -> float | None:
    normalized = normalize_estimate(raw, scale=scale)
    if normalized is None:
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    if scale.key == IELTS.key:
        return float(normalized)
    if scale.key == JLPT.key:
        return _JLPT_ORDER.get(normalized)
    if scale.key == CEFR.key:
        return _CEFR_ORDER.get(normalized)
    try:
        return float(normalized)
    except (TypeError, ValueError):
        return None
