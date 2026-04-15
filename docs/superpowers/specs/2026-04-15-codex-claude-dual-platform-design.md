# Prompt Language Coach Dual-Platform Design

## Goal

Evolve `prompt-language-coach` from a Claude-first plugin into a dual-platform product that supports both Claude and Codex while preserving the strongest native experience on each platform.

The product should feel easy to adopt, stay on by default in day-to-day usage, and teach users skills that transfer to IELTS writing and speaking instead of only correcting grammar.

## Problem Statement

The current repository supports:

- Claude Code via `UserPromptSubmit` hook injection
- Cursor via an `alwaysApply` rule file

It does not yet support Codex as a first-class platform. A naive port would create one of two bad outcomes:

- A lowest-common-denominator implementation that feels unnatural on both platforms
- Two disconnected products with duplicated logic and drifting teaching quality

The design needs to solve for product consistency, native UX, and pedagogy at the same time.

## Context

Current repository structure:

- `.claude-plugin/plugin.json` defines the Claude plugin package
- `hooks/language-coach.sh` injects coaching context for Claude Code
- `hooks/hooks.json` binds the hook to `UserPromptSubmit`
- `skills/language-coach/SKILL.md` exposes command-based configuration in Claude
- `cursor-rules/language-coach.mdc` provides a Cursor always-on rule

Recent repository history shows the project has been improving Claude plugin correctness and adding Cursor support, but it has not introduced a Codex-native packaging or runtime layer.

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

Claude should keep the current hook-based model because it provides the strongest automatic experience.

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

Codex should be implemented as a native Codex plugin, not as a Claude compatibility layer.

Responsibilities:

- package a `.codex-plugin/plugin.json`
- provide `skills/` for setup and management commands
- provide a user-facing always-on experience through Codex-native plugin installation plus a Codex hook configuration path

Codex-specific UX:

- plugin install path is official and discoverable
- command surface mirrors Claude conceptually but follows Codex naming and plugin conventions
- automatic coaching is achieved through Codex-native `UserPromptSubmit` hook support rather than Claude compatibility shims

### Important runtime distinction

Claude automatic coaching comes from hooks.

Codex automatic coaching should come from Codex-native hooks plus a skill-driven configuration flow. The design should not treat Codex as if it lacked a native submit-time context injection surface.

## Shared Core Design

The repository should be reorganized around a shared teaching core.

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

### Proposed structure

```text
.claude-plugin/
.codex-plugin/
hooks/
cursor-rules/
platforms/
  claude/
  codex/
  codex-hooks/
shared/
  config/
  pedagogy/
  prompts/
skills/
docs/
```

### Shared config layer

`shared/config/` should define:

- schema for user preferences
- defaults
- validation rules
- migration logic for future config versions

Suggested normalized fields:

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

`shared/pedagogy/` should define:

- feedback templates
- correction strategies
- IELTS-specific evaluation lenses
- takeaway rules
- drill generation rules
- review summarization templates

### Shared prompt assembly layer

`shared/prompts/` should assemble the final instruction text from config and selected mode, so both platforms draw from the same teaching logic.

## Command Design

Claude and Codex do not need identical command syntax, but they should expose the same conceptual actions.

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

Optional second-wave actions:

- `band <score>`
- `focus <writing|speaking|both>`
- `review now`
- `reset`

## Persistence Design

Use one normalized config schema, but do not force one physical storage location if platform conventions differ.

Recommended rule:

- shared schema
- adapter-owned persistence path

Example:

- Claude may continue using `~/.claude/language-coach.json`
- Codex may use a Codex-native path such as a plugin-owned config file under the Codex user directory

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

Implementation should proceed in this order:

1. define shared config schema
2. define shared pedagogy and prompt assembly
3. migrate Claude adapter onto shared core without changing user-visible behavior
4. add Codex plugin adapter on top of the shared core
5. add IELTS-specific modes
6. add review mode

This sequencing keeps current Claude users stable while enabling Codex without duplication.

## Testing Strategy

The implementation plan should include:

- schema validation tests
- prompt assembly tests by mode
- Claude adapter regression tests to preserve existing behavior
- Codex adapter tests for setup, command handling, generated hook configuration, and hook payload assembly
- golden tests for IELTS feedback templates
- tone and length checks for `everyday` mode so feedback stays compact

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
- lightweight default coaching
- explicit IELTS writing, speaking, and review modes

This design is the best balance of native UX, low user learning cost, maintainability, and real exam-oriented skill growth.
