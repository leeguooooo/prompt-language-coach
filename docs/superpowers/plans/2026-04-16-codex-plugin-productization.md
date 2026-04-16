# Codex Plugin Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing Codex adapter into a first-class plugin surface with a real install/control flow, aligned skill behavior, and product-grade docs.

**Architecture:** Keep the shared coaching core unchanged where possible, add Codex-specific integration commands in the shared management CLI, route the `language-coach` skill through host-aware behavior, and rewrite plugin metadata plus README content so Codex, Claude Code, and Cursor are presented as equal native platforms.

**Tech Stack:** Python 3 standard library, Markdown docs, Codex plugin manifest JSON, unittest.

---

## File Structure Map

- Modify: `.codex-plugin/plugin.json`
  Purpose: strengthen Codex plugin metadata so the package reads like a real multilingual product, not a generic adapter.
- Modify: `scripts/manage_language_coach.py`
  Purpose: add Codex integration commands and richer Codex-aware status output without changing the shared config model.
- Modify: `skills/language-coach/SKILL.md`
  Purpose: make the skill platform-aware and ensure Codex setup installs the Codex hook automatically.
- Modify: `tests/scripts/test_manage_language_coach.py`
  Purpose: cover new Codex integration commands and status behavior.
- Modify: `README.md`
  Purpose: present Codex, Claude Code, and Cursor as equal first-class platforms and add Codex installation/use instructions.
- Modify: `README.zh-CN.md`
  Purpose: keep Chinese docs in sync with the English product story and Codex instructions.

---

### Task 1: Add Codex integration CLI coverage first

**Files:**
- Modify: `tests/scripts/test_manage_language_coach.py`
- Modify: `scripts/manage_language_coach.py`

- [ ] **Step 1: Write the failing tests for Codex hook install and status**

```python
def test_codex_install_hook_command_writes_hooks_json(self):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        hooks_path = home / ".codex" / "hooks.json"

        result = subprocess.run(
            [
                "python3",
                "scripts/manage_language_coach.py",
                "--platform",
                "codex",
                "install-hook",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={"HOME": str(home)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(hooks_path.read_text(encoding="utf-8"))
        command = payload["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn("platforms/codex/hook_entry.py", command)


def test_codex_status_reports_hook_state(self):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        config_dir = home / ".codex"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "language-coach.json").write_text("{}", encoding="utf-8")

        result = subprocess.run(
            [
                "python3",
                "scripts/manage_language_coach.py",
                "--platform",
                "codex",
                "status",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={"HOME": str(home)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hook status:       not installed", result.stdout)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach -v
```

Expected: failure because `install-hook` is not yet a valid command and status does not yet show Codex hook state.

- [ ] **Step 3: Implement Codex integration commands in the management CLI**

```python
from platforms.codex.install_hooks import (
    HOOK_EVENT,
    install as install_codex_hook,
    load_payload as load_codex_hooks_payload,
    remove as remove_codex_hook,
)


def resolve_codex_hooks_path() -> Path:
    return Path.home() / ".codex" / "hooks.json"


def codex_hook_installed(hooks_path: Path) -> bool:
    payload = load_codex_hooks_payload(hooks_path)
    entries = payload.get("hooks", {}).get(HOOK_EVENT, [])
    return any(isinstance(entry, dict) for entry in entries)
```

Add parser entries:

```python
for name in ("install-hook", "remove-hook", "hook-status"):
    subparsers.add_parser(name)
```

Handle them in `main()` before config mutation:

```python
if args.command == "install-hook":
    hooks_path = resolve_codex_hooks_path()
    install_codex_hook(hooks_path, REPO_ROOT)
    print(f"Codex hook installed: {hooks_path}")
    return 0
if args.command == "remove-hook":
    hooks_path = resolve_codex_hooks_path()
    remove_codex_hook(hooks_path)
    print(f"Codex hook removed: {hooks_path}")
    return 0
if args.command == "hook-status":
    hooks_path = resolve_codex_hooks_path()
    print("installed" if codex_hook_installed(hooks_path) else "not installed")
    return 0
```

Extend `format_status()` for Codex:

```python
if platform == "codex":
    lines.append(
        f"Hook status:       {'installed' if codex_hook_installed(resolve_codex_hooks_path()) else 'not installed'}"
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach -v
```

