# Dual-Platform Language Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shared IELTS-aware language coaching core that powers both the existing Claude integration and a new Codex plugin plus hook flow without duplicating pedagogy.

**Architecture:** Move coaching logic into a dependency-free Python shared core, keep thin platform adapters for Claude and Codex, and route both hook entrypoints through one prompt builder. Claude continues to use hook injection; Codex adds a native plugin manifest plus user hook installer so automatic coaching works in normal Codex sessions.

**Tech Stack:** Bash, Python 3 standard library, Claude plugin files, Codex plugin manifest, Markdown skills, unittest.

---

## File Structure Map

### Shared core

- Create: `shared/config/__init__.py`
- Create: `shared/config/defaults.json`
- Create: `shared/config/schema.py`
- Create: `shared/config/io.py`
- Create: `shared/pedagogy/__init__.py`
- Create: `shared/pedagogy/modes.py`
- Create: `shared/prompts/__init__.py`
- Create: `shared/prompts/build_prompt.py`

Responsibilities:

- `shared/config/*` normalizes and validates config across platforms
- `shared/pedagogy/*` defines lightweight and IELTS-mode feedback rules
- `shared/prompts/build_prompt.py` converts normalized config into hook-ready instruction text

### Runtime entrypoints

- Create: `scripts/render_coaching_context.py`
- Create: `scripts/manage_language_coach.py`
- Modify: `hooks/language-coach.sh`

Responsibilities:

- `render_coaching_context.py` loads config, builds prompt text, and emits the correct hook JSON
- `manage_language_coach.py` handles config reads, writes, and Codex hook install tasks
- `hooks/language-coach.sh` remains the Claude hook shim and delegates to the shared Python path

### Codex adapter

- Create: `.codex-plugin/plugin.json`
- Create: `platforms/codex/hook_entry.py`
- Create: `platforms/codex/install_hooks.py`
- Create: `platforms/codex/templates/hooks.json`

Responsibilities:

- `.codex-plugin/plugin.json` exposes the plugin to Codex
- `hook_entry.py` is the Codex `UserPromptSubmit` hook target
- `install_hooks.py` writes or removes a language-coach entry in `~/.codex/hooks.json`
- `templates/hooks.json` provides the expected serialized hook shape for tests and installer output

### User-facing instructions and docs

- Modify: `skills/language-coach/SKILL.md`
- Modify: `README.md`

Responsibilities:

- `skills/language-coach/SKILL.md` becomes platform-aware and calls the shared management CLI
- `README.md` documents Claude, Cursor, and Codex install and usage flows

### Tests

- Create: `tests/shared/test_config_io.py`
- Create: `tests/shared/test_prompt_builder.py`
- Create: `tests/hooks/test_claude_hook_output.py`
- Create: `tests/hooks/test_codex_hook_install.py`
- Create: `tests/scripts/test_manage_language_coach.py`
- Create: `tests/fixtures/config_everyday.json`
- Create: `tests/fixtures/config_ielts_writing.json`

Responsibilities:

- config tests cover normalization and legacy compatibility
- prompt tests cover mode-specific output shape
- hook tests cover JSON payload format for Claude and Codex
- CLI tests cover setup-oriented writes and Codex hook install behavior

---

### Task 1: Build the shared config layer

**Files:**
- Create: `shared/config/__init__.py`
- Create: `shared/config/defaults.json`
- Create: `shared/config/schema.py`
- Create: `shared/config/io.py`
- Create: `tests/shared/test_config_io.py`
- Create: `tests/fixtures/config_everyday.json`

- [ ] **Step 1: Write the failing config normalization test**

