import tempfile
import unittest
from pathlib import Path

from scripts.build_changelog import categorize_commits, render_release_section, update_changelog


class BuildChangelogTests(unittest.TestCase):
    def test_categorize_commits_groups_by_prefix(self):
        categorized = categorize_commits(
            [
                "feat: add codex install docs",
                "fix: keep hook install idempotent",
                "docs: rewrite README top section",
                "misc cleanup",
            ]
        )

        self.assertEqual(categorized["Features"], ["feat: add codex install docs"])
        self.assertEqual(categorized["Fixes"], ["fix: keep hook install idempotent"])
        self.assertEqual(categorized["Docs"], ["docs: rewrite README top section"])
        self.assertEqual(categorized["Other"], ["misc cleanup"])

    def test_render_release_section_includes_version_and_sections(self):
        section = render_release_section(
            "0.9.0",
            "2026-04-16",
            [
                "feat: add codex hook commands",
                "docs: add codex install docs",
            ],
        )

        self.assertIn("## v0.9.0 - 2026-04-16", section)
        self.assertIn("### Features", section)
        self.assertIn("- feat: add codex hook commands", section)
        self.assertIn("### Docs", section)

    def test_update_changelog_appends_release_to_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            changelog = Path(tmp) / "CHANGELOG.md"
            changelog.write_text(
                "# Changelog\n\nAll notable changes to this project are recorded here.\n\n## v0.8.0 - 2026-04-15\n",
                encoding="utf-8",
            )

            update_changelog(changelog, "## v0.9.0 - 2026-04-16\n\n### Features\n- feat: add codex hook commands\n")

            content = changelog.read_text(encoding="utf-8")
            self.assertIn("## v0.8.0 - 2026-04-15", content)
            self.assertIn("## v0.9.0 - 2026-04-16", content)


if __name__ == "__main__":
    unittest.main()
