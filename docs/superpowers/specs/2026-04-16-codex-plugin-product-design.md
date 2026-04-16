# Prompt Language Coach Codex Plugin Product Design

## Goal

Ship `Prompt Language Coach` as a polished, high-conviction product that treats `Codex`, `Claude Code`, and `Cursor` as first-class platforms while making the Codex plugin experience strong enough to drive adoption, retention, and GitHub stars.

The Codex work should not be framed as "adding Codex support" to a Claude-first plugin. The product already spans multiple platforms. This design defines how to make the Codex surface feel native, complete, and marketable without weakening the equal standing of Claude Code and Cursor.

## Success Criteria

The result should satisfy all of the following:

1. Codex users can install the product as a real plugin, run setup once, and get automatic coaching on every prompt.
2. The default user experience is `always-on`, with a simple command-first control surface for pause, resume, and status.
3. README messaging positions the product as a universal language coach for AI editors, not an English-only utility and not a single-platform add-on.
4. GitHub visitors can understand the value and the supported platforms within seconds, with strong reasons to star the repo even before installation.
5. The repository structure clearly communicates `shared core + platform-native adapters`.

## Problem Statement

The repository already contains substantial Codex scaffolding:

- `.codex-plugin/plugin.json`
- `platforms/codex/hook_entry.py`
- `platforms/codex/install_hooks.py`
- shared config and prompt-building logic under `shared/`
- shared management and rendering CLIs under `scripts/`

What remains is productization:

- sharpen the Codex plugin surface into a truly native-feeling experience
- align docs and metadata with a multi-platform first-class product story
- make the GitHub landing experience strong enough to convert attention into stars
- keep behavior and command concepts consistent across all first-class platforms

## Product Principles

1. `Codex`, `Claude Code`, and `Cursor` are all first-class citizens.
2. The product is universal across language pairs: any native language can learn any target language.
3. `Always-on` coaching is the default experience.
4. Control must feel safe: users can always inspect status or turn coaching off immediately.
5. Shared pedagogy belongs in the core; native UX belongs in each platform adapter.
6. IELTS support is a differentiated mode, not the entire product definition.
7. The repository homepage is part of the product surface, not just documentation.

## Core Positioning

### Product statement

`Prompt Language Coach` is an always-on language coach inside AI editors. It corrects, upgrades, and teaches from every prompt while users continue their normal work.

### Positioning consequences

This product must not be described as:

- an English-only helper
- a Codex-only tool
- a Claude plugin with extra adapters
- an IELTS scorer with a little grammar correction

It should be described as:

- a universal language coach
- native on Claude Code, Codex, and Cursor
- always-on by default
- deeper when users want IELTS-focused practice

## User Segments

Primary audience:

- users whose native language is not the language they want to practice while using AI editors

Examples include:

- Chinese developers learning English
- English-speaking users learning Japanese
- Spanish-speaking users learning French
- bilingual users practicing advanced formal writing

Secondary audience:

- users preparing for IELTS or other exam-like written and spoken performance tasks

The product story should scale to both without collapsing into an exam-only brand.

## Options Considered

### Option A: Codex-only polish push

Make Codex the star and let Claude Code and Cursor remain mostly unchanged.

Pros:

- strongest Codex-specific focus
- fastest path to a more impressive Codex demo

Cons:

- breaks the equal-first-class platform model
- creates documentation drift across platforms
- weakens the product identity by over-attaching it to one host

### Option B: Pure cross-platform sameness

Force the same install language, command shape, and messaging across all platforms.

Pros:

- simple to explain internally
- lower documentation branching cost

Cons:

- makes each platform feel less native
- ignores real UX differences in hooks, plugin loading, and rule systems
- produces a generic rather than premium integration

### Option C: Shared core, native adapters, unified product story

Keep one product identity and one teaching core while making each platform feel native in its own integration surface.

Pros:

- preserves multi-platform first-class standing
- keeps the codebase maintainable
- supports strong GitHub storytelling and strong in-product UX at the same time

Cons:

- requires tighter docs, metadata, and packaging discipline
- requires more careful wording so platform equality stays credible

## Recommendation

Choose Option C.

It is the only option that supports the stated ambition: the product should feel premium, native, and star-worthy without being trapped inside one platform's identity.

## Product Experience

### North-star experience

The user installs the plugin, runs setup once, then forgets about configuration and simply works. Every prompt gets an unobtrusive coaching layer before the real model answer. The product quietly improves the user's target language over time without forcing context switching.

### Default interaction contract

1. Install plugin
2. Run setup
3. Answer a short onboarding flow
4. Continue normal work
5. Receive compact coaching automatically before the real answer
6. Use commands only when changing state, checking status, or entering deeper modes

### Always-on contract

`Always-on` is the default on all first-class platforms, but the implementation differs by platform:

- Claude Code: hook-driven automatic coaching
- Codex: plugin + hook-driven automatic coaching
- Cursor: native plugin/rule entry suited to that runtime

The product promise is the same even if the runtime mechanism differs.

## Control Surface

### Command-first control

The main user control surface is command-based, not config-file-based.

Required high-priority commands:

- `setup`
- `status`
- `off`
- `on`
- `mode`

Supporting commands:

