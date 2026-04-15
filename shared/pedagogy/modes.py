from __future__ import annotations

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
    if mode == "ielts-writing":
        return IELTS_WRITING_SECTIONS
    if mode == "ielts-speaking":
        return IELTS_SPEAKING_SECTIONS
    if mode == "review":
        return REVIEW_SECTIONS
    return EVERYDAY_SECTIONS


def guidance_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "ielts-writing":
        return (
            "Optimize feedback for IELTS writing improvement rather than grammar-only correction.",
            "Prefer rough band ranges over false precision.",
        )
    if mode == "ielts-speaking":
        return (
            "Optimize feedback for spoken naturalness, fluency, and lexical resource.",
            "Do not claim to score pronunciation from text alone.",
        )
    if mode == "review":
        return ("Summarize patterns across recent interactions.",)
    return (
        "Keep coaching compact and low-interruption.",
        "When the user writes fully in the native language, provide one concise natural target-language version first.",
    )
