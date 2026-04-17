import tempfile
import unittest
from pathlib import Path

from shared.codex.agents_md import (
    END_MARKER,
    START_MARKER,
    remove_block,
    upsert_block,
)


class CodexAgentsMdTests(unittest.TestCase):
    def test_creates_file_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "AGENTS.md"
            changed = upsert_block("hello world", path=path)
            self.assertTrue(changed)
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
            self.assertIn(START_MARKER, text)
            self.assertIn(END_MARKER, text)
            self.assertIn("hello world", text)

    def test_appends_without_touching_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            original = "# User note\n\nkeep me intact\n"
            path.write_text(original, encoding="utf-8")

            upsert_block("coaching block", path=path)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(original))
            self.assertIn("coaching block", text)

    def test_replaces_existing_block_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            existing = (
                "# Keep\n"
                f"{START_MARKER}\nold coach\n{END_MARKER}\n"
                "\n# Also keep\nstay\n"
            )
            path.write_text(existing, encoding="utf-8")

            upsert_block("new coach", path=path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("# Keep", text)
            self.assertIn("# Also keep", text)
            self.assertIn("stay", text)
            self.assertNotIn("old coach", text)
            self.assertIn("new coach", text)

    def test_second_upsert_is_noop_when_content_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            self.assertTrue(upsert_block("same", path=path))
            mtime = path.stat().st_mtime_ns
            self.assertFalse(upsert_block("same", path=path))
            self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_backup_created_only_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("user content\n", encoding="utf-8")

            upsert_block("v1", path=path)
            upsert_block("v2", path=path)

            backups = list(path.parent.glob(f"{path.name}.backup-prompt-language-coach.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "user content\n")

    def test_remove_keeps_surrounding_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text(
                f"# Before\nkeep\n\n{START_MARKER}\nblock\n{END_MARKER}\n\n# After\nkeep\n",
                encoding="utf-8",
            )
            self.assertTrue(remove_block(path=path))
            text = path.read_text(encoding="utf-8")
            self.assertIn("# Before", text)
            self.assertIn("# After", text)
            self.assertNotIn("block", text)
            self.assertNotIn(START_MARKER, text)

    def test_remove_deletes_file_when_only_block_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text(
                f"{START_MARKER}\nonly block\n{END_MARKER}\n",
                encoding="utf-8",
            )
            self.assertTrue(remove_block(path=path))
            self.assertFalse(path.exists())

    def test_remove_is_noop_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            self.assertFalse(remove_block(path=path))

    def test_remove_is_noop_without_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("unrelated\n", encoding="utf-8")
            self.assertFalse(remove_block(path=path))
            self.assertEqual(path.read_text(encoding="utf-8"), "unrelated\n")


if __name__ == "__main__":
    unittest.main()
