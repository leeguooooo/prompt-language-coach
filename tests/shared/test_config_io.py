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
                                "goal": "scored",
                                "mode": "ielts-speaking",
                                "style": "concise",
                                "targetEstimate": "N3",
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
        self.assertEqual(config["targets"][1]["mode"], "scored-speaking")
        self.assertEqual(config["targets"][1]["goal"], "scored")
        self.assertEqual(config["targets"][1]["targetEstimate"], "N3")
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

    def test_load_config_normalizes_legacy_ielts_shape_to_scored_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "ielts",
                        "mode": "ielts-speaking",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                        "ieltsFocus": "speaking",
                        "targetBand": "6.5",
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config["goal"], "scored")
        self.assertEqual(config["mode"], "scored-speaking")
        self.assertEqual(config["scoringFocus"], "speaking")
        self.assertEqual(config["targetEstimate"], "6.5")

    def test_save_config_persists_normalized_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            save_config(
                path,
                {
                    "nativeLanguage": "Japanese",
                    "targetLanguage": "English",
                    "goal": "scored",
                    "mode": "scored-writing",
                    "style": "concise",
                    "responseLanguage": "target",
                    "enabled": True,
                    "scoringFocus": "writing",
                    "targetEstimate": "7.0",
                    "currentLevel": "",
                    "version": 1,
                },
            )

            raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(raw["nativeLanguage"], "Japanese")
        self.assertEqual(raw["goal"], "scored")
        self.assertEqual(raw["mode"], "scored-writing")
        self.assertEqual(raw["scoringFocus"], "writing")
        self.assertEqual(raw["targetEstimate"], "7.0")
        self.assertNotIn("ieltsFocus", raw)
        self.assertNotIn("targetBand", raw)
        self.assertEqual(raw["version"], 1)


if __name__ == "__main__":
    unittest.main()
