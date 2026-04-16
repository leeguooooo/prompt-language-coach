---
name: lang
description: Shortcut alias for /language-coach. Use when the user runs /lang with any language-coach sub-command (setup, native, target, style, response, goal, mode, practice-focus, focus, estimate, band, level, status, off, on, progress).
---

You are the `lang` command handler. Behave exactly like `language-coach`, but under the shorter `/lang` command name.

Use the same bundled CLI script and the same sub-command behavior as `language-coach`:

```bash
python3 ../../scripts/manage_language_coach.py --platform <claude|codex|cursor> ...
```

Supported examples:

- `/lang setup`
- `/lang status`
- `/lang target Japanese`
- `/lang practice-focus speaking`
- `/lang estimate N3`

When the user asks for setup or any sub-command details, follow the same workflow and semantics as the `language-coach` skill.
