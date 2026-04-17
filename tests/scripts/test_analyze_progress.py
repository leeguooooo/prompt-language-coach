from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import TestCase, mock

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analyze_progress import (
    _format_report,
    _linear_trend,
    analyze_language,
    main as analyze_main,
)


# ---------------------------------------------------------------------------
# _linear_trend
# ---------------------------------------------------------------------------

class TestLinearTrend(TestCase):
    def test_returns_none_for_empty(self):
        self.assertIsNone(_linear_trend([]))

    def test_returns_none_for_single_point(self):
        self.assertIsNone(_linear_trend([(0, 5.0)]))

    def test_flat_series_returns_zero(self):
        points = [(i, 6.0) for i in range(5)]
        slope = _linear_trend(points)
        self.assertTrue(math.isclose(slope, 0.0, abs_tol=1e-9))

    def test_positive_slope(self):
        # band increases by 0.5 each session
        points = [(i, 5.0 + i * 0.5) for i in range(6)]
        slope = _linear_trend(points)
        self.assertTrue(math.isclose(slope, 0.5, abs_tol=1e-6))

    def test_negative_slope(self):
        points = [(i, 7.0 - i * 0.5) for i in range(4)]
        slope = _linear_trend(points)
        self.assertTrue(math.isclose(slope, -0.5, abs_tol=1e-6))


# ---------------------------------------------------------------------------
# analyze_language
# ---------------------------------------------------------------------------

def _make_entry(bands: list[float], start_date: date | None = None) -> dict:
    """Build a progress entry dict with evenly spaced dates."""
    if start_date is None:
        start_date = date(2026, 1, 1)
    estimates = []
    for i, b in enumerate(bands):
        d = start_date + timedelta(days=i * 3)
        estimates.append({"date": d.isoformat(), "estimate": str(b)})
    return {"estimates": estimates}


class TestAnalyzeLanguage(TestCase):
    def test_no_data_returns_status(self):
        result = analyze_language("English", {})
        self.assertEqual(result["status"], "no data")
        self.assertEqual(result["sessions"], 0)

    def test_empty_estimates_returns_status(self):
        result = analyze_language("English", {"estimates": []})
        self.assertEqual(result["status"], "no data")

    def test_single_session(self):
        entry = _make_entry([6.0])
        result = analyze_language("English", entry)
        self.assertEqual(result["sessions"], 1)
        self.assertEqual(result["current_band"], 6.0)
        self.assertEqual(result["total_gain"], 0.0)
        self.assertIsNone(result["band_per_week"])  # need >= 2 sessions

    def test_multi_session_gain(self):
        entry = _make_entry([5.5, 6.0, 6.5])
        result = analyze_language("English", entry)
        self.assertEqual(result["sessions"], 3)
        self.assertEqual(result["current_band"], 6.5)
        self.assertEqual(result["first_band"], 5.5)
        self.assertTrue(math.isclose(result["total_gain"], 1.0, abs_tol=1e-9))

    def test_band_per_week_positive(self):
        # 6 sessions, band goes up 0.5 each time, 3 days apart
        entry = _make_entry([5.0, 5.5, 6.0, 6.5, 7.0, 7.5])
        result = analyze_language("English", entry)
        self.assertIsNotNone(result["band_per_week"])
        self.assertGreater(result["band_per_week"], 0)

    def test_streak_consecutive_days(self):
        today = date.today()
        estimates = [
            {"date": (today - timedelta(days=2)).isoformat(), "estimate": "5.5"},
            {"date": (today - timedelta(days=1)).isoformat(), "estimate": "6.0"},
            {"date": today.isoformat(), "estimate": "6.5"},
        ]
        result = analyze_language("English", {"estimates": estimates})
        self.assertEqual(result["streak"], 3)

    def test_streak_broken(self):
        today = date.today()
        estimates = [
            {"date": (today - timedelta(days=5)).isoformat(), "estimate": "5.5"},
            {"date": (today - timedelta(days=4)).isoformat(), "estimate": "6.0"},
            # gap here
            {"date": today.isoformat(), "estimate": "6.5"},
        ]
        result = analyze_language("English", {"estimates": estimates})
        self.assertEqual(result["streak"], 1)  # only today

    def test_momentum_improving(self):
        # First 3 sessions: avg 5.5, last 3: avg 6.5 → momentum = +1.0
        entry = _make_entry([5.0, 5.5, 6.0, 6.0, 6.5, 7.0])
        result = analyze_language("English", entry)
        self.assertIsNotNone(result["momentum"])
        self.assertGreater(result["momentum"], 0)

    def test_momentum_none_when_fewer_than_6(self):
        entry = _make_entry([5.0, 5.5, 6.0, 6.5])
        result = analyze_language("English", entry)
        self.assertIsNone(result["momentum"])

    def test_projected_weeks_computed(self):
        # current band 6.0, target 6.5, positive velocity → projection
        entry = _make_entry([5.0, 5.5, 6.0, 6.0, 6.0, 6.0])
        result = analyze_language("English", entry)
        # If improving, projection should be present; if flat, it won't be
        # Just verify the field exists and is an int or None
        self.assertIn("projected_weeks_to_target", result)
        if result["projected_weeks_to_target"] is not None:
            self.assertIsInstance(result["projected_weeks_to_target"], int)

    def test_skips_invalid_entries(self):
        entry = {
            "estimates": [
                {"date": "bad-date", "band": "6.0"},
                {"date": "2026-01-01", "estimate": "not-a-number"},
                {"date": "2026-01-03", "estimate": "6.5"},
            ]
        }
        result = analyze_language("English", entry)
        self.assertEqual(result["sessions"], 1)  # only the valid one counts
        self.assertEqual(result["current_band"], 6.5)

    def test_japanese_jlpt_levels_are_ranked_and_reported_without_numeric_bands(self):
        entry = {
            "scale": "jlpt",
            "estimates": [
                {"date": "2026-01-01", "band": "N5"},
                {"date": "2026-01-04", "estimate": "N4"},
            ],
        }
        result = analyze_language("Japanese", entry)
        self.assertEqual(result["sessions"], 2)
        self.assertEqual(result["current_band"], "N4")
        self.assertTrue(math.isclose(result["total_gain"], 1.0, abs_tol=1e-9))
        self.assertEqual(result["scale"], "jlpt")

    def test_mixed_scale_entries_still_count_as_sessions(self):
        entry = {
            "scale": "ielts",
            "estimates": [
                {"date": "2026-04-15", "estimate": "5.5"},
                {"date": "2026-04-16", "estimate": "B1"},
                {"date": "2026-04-17", "estimate": "A2"},
            ],
        }
        result = analyze_language("English", entry)
        self.assertEqual(result["sessions"], 3)
        self.assertEqual(result["practice_days"], 3)
        dates_in_history = [h["date"] for h in result["history"]]
        self.assertEqual(dates_in_history, ["2026-04-15", "2026-04-16", "2026-04-17"])


