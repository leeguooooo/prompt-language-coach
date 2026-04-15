# Prompt Language Coach Dual-Platform Design

## Goal

Evolve `prompt-language-coach` from a Claude-first plugin into a shared language-coaching product that supports Claude and Codex as first-class runtime surfaces while keeping Cursor available as a lighter rule-based option.

The product should feel easy to adopt, stay on by default in day-to-day usage, and teach users skills that transfer to IELTS writing and speaking instead of only correcting grammar.

## Problem Statement

This document started as the design for adding Codex without duplicating pedagogy. On the current branch, that design is mostly implemented:

- Claude Code via `.claude-plugin/plugin.json`, `hooks/hooks.json`, and `hooks/language-coach.sh`
- Codex via `.codex-plugin/plugin.json`, `platforms/codex/hook_entry.py`, and `platforms/codex/install_hooks.py`
- Cursor via `cursor-rules/language-coach.mdc`
- Shared config, pedagogy, and prompt assembly under `shared/`
- Shared render and management CLIs under `scripts/`

The remaining doc job is to describe the product accurately:

- Claude and Codex now share one coaching core and one normalized config model
- Cursor remains intentionally simpler and does not use the shared JSON config
- IELTS-oriented modes exist in the shared core, but platform docs need to be explicit about where they are available

## Context

Current repository structure:

- `.claude-plugin/plugin.json` defines the Claude plugin package
- `.codex-plugin/plugin.json` defines the Codex plugin package
- `hooks/language-coach.sh` injects coaching context for Claude Code
- `hooks/hooks.json` binds the Claude hook to `UserPromptSubmit`
- `platforms/codex/hook_entry.py` is the Codex hook target
- `platforms/codex/install_hooks.py` installs or removes the Codex user hook
- `scripts/manage_language_coach.py` manages normalized config for Claude and Codex
- `scripts/render_coaching_context.py` emits hook JSON for both platforms
- `skills/language-coach/SKILL.md` exposes the command-based configuration flow
- `cursor-rules/language-coach.mdc` provides a Cursor always-on rule

## Product Principles

1. Keep the learning loop lightweight by default.
2. Use platform-native integration points instead of forcing one runtime across both tools.
3. Share the teaching brain, not necessarily the runtime shell.
4. Optimize for repeated daily use, not one-off novelty.
5. Teach reusable IELTS patterns and habits, not only sentence-level fixes.

## Options Considered

### Option A: Separate Claude and Codex implementations

Build and maintain two independent products with separate prompts, configuration, feedback logic, and runtime behavior.

Pros:

- Maximum platform freedom
- Fastest path to shipping platform-specific behavior

Cons:

- Teaching quality drifts over time
- Every IELTS improvement must be implemented twice
- Analytics, review logic, and user progression become fragmented

### Option B: One shared universal rule/prompt for all platforms

Use one common instruction payload everywhere and ignore platform differences.

Pros:

- Simple repository structure
- Minimal coordination cost

Cons:

- Wastes Claude hook advantages
- Fails to use Codex plugin and skill affordances well
- Produces a generic experience instead of a native one

### Option C: Shared learning core with platform-native adapters

Keep one shared pedagogy and configuration model, then implement Claude and Codex adapters that present the product natively on each platform.

Pros:

- Best long-term teaching consistency
- Best user experience on both platforms
- Clear separation between pedagogy and integration

Cons:

- Slightly higher upfront design and repo structure cost
- Requires a clean contract between core and adapters

## Recommendation

Choose Option C.

This is the only option that supports both business and learning goals:

- Claude keeps true automatic coaching through hooks
- Codex gets a real native plugin and skills story
- IELTS guidance, review logic, and configuration remain consistent
- Future expansion such as vocabulary drills, error memory, or score-oriented coaching only needs one core implementation

## User Experience Design

### North-star experience

The user installs the product, runs setup once, and then receives useful coaching in every session without feeling blocked from their actual task.

The product should behave like a quiet expert next to the user:

- present enough feedback to teach
- stay short enough not to annoy
- become deeper only when the user explicitly wants IELTS practice

### Default user journey

1. Install on Claude or Codex
2. Run `setup`
3. Answer a short onboarding flow
4. Continue normal work
5. Receive lightweight coaching before the actual answer
6. Switch into deeper IELTS modes only when needed

