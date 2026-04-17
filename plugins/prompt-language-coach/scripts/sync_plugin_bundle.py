"""Mirror the repo-root source tree into plugins/prompt-language-coach/.

The Codex marketplace manifest points at ``plugins/prompt-language-coach``
as a self-contained install source. That bundle must carry the exact same
scripts / shared / platforms / skills as the root, or marketplace users
will install stale code even after a version bump.

Run this script (or let ``bump_version.py`` run it) before every release.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_ROOT = REPO_ROOT / "plugins" / "prompt-language-coach"

# Directories that must be byte-identical between root and bundle.
MIRRORED_DIRS: tuple[str, ...] = (
    "scripts",
    "shared",
    "platforms",
    "skills",
)

# Top-level files that must be mirrored too.
MIRRORED_FILES: tuple[str, ...] = ()


def _rmtree_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def sync() -> list[Path]:
    if not BUNDLE_ROOT.exists():
        raise SystemExit(f"bundle root missing: {BUNDLE_ROOT}")

    touched: list[Path] = []
    for name in MIRRORED_DIRS:
        src = REPO_ROOT / name
        dst = BUNDLE_ROOT / name
        if not src.exists():
            continue
        _rmtree_if_exists(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        touched.append(dst)

    for name in MIRRORED_FILES:
        src = REPO_ROOT / name
        dst = BUNDLE_ROOT / name
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        touched.append(dst)

    return touched


def main() -> int:
    touched = sync()
    if not touched:
        print("Nothing to sync.")
        return 0
    for path in touched:
        rel = path.relative_to(REPO_ROOT)
        print(f"synced: {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
