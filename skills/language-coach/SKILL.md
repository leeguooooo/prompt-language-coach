---
name: language-coach
description: Language coaching for every prompt. Use when the user runs /language-coach with any sub-command (setup, native, target, style, response, goal, mode, focus, band, level, status, off, on). Routes to the correct action based on the argument provided.
---

You are the `language-coach` command handler. Read the sub-command and run the matching repo-root CLI command.

Default platform: `claude`
The shared `/language-coach` flow writes Claude config by default. It does **not** write `~/.codex/language-coach.json` unless the user explicitly asks for Codex and you run every command with `--platform codex`.

All commands below assume the current working directory is the repository root:

```bash
python3 scripts/manage_language_coach.py --platform <claude|codex> ...
```

---

## Setup

Ask these questions one at a time:

1. `What is your native language? (for example: Chinese, Japanese, Spanish)`
2. `What language are you learning? (for example: English, French, German)`
3. `What is your main goal? (everyday / ielts)`
4. `Which coaching style do you want? (teaching / concise / translate)`
5. `Which response language should I use after coaching? (native / target)`

If the user chooses `ielts`, ask these follow-ups one at a time:

1. `Which IELTS mode do you want? (ielts-writing / ielts-speaking)`
2. `What IELTS focus should I store? (writing / speaking / both)`
3. `What target band are you aiming for? (optional)`
4. `What is your current level? (optional)`

Then run the matching commands in order:

```bash
python3 scripts/manage_language_coach.py --platform <platform> native "<native>"
python3 scripts/manage_language_coach.py --platform <platform> target "<target>"
python3 scripts/manage_language_coach.py --platform <platform> goal "<goal>"
python3 scripts/manage_language_coach.py --platform <platform> style "<style>"
python3 scripts/manage_language_coach.py --platform <platform> response "<response>"
```

For Codex users, set `<platform>` to `codex` on every command in the setup flow. Do not imply that the default shared setup writes Codex config unless you are explicitly running the Codex platform variant.

If `goal` is `ielts`, also run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> mode "<ielts-mode>"
python3 scripts/manage_language_coach.py --platform <platform> focus "<focus>"
python3 scripts/manage_language_coach.py --platform <platform> band "<target-band>"
python3 scripts/manage_language_coach.py --platform <platform> level "<current-level>"
```

Finish by running:

```bash
python3 scripts/manage_language_coach.py --platform <platform> status
```

Confirm with a short summary of the stored configuration.

---

## Sub-commands

### native <lang>

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> native "<lang>"
```

Confirm: `Native language updated to: <lang>`

### target <lang>

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> target "<lang>"
```

Confirm: `Target language updated to: <lang>`

### Multi-target management

Use these commands to manage the `targets` list for auto-detected coaching across multiple target languages:

#### target-add <lang>

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> target-add "<lang>"
```

This appends a new target profile using the current shared coaching settings as defaults.

#### target-remove <lang>

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> target-remove "<lang>"
```

This removes the matching target profile from the multi-target list.

#### target-list

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> target-list
```

Relay the printed target language list back to the user.

### style <mode>

Valid values: `teaching`, `concise`, `translate`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> style "<mode>"
```

Confirm: `Style updated to: <mode>`

### response <mode>

Valid values: `native`, `target`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> response "<mode>"
```

Confirm: `Responses will use: <mode>`

### goal <mode>

Valid values: `everyday`, `ielts`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> goal "<mode>"
```

Notes:
- `goal everyday` resets the active mode to `everyday`
- `goal ielts` keeps the shared config in IELTS mode

### mode <mode>

Valid values: `everyday`, `ielts-writing`, `ielts-speaking`, `review`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> mode "<mode>"
```

Notes:
- IELTS modes automatically set `goal` to `ielts`
- `mode everyday` switches `goal` back to `everyday`

### focus <mode>

Valid values: `writing`, `speaking`, `both`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> focus "<mode>"
```

### band <score>

Examples: `6.5`, `7.0`, `7.5`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> band "<score>"
```

### level <text>

Examples: `B1`, `band 5.5`, `upper-intermediate`

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> level "<text>"
```

### status

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> status
```

Relay the formatted output back to the user.

### off

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> off
```

Confirm: `Language coach paused.`

### on

Run:

```bash
python3 scripts/manage_language_coach.py --platform <platform> on
```

Confirm: `Language coach active.`

---

## Fallback Help

If no argument or the command is unknown, show:

```text
Usage: /language-coach <command>

Commands:
  setup              Run the setup wizard
  native <lang>      Set your native language
  target <lang>      Set the language you are learning
  target-add <lang>  Add a target language profile to the multi-target list
  target-remove <lang>
                     Remove a target language profile from the multi-target list
  target-list        List the configured multi-target languages
  style <mode>       Set coaching style: teaching / concise / translate
  response <mode>    Set response language: native / target
  goal <mode>        Set the coaching goal: everyday / ielts
  mode <mode>        Set the coaching mode: everyday / ielts-writing / ielts-speaking / review
  focus <mode>       Set IELTS focus: writing / speaking / both
  band <score>       Set IELTS target band
  level <text>       Set current level
  status             Show current configuration
  off                Pause coaching
  on                 Resume coaching
```