- `native`
- `target`
- `style`
- `response`
- `goal`
- `focus`
- `band`
- `level`
- `progress`

### Why command-first matters

If the product is always-on, users need immediate psychological safety. A memorable `on/off` command is more important than exposing the JSON file shape.

Config files remain the persistence layer, but they are not the primary UX.

## Learning Model

### Supported modes

The product supports:

- `everyday`
- `ielts-writing`
- `ielts-speaking`
- `review`

### Everyday mode

This is the default and should optimize for low friction. The feedback block stays compact and teaches one transferable improvement at a time.

Expected structure:

- `Your original`
- `Corrected`
- `More natural`
- `1 key takeaway`

### IELTS modes

These exist as differentiated depth modes for users who want more than everyday correction.

`ielts-writing` should include:

- band range estimate
- strengths
- score-lowering issues
- rewritten higher-band version
- reusable pattern
- mini drill

`ielts-speaking` should include:

- fluency/coherence guidance from text
- lexical upgrade guidance
- grammar upgrade guidance
- natural spoken alternative
- reusable pattern
- mini drill

### Universal language-pair requirement

Examples, screenshots, and docs must make it obvious that the product is not locked to Chinese-to-English or English exam prep. IELTS is one powerful scenario layered on top of a universal product.

## Platform Architecture

### Shared core

The core owns:

- normalized config shape
- pedagogy and mode selection
- prompt construction
- progress tracking logic
- CLI management primitives

### Platform-native adapters

Each platform adapter owns:

- packaging and plugin metadata
- hook or rule registration
- platform-specific installation flow
- user-facing command naming where needed

### Structural rule

Repository structure should communicate:

- one product
- one teaching core
- three first-class platform adapters

It must not communicate:

- Claude as the "real" product and others as compatibility layers
- Codex as the new center replacing the others

## Codex-Specific Design

### Codex product standard

Codex should feel like a premium native plugin, not a repo script that happens to work in Codex.

That means:

- `.codex-plugin/plugin.json` must read like real product metadata
- the skill surface must be complete and user-legible
- install/remove behavior for hooks must be reliable and reversible
- setup and command behavior must align with the product story in README

### Codex installation strategy

Two installation paths should exist:

1. GitHub-first path for discoverability and star conversion
2. Codex-native plugin path for credibility and daily-use ergonomics

README should present both, but keep the GitHub path first because the repository is a major growth surface.

### Codex wow moment

The first successful Codex experience should prove three things quickly:

1. coaching is automatic
2. it works for arbitrary language pairs
3. deeper IELTS-oriented modes exist when needed

## Documentation and Growth Design

### README role

The README is a product landing page first and technical documentation second.

The upper section should answer, in order:

1. What is this?
2. Why is it special?
3. Which platforms are first-class?
4. How do I install it?
5. What happens after install?

### README first-screen goals

Within seconds, a visitor should understand:

- every prompt gets automatic coaching
- any language pair is supported
- the product is native on Claude Code, Codex, and Cursor
- IELTS mode is available for deeper practice

### Recommended first-screen content order

1. sharp one-line value proposition
2. primary demo image or motion showing coaching before the real answer
3. three core selling points
4. platform support matrix
5. install section

### Screenshot sequence

The visual order should be:

1. automatic coaching in action
2. non-English-pair or non-default-language example
3. IELTS mode example

If the README leads with only a Chinese-to-English correction example, many users will incorrectly classify the product as a narrow English utility.

## Quality Bar

Shipping quality requires more than code that runs.

Minimum release bar:

- Codex plugin metadata is complete and polished
- Codex setup and automatic coaching work end-to-end
- `on`, `off`, and `status` are documented and tested
- platform docs present Claude Code, Codex, and Cursor as equal first-class platforms
- README reflects actual behavior with no stale claims
- tests cover Codex hook install/remove and Codex config/progress paths

Higher bar for a star-seeking release:

- README reads like a premium product page
- platform matrix is explicit
- Codex installation is simple and believable
- examples visibly support the universal language-pair promise
- screenshots are selected for conversion, not just completeness

## Testing Strategy

Verification should cover:

- Codex hook installation and removal behavior
- silent no-op behavior when config is missing or disabled
- Codex config path handling
- Codex progress path handling
- command behavior for `status`, `on`, and `off`
- README and metadata consistency review before release

## Out of Scope

This design does not include:

- adding new pedagogy modes beyond the existing four
- building cloud sync or user accounts
- adding external analytics services
- changing the product name
- reducing Claude Code or Cursor to secondary support status

## Implementation Direction

The follow-on implementation plan should prioritize:

1. tightening Codex plugin packaging and command completeness
2. making docs reflect equal first-class platform support
3. upgrading README into a stronger landing page
4. filling test gaps around Codex control and persistence behavior

## Risks

1. Over-indexing on Codex could accidentally weaken the equal-platform story.
2. Over-indexing on IELTS could shrink the perceived audience.
3. Over-explaining internal implementation could dilute README conversion power.
4. Claiming first-class Cursor support without matching polish would damage trust.

## Decision Summary

Build `Prompt Language Coach` as a multi-platform native product with a strengthened Codex plugin surface, not as a single-platform tool with extras.

The product identity remains universal and editor-native. The Codex work should raise the overall product quality and growth potential, not redefine the product around one host.
