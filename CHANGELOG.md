# Changelog

All notable changes to this project are recorded here.

This file is updated by the release workflow via `scripts/build_changelog.py`.

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
