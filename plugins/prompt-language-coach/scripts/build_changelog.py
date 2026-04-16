#!/usr/bin/env python3
"""Build or update CHANGELOG.md from git history.

Usage:
    python3 scripts/build_changelog.py 0.9.0
"""
from __future__ import annotations

import subprocess
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
DEFAULT_SECTIONS = OrderedDict(
    [
        ("Features", ("feat:",)),
        ("Fixes", ("fix:",)),
        ("Docs", ("docs:",)),
        ("Refactors", ("refactor:",)),
        ("Tests", ("test:",)),
        ("CI", ("ci:",)),
        ("Chores", ("chore:",)),
    ]
)


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        tag = _run_git("describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commits_since(ref: str | None) -> list[str]:
    args = ["log", "--pretty=format:%s"]
    if ref:
        args.insert(1, f"{ref}..HEAD")
    output = _run_git(*args)
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def categorize_commits(commits: list[str]) -> OrderedDict[str, list[str]]:
    buckets: OrderedDict[str, list[str]] = OrderedDict((name, []) for name in DEFAULT_SECTIONS)
    buckets["Other"] = []
    for subject in commits:
        lowered = subject.casefold()
        matched = False
        for section, prefixes in DEFAULT_SECTIONS.items():
            if any(lowered.startswith(prefix) for prefix in prefixes):
                buckets[section].append(subject)
                matched = True
                break
        if not matched:
            buckets["Other"].append(subject)
    return buckets


def render_release_section(version: str, release_date: str, commits: list[str]) -> str:
    lines = [f"## v{version} - {release_date}", ""]
    if not commits:
        lines.append("- No user-facing changes recorded.")
        lines.append("")
        return "\n".join(lines)

    categorized = categorize_commits(commits)
    for section, entries in categorized.items():
        if not entries:
            continue
        lines.append(f"### {section}")
        lines.extend(f"- {entry}" for entry in entries)
        lines.append("")
    return "\n".join(lines)


def update_changelog(path: Path, release_section: str) -> None:
    header = "# Changelog\n\nAll notable changes to this project are recorded here.\n\n"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current.startswith("# Changelog"):
            path.write_text(current.rstrip() + "\n\n" + release_section.rstrip() + "\n", encoding="utf-8")
            return
    path.write_text(header + release_section.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <new-version>   e.g. 0.9.0")
        return 1

    version = sys.argv[1].strip()
    previous_tag = latest_tag()
    commits = commits_since(previous_tag)
    section = render_release_section(version, date.today().isoformat(), commits)
    update_changelog(CHANGELOG_PATH, section)
    print(f"Updated {CHANGELOG_PATH} from {'initial history' if previous_tag is None else previous_tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
