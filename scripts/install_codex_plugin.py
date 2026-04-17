from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    install_skill_wrappers(target_root=target_root, home=target_home)
    _seed_codex_agents_md(target_home=target_home)
    return target_root


def _seed_codex_agents_md(*, target_home: Path) -> None:
    """Seed ~/.codex/AGENTS.md so the first Codex turn already has coaching.

    Silently skipped if no config exists yet — setup commands write it later.
    """
    from shared.codex.agents_md import upsert_block
    from shared.config.io import load_config
    from shared.prompts.build_prompt import build_static_prompt
    from scripts.manage_language_coach import resolve_effective_config_path

    original_home = Path.home()
    if target_home == original_home:
        config_path = resolve_effective_config_path("codex")
    else:
        candidates = [
            target_home / ".codex" / "language-coach.json",
            target_home / ".prompt-language-coach" / "language-coach.json",
            target_home / ".claude" / "language-coach.json",
            target_home / ".cursor" / "language-coach.json",
        ]
        config_path = next((p for p in candidates if p.exists()), None)

    if config_path is None:
        return

    config = load_config(config_path)
    if not config.get("enabled", True):
        return

    static_text = build_static_prompt(config, repo_root=str(REPO_ROOT))
    agents_md_path = target_home / ".codex" / "AGENTS.md"
    upsert_block(static_text, path=agents_md_path)


def install_skill_wrappers(*, target_root: Path, home: Path) -> None:
    source_skills_root = target_root / "skills"
    user_skills_root = home / ".codex" / "skills"
    user_skills_root.mkdir(parents=True, exist_ok=True)
    stale_alias_dir = user_skills_root / "lang"
    if stale_alias_dir.exists():
        shutil.rmtree(stale_alias_dir)

    for skill_dir in source_skills_root.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        target_skill_dir = user_skills_root / skill_dir.name
        if target_skill_dir.exists():
            shutil.rmtree(target_skill_dir)
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        content = skill_md.read_text(encoding="utf-8")
        content = content.replace(
            "../../scripts/manage_language_coach.py",
            str(target_root / "scripts" / "manage_language_coach.py"),
        )
        content = content.replace(
            "../../scripts/analyze_progress.py",
            str(target_root / "scripts" / "analyze_progress.py"),
        )
        (target_skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def main() -> int:
    target_root = install_codex_plugin()
    print(f"Installed Codex plugin: {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
