import tempfile
import unittest
from pathlib import Path

from scripts.install_codex_plugin import install_codex_plugin, resolve_source_bundle_root


class InstallCodexPluginTests(unittest.TestCase):
    def test_install_copies_plugin_bundle_and_installs_skill_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            legacy_lang_dir = home / ".codex" / "skills" / "lang"
            legacy_lang_dir.mkdir(parents=True, exist_ok=True)
            (legacy_lang_dir / "SKILL.md").write_text("legacy alias\n", encoding="utf-8")
            target_root = install_codex_plugin(home=home)

            self.assertEqual(
                target_root,
                home / ".codex" / "plugins" / "prompt-language-coach",
            )
            self.assertTrue((target_root / ".codex-plugin" / "plugin.json").exists())
            self.assertTrue((target_root / "skills" / "language-coach" / "SKILL.md").exists())
            wrapper_root = home / ".codex" / "skills"
            self.assertTrue((wrapper_root / "language-coach" / "SKILL.md").exists())
            self.assertTrue((wrapper_root / "language-review" / "SKILL.md").exists())
            self.assertFalse((wrapper_root / "lang" / "SKILL.md").exists())
            coach_text = (wrapper_root / "language-coach" / "SKILL.md").read_text(encoding="utf-8")
            review_text = (wrapper_root / "language-review" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(str(target_root / "scripts" / "manage_language_coach.py"), coach_text)
            self.assertNotIn("../../scripts/manage_language_coach.py", coach_text)
            self.assertIn(str(target_root / "scripts" / "analyze_progress.py"), review_text)
            self.assertNotIn("../../scripts/analyze_progress.py", review_text)

    def test_repo_root_prefers_self_contained_bundle_source(self) -> None:
        source_root = resolve_source_bundle_root()
        self.assertTrue((source_root / ".codex-plugin" / "plugin.json").exists())
        self.assertEqual(source_root.name, "prompt-language-coach")


if __name__ == "__main__":
    unittest.main()