```python
# tests/shared/test_config_io.py
import json
import tempfile
import unittest
from pathlib import Path

from shared.config.io import load_config, save_config


class ConfigIOTests(unittest.TestCase):
    def test_load_config_normalizes_legacy_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            path.write_text(
                json.dumps(
                    {
                        "native": "Chinese",
                        "target": "English",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config["nativeLanguage"], "Chinese")
        self.assertEqual(config["targetLanguage"], "English")
        self.assertEqual(config["goal"], "everyday")
        self.assertEqual(config["mode"], "everyday")
        self.assertEqual(config["responseLanguage"], "native")
        self.assertEqual(config["version"], 1)

    def test_save_config_persists_normalized_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "language-coach.json"
            save_config(
                path,
                {
                    "nativeLanguage": "Japanese",
                    "targetLanguage": "English",
                    "goal": "ielts",
                    "mode": "ielts-writing",
                    "style": "concise",
                    "responseLanguage": "target",
                    "enabled": True,
                    "ieltsFocus": "writing",
                    "targetBand": "7.0",
                    "currentLevel": "",
                    "version": 1,
                },
            )

            raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(raw["nativeLanguage"], "Japanese")
        self.assertEqual(raw["mode"], "ielts-writing")
        self.assertEqual(raw["version"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the config test to verify it fails**

Run:

```bash
python3 -m unittest tests.shared.test_config_io -v
```

Expected: `ModuleNotFoundError` for `shared.config.io`

- [ ] **Step 3: Add defaults and schema validation**

```json
// shared/config/defaults.json
{
  "nativeLanguage": "Chinese",
  "targetLanguage": "English",
  "goal": "everyday",
  "mode": "everyday",
  "style": "teaching",
  "responseLanguage": "native",
  "enabled": true,
  "ieltsFocus": "both",
  "targetBand": "",
  "currentLevel": "",
  "version": 1
}
```

```python
# shared/config/schema.py
from __future__ import annotations

ALLOWED_GOALS = {"everyday", "ielts"}
ALLOWED_MODES = {"everyday", "ielts-writing", "ielts-speaking", "review"}
ALLOWED_STYLES = {"teaching", "concise", "translate"}
ALLOWED_RESPONSE_LANGUAGES = {"native", "target"}
ALLOWED_IELTS_FOCUS = {"writing", "speaking", "both"}

LEGACY_KEY_MAP = {
    "native": "nativeLanguage",
    "target": "targetLanguage",
}


def normalize_config(raw: dict, defaults: dict) -> dict:
    data = dict(defaults)
    migrated = dict(raw)
    for legacy_key, new_key in LEGACY_KEY_MAP.items():
        if legacy_key in migrated and new_key not in migrated:
            migrated[new_key] = migrated[legacy_key]

    data.update({k: v for k, v in migrated.items() if v is not None})

    if data["goal"] not in ALLOWED_GOALS:
        data["goal"] = defaults["goal"]
    if data["mode"] not in ALLOWED_MODES:
        data["mode"] = defaults["mode"]
    if data["style"] not in ALLOWED_STYLES:
        data["style"] = defaults["style"]
    if data["responseLanguage"] not in ALLOWED_RESPONSE_LANGUAGES:
        data["responseLanguage"] = defaults["responseLanguage"]
    if data["ieltsFocus"] not in ALLOWED_IELTS_FOCUS:
        data["ieltsFocus"] = defaults["ieltsFocus"]

    if data["goal"] == "ielts" and data["mode"] == "everyday":
        data["mode"] = "ielts-writing"

    data["enabled"] = bool(data["enabled"])
    data["version"] = 1
    return data
```

```python
# shared/config/io.py
from __future__ import annotations

import json
from pathlib import Path

from shared.config.schema import normalize_config

DEFAULTS_PATH = Path(__file__).with_name("defaults.json")


def load_defaults() -> dict:
    return json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))


def load_config(path: Path) -> dict:
    defaults = load_defaults()
    if not path.exists():
        return dict(defaults)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return normalize_config(raw, defaults)


def save_config(path: Path, config: dict) -> None:
    defaults = load_defaults()
    normalized = normalize_config(config, defaults)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Add the package marker and fixture**

```python
# shared/config/__init__.py
from shared.config.io import load_config, load_defaults, save_config

__all__ = ["load_config", "load_defaults", "save_config"]
```

```json
// tests/fixtures/config_everyday.json
{
  "nativeLanguage": "Chinese",
  "targetLanguage": "English",
  "goal": "everyday",
  "mode": "everyday",
  "style": "teaching",
  "responseLanguage": "native",
  "enabled": true,
  "ieltsFocus": "both",
  "targetBand": "",
  "currentLevel": "",
  "version": 1
}
```

- [ ] **Step 5: Run the config test to verify it passes**

Run:

