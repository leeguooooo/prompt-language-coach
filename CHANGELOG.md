# Changelog

All notable changes to this project are recorded here.

This file is updated by the release workflow via `scripts/build_changelog.py`.

## v0.11.4 - 2026-04-17

### Fixes
- `analyze_progress` was dropping history entries whose recorded
  estimate did not parse under the language's declared scale (e.g.
  `B1` in an English file marked `scale=ielts`), so a user with 3
  recorded sessions across 3 different days saw `1 session over 1
  day` and all but one entry vanished from the history list. Session
  and practice-day counts now include every dated, non-garbage
  estimate (parseable under any known scale); slope/momentum still
  only consume entries that parse cleanly under the declared scale,
  so cross-scale mixing never corrupts the velocity math.

## v0.11.3 - 2026-04-17

### Fixes
- Make the Cursor installer cross-platform. On Windows,
  `bash "${CURSOR_PLUGIN_ROOT}/hooks/cursor-language-coach.sh"`
  resolves to `C:\Windows\System32\bash.exe` (WSL), which cannot read
  Windows paths from the `.sh` wrapper — so the hook never fired and
  `hook-status` always said `not installed`. The installer now detects
  Windows and writes a direct `python render_coaching_context.py
  --platform cursor` command with absolute paths instead. POSIX
  behavior is unchanged.
- `is_managed_entry` now recognizes both the POSIX bash wrapper and
  the Windows Python-direct command as managed, so
  install/remove/idempotency hold on both operating systems.

## v0.11.2 - 2026-04-17

### Fixes
- Skip the full coaching box for trivial inputs. One-word target-language
  messages like `English` or `ok` used to produce a four-section box
  that just repeated the same word back — now the coach passes them
  through without ceremony unless there is an actual error, native
  fallback, or meaningful upgrade.

## v0.11.1 - 2026-04-17

### Fixes
- Teach the `language-coach` skill to dispatch the new vocab commands
  (`vocab on|off`, `vocab [<lang>]`, `track-vocab`, `mark-vocab-mastered`).
  The 0.11.0 release added the underlying CLI but not the skill routing,
  so `/language-coach:language-coach vocab on` fell through to the
  fallback help text.

## v0.11.0 - 2026-04-17

### Features
- Add `vocab focus` tracking for scored coaching modes. The coach can now
  persist `gap`, `correction`, and `upgrade` vocab entries in
  `~/.prompt-language-coach/vocab-focus.json`, mirror the snapshot to
  Claude/Codex/Cursor homes, and advance entries into a mastered audit
  list after three correct uses.
- Add CLI support for `track-vocab`, `mark-vocab-mastered`, `vocab
  <language>`, and `vocab on|off`, alongside the new `vocabFocus`
  config flag.

### Internal
- Prompt construction now injects compact vocab tracking and recall rules
  only when `vocabFocus=true` and the mode is `scored-writing` or
  `scored-speaking`, and only then loads recent active vocab entries into
  coaching context.
- Extend tests to cover vocab mirroring, active-entry capping, mastery
  promotion, config normalization, and prompt gating.

## v0.10.0 - 2026-04-17

### Fixes
- Install the Cursor `sessionStart` hook into `~/.cursor/hooks.json`
  (the "top-level" location) instead of relying on the plugin manifest's
  `hooks` field. Plugin-manifest hooks are reported unreliable on current
  Cursor releases — `${CURSOR_PLUGIN_ROOT}` does not always expand and
  the manifest is not always reloaded after edits. The setup flow and
  `manage_language_coach.py --platform cursor install-hook` now both
  write a managed entry to the top-level hooks file with an absolute
  path, and the original plugin-manifest wiring stays in place as a
  backup.
- `scripts/sync_plugin_bundle.py` mirrors `scripts/`, `shared/`,
  `platforms/`, and `skills/` into `plugins/prompt-language-coach/`
  before every release so marketplace installs never ship stale code
  behind a bumped version. `bump_version.py` calls it automatically.

### Internal
- New `platforms/cursor/install_hooks.py` mirrors the Codex installer:
  idempotent upsert, preserves unrelated entries in the shared
  `hooks.json`, and removes only the managed entry on uninstall.
- `manage_language_coach.py` now handles `--platform cursor
  install-hook / remove-hook / hook-status` alongside Codex.

## v0.9.0 - 2026-04-17

### Fixes
- Stop flooding the Codex transcript with coaching instructions every turn.
  Codex renders `UserPromptSubmit` hook `additionalContext` as a visible
  "hook context:" cell and ignores `suppressOutput`, so the 2KB teaching
  prompt was being shown to the user on every prompt. The static coaching
  rules now live in a marker-bounded block inside `~/.codex/AGENTS.md`,
  which Codex loads silently as ambient instructions. The per-turn hook
  emits only the small dynamic progress note.

### Internal
- New `shared/codex/agents_md.py` manages the marker block with atomic
  writes, a one-time backup on first edit, and idempotent short-circuit
  when the rendered content is unchanged.
- `build_prompt` split into `build_static_prompt` + `build_progress_note`
  so each platform can wire them up differently.
- `install_codex_plugin.py` now seeds `~/.codex/AGENTS.md` on install;
  `manage_language_coach.py remove-hook` and `off` clear the block.