Expected: all tests in `tests.scripts.test_manage_language_coach` pass.

---

### Task 2: Make the shared skill Codex-aware and setup-aware

**Files:**
- Modify: `skills/language-coach/SKILL.md`
- Modify: `tests/scripts/test_manage_language_coach.py`

- [ ] **Step 1: Write the failing setup behavior test**

```python
def test_codex_install_hook_command_prints_expected_message(self):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)

        result = subprocess.run(
            [
                "python3",
                "scripts/manage_language_coach.py",
                "--platform",
                "codex",
                "install-hook",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={"HOME": str(home)},
        )

        self.assertIn("Codex hook installed:", result.stdout)
```

- [ ] **Step 2: Run the tests to verify current messaging or behavior is missing**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach -v
```

Expected: failure until the new command output is finalized.

- [ ] **Step 3: Update the skill instructions to use host-aware behavior**

```md
Default platform: use the current host platform.

- In Codex, use `--platform codex`
- In Claude Code, use `--platform claude`
- In Cursor, use `--platform cursor`
```

In the Codex setup flow, append:

```bash
python3 scripts/manage_language_coach.py --platform codex install-hook
python3 scripts/manage_language_coach.py --platform codex status
```

Add explicit Codex control entries:

```text
/language-coach off
/language-coach on
/language-coach status
```

and note that `setup` on Codex installs automatic prompt coaching.

- [ ] **Step 4: Run the tests to verify the CLI behavior remains green**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach tests.hooks.test_codex_hook_install -v
```

Expected: both suites pass.

---

### Task 3: Productize the plugin metadata and README surfaces

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: Update Codex plugin metadata to reflect the real product**

```json
{
  "description": "Always-on language coaching for any language pair, with everyday and IELTS modes.",
  "keywords": [
    "language-learning",
    "multilingual",
    "codex",
    "claude-code",
    "cursor",
    "ielts",
    "coaching"
  ],
  "interface": {
    "shortDescription": "An always-on language coach for Codex",
    "longDescription": "Coach every prompt, support any native-to-target language pair, and switch into IELTS writing or speaking practice when needed.",
    "defaultPrompt": [
      "Use Prompt Language Coach to improve my target language while I work.",
      "Use Prompt Language Coach for Japanese to English practice.",
      "Use Prompt Language Coach in IELTS writing mode."
    ]
  }
}
```

- [ ] **Step 2: Rewrite the top README sections around the multi-platform story**

Replace Claude-only framing with:

```md
> An always-on language coach for AI editors. Improve any target language while you work in Codex, Claude Code, or Cursor.
```

Add a first-class platform matrix:

```md
| Platform | Native integration | Status |
| --- | --- | --- |
| Codex | `.codex-plugin` + `UserPromptSubmit` hook | First-class |
| Claude Code | `.claude-plugin` + `UserPromptSubmit` hook | First-class |
| Cursor | native plugin/rule surface | First-class |
```

Add a Codex install section before or alongside Claude/Cursor with:

```md
### Codex

**Prerequisites:** `python3`

1. Install the plugin from this repository into your Codex plugin surface.
2. Run `/language-coach setup`
3. The setup flow writes `~/.codex/language-coach.json` and installs the Codex `UserPromptSubmit` hook.
```

Update the "How it works" section to mention Codex explicitly and change language-pair examples so they are not English-only.

- [ ] **Step 3: Mirror the same product story in Chinese docs**

Update `README.zh-CN.md` to:

- present Codex, Claude Code, and Cursor as equal first-class platforms
- add Codex install and setup instructions
- describe the product as supporting any native-language to target-language pair
- keep IELTS as a strong mode, not the entire brand

- [ ] **Step 4: Run targeted verification for docs-adjacent behavior**

Run:

```bash
python3 -m unittest tests.scripts.test_manage_language_coach tests.hooks.test_codex_hook_install -v
python3 scripts/manage_language_coach.py --platform codex status
python3 scripts/manage_language_coach.py --platform codex hook-status
```

Expected:

- unit tests pass
- Codex status prints a `Hook status:` line
- hook-status prints either `installed` or `not installed`

