# prompt-language-coach

A Claude Code plugin that provides real-time language coaching on every prompt. Configure your native language and target language once — from that point on, every message you write is automatically coached before Claude answers the actual request.

Designed for any language learner. Any language pair is supported through free configuration.

---

## Prerequisites

- **`jq`** — required for JSON parsing in the hook script.
  - macOS: `brew install jq`
  - Linux: `apt install jq`

---

## Installation

```bash
# 1. Add marketplace
/plugin marketplace add github:leeguooooo/prompt-language-coach

# 2. Install plugin
/plugin install prompt-language-coach@prompt-language-coach

# 3. Configure (runs a one-time setup wizard)
/language-coach setup
```

---

## Commands

| Command | Description |
|---|---|
| `/language-coach setup` | Interactive wizard to configure native language, target language, style, and response language |
| `/language-coach native <lang>` | Update your native language (e.g. `Chinese`, `Japanese`) |
| `/language-coach target <lang>` | Update the language you are learning (e.g. `English`, `French`) |
| `/language-coach style <mode>` | Set coaching style: `teaching`, `concise`, or `translate` |
| `/language-coach response <mode>` | Set response language: `native` or `target` |
| `/language-coach status` | Show current configuration |
| `/language-coach off` | Pause coaching (config preserved) |
| `/language-coach on` | Resume coaching |

---

## Configuration

Config is stored at `~/.claude/language-coach.json`:

```json
{
  "native": "zh",
  "target": "en",
  "style": "teaching",
  "enabled": true,
  "responseLanguage": "native"
}
```

| Field | Values | Default | Description |
|---|---|---|---|
| `native` | any language name | `"zh"` | Your native language |
| `target` | any language name | `"en"` | Language you are learning |
| `style` | `teaching` / `concise` / `translate` | `"teaching"` | Output verbosity |
| `enabled` | `true` / `false` | `true` | Toggle coaching on/off without losing config |
| `responseLanguage` | `native` / `target` | `"native"` | Language Claude uses when answering the actual request |

---

## Coaching styles

- **teaching** — shows error reasons, corrected version, and a more natural native-like version
- **concise** — corrected version and natural version only, no explanations
- **translate** — just gives the target language version of what you wrote

---

## How it works

Every time you send a message, the `UserPromptSubmit` hook fires and runs `language-coach.sh`. The script reads your config and injects coaching instructions into Claude's context for that turn. Claude coaches your writing first, then answers your actual request.

The hook exits silently (no coaching, no crash) when:
- `jq` is not installed
- The config file does not exist yet
- `enabled` is set to `false`

---

## Example output

**When you write in your target language:**

```
**English correction:**
> [your original sentence]

Key issues:
- [mistake 1]
- [mistake 2]

Corrected: "[fixed version]"
More natural: "[native-like version]"
```

**When you write fully in your native language:**

```
**Natural English version:**
> [one concise, natural target-language version]
```

---

## Author

[leeguooooo](https://github.com/leeguooooo)
