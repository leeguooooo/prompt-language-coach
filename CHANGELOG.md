# Changelog

All notable changes to this project are recorded here.

This file is updated by the release workflow via `scripts/build_changelog.py`.

## v0.12.2 - 2026-04-18

### Fixes
- **[HIGH] English scored targets in multi-target mode reported the wrong
  scoring scale.** `_target_summary` / `_target_body` passed the display
  placeholder `"{DetectedLanguage}"` into `scale_for_language()`, which fell
  back to CEFR because the placeholder is not a known language. Result: an
  English `scored-writing` target with `targetEstimate=7.0` rendered
  `Scoring scale: CEFR.` instead of `IELTS.`, and the scoring guidance lines
  came from CEFR instead of IELTS, biasing the estimate. Scale / guidance /
  sections now resolve from the configured `target["targetLanguage"]`; only
  the box title keeps the `{DetectedLanguage}` placeholder for Claude to
  substitute at runtime.
- **[MEDIUM] `target <lang>` was misleading in multi-target mode.** It only
  updated top-level `targetLanguage`, which `build_static_prompt` ignores
  when `targets[]` is non-empty, so users saw `Target language updated to:
  Korean` yet coaching continued against the previous profiles. The command
  now (a) promotes the matching profile to primary when `<lang>` is already
  in `targets[]`, and (b) explicitly states that it only updated the
  fallback language and suggests `target-add <lang>` when it is not. README
  and skill docs updated to describe the real behavior.

## v0.12.1 - 2026-04-18

### Fixes
- **[CRITICAL] Cursor hook crashed silently on Windows**. `print(json.dumps(…,
  ensure_ascii=False))` raised `UnicodeEncodeError: 'gbk' codec can't encode
  character '\U0001f4da'` when PowerShell's default stdout encoding (GBK/cp936)
  met the 📚 emoji in our coaching box title. Hooks showed `installed` and
  status `on`, but `additional_context` never reached Cursor so the coaching
  block did not appear. `scripts/render_coaching_context.py` now
  `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at import time
  so every platform writes valid UTF-8 JSON regardless of the console locale.
- **[HIGH] `mode` / `style` / `goal` commands had no visible effect for
  multi-target users.** `defaults.json` seeded `targets` with hardcoded
  `goal=everyday, mode=everyday, style=teaching`, and `build_static_prompt`
  preferred the `targets` list over top-level fields, so a user running
  `mode scored-writing` saw the saved config change but the generated coaching
  prompt stayed on everyday/teaching. `apply_command` now propagates
  `mode`/`style`/`goal`/`response`/`estimate`/`focus`/`level`/`vocab` changes
  to every entry in `targets`, and `defaults.json` no longer pre-seeds
  hardcoded per-target fields.
- **[HIGH] Cross-platform config changes did not refresh Claude static
  prompt.** `sync_claude_md` was gated on `platform == "claude"`, so a
  `mode scored-writing` invocation from Codex or Cursor synced the JSON
  config files but left `~/.prompt-language-coach/claude-coaching.md` and the
  `@`-import in `~/.claude/CLAUDE.md` stale. It now fires whenever
  `~/.claude/` exists, matching the platform-agnostic behavior of
  `sync_codex_agents_md`.
- **[MEDIUM] Same-day `track-estimate` calls collapsed to a single session.**
  `cmd_record_estimate` explicitly overwrote any prior entry with the same
  date, and `_merge_estimates` keyed by `date` alone, so 5 distinct sessions
  recorded in one day showed up as 1. Records now carry a `timestamp` field
  (seconds precision) and always append; merges dedupe by
  `(timestamp, estimate, text)` so bit-identical cross-platform writes still
  collapse but distinct sessions on the same day are preserved.
- **[MEDIUM] `pytest -q` failed at collection** with `ModuleNotFoundError: No
  module named 'platforms'`. A repo-root `conftest.py` now inserts the repo
  root into `sys.path` so both `pytest` and `python3 -m pytest` work.

## v0.12.0 - 2026-04-18

### Improvements
- **Cut coaching overhead by ~60%** through prompt deduplication and
  sharing. On Claude Code, the per-turn cost dropped from ~2,477 tokens
  (when both CLAUDE.md and the hook injected the same ~1,200-token
  static block) to ~754 tokens for the static part — and the hook
  itself now only emits the dynamic progress note (~25 tokens).
- `build_static_prompt` no longer repeats the Triviality filter,
  IMPORTANT compaction reminder, or Box framing three times in
  multi-target mode. When every configured target produces the same
  body (guidance/sections/box framing), the body is emitted once as a
  "Shared coaching body" block instead of per-target.
- `sync_claude_md` now writes the coaching text to
  `~/.prompt-language-coach/claude-coaching.md` and references it in
  `~/.claude/CLAUDE.md` via a single `@`-import line inside the marker
  block. User's CLAUDE.md stays clean (3 lines instead of ~40);
  approve the import once on first run and it Just Works.

### Internal
- `_target_body` factored out of `_target_summary` so the guidance /
  sections / box framing lines can be compared across targets and
  shared when identical.
- `sync_claude_md` removes the external `claude-coaching.md` when the
  user disables coaching (so uninstall leaves no orphan files).

## v0.11.5 - 2026-04-17

### Fixes
- Config is now always read from and written to the shared
  `~/.prompt-language-coach/language-coach.json` regardless of which
  platform (`claude`, `codex`, `cursor`) invokes the CLI. Per-platform
  mirrors (`~/.claude/`, `~/.codex/`, `~/.cursor/`) continue to be
  written on every save for backward compatibility. First-time startup
  automatically migrates any existing per-platform config to the shared
  location so no manual action is required.

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
