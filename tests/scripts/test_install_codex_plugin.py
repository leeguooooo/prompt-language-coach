import tempfile
import unittest
from pathlib import Path

from scripts.install_codex_plugin import install_codex_plugin, resolve_source_bundle_root


class InstallCodexPluginTests(unittest.TestCase):
    def test_install_copies_plugin_bundle_to_active_codex_plugins_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target_root = install_codex_plugin(home=home)

            self.assertEqual(
                target_root,
                home / ".codex" / "plugins" / "prompt-language-coach",
            )
            self.assertTrue((target_root / ".codex-plugin" / "plugin.json").exists())
            self.assertTrue((target_root / "skills" / "language-coach" / "SKILL.md").exists())
            self.assertTrue((target_root / "skills" / "lang" / "SKILL.md").exists())

    def test_repo_root_prefers_self_contained_bundle_source(self) -> None:
        source_root = resolve_source_bundle_root()
        self.assertTrue((source_root / ".codex-plugin" / "plugin.json").exists())
        self.assertEqual(source_root.name, "prompt-language-coach")


if __name__ == "__main__":
    unittest.main()
