from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.config.schema import normalize_config

DEFAULTS_PATH = Path(__file__).with_name("defaults.json")


def load_defaults() -> dict[str, Any]:
    return json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))


def load_config(path: Path) -> dict[str, Any]:
    defaults = load_defaults()
    if not path.exists():
        return dict(defaults)

    raw = json.loads(path.read_text(encoding="utf-8"))
    return normalize_config(raw, defaults)


def save_config(path: Path, config: dict[str, Any]) -> None:
    defaults = load_defaults()
    normalized = normalize_config(config, defaults)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
