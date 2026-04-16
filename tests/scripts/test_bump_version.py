import json
import tempfile
import unittest
from pathlib import Path

from scripts.bump_version import _bump_json_field, _bump_marketplace


class BumpVersionTests(unittest.TestCase):
    def test_bump_json_field_updates_codex_plugin_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "plugin.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "prompt-language-coach",
                        "version": "0.8.0",
                    }
                ),
                encoding="utf-8",
            )

            changed = _bump_json_field(manifest, "0.9.0")

            self.assertTrue(changed)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "0.9.0")

    def test_bump_marketplace_updates_language_coach_entry_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            marketplace = Path(tmp) / "marketplace.json"
            marketplace.write_text(
                json.dumps(
                    {
                        "plugins": [
                            {"name": "language-coach", "version": "0.8.0"},
                            {"name": "other-plugin", "version": "1.0.0"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            changed = _bump_marketplace(marketplace, "language-coach", "0.9.0")

            self.assertTrue(changed)
            payload = json.loads(marketplace.read_text(encoding="utf-8"))
            versions = {entry["name"]: entry["version"] for entry in payload["plugins"]}
            self.assertEqual(versions["language-coach"], "0.9.0")
            self.assertEqual(versions["other-plugin"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
