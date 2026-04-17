import json
import tempfile
import unittest
from pathlib import Path

from shared.prompts.build_prompt import build_prompt, build_static_prompt, build_vocab_note


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
        self.assertNotIn("JLPT estimate", prompt)
        self.assertIn(MIXED_LANGUAGE_GUIDANCE, prompt)
        self.assertIn("Deliver all coaching feedback in Chinese.", prompt)
        self.assertNotIn("Detect which target language the user wrote in", prompt)

    def test_ielts_writing_prompt_includes_exam_feedback(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        prompt = build_prompt(config, repo_root="/tmp/repo")

        self.assertIn("- Estimate", prompt)
        self.assertIn("Scoring scale: IELTS.", prompt)
        self.assertIn("Target estimate: 7.0.", prompt)
        self.assertIn("Reusable pattern", prompt)
        self.assertIn("Mini drill", prompt)
        self.assertIn(MIXED_LANGUAGE_GUIDANCE, prompt)
        self.assertIn("╭─ 📚 Scored Writing Coaching ─", prompt)
        self.assertIn("Do not start above 5.5 on a first scored sample", prompt)
        self.assertIn("track-estimate", prompt)

    def test_vocab_focus_prompt_rules_render_only_when_flag_enabled(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["vocabFocus"] = True

        prompt = build_static_prompt(config, repo_root="/tmp/repo")

        self.assertIn("Vocab focus:", prompt)
        self.assertIn("track-vocab", prompt)
        self.assertIn('Focus word: you reached for 吐槽 again', prompt)
        self.assertIn("mark-vocab-mastered", prompt)
        self.assertIn("Skip upgrade when the message was 100% target language.", prompt)

        config["vocabFocus"] = False
        prompt = build_static_prompt(config, repo_root="/tmp/repo")
        self.assertNotIn("Vocab focus:", prompt)
        self.assertNotIn("track-vocab", prompt)
        self.assertNotIn("mark-vocab-mastered", prompt)

    def test_vocab_focus_requires_scored_mode(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["vocabFocus"] = True
        config["mode"] = "everyday"
        config["goal"] = "everyday"

        prompt = build_static_prompt(config, repo_root="/tmp/repo")

        self.assertNotIn("Vocab focus:", prompt)
        self.assertNotIn("track-vocab", prompt)
        self.assertNotIn("mark-vocab-mastered", prompt)

    def test_build_vocab_note_lists_recent_active_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vocab_path = Path(tmp) / "vocab-focus.json"
            vocab_path.write_text(
                json.dumps(
                    {
                        "English": {
                            "entries": [
                                {
                                    "date": "2026-04-17",
                                    "type": "gap",
                                    "native": "吐槽",
                                    "target": "vent about",
                                    "context": "I want to 吐槽 this bug",
                                    "note": "vent = express frustration",
                                    "masteredHits": 0,
                                },
                                {
                                    "date": "2026-04-17",
                                    "type": "correction",
                                    "wrong": "effect",
                                    "right": "affect",
                                    "context": "the bug effects perf",
                                    "note": "affect = verb",
                                    "masteredHits": 0,
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            note = build_vocab_note(str(vocab_path))

        self.assertIn("Active vocab focus:", note)
        self.assertIn("English gap: 吐槽 -> vent about", note)
        self.assertIn("English correction: effect -> affect", note)

    def test_vocab_note_is_only_included_when_feature_is_active(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as tmp:
            vocab_path = Path(tmp) / "vocab-focus.json"
            vocab_path.write_text(
                json.dumps(
                    {
                        "English": {
                            "entries": [
                                {
                                    "date": "2026-04-17",
                                    "type": "gap",
                                    "native": "吐槽",
                                    "target": "vent about",
                                    "masteredHits": 0,
                                }
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config["vocabFocus"] = False
            prompt = build_prompt(config, vocab_path=str(vocab_path))
            self.assertNotIn("Active vocab focus:", prompt)

            config["vocabFocus"] = True
            config["mode"] = "everyday"
            config["goal"] = "everyday"
            prompt = build_prompt(config, vocab_path=str(vocab_path))
            self.assertNotIn("Active vocab focus:", prompt)

            config["mode"] = "scored-writing"
            config["goal"] = "scored"
            prompt = build_prompt(config, vocab_path=str(vocab_path))
            self.assertIn("Active vocab focus:", prompt)

    def test_ielts_writing_prompt_penalizes_native_language_fallback(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )

        prompt = build_prompt(config)

        self.assertIn(
            "If the user falls back to native-language words or phrases to complete key meaning, treat that as evidence that the target language alone was not enough for the task.",
            prompt,
        )
        self.assertIn(
            "If the sample is short, fragmented, or depends on native-language fallback to complete core meaning, keep the estimate at 4.5 or below unless there is strong contrary evidence elsewhere in the message.",
            prompt,
        )

    def test_ielts_speaking_prompt_avoids_fake_pronunciation_scoring(self) -> None:
        config = json.loads(
            (FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8")
        )
        config["mode"] = "scored-speaking"
        prompt = build_prompt(config)

        self.assertIn("Do not claim to score pronunciation from text alone", prompt)
        self.assertIn("Scoring scale: IELTS.", prompt)
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
        self.assertIn("Scoring scale: JLPT.", prompt)
        self.assertIn("Target estimate: N3.", prompt)
        self.assertIn("Default to N5 on a first scored sample", prompt)


if __name__ == "__main__":
    unittest.main()