### Onboarding questions

Use the same logical onboarding flow on both platforms:

1. Native language
2. Target language
3. Primary goal: `everyday` or `ielts`
4. Preferred coaching depth: `teaching`, `concise`, or `translate`
5. Response language: `native` or `target`
6. If `ielts`, ask target skill focus: `writing`, `speaking`, or `both`
7. If `ielts`, ask target band and current estimated level if known

These answers should produce a single normalized config object shared across platforms.

## Learning Model

### Mode model

The product should support four explicit modes:

- `everyday`
- `ielts-writing`
- `ielts-speaking`
- `review`

`everyday` is the default and should optimize for low interruption.

`ielts-writing` and `ielts-speaking` should activate expanded pedagogy tailored to the exam.

`review` should summarize recurring mistakes, reusable phrases, and next drills from prior interactions or saved snapshots.

### Default feedback shape

For `everyday`, always return a compact four-part coaching block before the actual assistant response:

- `Your original`
- `Corrected`
- `More natural`
- `1 key takeaway`

This gives the user one teachable point without turning every interaction into a lesson.

### IELTS feedback shape

For `ielts-writing`, expand feedback into:

- `Band estimate` as a rough range, not a false-precision score
- `What is working`
- `What lowers the score`
- `Rewritten higher-band version`
- `Reusable pattern`
- `Mini drill`

For `ielts-speaking`, use a text-only approximation of speaking criteria:

- `Fluency and coherence`
- `Lexical resource`
- `Grammatical range and accuracy`
- `Natural spoken alternative`
- `Reusable pattern`
- `Mini drill`

The product must not claim to score pronunciation from plain text.

### Teaching goal

The teaching unit should not be "correction". It should be "transferable upgrade".

Every meaningful coaching pass should try to leave the user with at least one of:

- a reusable IELTS-compatible phrase pattern
- a clearer discourse structure
- a corrected grammar habit
- a contrast between technically correct and native-like expression

## Platform Strategy

### Claude adapter

Claude keeps the current hook-based model because it provides the strongest automatic experience.

Responsibilities:

- Load normalized config from disk
- Translate config into a coaching instruction payload
- Inject coaching context on `UserPromptSubmit`
- Expose management commands through Claude skill commands

Claude-specific UX:

- true automatic coaching on every prompt
- setup and mode switching through existing command surface
- low-friction pause and resume

### Codex adapter

Codex is implemented as a native Codex plugin, not as a Claude compatibility layer.

Current responsibilities:

- package a `.codex-plugin/plugin.json`
- provide `skills/` for setup and management commands
- provide a user-facing always-on experience through Codex-native plugin installation plus a Codex hook configuration path

Codex-specific UX:

- plugin install path is official and discoverable
- command surface mirrors Claude conceptually but follows Codex naming and plugin conventions
- automatic coaching is achieved through Codex-native `UserPromptSubmit` hook support rather than Claude compatibility shims

### Cursor adapter

Cursor remains a lighter companion surface rather than a full adapter on top of the shared Python runtime.

Current responsibilities:

- ship an `alwaysApply` rule file in `cursor-rules/language-coach.mdc`
- provide an easy copy/paste or checked-in workspace rule for everyday coaching
- keep customization manual and local to the rule text

Cursor-specific UX:

- no hook installer
- no shared JSON config file
- best fit for lightweight everyday coaching rather than dynamic IELTS mode switching

### Important runtime distinction

Claude automatic coaching comes from hooks.

Codex automatic coaching comes from Codex-native hooks plus a skill-driven or CLI-driven configuration flow.

Cursor coaching comes from a static rule file and is intentionally not coupled to the Claude/Codex config loader.

## Shared Core Design

The repository is now organized around a shared teaching core for Claude and Codex.

### Version boundary

This design defines a v1 delivery target and an explicit post-v1 expansion lane.

V1 includes:

- shared config schema
- shared pedagogy and prompt assembly
- Claude adapter migration onto the shared core
- Codex plugin adapter
- Codex hook adapter
- `everyday`, `ielts-writing`, and `ielts-speaking` modes

Post-v1 includes:

- persistent personalized review history
- cross-platform config import and export
- richer progress tracking and recurring mistake memory

### Current structure

