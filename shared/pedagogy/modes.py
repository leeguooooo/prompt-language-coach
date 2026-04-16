from __future__ import annotations

from shared.config.schema import canonicalize_mode

MIXED_LANGUAGE_GUIDANCE = (
    "If the user mixes native-language words or phrases into their "
    "target-language message (because they cannot express the full meaning "
    "in the target language), provide one complete natural target-language "
    "version of the entire message — covering both what was written in the "
    "target language and what was written in the native language. Then "
    "explain what the native-language portions should have been in the "
    "target language."
)

MIXED_LANGUAGE_SCORING_GUIDANCE = (
    "If the user falls back to native-language words or phrases to complete "
    "key meaning, treat that as evidence that the target language alone was "
    "not enough for the task."
)

EVERYDAY_SECTIONS = (
    "Your original",
    "Corrected",
    "More natural",
    "1 key takeaway",
)

IELTS_WRITING_SECTIONS = (
    "Band estimate",
    "What is working",
    "What lowers the score",
    "Rewritten higher-band version",
    "Reusable pattern",
    "Mini drill",
)

IELTS_SPEAKING_SECTIONS = (
    "Fluency and coherence",
    "Lexical resource",
    "Grammatical range and accuracy",
    "Natural spoken alternative",
    "Reusable pattern",
    "Mini drill",
)

REVIEW_SECTIONS = (
    "Review summary",
    "Recurring mistakes",
    "Reusable pattern",
    "Next drill",
)


def sections_for_mode(mode: str) -> tuple[str, ...]:
    normalized = canonicalize_mode(mode, default="everyday")
    if normalized == "scored-writing":
        return IELTS_WRITING_SECTIONS
    if normalized == "scored-speaking":
        return IELTS_SPEAKING_SECTIONS
    if normalized == "review":
        return REVIEW_SECTIONS
    return EVERYDAY_SECTIONS


def guidance_for_mode(mode: str) -> tuple[str, ...]:
    normalized = canonicalize_mode(mode, default="everyday")
    if normalized == "scored-writing":
        return (
            "Optimize feedback for score-oriented writing improvement rather than grammar-only correction.",
            "Prefer rough band ranges over false precision.",
            MIXED_LANGUAGE_GUIDANCE,
            MIXED_LANGUAGE_SCORING_GUIDANCE,
        )
    if normalized == "scored-speaking":
        return (
            "Optimize feedback for spoken naturalness, fluency, and lexical resource.",
            "Do not claim to score pronunciation from text alone.",
            MIXED_LANGUAGE_GUIDANCE,
        )
    if normalized == "review":
        return ("Summarize patterns across recent interactions.",)
    return (
        "Keep coaching compact and low-interruption.",
        "When the user writes fully in the native language, provide one concise natural target-language version first.",
        MIXED_LANGUAGE_GUIDANCE,
    )