```bash
python3 -m unittest tests.shared.test_config_io -v
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add shared/config tests/shared/test_config_io.py tests/fixtures/config_everyday.json
git commit -F - <<'EOF'
Normalize language coach config across platforms

Introduce a dependency-free shared config layer so Claude and Codex
can use one schema while preserving adapter-specific storage paths.

Constraint: Must not add third-party dependencies for validation or CLI handling
Rejected: Keep platform-specific config shapes forever | would duplicate pedagogy and migration logic
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Any new config field must be added through shared normalization first, not ad hoc in platform scripts
Tested: python3 -m unittest tests.shared.test_config_io -v
Not-tested: Cross-tool config import/export flows
EOF
```

### Task 2: Build prompt assembly for everyday and IELTS modes

**Files:**
- Create: `shared/pedagogy/__init__.py`
- Create: `shared/pedagogy/modes.py`
- Create: `shared/prompts/__init__.py`
- Create: `shared/prompts/build_prompt.py`
- Create: `tests/shared/test_prompt_builder.py`
- Create: `tests/fixtures/config_ielts_writing.json`

- [ ] **Step 1: Write failing prompt builder tests**

```python
# tests/shared/test_prompt_builder.py
import json
import unittest
from pathlib import Path

from shared.prompts.build_prompt import build_prompt


FIXTURES = Path("tests/fixtures")


class PromptBuilderTests(unittest.TestCase):
    def test_everyday_prompt_stays_compact(self):
        config = json.loads((FIXTURES / "config_everyday.json").read_text(encoding="utf-8"))
        prompt = build_prompt(config)

        self.assertIn("Your original", prompt)
        self.assertIn("Corrected", prompt)
        self.assertIn("More natural", prompt)
        self.assertIn("1 key takeaway", prompt)
        self.assertNotIn("Band estimate", prompt)

    def test_ielts_writing_prompt_includes_exam_feedback(self):
        config = json.loads((FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8"))
        prompt = build_prompt(config)

        self.assertIn("Band estimate", prompt)
        self.assertIn("Reusable pattern", prompt)
        self.assertIn("Mini drill", prompt)

    def test_ielts_speaking_prompt_avoids_fake_pronunciation_scoring(self):
        config = json.loads((FIXTURES / "config_ielts_writing.json").read_text(encoding="utf-8"))
        config["mode"] = "ielts-speaking"
        prompt = build_prompt(config)

        self.assertIn("Do not claim to score pronunciation from text alone", prompt)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the prompt tests to verify they fail**

Run:

```bash
python3 -m unittest tests.shared.test_prompt_builder -v
```

Expected: `ModuleNotFoundError` for `shared.prompts.build_prompt`

- [ ] **Step 3: Implement mode rules**

```python
# shared/pedagogy/modes.py
EVERYDAY_SECTIONS = [
    "Your original",
    "Corrected",
    "More natural",
    "1 key takeaway",
]

IELTS_WRITING_SECTIONS = [
    "Band estimate",
    "What is working",
    "What lowers the score",
    "Rewritten higher-band version",
    "Reusable pattern",
    "Mini drill",
]

IELTS_SPEAKING_SECTIONS = [
    "Fluency and coherence",
    "Lexical resource",
    "Grammatical range and accuracy",
    "Natural spoken alternative",
    "Reusable pattern",
    "Mini drill",
]
```

```python
# shared/prompts/build_prompt.py
from __future__ import annotations

from shared.pedagogy.modes import (
    EVERYDAY_SECTIONS,
    IELTS_SPEAKING_SECTIONS,
    IELTS_WRITING_SECTIONS,
)


def _response_instruction(config: dict) -> str:
    target = config["targetLanguage"]
    native = config["nativeLanguage"]
    response_language = target if config["responseLanguage"] == "target" else native
    return f"After coaching, answer the actual request in {response_language}."


