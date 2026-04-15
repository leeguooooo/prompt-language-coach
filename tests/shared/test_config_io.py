import json
import tempfile
import unittest
from pathlib import Path

from shared.config.io import load_config, save_config


class ConfigIOTests(unittest.TestCase):
    def test_load_config_accepts_multi_target_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "everyday",
                        "mode": "everyday",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                        "targets": [
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
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(len(config["targets"]), 2)
        self.assertEqual(config["targets"][0]["targetLanguage"], "English")
        self.assertEqual(config["targets"][1]["targetLanguage"], "Japanese")
        self.assertEqual(config["targets"][1]["mode"], "ielts-speaking")
        self.assertEqual(config["targets"][1]["goal"], "ielts")
        self.assertEqual(config["targets"][1]["responseLanguage"], "native")

    def test_load_config_normalizes_legacy_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            path.write_text(
                json.dumps(
                    {
                        "native": "Chinese",
                        "target": "English",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config["nativeLanguage"], "Chinese")
        self.assertEqual(config["targetLanguage"], "English")
        self.assertEqual(config["goal"], "everyday")
        self.assertEqual(config["mode"], "everyday")
        self.assertEqual(config["responseLanguage"], "native")
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["targets"], [])

    def test_load_config_normalizes_ielts_mode_back_to_ielts_goal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "everyday",
                        "mode": "ielts-speaking",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config["goal"], "ielts")
        self.assertEqual(config["mode"], "ielts-speaking")

    def test_save_config_persists_normalized_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            save_config(
                path,
                {
                    "nativeLanguage": "Japanese",
                    "targetLanguage": "English",
                    "goal": "ielts",
                    "mode": "ielts-writing",
                    "style": "concise",
                    "responseLanguage": "target",
                    "enabled": True,
                    "ieltsFocus": "writing",
                    "targetBand": "7.0",
                    "currentLevel": "",
                    "version": 1,
                },
            )

            raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(raw["nativeLanguage"], "Japanese")
        self.assertEqual(raw["mode"], "ielts-writing")
        self.assertEqual(raw["version"], 1)


if __name__ == "__main__":
    unittest.main()
