# prompt-language-coach

> Real-time language coaching inside your AI editor — automatically correct your writing and learn natural expressions on every prompt.

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://github.com/leeguooooo/prompt-language-coach)
[![Cursor](https://img.shields.io/badge/Cursor-Rules-purple)](https://github.com/leeguooooo/prompt-language-coach)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

Every message you send in Claude Code is automatically coached **before** Claude answers your actual request:

- Writing in your target language? → Get grammar fixes + natural native-like expressions
- Writing in your native language? → Get one clean, natural target-language version
- Mixed? → Get a complete natural version of the whole meaning

Works for **any language pair**: Chinese → English, Japanese → English, Spanish → French, etc.

---

## Demo

**You write:**
> "I want to know how can i to fix this bug in my code"

**Claude coaches first:**
```
English correction:
> "I want to know how can i to fix this bug in my code"

Key issues:
- "how can i to fix" → remove "to" after modal verb: "how I can fix"
- "i" should be capitalized: "I"

Corrected: "I want to know how I can fix this bug in my code."
More natural: "How do I fix this bug?" / "Can you help me debug this?"
```

Then Claude answers your actual question.

---

## Installation

### Claude Code

**Prerequisites:** `jq` — `brew install jq` (macOS) / `apt install jq` (Linux)

```
/plugin marketplace add leeguooooo/plugins
/plugin install prompt-language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

### Cursor

Copy the rule file to your project or global Cursor rules:

```bash
# Project-level (this project only)
mkdir -p .cursor/rules
curl -o .cursor/rules/language-coach.mdc \
  https://raw.githubusercontent.com/leeguooooo/prompt-language-coach/main/cursor-rules/language-coach.mdc
```

Or paste the contents of [`cursor-rules/language-coach.mdc`](cursor-rules/language-coach.mdc) into **Cursor Settings → Rules for AI** (global).

Edit the rule to set your native language, target language, and preferred response language.

---

## Setup wizard

Run `/language-coach setup` and answer four questions:

1. What is your native language? (e.g. Chinese, Japanese, Spanish)
2. What language are you learning? (e.g. English, French, German)
3. Which coaching style? (`teaching` / `concise` / `translate`)
4. Should Claude respond in your native or target language?

That's it — coaching activates immediately on every prompt.

---

## Commands

| Command | Description |
|---|---|
| `/language-coach:language-coach setup` | One-time interactive setup wizard |
| `/language-coach:language-coach native <lang>` | Change your native language |
| `/language-coach:language-coach target <lang>` | Change the language you are learning |
| `/language-coach:language-coach style <mode>` | Switch coaching style: `teaching`, `concise`, `translate` |
| `/language-coach:language-coach response <mode>` | Switch response language: `native` or `target` |
| `/language-coach:language-coach status` | Show current config |
| `/language-coach:language-coach off` | Pause coaching (config preserved) |
| `/language-coach:language-coach on` | Resume coaching |

---

## Coaching styles

| Style | What you get |
|---|---|
| `teaching` | Error explanation + corrected version + natural version |
| `concise` | Corrected version + natural version (no explanations) |
| `translate` | Target-language version only |

---

## Configuration

Config is stored at `~/.claude/language-coach.json` (global, not project-specific):

```json
{
  "native": "Chinese",
  "target": "English",
  "style": "teaching",
  "enabled": true,
  "responseLanguage": "native"
}
```

| Field | Values | Default | Description |
|---|---|---|---|
| `native` | any language name | `"Chinese"` | Your native language |
| `target` | any language name | `"English"` | Language you are learning |
| `style` | `teaching` / `concise` / `translate` | `"teaching"` | Output verbosity |
| `enabled` | `true` / `false` | `true` | Toggle on/off without losing config |
| `responseLanguage` | `native` / `target` | `"native"` | Language Claude uses for answers |

---

## How it works

This plugin registers a `UserPromptSubmit` hook in Claude Code. On every message:

1. The hook script reads `~/.claude/language-coach.json`
2. Builds a coaching instruction based on your config
3. Injects it into Claude's context via `hookSpecificOutput.additionalContext`
4. Claude coaches your writing first, then answers your actual request

The hook exits silently (no coaching, no crash) when:
- `jq` is not installed
- The config file does not exist yet
- `enabled` is `false`

---

## Use cases

- **ESL learners** preparing for English-speaking job markets (Australia, UK, US, Canada)
- **Language students** who want immersive practice without leaving their dev workflow
- **Remote workers** who write in a second language every day
- **Engineers** who want to improve writing quality in technical communication

---

## Why this approach?

Most language apps are separate tools that pull you away from your work. This plugin makes every coding session a language practice session — zero context switching, zero extra effort.

---

## Manual install (without marketplace)

If you prefer to install manually, clone the repo and add the hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"/path/to/prompt-language-coach/hooks/language-coach.sh\""
          }
        ]
      }
    ]
  }
}
```

Then create `~/.claude/language-coach.json` with your config.

---

## Contributing

PRs welcome. If you want to add a new coaching style, improve the prompt, or add a new command — open an issue first to discuss.

---

## Author

Built by [leeguooooo](https://github.com/leeguooooo) — a senior frontend engineer using this plugin daily while preparing for the Australian job market.

---

## Related

- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code hooks guide](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code plugin marketplace](https://docs.anthropic.com/en/docs/claude-code/plugins)
