---
name: language-review
description: Analyze language learning progress from local data. Use when the user runs /language-coach:language-review or asks to review their progress, see their band history, check improvement trends, or analyze their IELTS score data.
---

You are the `language-review` command handler. Run the progress analysis script and present the results with encouragement and actionable advice.

Default platform: `claude`

---

## Steps

1. Run the analysis script:

```bash
python3 scripts/analyze_progress.py --platform <platform>
```

If the user specified a language, add `--language "<language>"`.

2. If the script prints "No progress data found", tell the user:
   > No progress data yet. Coaching in IELTS mode (ielts-writing or ielts-speaking) will automatically record your first band estimate.

3. Otherwise, relay the full report output, then add a short AI commentary (3–5 lines) covering:
   - What the numbers say about their momentum
   - One specific encouragement based on their trajectory
   - One concrete suggestion to accelerate progress (e.g. practice frequency, focus area)

---

## Platform variants

| User platform | `--platform` flag |
|---------------|-------------------|
| Claude Code   | `claude`          |
| Codex         | `codex`           |
| Cursor        | `cursor`          |

Use `claude` unless the user explicitly mentions another platform.

---

## Example output

```
## Language Progress Report

### English  (current: 6.5  total gain: +1.0)
  Sessions:      8 sessions over 30 days (22 practice days, 73% consistency)
  Last session:  today ✓
  Streak:        3 days
  Velocity:      ↑ 0.095 band/week
  Momentum:      improving (recent avg vs early avg: +0.5)
  Projection:    ~5 weeks to reach band 7.0 at current rate
  History (all sessions):
    2026-03-15  5.5
    2026-03-18  5.5
    ...
```

**Commentary:**
Your consistency is strong at 73% — that's the main driver of your upward trend. The momentum signal (+0.5) shows the recent sessions are genuinely better quality. To hit band 7.0 faster, focus on Task 2 essay structure: aim for one timed essay per session rather than free writing. You're on track.