```text
.claude-plugin/
.codex-plugin/
hooks/
cursor-rules/
platforms/
  codex/
shared/
  config/
  pedagogy/
  prompts/
scripts/
skills/
tests/
docs/
```

### Shared config layer

`shared/config/` defines:

- schema for user preferences
- defaults
- validation rules
- migration logic for future config versions

Normalized fields:

- `nativeLanguage`
- `targetLanguage`
- `goal`
- `mode`
- `style`
- `responseLanguage`
- `enabled`
- `ieltsFocus`
- `targetBand`
- `currentLevel`
- `version`

### Shared pedagogy layer

`shared/pedagogy/` defines:

- section layouts per mode
- compact everyday guidance
- IELTS-specific evaluation lenses
- review-mode summary structure

### Shared prompt assembly layer

`shared/prompts/` assembles the final instruction text from config and selected mode so both platforms draw from the same teaching logic.

## Command Design

Claude and Codex do not need identical command syntax, but they expose the same conceptual actions through the shared `skills/language-coach/SKILL.md` flow and `scripts/manage_language_coach.py`.

Required actions:

- `setup`
- `status`
- `on`
- `off`
- `mode <everyday|ielts-writing|ielts-speaking|review>`
- `style <teaching|concise|translate>`
- `native <lang>`
- `target <lang>`
- `response <native|target>`
- `goal <everyday|ielts>`

Implemented second-wave actions on this branch:

- `band <score>`
- `focus <writing|speaking|both>`

## Persistence Design

Use one normalized config schema, but do not force one physical storage location if platform conventions differ.

Current rule:

- shared schema
- adapter-owned persistence path

Actual paths on this branch:

- Claude uses `~/.claude/language-coach.json`
- Codex uses `~/.codex/language-coach.json`
- Cursor uses local or global rule text and does not read a JSON config file

If both platforms are installed for the same user later, config import and export belongs in the post-v1 lane. Cross-tool live coupling is explicitly out of scope for v1.

## Review and Memory Design

If the product aims to produce real IELTS gains, it needs a review loop.

Phase 1:

- no long-term history required
- provide session-level `review` summaries derived from recent interactions

Phase 2:

- store recurring mistakes, high-value phrase upgrades, and completed drills
- generate personalized review sessions

This should be designed into the schema now even if persistence is deferred.

## Safety and Honesty Rules

The product must:

- avoid false precision when estimating IELTS band
- avoid pretending to score pronunciation from text
- clearly separate correction from exam scoring
- remain short by default unless the user explicitly enters a deeper mode

## Rollout Plan Shape

The branch followed this order, and future changes should preserve the same separation of concerns:

1. define shared config schema
2. define shared pedagogy and prompt assembly
3. migrate Claude adapter onto shared core without changing user-visible behavior
4. add Codex plugin adapter on top of the shared core
5. add IELTS-specific modes
6. add review mode

This sequencing keeps current Claude users stable while enabling Codex without duplication.

## Testing Strategy

The current verification path is:

- `python3 -m unittest tests.shared.test_config_io tests.shared.test_prompt_builder tests.hooks.test_claude_hook_output tests.hooks.test_codex_hook_install tests.scripts.test_manage_language_coach -v`
- `python3 scripts/render_coaching_context.py --platform claude --config tests/fixtures/config_everyday.json`
- `python3 scripts/render_coaching_context.py --platform codex --config tests/fixtures/config_ielts_writing.json`

That coverage exercises:

- schema normalization and persistence
- prompt assembly by mode
- Claude hook payload output
- Codex hook installer behavior
- command handling in `scripts/manage_language_coach.py`

## Open Questions Resolved

### Should Claude and Codex share the same runtime?

No. They should share the same teaching core and product contract, but each should use its strongest native runtime affordance.

### Should coaching always be detailed?

No. Lightweight by default is required for adoption. Depth belongs to IELTS modes.

### Should the product focus only on correction?

No. Correction is necessary but insufficient. The product should also teach reusable patterns, better discourse, and compact drills.

## Final Design Summary

Build one learning product with:

- one shared teaching core
- one normalized config model
- a Claude hook adapter
- a Codex plugin plus hook adapter
- a Cursor rule-based companion surface
- lightweight default coaching
- explicit IELTS writing, speaking, and review modes

This design is the best balance of native UX, low user learning cost, maintainability, and real exam-oriented skill growth.
