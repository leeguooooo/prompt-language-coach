from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.codex.agents_md import remove_block, upsert_block
from shared.config.io import load_config
from shared.prompts.build_prompt import (
    build_progress_note,
    build_prompt,
    build_static_prompt,
)
from scripts.manage_language_coach import (
    ensure_progress_snapshot,
    ensure_vocab_snapshot,
    resolve_effective_config_path,
    resolve_progress_path,
    resolve_vocab_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices={"claude", "codex", "cursor"}, required=True)
    parser.add_argument("--config")
    return parser.parse_args()


def _emit(platform: str, context_text: str) -> None:
    if platform == "cursor":
        payload = {"additional_context": context_text}
    else:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context_text,
            }
        }
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser() if args.config else None
    if config_path is None or not config_path.exists():
        effective_path = resolve_effective_config_path(args.platform)
        if effective_path is None:
            if args.platform == "codex":
                remove_block()
            return 0
        config_path = effective_path

    config = load_config(config_path)
    if not config["enabled"]:
        if args.platform == "codex":
            remove_block()
        return 0

    ensure_progress_snapshot(args.platform)
    progress_file = resolve_progress_path(args.platform)
    ensure_vocab_snapshot(args.platform)
    vocab_file = resolve_vocab_path(args.platform)

    if args.platform == "codex":
        static_text = build_static_prompt(
            config,
            repo_root=str(REPO_ROOT),
            vocab_path=str(vocab_file),
        )
        upsert_block(static_text)
        note = build_progress_note(str(progress_file))
        _emit(args.platform, note)
        return 0

    coaching_text = build_prompt(
        config,
        repo_root=str(REPO_ROOT),
        progress_path=str(progress_file),
        vocab_path=str(vocab_file),
    )
    _emit(args.platform, coaching_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
