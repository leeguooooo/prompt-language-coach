import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"


class CodexMarketplaceTests(unittest.TestCase):
    def test_repo_marketplace_manifest_exists(self):
        self.assertTrue(MARKETPLACE_PATH.exists(), MARKETPLACE_PATH)

    def test_repo_marketplace_points_to_repo_root_plugin(self):
        marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
        manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(marketplace["name"], "prompt-language-coach")
        self.assertEqual(marketplace["interface"]["displayName"], "Prompt Language Coach")
        self.assertEqual(len(marketplace["plugins"]), 1)

        plugin = marketplace["plugins"][0]
        self.assertEqual(plugin["name"], manifest["name"])
        self.assertEqual(plugin["source"]["source"], "local")
        self.assertEqual(plugin["source"]["path"], "./")
        self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
        self.assertEqual(plugin["category"], "Education")


if __name__ == "__main__":
    unittest.main()
