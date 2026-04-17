"""Marker-bounded management of ~/.codex/AGENTS.md for prompt-language-coach.

Codex loads ~/.codex/AGENTS.md on every turn as ambient user instructions that
are hidden from the TUI transcript but visible to the model. Using the same
marker-bounded convention as other Codex-aware tools (e.g. oh-my-codex's
``<!-- OMX:RUNTIME:START --> ... <!-- OMX:RUNTIME:END -->``), we upsert our
coaching block without touching anything outside our markers.
"""

from __future__ import annotations

import datetime as _datetime
import os
import tempfile
from pathlib import Path


START_MARKER = "<!-- prompt-language-coach:start -->"
END_MARKER = "<!-- prompt-language-coach:end -->"


def default_agents_md_path() -> Path:
    return Path.home() / ".codex" / "AGENTS.md"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _backup_once(path: Path) -> None:
    """Create a single timestamped backup the first time we touch the file."""
    if not path.exists():
        return
    existing_backups = list(path.parent.glob(f"{path.name}.backup-prompt-language-coach.*"))
    if existing_backups:
        return
    timestamp = _datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.parent / f"{path.name}.backup-prompt-language-coach.{timestamp}"
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def _compose_block(content: str) -> str:
    body = content.strip("\n")
    return f"{START_MARKER}\n{body}\n{END_MARKER}" if body else f"{START_MARKER}\n{END_MARKER}"


def _find_block(text: str) -> tuple[int, int] | None:
    start = text.find(START_MARKER)
    if start == -1:
        return None
    end = text.find(END_MARKER, start + len(START_MARKER))
    if end == -1:
        return None
    return start, end + len(END_MARKER)


def upsert_block(content: str, *, path: Path | None = None) -> bool:
    """Insert or replace our marker block. Returns True if the file changed."""
    target_path = path or default_agents_md_path()
    new_block = _compose_block(content)

    if not target_path.exists():
        _atomic_write(target_path, new_block + "\n")
        return True

    existing_text = target_path.read_text(encoding="utf-8")
    span = _find_block(existing_text)

    if span is not None:
        start, end = span
        new_text = existing_text[:start] + new_block + existing_text[end:]
    else:
        separator = "" if existing_text.endswith("\n") else "\n"
        if existing_text.strip():
            separator += "\n"
        new_text = existing_text + separator + new_block + "\n"

    if new_text == existing_text:
        return False

    _backup_once(target_path)
    _atomic_write(target_path, new_text)
    return True


def remove_block(*, path: Path | None = None) -> bool:
    """Remove our marker block. Returns True if the file changed."""
    target_path = path or default_agents_md_path()
    if not target_path.exists():
        return False

    existing_text = target_path.read_text(encoding="utf-8")
    span = _find_block(existing_text)
    if span is None:
        return False

    start, end = span
    before = existing_text[:start].rstrip("\n")
    after = existing_text[end:].lstrip("\n")
    joiner = "\n\n" if before and after else ""
    new_text = (before + joiner + after).rstrip("\n")

    _backup_once(target_path)

    if not new_text.strip():
        try:
            target_path.unlink()
        except OSError:
            _atomic_write(target_path, "")
        return True

    _atomic_write(target_path, new_text + "\n")
    return True
