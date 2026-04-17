import filecmp
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import sync_plugin_bundle


class SyncPluginBundleTests(unittest.TestCase):
    def test_sync_copies_all_mirrored_dirs_into_bundle(self) -> None:
        touched = sync_plugin_bundle.sync()
        for name in sync_plugin_bundle.MIRRORED_DIRS:
            bundle_dir = sync_plugin_bundle.BUNDLE_ROOT / name
            self.assertIn(bundle_dir, touched)
            self.assertTrue(bundle_dir.is_dir())

    def test_sync_makes_bundle_byte_identical_for_key_files(self) -> None:
        sync_plugin_bundle.sync()
        for rel in (
            "scripts/manage_language_coach.py",
            "scripts/render_coaching_context.py",
            "shared/codex/agents_md.py",
            "platforms/cursor/install_hooks.py",
            "skills/language-coach/SKILL.md",
        ):
            root_file = sync_plugin_bundle.REPO_ROOT / rel
            bundle_file = sync_plugin_bundle.BUNDLE_ROOT / rel
            self.assertTrue(bundle_file.exists(), f"bundle missing {rel}")
            self.assertTrue(
                filecmp.cmp(root_file, bundle_file, shallow=False),
                f"{rel} differs between root and bundle",
            )

    def test_sync_excludes_pycache_noise(self) -> None:
        sync_plugin_bundle.sync()
        bundle_root = sync_plugin_bundle.BUNDLE_ROOT
        self.assertFalse(list(bundle_root.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
