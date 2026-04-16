from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLED_PLUGIN_ROOT = REPO_ROOT / "plugins" / "prompt-language-coach"


def resolve_source_bundle_root() -> Path:
    if (BUNDLED_PLUGIN_ROOT / ".codex-plugin" / "plugin.json").exists():
        return BUNDLED_PLUGIN_ROOT
    return REPO_ROOT


def install_codex_plugin(*, home: Path | None = None) -> Path:
    source_root = resolve_source_bundle_root()
    target_home = home or Path.home()
    target_root = target_home / ".codex" / "plugins" / "prompt-language-coach"
    target_root.parent.mkdir(parents=True, exist_ok=True)
    if target_root.exists():
        shutil.rmtree(target_root)
    shutil.copytree(source_root, target_root)
    return target_root


def main() -> int:
    target_root = install_codex_plugin()
    print(f"Installed Codex plugin: {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