def build_prompt(config: dict) -> str:
    mode = config["mode"]
    base = [
        f"Language coaching preference (native: {config['nativeLanguage']} → target: {config['targetLanguage']}).",
        f"Goal: {config['goal']}.",
        f"Style: {config['style']}.",
    ]

    if mode == "everyday":
        sections = EVERYDAY_SECTIONS
        guidance = [
            "Keep coaching compact and low-interruption.",
            "When the user writes fully in the native language, provide one concise natural target-language version first.",
        ]
    elif mode == "ielts-writing":
        sections = IELTS_WRITING_SECTIONS
        guidance = [
            "Optimize feedback for IELTS writing improvement rather than grammar-only correction.",
            "Prefer rough band ranges over false precision.",
        ]
    elif mode == "ielts-speaking":
        sections = IELTS_SPEAKING_SECTIONS
        guidance = [
            "Optimize feedback for spoken naturalness, fluency, and lexical resource.",
            "Do not claim to score pronunciation from text alone.",
        ]
    else:
        sections = ["Review summary", "Recurring mistakes", "Reusable pattern", "Next drill"]
        guidance = ["Summarize patterns across recent interactions."]

    section_text = "\n".join(f"- {section}" for section in sections)
    guidance_text = "\n".join(f"- {line}" for line in guidance)
    return "\n".join(base + [guidance_text, section_text, _response_instruction(config)])
```

- [ ] **Step 4: Add package markers and IELTS fixture**

```python
# shared/pedagogy/__init__.py
from shared.pedagogy.modes import EVERYDAY_SECTIONS, IELTS_SPEAKING_SECTIONS, IELTS_WRITING_SECTIONS

__all__ = ["EVERYDAY_SECTIONS", "IELTS_SPEAKING_SECTIONS", "IELTS_WRITING_SECTIONS"]
```

```python
# shared/prompts/__init__.py
from shared.prompts.build_prompt import build_prompt

__all__ = ["build_prompt"]
```

```json
// tests/fixtures/config_ielts_writing.json
{
  "nativeLanguage": "Chinese",
  "targetLanguage": "English",
  "goal": "ielts",
  "mode": "ielts-writing",
  "style": "teaching",
  "responseLanguage": "target",
  "enabled": true,
  "ieltsFocus": "writing",
  "targetBand": "7.0",
  "currentLevel": "6.0",
  "version": 1
}
```

- [ ] **Step 5: Run the prompt tests to verify they pass**

Run:

```bash
python3 -m unittest tests.shared.test_prompt_builder -v
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add shared/pedagogy shared/prompts tests/shared/test_prompt_builder.py tests/fixtures/config_ielts_writing.json
git commit -F - <<'EOF'
Define lightweight and IELTS-specific coaching prompts

Add one prompt builder that turns normalized config into compact
everyday guidance or deeper IELTS-focused instruction blocks.

Constraint: Feedback must stay compact by default to preserve daily usability
Rejected: Separate prompt builders per platform | would split pedagogy and drift over time
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Add new teaching modes by extending shared prompt assembly, not by hardcoding platform-specific strings first
Tested: python3 -m unittest tests.shared.test_prompt_builder -v
Not-tested: Real-session prompt length behavior inside Claude or Codex
EOF
```

### Task 3: Route Claude hooks through the shared core

**Files:**
- Create: `scripts/render_coaching_context.py`
- Modify: `hooks/language-coach.sh`
- Create: `tests/hooks/test_claude_hook_output.py`

- [ ] **Step 1: Write the failing Claude hook output test**

```python
# tests/hooks/test_claude_hook_output.py
import json
import subprocess
import unittest


