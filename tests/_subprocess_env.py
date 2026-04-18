"""Cross-platform helpers for building subprocess env dicts in tests.

Windows `Path.home()` reads `USERPROFILE` (not `HOME`), so a bare `HOME`-only
env dict causes `RuntimeError: Could not determine home directory.` on the
Windows CI runner. On top of that, Windows python needs a handful of system
env vars (`SYSTEMROOT`, `PATH`, etc.) just to start. Inheriting `os.environ`
and overriding the home-related keys is the cheapest way to stay hermetic
while keeping both OSes happy.
"""
from __future__ import annotations

import os
from pathlib import Path


def env_for_home(home: Path | str) -> dict[str, str]:
    """Return a subprocess env dict that points every home-path var at `home`.

    Inherits the parent `os.environ` (needed for Windows startup DLLs / PATH)
    and overrides `HOME`, `USERPROFILE`, `HOMEDRIVE`, and `HOMEPATH` so
    `Path.home()` resolves to the test sandbox on both POSIX and Windows.
    """
    env = os.environ.copy()
    home_str = str(home)
    env["HOME"] = home_str
    env["USERPROFILE"] = home_str
    if os.name == "nt" and len(home_str) >= 2 and home_str[1] == ":":
        env["HOMEDRIVE"] = home_str[:2]
        env["HOMEPATH"] = home_str[2:] or "\\"
    else:
        env.pop("HOMEDRIVE", None)
        env.pop("HOMEPATH", None)
    return env
