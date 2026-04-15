# prompt-language-coach

> Real-time language coaching inside your AI editor — automatically correct your writing and learn natural expressions on every prompt.

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://github.com/leeguooooo/prompt-language-coach)
[![Codex](https://img.shields.io/badge/Codex-Plugin-green)](https://github.com/leeguooooo/prompt-language-coach)
[![Cursor](https://img.shields.io/badge/Cursor-Rules-purple)](https://github.com/leeguooooo/prompt-language-coach)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

This repository currently supports three editor surfaces:

- **Claude Code** via a marketplace/plugin install plus a `UserPromptSubmit` hook
- **Codex** via a native Codex plugin plus a `UserPromptSubmit` hook installer
- **Cursor** via an always-on rule file

Claude and Codex share the same Python coaching core and normalized config schema. Cursor is a lighter rule-based surface for everyday coaching.

Every message you send in Claude Code or Codex is coached **before** the assistant answers your actual request:

- Writing in your target language? → Get grammar fixes + natural native-like expressions
- Writing in your native language? → Get one clean, natural target-language version
- Mixed? → Get a complete natural version of the whole meaning

For Claude and Codex, the shared core also supports:

- `everyday`
- `ielts-writing`
- `ielts-speaking`
- `review`

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

**Prerequisites:** `python3`

```
/plugin marketplace add leeguooooo/plugins
/plugin install prompt-language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

### Codex

Copy the repo into your local Codex plugins directory:

```bash
mkdir -p ~/.codex/plugins
cp -R /absolute/path/to/prompt-language-coach ~/.codex/plugins/prompt-language-coach
```

If your Codex setup uses `~/.agents/plugins/marketplace.json` for plugin discovery, add or update an entry that points to `~/.codex/plugins/prompt-language-coach`, then restart Codex.

Install the Codex `UserPromptSubmit` hook:

```bash
python3 /absolute/path/to/prompt-language-coach/platforms/codex/install_hooks.py \
  --repo-root /absolute/path/to/prompt-language-coach \
  install
```

The Codex hook reads `~/.codex/language-coach.json`. Populate it with the Codex CLI examples below. The shared `/language-coach:language-coach setup` flow defaults to Claude config unless the command path explicitly runs with `--platform codex`.

### Cursor

Copy the rule file to your project or global Cursor rules:

```bash
# Project-level (this project only)
mkdir -p .cursor/rules
curl -o .cursor/rules/language-coach.mdc \
  https://raw.githubusercontent.com/leeguooooo/prompt-language-coach/main/cursor-rules/language-coach.mdc
```

Or paste the contents of [`cursor-rules/language-coach.mdc`](cursor-rules/language-coach.mdc) into **Cursor Settings → Rules for AI** (global).

Edit the rule to set your native language, target language, and preferred response language. The shipped Cursor rule is the lightweight everyday-teaching variant and does not read the shared Claude/Codex JSON config.

---

## Setup and usage

### Claude Code setup

Run `/language-coach:language-coach setup` and answer the onboarding questions:

1. What is your native language?
2. What language are you learning?
3. What is your main goal? (`everyday` / `ielts`)
4. Which coaching style? (`teaching` / `concise` / `translate`)
5. Which response language should be used after coaching? (`native` / `target`)

If you choose `ielts`, the setup flow also stores:

1. Active IELTS mode: `ielts-writing` or `ielts-speaking`
2. IELTS focus: `writing`, `speaking`, or `both`
3. Target band
4. Current level

After setup, Claude coaching activates automatically on every prompt.

### Codex usage

Once the plugin is installed and the hook is enabled, Codex coaching also runs automatically on every prompt.

Codex config is not created by the default shared setup flow. To configure Codex, use the Codex CLI commands below so they write `~/.codex/language-coach.json`.

The underlying CLI is:

```bash
python3 scripts/manage_language_coach.py --platform codex <command>
```

Examples:

```bash
python3 scripts/manage_language_coach.py --platform codex native Chinese
python3 scripts/manage_language_coach.py --platform codex target English
python3 scripts/manage_language_coach.py --platform codex goal ielts
python3 scripts/manage_language_coach.py --platform codex mode ielts-writing
python3 scripts/manage_language_coach.py --platform codex focus writing
python3 scripts/manage_language_coach.py --platform codex band 7.0
python3 scripts/manage_language_coach.py --platform codex response target
python3 scripts/manage_language_coach.py --platform codex status
```

The same CLI also works for Claude with `--platform claude`.

### Cursor usage

Cursor uses the rule file directly. After you copy or paste the rule, coaching applies to every prompt in that workspace or in your global Cursor settings.

To customize Cursor:

1. Change `native: ...`
2. Change `target: ...`
3. Change the response language line at the bottom

For IELTS-specific modes, use Claude or Codex, which both route through the shared mode-aware prompt builder.

---

## Commands

| Command | Description |
|---|---|
| `/language-coach:language-coach setup` | One-time interactive setup wizard |
| `/language-coach:language-coach native <lang>` | Change your native language |
| `/language-coach:language-coach target <lang>` | Change the language you are learning |
| `/language-coach:language-coach style <mode>` | Switch coaching style: `teaching`, `concise`, `translate` |
| `/language-coach:language-coach response <mode>` | Switch response language: `native` or `target` |
| `/language-coach:language-coach goal <mode>` | Switch learning goal: `everyday` or `ielts` |
| `/language-coach:language-coach mode <mode>` | Switch coaching mode: `everyday`, `ielts-writing`, `ielts-speaking`, or `review` |
| `/language-coach:language-coach focus <mode>` | Set IELTS focus: `writing`, `speaking`, or `both` |
| `/language-coach:language-coach band <score>` | Store your IELTS target band |
| `/language-coach:language-coach level <text>` | Store your current level |
| `/language-coach:language-coach status` | Show current config |
| `/language-coach:language-coach off` | Pause coaching (config preserved) |
| `/language-coach:language-coach on` | Resume coaching |

---

For Codex or local repo usage, the equivalent surface is:

```bash
python3 scripts/manage_language_coach.py --platform <claude|codex> <command>
```

Supported CLI commands: `status`, `on`, `off`, `native`, `target`, `style`, `response`, `goal`, `mode`, `focus`, `band`, `level`.

---

## Modes

| Mode | What you get |
|---|---|
| `everyday` | Compact coaching with `Your original`, `Corrected`, `More natural`, and `1 key takeaway` |
| `ielts-writing` | IELTS-oriented writing feedback with band range, score-lowering issues, rewrite, reusable pattern, and drill |
| `ielts-speaking` | Spoken-naturalness feedback from text with fluency, lexical, grammar, pattern, and drill guidance |
| `review` | Compact review summary of recurring mistakes, reusable patterns, and the next drill |

## Coaching styles

| Style | What it changes |
|---|---|
| `teaching` | Explanatory coaching with reasons and upgrade guidance |
| `concise` | Shorter correction-focused coaching |
| `translate` | Target-language-first coaching with minimal explanation |

---

## Configuration

Platform-specific storage:

- Claude: `~/.claude/language-coach.json`
- Codex: `~/.codex/language-coach.json`
- Cursor: edit `.cursor/rules/language-coach.mdc` or your global Cursor rules directly

Claude and Codex use the same normalized JSON schema:

```json
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

| Field | Values | Default | Description |
|---|---|---|---|
| `nativeLanguage` | any language name | `"Chinese"` | Your native language |
| `targetLanguage` | any language name | `"English"` | Language you are learning |
| `goal` | `everyday` / `ielts` | `"everyday"` | Top-level learning goal |
| `mode` | `everyday` / `ielts-writing` / `ielts-speaking` / `review` | `"everyday"` | Active coaching mode |
| `style` | `teaching` / `concise` / `translate` | `"teaching"` | Output verbosity |
| `responseLanguage` | `native` / `target` | `"native"` | Language used after coaching |
| `enabled` | `true` / `false` | `true` | Toggle on/off without losing config |
| `ieltsFocus` | `writing` / `speaking` / `both` | `"both"` | Stored IELTS emphasis |
| `targetBand` | free text | `""` | IELTS target band |
| `currentLevel` | free text | `""` | Current estimated level |
| `version` | integer | `1` | Schema version |

Legacy `native` / `target` keys are normalized into the current schema when Claude or Codex loads config through the shared Python layer.

---

## How it works

Claude and Codex both render the same coaching context through the shared Python core:

1. `shared/config/` loads and normalizes platform config
2. `shared/pedagogy/modes.py` selects the feedback shape for the active mode
3. `shared/prompts/build_prompt.py` builds the coaching instruction text
4. `scripts/render_coaching_context.py` emits hook JSON with `hookSpecificOutput.additionalContext`

Platform adapters:

- Claude shell hook: `hooks/language-coach.sh`
- Codex hook entry: `platforms/codex/hook_entry.py`
- Cursor rule file: `cursor-rules/language-coach.mdc`

Claude and Codex hooks exit silently (no coaching, no crash) when:

- `python3` is not installed
- The platform config file does not exist yet
- `enabled` is `false`

Cursor always applies its rule until you remove or edit the rule file.

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

## Manual install

### Claude

If you prefer to install Claude manually, clone the repo and add the hook to your `~/.claude/settings.json`:

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

### Codex

Install the hook directly against your current checkout:

```bash
python3 platforms/codex/install_hooks.py --repo-root "$(pwd)" install
```

Remove it later with:

```bash
python3 platforms/codex/install_hooks.py --repo-root "$(pwd)" remove
```

Then create or update `~/.codex/language-coach.json` with:

```bash
python3 scripts/manage_language_coach.py --platform codex native Chinese
python3 scripts/manage_language_coach.py --platform codex target English
python3 scripts/manage_language_coach.py --platform codex status
```

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

```shell

/language-coach:language-coach setup

⏺ 你的母语是什么？（例如：Chinese、Japanese、Spanish）

❯ chinese

⏺ 你正在学习哪种语言？（例如：English、French、Japanese）

❯ english, japanese

⏺ 你的主要学习目标是什么？（everyday / ielts）

❯ ielts

⏺ 你想要哪种 IELTS 模式？（ielts-writing / ielts-speaking）

❯ ielts-writing and ielts-speaking

⏺ 目标雅思分数是多少？（可选，例如：6.5、7.0，直接回车跳过）

❯ 6.5

⏺ 你目前的英语水平大概是？（可选，例如：B1、band 5.5，直接回车跳过）

❯ 高中生水平

⏺ 你想要哪种 coaching 风格？（teaching 详细讲解 / concise 只给纠正 / translate 只给翻译）

❯ teaching

⏺ Coaching 之后，我用哪种语言回答你的实际问题？（native 母语中文 / target 目标语言英文）

❯ native

⏺ 收到！开始配置：

⏺ Bash(\
      python3 scripts/manage_language_coach.py --platform claude native "Chinese" && \…)
  ⎿  Native language updated to: Chinese
     Config file: /Users/leo/.claude/language-coach.json
     Target language updated to: English
     … +17 lines (ctrl+o to expand)

⏺ Bash(python3 scripts/manage_language_coach.py --platform claude status)
  ⎿  Platform:          claude
     Native language:   Chinese
     Target language:   English
     … +10 lines (ctrl+o to expand)

⏺ 配置完成！

  ┌──────────┬────────────────────────────────┐
  │   项目   │              设置              │
  ├──────────┼────────────────────────────────┤
  │ 母语     │ Chinese                        │
  ├──────────┼────────────────────────────────┤
  │ 目标语言 │ English + Japanese（自动识别） │
  ├──────────┼────────────────────────────────┤
  │ 目标     │ IELTS                          │
  ├──────────┼────────────────────────────────┤
  │ 模式     │ IELTS Writing（兼顾 Speaking） │
  ├──────────┼────────────────────────────────┤
  │ 风格     │ Teaching（详细讲解）           │
  ├──────────┼────────────────────────────────┤
  │ 回答语言 │ 中文                           │
  ├──────────┼────────────────────────────────┤
  │ 目标分数 │ 6.5                            │
  ├──────────┼────────────────────────────────┤
  │ 当前水平 │ 高中生水平                     │
  └──────────┴────────────────────────────────┘

  现在写英文时会出现 ╭─ 📚 English · IELTS Writing ─ 的 coaching box，写日文时自动切换为 ╭─ 📚 Japanese · IELTS Writing ─。运行 /reload-plugins 让新配置生效。

/reload-plugins
  ⎿  Reloaded: 5 plugins · 10 skills · 7 agents · 5 hooks · 0 plugin MCP servers · 1 plugin LSP server

❯ ok, It's work well.

⏺ ╭─ 📚 English · IELTS Writing ──────────
  │ Band 估分： 这句较短，单独难评分，但有语法错误
  │ 亮点： 用了副词 "well" 修饰动词 ✓
  │ 扣分项： "It's work well" — it's = it is，后面不能接动词原形
  │ 高分改写： "It's working well." / "It works well."
  │ 可复用句式： It + works/is working + adverb — 描述功能正常运转
  │ 练习： "The system ___ well after the update." 填 works 还是 is working？
  ╰─────────────────────────────────────────

  ---
  一切正常！插件 0.4.1，IELTS 模式已生效，hook 也在正确注入双语配置。

  今天整个 language-coach 从 v0.2.0 进化到了 v0.4.1，功能完整，可以正式使用了。

```