class ClaudeHookOutputTests(unittest.TestCase):
    def test_render_script_emits_user_prompt_submit_payload(self):
        result = subprocess.run(
            [
                "python3",
                "scripts/render_coaching_context.py",
                "--platform",
                "claude",
                "--config",
                "tests/fixtures/config_everyday.json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("Language coaching preference", payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the Claude hook test to verify it fails**

Run:

```bash
python3 -m unittest tests.hooks.test_claude_hook_output -v
```

Expected: file-not-found failure for `scripts/render_coaching_context.py`

- [ ] **Step 3: Implement the shared render script**

```python
# scripts/render_coaching_context.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared.config.io import load_config
from shared.prompts.build_prompt import build_prompt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices={"claude", "codex"}, required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(Path(args.config))
    if not config["enabled"]:
        return 0

    prompt = build_prompt(config)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": prompt,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Update the Claude shell hook to delegate**

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$HOME/.claude/language-coach.json"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

python3 "$REPO_ROOT/scripts/render_coaching_context.py" \
  --platform claude \
  --config "$CONFIG"
```

- [ ] **Step 5: Run the Claude hook test to verify it passes**

Run:

```bash
python3 -m unittest tests.hooks.test_claude_hook_output -v
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add scripts/render_coaching_context.py hooks/language-coach.sh tests/hooks/test_claude_hook_output.py
git commit -F - <<'EOF'
Route Claude coaching through the shared prompt renderer

Keep the Claude hook entrypoint stable while moving prompt assembly
into the shared Python layer so both platforms emit the same teaching logic.

Constraint: Existing Claude users should not have to change how the hook is installed
Rejected: Rewrite the Claude hook directly in Python only | risks breaking existing install assumptions unnecessarily
Confidence: high
Scope-risk: moderate
Reversibility: clean
Directive: The shell hook should stay thin; keep prompt logic out of bash
Tested: python3 -m unittest tests.hooks.test_claude_hook_output -v
Not-tested: Live Claude Code session with marketplace-installed plugin
EOF
```

### Task 4: Consolidate command handling into a shared management CLI

**Files:**
- Create: `scripts/manage_language_coach.py`
- Modify: `skills/language-coach/SKILL.md`
- Create: `tests/scripts/test_manage_language_coach.py`

- [ ] **Step 1: Write the failing management CLI test**

```python
# tests/scripts/test_manage_language_coach.py
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class ManageLanguageCoachTests(unittest.TestCase):
    def test_set_mode_updates_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "language-coach.json"
            config_path.write_text(
                json.dumps(
                    {
                        "nativeLanguage": "Chinese",
                        "targetLanguage": "English",
                        "goal": "everyday",
                        "mode": "everyday",
                        "style": "teaching",
                        "responseLanguage": "native",
                        "enabled": True,
                        "ieltsFocus": "both",
                        "targetBand": "",
                        "currentLevel": "",
                        "version": 1,
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "scripts/manage_language_coach.py",
                    "--config",
                    str(config_path),
                    "mode",
                    "ielts-writing",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["mode"], "ielts-writing")
            self.assertEqual(updated["goal"], "ielts")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the CLI test to verify it fails**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach -v
```

Expected: file-not-found failure for `scripts/manage_language_coach.py`

- [ ] **Step 3: Implement the management CLI**

```python
# scripts/manage_language_coach.py
from __future__ import annotations

import argparse
from pathlib import Path

from shared.config.io import load_config, save_config


def resolve_default_config(platform: str) -> Path:
    home = Path.home()
    if platform == "codex":
        return home / ".codex" / "language-coach.json"
    return home / ".claude" / "language-coach.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices={"claude", "codex"}, default="claude")
    parser.add_argument("--config")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("status", "on", "off"):
        subparsers.add_parser(name)

    for name in ("native", "target", "style", "response", "goal", "mode", "band", "focus"):
        child = subparsers.add_parser(name)
        child.add_argument("value")

    args = parser.parse_args()
    path = Path(args.config) if args.config else resolve_default_config(args.platform)
    config = load_config(path)

    if args.command == "native":
        config["nativeLanguage"] = args.value
    elif args.command == "target":
        config["targetLanguage"] = args.value
    elif args.command == "style":
        config["style"] = args.value
    elif args.command == "response":
        config["responseLanguage"] = args.value
    elif args.command == "goal":
        config["goal"] = args.value
    elif args.command == "mode":
        config["mode"] = args.value
        if args.value.startswith("ielts"):
            config["goal"] = "ielts"
    elif args.command == "band":
        config["targetBand"] = args.value
    elif args.command == "focus":
        config["ieltsFocus"] = args.value
    elif args.command == "on":
        config["enabled"] = True
    elif args.command == "off":
        config["enabled"] = False
    elif args.command == "status":
        print(config)
        return 0

    save_config(path, config)
    print(f"saved:{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Update the skill to use the shared CLI**

```md
### setup
Ask the onboarding questions one at a time, then run:

```bash
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude native "Chinese"
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude target "English"
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude goal "ielts"
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude mode "ielts-writing"
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude style "teaching"
python3 "/path/to/repo/scripts/manage_language_coach.py" --platform claude response "native"
```

For Codex, replace `--platform claude` with `--platform codex`.
```

- [ ] **Step 5: Run the CLI test to verify it passes**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach -v
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add scripts/manage_language_coach.py skills/language-coach/SKILL.md tests/scripts/test_manage_language_coach.py
git commit -F - <<'EOF'
Unify language coach command handling across Claude and Codex

Replace ad hoc config mutation with a single dependency-free CLI so
both platform adapters can manage the same normalized schema safely.

Constraint: The existing skill must remain readable and command-oriented for end users
Rejected: Keep one-line Python snippets embedded in the skill forever | too brittle once modes and Codex support expand
Confidence: high
Scope-risk: moderate
Reversibility: clean
Directive: New user-facing commands should map to this CLI before updating platform-specific docs
Tested: python3 -m unittest tests.scripts.test_manage_language_coach -v
Not-tested: Interactive setup flow inside Claude or Codex UIs
EOF
```

### Task 5: Add the Codex plugin and automatic hook installer

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `platforms/codex/hook_entry.py`
- Create: `platforms/codex/install_hooks.py`
- Create: `platforms/codex/templates/hooks.json`
- Create: `tests/hooks/test_codex_hook_install.py`

- [ ] **Step 1: Write the failing Codex installer test**

```python
# tests/hooks/test_codex_hook_install.py
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class CodexHookInstallTests(unittest.TestCase):
    def test_installer_writes_user_prompt_submit_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            hooks_path = Path(tmp) / "hooks.json"
            result = subprocess.run(
                [
                    "python3",
                    "platforms/codex/install_hooks.py",
                    "--hooks-path",
                    str(hooks_path),
                    "--repo-root",
                    str(Path.cwd()),
                    "install",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            command = payload["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            self.assertIn("platforms/codex/hook_entry.py", command)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the Codex installer test to verify it fails**

Run:

```bash
python3 -m unittest tests.hooks.test_codex_hook_install -v
```

Expected: file-not-found failure for `platforms/codex/install_hooks.py`

- [ ] **Step 3: Add the Codex plugin manifest**

```json
{
  "name": "prompt-language-coach",
  "version": "0.2.0",
  "description": "Real-time language coaching with everyday and IELTS modes.",
  "author": {
    "name": "leeguooooo"
  },
  "homepage": "https://github.com/leeguooooo/prompt-language-coach",
  "repository": "https://github.com/leeguooooo/prompt-language-coach",
  "license": "MIT",
  "keywords": ["language-learning", "ielts", "writing", "coaching"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Prompt Language Coach",
    "shortDescription": "Language coaching for everyday work and IELTS practice",
    "longDescription": "Correct writing, teach more natural phrasing, and switch into IELTS-oriented writing or speaking modes.",
    "developerName": "leeguooooo",
    "category": "Education",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Use Prompt Language Coach to improve my English while I work.",
      "Use Prompt Language Coach in IELTS writing mode."
    ]
  }
}
```

- [ ] **Step 4: Implement the Codex hook entry and installer**

```python
# platforms/codex/hook_entry.py
from __future__ import annotations

from pathlib import Path
import subprocess


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    config_path = Path.home() / ".codex" / "language-coach.json"
    if not config_path.exists():
        return 0

    command = [
        "python3",
        str(repo_root / "scripts" / "render_coaching_context.py"),
        "--platform",
        "codex",
        "--config",
        str(config_path),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# platforms/codex/install_hooks.py
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_hook_command(repo_root: Path) -> str:
    return f'python3 "{repo_root / "platforms" / "codex" / "hook_entry.py"}"'


def install(hooks_path: Path, repo_root: Path) -> None:
    payload = {"hooks": {}}
    if hooks_path.exists():
        payload = json.loads(hooks_path.read_text(encoding="utf-8"))
    payload.setdefault("hooks", {})
    payload["hooks"]["UserPromptSubmit"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": build_hook_command(repo_root),
                }
            ]
        }
    ]
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def remove(hooks_path: Path) -> None:
    if not hooks_path.exists():
        return
    payload = json.loads(hooks_path.read_text(encoding="utf-8"))
    payload.get("hooks", {}).pop("UserPromptSubmit", None)
    hooks_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hooks-path", default=str(Path.home() / ".codex" / "hooks.json"))
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("command", choices={"install", "remove"})
    args = parser.parse_args()

    hooks_path = Path(args.hooks_path)
    repo_root = Path(args.repo_root)
    if args.command == "install":
        install(hooks_path, repo_root)
    else:
        remove(hooks_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```json
// platforms/codex/templates/hooks.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/ABSOLUTE/PATH/TO/platforms/codex/hook_entry.py\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run the Codex installer test to verify it passes**

Run:

```bash
python3 -m unittest tests.hooks.test_codex_hook_install -v
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add .codex-plugin/plugin.json platforms/codex tests/hooks/test_codex_hook_install.py
git commit -F - <<'EOF'
Add a Codex-native plugin and user hook installer

Package the project as a Codex plugin and provide an installer that
adds automatic coaching to Codex through the native UserPromptSubmit hook.

Constraint: Codex discovers hooks from config-layer hooks.json files rather than from plugin manifests directly
Rejected: Require users to manually hand-edit ~/.codex/hooks.json | too error-prone for a learning product
Confidence: medium
Scope-risk: moderate
Reversibility: clean
Directive: Treat the Codex hook installer as the only writer of managed hook entries for this plugin
Tested: python3 -m unittest tests.hooks.test_codex_hook_install -v
Not-tested: Marketplace-installed plugin flow end-to-end inside a real Codex client
EOF
```

### Task 6: Document the dual-platform product and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-04-15-codex-claude-dual-platform-design.md`

- [ ] **Step 1: Update README installation and usage sections**

```md
## Installation

### Claude Code

...existing Claude install flow...

### Codex

```bash
mkdir -p ~/.codex/plugins
cp -R /absolute/path/to/prompt-language-coach ~/.codex/plugins/prompt-language-coach
```

Add or update `~/.agents/plugins/marketplace.json` so the entry points to that plugin path, restart Codex, then run the plugin skill setup flow.

During setup, install the Codex hook with:

```bash
python3 /absolute/path/to/prompt-language-coach/platforms/codex/install_hooks.py \
  --repo-root /absolute/path/to/prompt-language-coach \
  install
```
```

- [ ] **Step 2: Add Codex-specific command examples and IELTS mode docs**

```md
## Modes

- `everyday`: lightweight correction and one key takeaway
- `ielts-writing`: score-oriented writing feedback, rewrite, pattern, drill
- `ielts-speaking`: spoken-naturalness feedback from text, pattern, drill
- `review`: summarize repeated mistakes and next practice items
```

- [ ] **Step 3: Run the full test suite**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: `OK`

- [ ] **Step 4: Run direct render smoke tests**

Run:

```bash
python3 scripts/render_coaching_context.py --platform claude --config tests/fixtures/config_everyday.json
python3 scripts/render_coaching_context.py --platform codex --config tests/fixtures/config_ielts_writing.json
```

Expected:

- Both commands exit `0`
- Both outputs are valid JSON with `hookSpecificOutput.hookEventName = "UserPromptSubmit"`

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/specs/2026-04-15-codex-claude-dual-platform-design.md
git commit -F - <<'EOF'
Explain dual-platform install and IELTS learning modes

Update the docs so users can install the product on Claude or Codex
and understand the lightweight default loop versus explicit IELTS modes.

Constraint: The README must stay usable for non-technical learners despite now supporting two platforms
Rejected: Keep Codex setup undocumented until later | would make the plugin technically present but practically unusable
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep installation docs aligned with real file paths and tested setup commands
Tested: python3 -m unittest discover -s tests -p 'test_*.py' -v; python3 scripts/render_coaching_context.py --platform claude --config tests/fixtures/config_everyday.json; python3 scripts/render_coaching_context.py --platform codex --config tests/fixtures/config_ielts_writing.json
Not-tested: Marketplace publication metadata review by external users
EOF
```

## Self-Review

- Spec coverage:
  - shared config and prompt core covered in Tasks 1-2
  - Claude migration covered in Task 3
  - command surface and config writes covered in Task 4
  - Codex plugin and auto hook setup covered in Task 5
  - docs and verification covered in Task 6
- Placeholder scan:
  - no `TBD`, `TODO`, or implied "fill this in later" steps remain
- Type consistency:
  - normalized config keys stay `nativeLanguage`, `targetLanguage`, `goal`, `mode`, `style`, `responseLanguage`, `enabled`, `ieltsFocus`, `targetBand`, `currentLevel`, `version`

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-15-dual-platform-language-coach.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
