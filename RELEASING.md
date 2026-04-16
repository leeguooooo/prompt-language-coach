# Releasing Prompt Language Coach

This repository ships one product across three first-class plugin surfaces:

- Codex
- Claude Code
- Cursor

The release source of truth is:

1. per-platform `plugin.json` versions
2. the git tag
3. the GitHub Release

Claude marketplace sync is a downstream step. It is not the canonical release record.

## What gets versioned

These files must always stay on the same version:

- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`

## Standard release flow

Use the GitHub Actions `Release` workflow.

1. Open `Actions` -> `Release`
2. Click `Run workflow`
3. Enter the new version, for example `0.9.0`

The workflow will:

1. run the full unittest verification suite
2. bump all three plugin manifests with `scripts/bump_version.py`
3. update `CHANGELOG.md` with `scripts/build_changelog.py`
4. commit the version bump and changelog
5. create tag `v<version>`
6. push the branch and tag
7. create a GitHub Release
8. notify the Claude marketplace repo if `PLUGINS_REPO_TOKEN` is configured

## Why Codex updates work this way

As of 2026-04-16, this repo does not depend on a public Codex-specific publish API.

Instead, Codex updates are distributed through the same canonical release artifacts as the other platforms:

- updated `.codex-plugin/plugin.json`
- tagged git history
- GitHub Release metadata

That keeps the update lane stable even if Codex distribution mechanics change later.

## Local dry run

Before triggering a release, you can run the same verification locally:

```bash
python3 -m unittest \
  tests.shared.test_config_io \
  tests.shared.test_prompt_builder \
  tests.hooks.test_claude_hook_output \
  tests.hooks.test_codex_hook_install \
  tests.scripts.test_analyze_progress \
  tests.scripts.test_build_changelog \
  tests.scripts.test_bump_version \
  tests.scripts.test_manage_language_coach \
  -v
```

You can also preview the version bump and changelog generation locally:

```bash
python3 scripts/bump_version.py 0.9.0
python3 scripts/build_changelog.py 0.9.0
```

Review the diff before committing.

## Release responsibilities

### Codex

- version comes from `.codex-plugin/plugin.json`
- changelog is inherited from the repo release
- no separate publish token is required in this repo today

### Claude Code

- version comes from `.claude-plugin/plugin.json`
- optional marketplace sync uses `PLUGINS_REPO_TOKEN`

### Cursor

- version comes from `.cursor-plugin/plugin.json`
- distributed through the same tagged repo release flow

## If the marketplace sync fails

The GitHub release is still valid.

Codex, Cursor, and the source repo stay correctly versioned. Only the downstream Claude marketplace sync needs a retry.
