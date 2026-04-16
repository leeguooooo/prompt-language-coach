from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.manage_language_coach import load_progress_data, resolve_progress_path as resolve_progress_path
from shared.proficiency import estimate_sort_value, normalize_estimate, scale_for_language


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze language learning progress.")
    parser.add_argument("--platform", choices=("claude", "codex", "cursor"), default="claude")
    parser.add_argument("--language", default=None, help="Filter to a single language.")
    return parser.parse_args()


def _parse_date(s: str) -> date | None:
    try:
        return datetime.fromisoformat(s).date()
    except (ValueError, TypeError):
        return None


def _linear_trend(points: list[tuple[int, float]]) -> float | None:
    """Slope of best-fit line (band/day). Returns None if < 2 points."""
    n = len(points)
    if n < 2:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0:
        return None
    return num / den


def analyze_language(language: str, entry: dict[str, Any]) -> dict[str, Any]:
    scale = scale_for_language(language, entry.get("scale"))
    estimates: list[dict[str, str]] = entry.get("estimates", [])
    if not estimates:
        return {"language": language, "sessions": 0, "status": "no data", "scale": scale.key}

    # Parse all valid entries; carry optional text field
    dated: list[tuple[date, float, str, str]] = []
    for e in estimates:
        d = _parse_date(e.get("date", ""))
        band_display = normalize_estimate(e.get("band", ""), scale=scale) or e.get("band", "")
        b = estimate_sort_value(e.get("band", ""), scale=scale)
        if d is not None and b is not None:
            dated.append((d, b, band_display, e.get("text", "")))

    if not dated:
        return {"language": language, "sessions": 0, "status": "no data", "scale": scale.key}

    dated.sort(key=lambda x: x[0])
    sessions = len(dated)
    first_date, first_band_value, first_band, _ = dated[0]
    last_date, last_band_value, last_band, _ = dated[-1]
    today = date.today()
    days_active = (last_date - first_date).days + 1
    days_since_last = (today - last_date).days

    # Unique practice days
    practice_days = len({d for d, _, _display, _t in dated})
    consistency_pct = round(practice_days / max(days_active, 1) * 100)

    # Best / worst session
    best_band = max(b for _, b, _display, _t in dated)

    # Trend: slope in band/day, convert to band/week
    indexed = [(i, b) for i, (_, b, _display, _t) in enumerate(dated)]
    slope_per_session = _linear_trend(indexed)
    # Average time between sessions
    if sessions > 1 and days_active > 0:
        sessions_per_week = sessions / (days_active / 7)
        band_per_week = (
            round(slope_per_session * sessions_per_week, 3)
            if slope_per_session is not None
            else None
        )
    else:
        band_per_week = None

    # Projected band at target (6.5 default) — weeks needed
    target_band = 6.5
    projected_weeks: int | None = None
    if scale.key == "ielts" and band_per_week and band_per_week > 0 and last_band_value < target_band:
        projected_weeks = int((target_band - last_band_value) / band_per_week)

    # Streak: consecutive days ending on last practice day
    date_set = {d for d, _, _display, _t in dated}
    streak = 0
    cursor = last_date
    while cursor in date_set:
        streak += 1
        cursor -= timedelta(days=1)

    # Recent momentum: last 3 vs first 3 sessions
    if sessions >= 6:
        early_avg = sum(b for _, b, _display, _t in dated[:3]) / 3
        recent_avg = sum(b for _, b, _display, _t in dated[-3:]) / 3
        momentum = round(recent_avg - early_avg, 2)
    else:
        momentum = None

    return {
        "language": language,
        "scale": scale.key,
        "unit_label": scale.unit_label,
        "sessions": sessions,
        "current_band": last_band_value if scale.key == "ielts" else last_band,
        "first_band": first_band_value,
        "best_band": best_band,
        "total_gain": round(last_band_value - first_band_value, 2),
        "days_active": days_active,
        "practice_days": practice_days,
        "consistency_pct": consistency_pct,
        "days_since_last": days_since_last,
        "band_per_week": band_per_week,
        "streak": streak,
        "momentum": momentum,
        "projected_weeks_to_target": projected_weeks,
        "target_band": target_band,
        "history": [{"date": str(d), "estimate": display, "text": t} for d, _sort, display, t in dated],
    }


def _format_report(analyses: list[dict[str, Any]]) -> str:
    lines: list[str] = ["## Language Progress Report", ""]

    for a in analyses:
        lang = a["language"]
        if a.get("status") == "no data":
            lines += [f"### {lang}", "  No data recorded yet.", ""]
            continue

        band = a["current_band"]
        gain = a["total_gain"]
        gain_str = f"+{gain}" if gain >= 0 else str(gain)
        lines += [f"### {lang}  (current: {band}  total gain: {gain_str})"]

        lines.append(f"  Sessions:      {a['sessions']} sessions "
                     f"over {a['days_active']} days "
                     f"({a['practice_days']} practice days, {a['consistency_pct']}% consistency)")

        if a["days_since_last"] == 0:
            lines.append("  Last session:  today ✓")
        elif a["days_since_last"] == 1:
            lines.append("  Last session:  yesterday")
        else:
            lines.append(f"  Last session:  {a['days_since_last']} days ago")

        if a["streak"] > 1:
            lines.append(f"  Streak:        {a['streak']} days")

        if a["band_per_week"] is not None:
            bpw = a["band_per_week"]
            direction = "↑" if bpw > 0 else ("↓" if bpw < 0 else "→")
            lines.append(
                f"  Velocity:      {direction} {abs(bpw):.3f} {a.get('unit_label', 'band')}/week"
            )

        if a["momentum"] is not None:
            m = a["momentum"]
            lines.append(f"  Momentum:      {'improving' if m > 0 else 'plateauing'} "
                         f"(recent avg vs early avg: {'+' if m >= 0 else ''}{m})")

        if a["projected_weeks_to_target"] is not None:
            lines.append(f"  Projection:    ~{a['projected_weeks_to_target']} weeks to reach "
                         f"band {a['target_band']} at current rate")

        if a["sessions"] >= 2:
            lines.append("  History (all sessions):")
            for entry in a["history"]:
                text = entry.get("text", "")
                if text:
                    lines.append(f"    {entry['date']}  estimate {entry['estimate']}  \"{text}\"")
                else:
                    lines.append(f"    {entry['date']}  estimate {entry['estimate']}")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    progress_path = resolve_progress_path(args.platform)
    data = load_progress_data(args.platform)

    if not data:
        print(f"No progress data found at {progress_path}.")
        print("Start a coaching session in scored mode to record your first estimate.")
        return 0

    if args.language:
        matched = {k: v for k, v in data.items() if k.casefold() == args.language.casefold()}
        if not matched:
            print(f"No data for language: {args.language}")
            return 0
        data = matched

    analyses = [analyze_language(lang, entry) for lang, entry in sorted(data.items())]
    print(_format_report(analyses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
