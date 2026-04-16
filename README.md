# prompt-language-coach

> [English](README.md) | [中文](README.zh-CN.md)

> An always-on language coach for AI editors — improve any target language while you work in Codex, Claude Code, or Cursor.

[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-green)](https://github.com/leeguooooo/prompt-language-coach)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://github.com/leeguooooo/prompt-language-coach)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-Plugin-black)](https://github.com/leeguooooo/prompt-language-coach)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---
<img width="1662" height="894" alt="image" src="https://github.com/user-attachments/assets/1d0dfab7-f1d0-47cb-a7b3-5737bab14346" />

## What it does

Prompt Language Coach works natively in **Codex**, **Claude Code**, and **Cursor**.

Every message you send is coached **before** the real model answer:

- Writing in your target language? → Get grammar fixes + natural native-like expressions
- Writing in your native language? → Get one clean, natural target-language version
- Mixed? → Get a complete natural version of the whole meaning

The coaching core supports:

- `everyday`
- `scored-writing`
- `scored-speaking`
- `review`

Works for **any language pair**: Chinese → English, Japanese → English, Spanish → French, etc.

Why people install it:

- **Always-on coaching** — every prompt becomes a language practice rep
- **Any language pair** — not limited to English learners
- **IELTS depth when needed** — switch from lightweight correction to exam-oriented practice

| Platform | Native integration | Status |
| --- | --- | --- |
| Codex | `.codex-plugin` + `UserPromptSubmit` hook | First-class |
| Claude Code | `.claude-plugin` + `UserPromptSubmit` hook | First-class |
| Cursor | `.cursor-plugin` / rule-based session integration | First-class |

---

## Demo

Every message you send gets coached **before** the assistant answers. The coaching appears in a visual box so it never blends with the actual answer.

**Everyday mode** — you write:
> "I want to know how can i to fix this bug in my code"

**The assistant coaches first, then answers:**
```
╭─ 📚 English Coaching ─────────────────────
│ 原文：   "I want to know how can i to fix this bug"
│ 纠正：   "I want to know how I can fix this bug"
│ 更自然： "How do I fix this bug?" / "Can you help me debug this?"
│ 关键点： modal verb + bare infinitive — "can fix", not "can to fix"
╰────────────────────────────────────────────

(Claude's actual answer follows here)
```

**Scored Writing mode** — you write:
> "The environment is very important and we should protect it because many reason."

**The assistant coaches:**
```
╭─ 📚 English · Scored Writing ─────────────
│ Estimate：   5.0–5.5
│ 亮点：       主题明确，有因果逻辑意识
│ 扣分项：     "many reason" → "many reasons"；论点空洞，缺乏具体论据
│ 高分改写：   "Environmental protection is critical, as unchecked
│              pollution threatens biodiversity and public health."
│ 可复用句式： "[Topic] is critical, as [specific consequence]."
│ 练习：       用上面句式写一句关于 education 的句子
╰────────────────────────────────────────────

(Claude's actual answer follows here)
```

---

## Installation

### Codex

**Prerequisites:** `python3`

Add the repository as a Codex marketplace source:

```bash
codex marketplace add leeguooooo/prompt-language-coach
```

Then:

1. Restart Codex
2. Open the plugin directory and install **Prompt Language Coach**
3. Run `/language-coach setup`

The setup flow writes `~/.codex/language-coach.json` and installs the Codex `UserPromptSubmit` hook automatically.

### Claude Code

**Prerequisites:** `python3`

```
/plugin marketplace add leeguooooo/plugins
/plugin install language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

### Cursor

**Prerequisites:** `python3`

Install from the Cursor plugin marketplace, or add the marketplace repo directly:

1. Open **Cursor Settings → Plugins → Marketplace**
2. Add marketplace: `leeguooooo/plugins`
3. Install **language-coach**

Then run the setup command in Cursor's AI panel:

```
/language-coach setup
```

The setup wizard asks your native language, target language, goal, style, and response language — same as Claude Code — and stores config at `~/.cursor/language-coach.json`.

---

## Setup and usage

### Codex setup

Run `/language-coach setup` and answer the onboarding questions.

On Codex, the setup flow also installs the automatic `UserPromptSubmit` hook so coaching starts on every prompt right away. Your Codex config is stored at `~/.codex/language-coach.json`.

### Claude Code setup

Run `/language-coach:language-coach setup` and answer the onboarding questions:

1. What is your native language?
2. What language are you learning?
3. What is your main goal? (`everyday` / `scored`)
4. Which coaching style? (`teaching` / `concise` / `translate`)
5. Which response language should be used after coaching? (`native` / `target`)

If you choose `scored`, the setup flow also stores:

1. Active scored mode: `scored-writing` or `scored-speaking`
2. Scoring focus: `writing`, `speaking`, or `both`
3. Target estimate
4. Current level

After setup, Claude coaching activates automatically on every prompt.

---

## Commands

On **Codex** and **Cursor**, use `/language-coach ...`.

On **Claude Code**, use `/language-coach:language-coach ...`.

| Command | Description |
|---|---|
| `/language-coach setup` | One-time interactive setup wizard |
| `/language-coach native <lang>` | Change your native language |
| `/language-coach target <lang>` | Change the language you are learning |
| `/language-coach style <mode>` | Switch coaching style: `teaching`, `concise`, `translate` |
| `/language-coach response <mode>` | Switch response language: `native` or `target` |
| `/language-coach goal <mode>` | Switch learning goal: `everyday` or `scored` |
| `/language-coach mode <mode>` | Switch coaching mode: `everyday`, `scored-writing`, `scored-speaking`, or `review` |
| `/language-coach practice-focus <mode>` | Set scoring focus: `writing`, `speaking`, or `both` |
| `/language-coach focus <mode>` | Legacy alias for `practice-focus` |
| `/language-coach estimate <value>` | Store your target estimate |
| `/language-coach band <score>` | Legacy alias for `estimate` |
| `/language-coach level <text>` | Store your current level |
| `/language-coach status` | Show current config |
| `/language-coach off` | Pause coaching (config preserved) |
| `/language-coach on` | Resume coaching |
| `/language-coach progress` | Show estimate history for all languages |
| `/language-coach progress <lang>` | Show estimate history for a specific language |

---

## Modes

| Mode | What you get |
|---|---|
| `everyday` | Compact coaching with `Your original`, `Corrected`, `More natural`, and `1 key takeaway` |
| `scored-writing` | Score-oriented writing feedback using the target language's best-fit scale, with estimate, problems, rewrite, reusable pattern, and drill |
| `scored-speaking` | Score-oriented spoken-naturalness feedback from text with fluency, lexical, grammar, pattern, and drill guidance |
| `review` | Compact review summary of recurring mistakes, reusable patterns, and the next drill |

## Progress tracking

Estimates are automatically recorded to the shared progress file (`~/.prompt-language-coach/language-progress.json`) and mirrored to the legacy platform-specific files whenever:

1. The active mode is `scored-writing` or `scored-speaking`
2. The user wrote in a target language (not purely in the native language)
3. Claude gives a scale estimate in the coaching box

Progress is stored permanently and never deleted. Use `/language-coach:language-coach progress` to see your history:

```
English progress (last 5 sessions):
  2026-04-13  5.5
  2026-04-14  5.5
  2026-04-15  6.0
Current estimate: 6.0
```

If you also use [Claude Status Bar](https://github.com/leeguooooo/claude-code-usage-bar), the current estimate and trend appear automatically in the status bar (`📚 EN:6.0↑`), and the pet reacts to your coaching activity.

---

## Coaching styles

| Style | What it changes |
|---|---|
| `teaching` | Explanatory coaching with reasons and upgrade guidance |
| `concise` | Shorter correction-focused coaching |
| `translate` | Target-language-first coaching with minimal explanation |

---

## Configuration

Config is stored in the platform-specific config file:

- Codex: `~/.codex/language-coach.json`
- Claude Code: `~/.claude/language-coach.json`
- Cursor: `~/.cursor/language-coach.json`

The normalized JSON schema:

```json
{
  "nativeLanguage": "Chinese",
  "targetLanguage": "English",
  "goal": "scored",
  "mode": "scored-writing",
  "style": "teaching",
  "responseLanguage": "target",
  "enabled": true,
  "scoringFocus": "writing",
  "targetEstimate": "7.0",
  "currentLevel": "6.0",
  "version": 1
}
```

| Field | Values | Default | Description |
|---|---|---|---|
| `nativeLanguage` | any language name | `"Chinese"` | Your native language |
| `targetLanguage` | any language name | `"English"` | Language you are learning |
| `goal` | `everyday` / `scored` | `"everyday"` | Top-level learning goal |
| `mode` | `everyday` / `scored-writing` / `scored-speaking` / `review` | `"everyday"` | Active coaching mode |
| `style` | `teaching` / `concise` / `translate` | `"teaching"` | Output verbosity |
| `responseLanguage` | `native` / `target` | `"native"` | Language used after coaching |
| `enabled` | `true` / `false` | `true` | Toggle on/off without losing config |
| `scoringFocus` | `writing` / `speaking` / `both` | `"both"` | Stored scored-mode emphasis |
| `targetEstimate` | free text | `""` | Target estimate on the active language scale |
| `currentLevel` | free text | `""` | Current estimated level |
| `version` | integer | `1` | Schema version |

Legacy `native` / `target` keys are automatically normalized into the current schema on load.

---

## How it works

Codex, Claude Code, and Cursor all render coaching through the shared Python core:

1. `shared/config/` loads and normalizes platform config
2. `shared/pedagogy/modes.py` selects the feedback shape for the active mode
3. `shared/prompts/build_prompt.py` builds the coaching instruction text
4. `scripts/render_coaching_context.py` emits the hook JSON payload

**Codex** uses `.codex-plugin/plugin.json` plus `platforms/codex/hook_entry.py` — coaching fires on every prompt through a Codex `UserPromptSubmit` hook.

**Claude Code** uses a `UserPromptSubmit` hook (`hooks/language-coach.sh`) — coaching fires on every prompt via `hookSpecificOutput.additionalContext`.

**Cursor** uses a `sessionStart` hook (`hooks/cursor-language-coach.sh`) — coaching context is injected once at session start via `additional_context`.

All integrations exit silently — no coaching, no crash — when:

- `python3` is not installed
- The platform config file does not exist yet (`~/.codex/language-coach.json`, `~/.claude/language-coach.json`, or `~/.cursor/language-coach.json`)
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

## Manual install

### Codex

You can also use a local checkout as a Codex marketplace source:

```bash
codex marketplace add .
```

Then run:

```bash
/language-coach setup
```

After restarting Codex, install the plugin from the plugin directory. The setup flow writes `~/.codex/language-coach.json` and installs the Codex `UserPromptSubmit` hook in `~/.codex/hooks.json`.

### Claude Code

Clone the repo and add the hook to your `~/.claude/settings.json`:

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

### Cursor

Clone the repo. Cursor picks up the plugin automatically from `.cursor-plugin/plugin.json` if the repo is placed in `~/.cursor/plugins/local/language-coach`. The hook reads config from `~/.cursor/language-coach.json`.

Run setup from the Cursor AI panel:

```
/language-coach setup
```

---

## Contributing

PRs welcome. If you want to add a new coaching style, improve the prompt, or add a new command — open an issue first to discuss.

---

## Author

Built by [leeguooooo](https://github.com/leeguooooo) — a senior frontend engineer using this plugin daily while preparing for the Australian job market.

---

## Real-world walkthrough

This walkthrough uses the Claude Code command surface, but the coaching model and stored config concepts are the same on Codex and Cursor.

A complete example: Chinese high school student learning both English and Japanese in scored mode (target estimate 6.5).

### 1. Install and run setup

```
/plugin marketplace add leeguooooo/plugins
/plugin install language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

The wizard asks one question at a time:

```
What is your native language?          → Chinese
What language are you learning?        → english, japanese
What is your main goal?                → scored
Which scored mode?                     → scored-writing and scored-speaking
Target estimate?                       → 6.5
Current level?                         → 高中生水平
Coaching style?                        → teaching
Response language after coaching?      → native
```

Final config stored at `~/.claude/language-coach.json`:

| Field | Value |
|---|---|
| Native language | Chinese |
| Target languages | English + Japanese (auto-detected) |
| Goal | scored |
| Mode | Scored Writing |
| Style | Teaching (detailed) |
| Response language | Chinese (native) |
| Target estimate | 6.5 |
| Current level | 高中生水平 |

### 2. Reload and write

```
/reload-plugins
```

From now on every message is coached automatically. The coaching box appears **before** Claude's actual answer, clearly separated.

**Writing English with a grammar error:**

User types: `"ok, It's work well."`

```
╭─ 📚 English · Scored Writing ─────────────
│ Estimate：   这句较短，但有语法错误
│ 亮点：       用了副词 "well" 修饰动词 ✓
│ 扣分项：     "It's work well" — it's = it is，后面不能接动词原形
│ 高分改写：   "It works well." / "It's working well."
│ 可复用句式： It + works / is working + adverb — 描述某物正常运转
│ 练习：       "The system ___ well after the update." — works 还是 is working？
╰─────────────────────────────────────────────

（Claude 的实际回答在这里，无边框）
```

**Writing Japanese** triggers the same structure with a Japanese-specific header:

```
╭─ 📚 Japanese · Scored Writing ────────────
│ ...
╰─────────────────────────────────────────────
```

Switch mode anytime:

```
/language-coach:language-coach mode everyday       # back to everyday coaching
/language-coach:language-coach mode scored-writing  # back to scored writing
/language-coach:language-coach status              # show current config
```

---

## Related

- [Claude Status Bar](https://github.com/leeguooooo/claude-code-usage-bar) — shows your current language estimate progress (`📚 EN:6.0↑`) alongside Claude rate-limit and context usage in the status bar. Reads the mirrored progress file written by this plugin.
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code hooks guide](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code plugin marketplace](https://docs.anthropic.com/en/docs/claude-code/plugins)
