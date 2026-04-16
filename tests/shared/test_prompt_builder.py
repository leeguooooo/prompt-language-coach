import json
import unittest
from pathlib import Path

from shared.prompts.build_prompt import build_prompt


FIXTURES = Path("tests/fixtures")
MIXED_LANGUAGE_GUIDANCE = (
    "If the user mixes native-language words or phrases into their "
    "target-language message (because they cannot express the full meaning "
    "in the target language), provide one complete natural target-language "
    "version of the entire message — covering both what was written in the "
    "target language and what was written in the native language. Then "
    "explain what the native-language portions should have been in the "
    "target language."
)


class PromptBuilderTests(unittest.TestCase):
    def test_multi_target_prompt_includes_auto_detection_instructions(self) -> None:
        config = json.loads(
            (FIXTURES / "config_everyday.json").read_text(encoding="utf-8")
        )
        config["targets"] = [
            {
                "targetLanguage": "English",
                "goal": "everyday",
                "mode": "everyday",
                "style": "teaching",
            },
            {
                "targetLanguage": "Japanese",
                "goal": "scored",
                "mode": "ielts-speaking",
                "style": "concise",
                "targetEstimate": "N3",
            },
        ]

        prompt = build_prompt(config)

        self.assertIn("Target language profiles:", prompt)
        self.assertIn(
            "Detect which target language the user is currently writing in based on the message content.",
            prompt,
        )
        self.assertIn(
            "Apply the coaching config for that detected language before coaching.",
            prompt,
        )
        self.assertIn(
            "Substitute the detected language name into the box title and use '╭─ 📚 {DetectedLanguage} Coaching ─' as the opening line.",
            prompt,
        )
        self.assertIn("English", prompt)
        self.assertIn("Japanese", prompt)
        self.assertIn("╭─ 📚 {DetectedLanguage} Coaching ─", prompt)
        self.assertIn("│ ", prompt)
        self.assertIn("╰", prompt)
        self.assertIn("Deliver all coaching feedback in Chinese.", prompt)

    def test_multi_target_ielts_writing_prompt_uses_detected_language_in_title(self) -> None:
        config = json.loads(
            (FIXTURES / "config_everyday.json").read_text(encoding="utf-8")
        )
        config["targets"] = [
            {
                "targetLanguage": "English",
                "goal": "scored",
                "mode": "scored-writing",
                "style": "teaching",
                "targetEstimate": "7.5",
            },
            {
                "targetLanguage": "Japanese",
                "goal": "everyday",
                "mode": "everyday",
                "style": "concise",
            },
        ]

        prompt = build_prompt(config)

        self.assertIn(
            "Substitute the detected language name into the box title and use '╭─ 📚 {DetectedLanguage} · Scored Writing ─' as the opening line.",
            prompt,
        )
        self.assertIn("English", prompt)
        self.assertIn("Japanese", prompt)
        self.assertIn("Target estimate: 7.5.", prompt)

    def test_everyday_prompt_stays_compact(self) -> None:
        config = json.loads(
            (FIXTURES / "config_everyday.json").read_text(encoding="utf-8")
        )
        prompt = build_prompt(config)

        self.assertIn("Your original", prompt)
        self.assertIn("Corrected", prompt)
        self.assertIn("More natural", prompt)
        self.assertIn("1 key takeaway", prompt)
        self.assertIn("╭─ 📚 Language Coaching ─", prompt)
        self.assertIn("│ ", prompt)
        self.assertIn("╰─────────────────────────────────────", prompt)
        self.assertNotIn("Band estimate", prompt)
        self.assertIn(MIXED_LANGUAGE_GUIDANCE, prompt)
        self.assertIn("Deliver all coaching feedback in Chinese.", prompt)
        self.assertNotIn("Detect which target language the user wrote in", prompt)

    def test_ielts_writing_prompt_includes_exam_feedback(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        prompt = build_prompt(config, repo_root="/tmp/repo")

        self.assertIn("Band estimate", prompt)
        self.assertIn("Target estimate: 7.0.", prompt)
        self.assertIn("Reusable pattern", prompt)
        self.assertIn("Mini drill", prompt)
        self.assertIn(MIXED_LANGUAGE_GUIDANCE, prompt)
        self.assertIn("╭─ 📚 Scored Writing Coaching ─", prompt)
        self.assertIn("Do not start above 5.5 on a first scored sample", prompt)
        self.assertIn("track-estimate", prompt)

    def test_ielts_speaking_prompt_avoids_fake_pronunciation_scoring(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["mode"] = "scored-speaking"
        prompt = build_prompt(config)

        self.assertIn("Do not claim to score pronunciation from text alone", prompt)
        self.assertIn(MIXED_LANGUAGE_GUIDANCE, prompt)
        self.assertIn("╭─ 📚 Scored Speaking Coaching ─", prompt)

    def test_japanese_prompt_switches_scoring_scale_to_jlpt(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["targetLanguage"] = "Japanese"
        config["currentLevel"] = "N5"
        config["targetEstimate"] = "N3"

        prompt = build_prompt(config)

        self.assertIn("Estimate using JLPT levels (N5, N4, N3, N2, N1)", prompt)
        self.assertIn("Target estimate: N3.", prompt)
        self.assertIn("Default to N5 on a first scored sample", prompt)


if __name__ == "__main__":
    unittest.main()
