import json
import unittest
from pathlib import Path

from shared.prompts.build_prompt import build_prompt


FIXTURES = Path("tests/fixtures")


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
                "goal": "ielts",
                "mode": "ielts-speaking",
                "style": "concise",
                "targetBand": "7.0",
            },
        ]

        prompt = build_prompt(config)

        self.assertIn("Target language profiles:", prompt)
        self.assertIn("Detect which target language the user wrote in", prompt)
        self.assertIn("English", prompt)
        self.assertIn("Japanese", prompt)
        self.assertIn("Deliver all coaching feedback in Chinese.", prompt)

    def test_everyday_prompt_stays_compact(self) -> None:
        config = json.loads(
            (FIXTURES / "config_everyday.json").read_text(encoding="utf-8")
        )
        prompt = build_prompt(config)

        self.assertIn("Your original", prompt)
        self.assertIn("Corrected", prompt)
        self.assertIn("More natural", prompt)
        self.assertIn("1 key takeaway", prompt)
        self.assertNotIn("Band estimate", prompt)
        self.assertIn("Deliver all coaching feedback in Chinese.", prompt)
        self.assertNotIn("Detect which target language the user wrote in", prompt)

    def test_ielts_writing_prompt_includes_exam_feedback(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        prompt = build_prompt(config)

        self.assertIn("Band estimate", prompt)
        self.assertIn("Reusable pattern", prompt)
        self.assertIn("Mini drill", prompt)

    def test_ielts_speaking_prompt_avoids_fake_pronunciation_scoring(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["mode"] = "ielts-speaking"
        prompt = build_prompt(config)

        self.assertIn("Do not claim to score pronunciation from text alone", prompt)


if __name__ == "__main__":
    unittest.main()