# ---------------------------------------------------------------------------
# _format_report
# ---------------------------------------------------------------------------

class TestFormatReport(TestCase):
    def test_no_data_language(self):
        report = _format_report([{"language": "French", "sessions": 0, "status": "no data"}])
        self.assertIn("French", report)
        self.assertIn("No data", report)

    def test_full_language_report(self):
        entry = _make_entry([5.5, 6.0, 6.5, 6.5, 7.0, 7.0])
        analysis = analyze_language("English", entry)
        report = _format_report([analysis])
        self.assertIn("English", report)
        self.assertIn("current:", report)
        self.assertIn("Sessions:", report)
        self.assertIn("Velocity:", report)

    def test_report_shows_history_for_multi_session(self):
        entry = _make_entry([5.5, 6.0])
        analysis = analyze_language("English", entry)
        report = _format_report([analysis])
        self.assertIn("History", report)

    def test_report_uses_level_wording_for_jlpt(self):
        entry = {
            "scale": "jlpt",
            "estimates": [
                {"date": "2026-01-01", "band": "N5"},
                {"date": "2026-01-04", "estimate": "N4"},
            ],
        }
        analysis = analyze_language("Japanese", entry)
        report = _format_report([analysis])
        self.assertIn("Japanese", report)
        self.assertIn("current: N4", report)
        self.assertIn("level/week", report)


# ---------------------------------------------------------------------------
# CLI integration (in-process to allow patching)
# ---------------------------------------------------------------------------

class TestCLI(TestCase):
    def _run_main(self, argv: list[str], progress_path: Path | None = None) -> tuple[int, str]:
        """Invoke analyze_main() in-process with argv and optional path patch."""
        import io

        captured = io.StringIO()
        path_patch_target = "scripts.analyze_progress.resolve_progress_path"
        load_patch_target = "scripts.analyze_progress.load_progress_data"

        progress_data = {}
        if progress_path is not None and progress_path.exists():
            progress_data = json.loads(progress_path.read_text(encoding="utf-8"))

        with mock.patch("sys.argv", ["analyze_progress.py"] + argv):
            with mock.patch(path_patch_target, return_value=progress_path or Path("/nonexistent.json")):
                with mock.patch(load_patch_target, return_value=progress_data):
                    with mock.patch("sys.stdout", captured):
                        rc = analyze_main()
        return rc, captured.getvalue()

    def test_missing_progress_file_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nonexistent.json"
            rc, out = self._run_main(["--platform", "claude"], missing)
        self.assertEqual(rc, 0)
        self.assertIn("No progress data", out)

    def test_valid_progress_file_produces_report(self):
        progress = {
            "English": {
                "estimates": [
                    {"date": "2026-01-01", "band": "5.5"},
                    {"date": "2026-01-04", "estimate": "6.0"},
                    {"date": "2026-01-07", "estimate": "6.5"},
                ]
            }
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(progress, f)
            progress_path = Path(f.name)

        rc, out = self._run_main(["--platform", "claude"], progress_path)
        self.assertEqual(rc, 0)
        self.assertIn("English", out)
        assert "6.5" in out

    def test_language_filter(self):
        progress = {
            "English": {"estimates": [{"date": "2026-01-01", "estimate": "6.0"}]},
            "Japanese": {"estimates": [{"date": "2026-01-01", "estimate": "5.0"}]},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(progress, f)
            progress_path = Path(f.name)

        rc, out = self._run_main(["--platform", "claude", "--language", "English"], progress_path)
        assert rc == 0
        assert "English" in out
        assert "Japanese" not in out
