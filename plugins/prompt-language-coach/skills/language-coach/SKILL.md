---
name: language-coach
description: Language coaching for every prompt. Use when the user runs /language-coach with any sub-command (setup, native, target, style, response, goal, mode, focus, band, level, status, off, on). Routes to the correct action based on the argument provided.
---

You are the `language-coach` command handler. Read the sub-command and run the matching bundled CLI command.

Default platform: use the current host platform.

- In Codex, use `--platform codex`
- In Claude Code, use `--platform claude`
- In Cursor, use `--platform cursor`

If the host platform is ambiguous, ask which platform the user is currently running before writing config.

Resolve the script path relative to this skill directory:

- Skill path: `skills/language-coach/SKILL.md`
- Bundled CLI path: `../../scripts/manage_language_coach.py`

All commands below should call that bundled script path directly:

```bash
python3 ../../scripts/manage_language_coach.py --platform <claude|codex|cursor> ...
```

---

## Setup

Ask these questions one at a time:

1. `What is your native language? (for example: Chinese, Japanese, Spanish)`
2. `What language are you learning? (for example: English, French, German)`
3. `What is your main goal? (everyday / scored)`
4. `Which coaching style do you want? (teaching / concise / translate)`
5. `Which response language should I use after coaching? (native / target)`

If the user chooses `scored`, ask these follow-ups one at a time:

1. `Which scored mode do you want? (scored-writing / scored-speaking)`
2. `What scoring focus should I store? (writing / speaking / both)`
3. `What target estimate are you aiming for? (optional)`
4. `What is your current level? (optional)`

Then run the matching commands in order:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> native "<native>"
python3 ../../scripts/manage_language_coach.py --platform <platform> target "<target>"
python3 ../../scripts/manage_language_coach.py --platform <platform> goal "<goal>"
python3 ../../scripts/manage_language_coach.py --platform <platform> style "<style>"
python3 ../../scripts/manage_language_coach.py --platform <platform> response "<response>"
```

For Codex users, set `<platform>` to `codex` on every command in the setup flow.
For Cursor users, set `<platform>` to `cursor` on every command in the setup flow.
Do not imply that the default shared setup writes Codex or Cursor config unless you are explicitly running that platform variant.

If `goal` is `scored`, also run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> mode "<scored-mode>"
python3 ../../scripts/manage_language_coach.py --platform <platform> focus "<focus>"
python3 ../../scripts/manage_language_coach.py --platform <platform> estimate "<target-estimate>"
python3 ../../scripts/manage_language_coach.py --platform <platform> level "<current-level>"
```

Finish by running:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> status
```

For Codex users, also run:

```bash
python3 ../../scripts/manage_language_coach.py --platform codex install-hook
python3 ../../scripts/manage_language_coach.py --platform codex status
```

For Cursor users, also run:

```bash
python3 ../../scripts/manage_language_coach.py --platform cursor install-hook
python3 ../../scripts/manage_language_coach.py --platform cursor status
```

The Cursor ``install-hook`` writes to ``~/.cursor/hooks.json`` (the top-level location). Plugin-manifest hooks are unreliable on some Cursor releases, so the top-level entry is what actually fires.

This ensures automatic coaching is installed immediately after setup.

Confirm with a short summary of the stored configuration.

---

## Sub-commands

### native <lang>

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> native "<lang>"
```

Confirm: `Native language updated to: <lang>`

### target <lang>

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> target "<lang>"
```

Confirm: `Target language updated to: <lang>`

### Multi-target management

Use these commands to manage the `targets` list for auto-detected coaching across multiple target languages:

#### target-add <lang>

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> target-add "<lang>"
```

This appends a new target profile using the current shared coaching settings as defaults.

#### target-remove <lang>

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> target-remove "<lang>"
```

This removes the matching target profile from the multi-target list.

#### target-list

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> target-list
```

Relay the printed target language list back to the user.

### style <mode>

Valid values: `teaching`, `concise`, `translate`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> style "<mode>"
```

Confirm: `Style updated to: <mode>`

### response <mode>

Valid values: `native`, `target`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> response "<mode>"
```

Confirm: `Responses will use: <mode>`

### goal <mode>

Valid values: `everyday`, `scored`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> goal "<mode>"
```

Notes:
- `goal everyday` resets the active mode to `everyday`
- `goal scored` keeps the shared config in scored mode

### mode <mode>

Valid values: `everyday`, `scored-writing`, `scored-speaking`, `review`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> mode "<mode>"
```

