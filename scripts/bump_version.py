#!/usr/bin/env python3
"""Bump the version across all plugin manifests in one shot.

Usage:
    python3 scripts/bump_version.py 0.8.0

Files updated (in this repo):
    .claude-plugin/plugin.json
    .cursor-plugin/plugin.json
    .codex-plugin/plugin.json

Files updated (in the sibling plugins repo, if present):
    ../plugins/.claude-plugin/marketplace.json  — language-coach entry only

Release model:
    - Git tags and GitHub releases are the canonical release record
    - Codex, Claude Code, and Cursor all read their shipped version from plugin.json
    - Claude marketplace sync is an extra downstream step, not the source of truth
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_REPO = REPO_ROOT.parent / "plugins"

# Files inside this repo that carry a top-level "version" field
OWN_MANIFESTS = [
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
    REPO_ROOT / ".codex-plugin"  / "plugin.json",
]

# Marketplace file in the sibling plugins repo
MARKETPLACE = PLUGINS_REPO / ".claude-plugin" / "marketplace.json"
PLUGIN_NAME  = "language-coach"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT.parent))
    except ValueError:
        return str(path)


def _bump_json_field(path: Path, new_version: str) -> bool:
    """Set top-level 'version' in a JSON file. Returns True if changed."""
    if not path.exists():
        print(f"  skip (not found): {path}")
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    old = data.get("version", "<none>")
    if old == new_version:
        print(f"  already {new_version}: {_display_path(path)}")
        return False
    data["version"] = new_version
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {old} → {new_version}: {_display_path(path)}")
    return True


def _bump_marketplace(path: Path, plugin_name: str, new_version: str) -> bool:
    """Set 'version' for a named plugin entry in a marketplace JSON."""
    if not path.exists():
        print(f"  skip (not found): {path}")
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for entry in data.get("plugins", []):
        if entry.get("name") == plugin_name:
            old = entry.get("version", "<none>")
            if old != new_version:
                entry["version"] = new_version
                changed = True
                print(f"  {old} → {new_version}: {_display_path(path)} [{plugin_name}]")
            else:
                print(f"  already {new_version}: {_display_path(path)} [{plugin_name}]")
    if changed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <new-version>   e.g. 0.8.0")
        return 1

    new_version = sys.argv[1].strip()
    print(f"Bumping to {new_version} …\n")

    any_changed = False
    for manifest in OWN_MANIFESTS:
        any_changed |= _bump_json_field(manifest, new_version)

    any_changed |= _bump_marketplace(MARKETPLACE, PLUGIN_NAME, new_version)

    if not any_changed:
        print("\nNothing to change.")
    else:
        print(f"\nDone. Commit both repos and push:")
        print(f"  cd {REPO_ROOT} && git add -p && git commit -m 'Bump version to {new_version}'")
        print(f"  cd {PLUGINS_REPO} && git add -p && git commit -m 'Bump language-coach to {new_version}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