Notes:
- scored modes automatically set `goal` to `scored`
- `mode everyday` switches `goal` back to `everyday`

### practice-focus <mode>

Valid values: `writing`, `speaking`, `both`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> practice-focus "<mode>"
```

`focus` remains available as a legacy alias.

### estimate <value>

Examples: `6.5`, `N3`, `B1`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> estimate "<value>"
```

### level <text>

Examples: `B1`, `band 5.5`, `upper-intermediate`

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> level "<text>"
```

### status

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> status
```

Relay the formatted output back to the user.

### install-hook

Codex or Cursor. Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform codex install-hook
# or
python3 ../../scripts/manage_language_coach.py --platform cursor install-hook
```

Confirm: `Codex hook installed: <path>` or `Cursor hook installed: <path>`

### remove-hook

Codex or Cursor. Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform codex remove-hook
# or
python3 ../../scripts/manage_language_coach.py --platform cursor remove-hook
```

Confirm: `Codex hook removed: <path>` or `Cursor hook removed: <path>`

### hook-status

Codex or Cursor. Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform codex hook-status
# or
python3 ../../scripts/manage_language_coach.py --platform cursor hook-status
```

Relay `installed` or `not installed` back to the user.

### progress [language]

Show raw estimate history for all languages (or a single language).

Run:

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> progress
# or for a specific language:
python3 ../../scripts/manage_language_coach.py --platform <platform> progress "<language>"
```

Relay the output back to the user. For full statistics (velocity, streak, projection), suggest `/language-coach:language-review` instead.

### vocab on | off

Toggle the vocab focus feature (tracks gap / correction / upgrade words that need practice). Only active when mode is `scored-writing` or `scored-speaking`.

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> vocab on
# or
python3 ../../scripts/manage_language_coach.py --platform <platform> vocab off
```

Confirm: `Vocab focus enabled.` or `Vocab focus disabled.`

### vocab [language]

Show the current active vocab focus list (and the most recent mastered entries).

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> vocab
# or for a specific language:
python3 ../../scripts/manage_language_coach.py --platform <platform> vocab "<language>"
```

Relay the printed output back to the user.

### track-vocab <language> gap|correction|upgrade ...

Silently invoked by the coaching prompt when vocabFocus is on. Users do not typically run this directly — the model calls it after each coaching turn. Signatures:

```bash
# native-language fallback inside a target-language message (strongest signal)
python3 ../../scripts/manage_language_coach.py --platform <platform> track-vocab <lang> gap \
  --native "<native-word>" --target "<target-word>" [--context "<C>"] [--note "<N>"]

# user wrote a wrong target-language word that coaching corrected
python3 ../../scripts/manage_language_coach.py --platform <platform> track-vocab <lang> correction \
  --wrong "<wrong>" --right "<right>" [--context "<C>"] [--note "<N>"]

# user wrote a low-band target-language word that coaching upgraded (mixed-language messages only)
python3 ../../scripts/manage_language_coach.py --platform <platform> track-vocab <lang> upgrade \
  --from "<from>" --to "<to>" [--context "<C>"] [--note "<N>"]
```

### mark-vocab-mastered <language> <identifier>

Silently invoked by the coaching prompt when a focus entry is used correctly in the current message. Three correct uses promote the entry into the mastered audit list.

```bash
python3 ../../scripts/manage_language_coach.py --platform <platform> mark-vocab-mastered <lang> "<identifier>"
```

`<identifier>` is the `target` / `right` / `to` field of the original focus entry.

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
  goal <mode>        Set the coaching goal: everyday / scored
  mode <mode>        Set the coaching mode: everyday / scored-writing / scored-speaking / review
  practice-focus <mode>
                     Set scoring focus: writing / speaking / both
  focus <mode>       Legacy alias for practice-focus
  estimate <value>   Set target estimate
  band <score>       Legacy alias for estimate
  level <text>       Set current level
  status             Show current configuration
  progress [lang]    Show raw estimate history (use /language-coach:language-review for full stats)
  vocab on|off       Toggle vocab focus tracking (scored modes only)
  vocab [lang]       Show active vocab focus list
  install-hook       Install the Codex UserPromptSubmit hook
  remove-hook        Remove the Codex UserPromptSubmit hook
  hook-status        Show whether the Codex hook is installed
  off                Pause coaching
  on                 Resume coaching

See also: /language-coach:language-review  — analyze your progress data with stats and AI commentary
```
