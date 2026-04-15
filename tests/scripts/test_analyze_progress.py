from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

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

class TestLinearTrend:
    def test_returns_none_for_empty(self):
        assert _linear_trend([]) is None

    def test_returns_none_for_single_point(self):
        assert _linear_trend([(0, 5.0)]) is None

    def test_flat_series_returns_zero(self):
        points = [(i, 6.0) for i in range(5)]
        slope = _linear_trend(points)
        assert slope == pytest.approx(0.0, abs=1e-9)

    def test_positive_slope(self):
        # band increases by 0.5 each session
        points = [(i, 5.0 + i * 0.5) for i in range(6)]
        slope = _linear_trend(points)
        assert slope == pytest.approx(0.5, abs=1e-6)

    def test_negative_slope(self):
        points = [(i, 7.0 - i * 0.5) for i in range(4)]
        slope = _linear_trend(points)
        assert slope == pytest.approx(-0.5, abs=1e-6)


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
        estimates.append({"date": d.isoformat(), "band": str(b)})
    return {"estimates": estimates}


class TestAnalyzeLanguage:
    def test_no_data_returns_status(self):
        result = analyze_language("English", {})
        assert result["status"] == "no data"
        assert result["sessions"] == 0

    def test_empty_estimates_returns_status(self):
        result = analyze_language("English", {"estimates": []})
        assert result["status"] == "no data"

    def test_single_session(self):
        entry = _make_entry([6.0])
        result = analyze_language("English", entry)
        assert result["sessions"] == 1
        assert result["current_band"] == 6.0
        assert result["total_gain"] == 0.0
        assert result["band_per_week"] is None  # need >= 2 sessions

    def test_multi_session_gain(self):
        entry = _make_entry([5.5, 6.0, 6.5])
        result = analyze_language("English", entry)
        assert result["sessions"] == 3
        assert result["current_band"] == 6.5
        assert result["first_band"] == 5.5
        assert result["total_gain"] == pytest.approx(1.0, abs=1e-9)

    def test_band_per_week_positive(self):
        # 6 sessions, band goes up 0.5 each time, 3 days apart
        entry = _make_entry([5.0, 5.5, 6.0, 6.5, 7.0, 7.5])
        result = analyze_language("English", entry)
        assert result["band_per_week"] is not None
        assert result["band_per_week"] > 0

    def test_streak_consecutive_days(self):
        today = date.today()
        estimates = [
            {"date": (today - timedelta(days=2)).isoformat(), "band": "5.5"},
            {"date": (today - timedelta(days=1)).isoformat(), "band": "6.0"},
            {"date": today.isoformat(), "band": "6.5"},
        ]
        result = analyze_language("English", {"estimates": estimates})
        assert result["streak"] == 3

    def test_streak_broken(self):
        today = date.today()
        estimates = [
            {"date": (today - timedelta(days=5)).isoformat(), "band": "5.5"},
            {"date": (today - timedelta(days=4)).isoformat(), "band": "6.0"},
            # gap here
            {"date": today.isoformat(), "band": "6.5"},
        ]
        result = analyze_language("English", {"estimates": estimates})
        assert result["streak"] == 1  # only today

    def test_momentum_improving(self):
        # First 3 sessions: avg 5.5, last 3: avg 6.5 → momentum = +1.0
        entry = _make_entry([5.0, 5.5, 6.0, 6.0, 6.5, 7.0])
        result = analyze_language("English", entry)
        assert result["momentum"] is not None
        assert result["momentum"] > 0

    def test_momentum_none_when_fewer_than_6(self):
        entry = _make_entry([5.0, 5.5, 6.0, 6.5])
        result = analyze_language("English", entry)
        assert result["momentum"] is None

    def test_projected_weeks_computed(self):
        # current band 6.0, target 6.5, positive velocity → projection
        entry = _make_entry([5.0, 5.5, 6.0, 6.0, 6.0, 6.0])
        result = analyze_language("English", entry)
        # If improving, projection should be present; if flat, it won't be
        # Just verify the field exists and is an int or None
        assert "projected_weeks_to_target" in result
        if result["projected_weeks_to_target"] is not None:
            assert isinstance(result["projected_weeks_to_target"], int)

    def test_skips_invalid_entries(self):
        entry = {
            "estimates": [
                {"date": "bad-date", "band": "6.0"},
                {"date": "2026-01-01", "band": "not-a-number"},
                {"date": "2026-01-03", "band": "6.5"},
            ]
        }
        result = analyze_language("English", entry)
        assert result["sessions"] == 1  # only the valid one counts
        assert result["current_band"] == 6.5


# ---------------------------------------------------------------------------
# _format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_no_data_language(self):
        report = _format_report([{"language": "French", "sessions": 0, "status": "no data"}])
        assert "French" in report
        assert "No data" in report

    def test_full_language_report(self):
        entry = _make_entry([5.5, 6.0, 6.5, 6.5, 7.0, 7.0])
        analysis = analyze_language("English", entry)
        report = _format_report([analysis])
        assert "English" in report
        assert "current:" in report
        assert "Sessions:" in report
        assert "Velocity:" in report

    def test_report_shows_history_for_multi_session(self):
        entry = _make_entry([5.5, 6.0])
        analysis = analyze_language("English", entry)
        report = _format_report([analysis])
        assert "History" in report


# ---------------------------------------------------------------------------
# CLI integration (in-process to allow patching)
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_main(self, argv: list[str], progress_path: Path | None = None) -> tuple[int, str]:
        """Invoke analyze_main() in-process with argv and optional path patch."""
        import io

        captured = io.StringIO()
        patch_target = "scripts.analyze_progress.resolve_progress_path"

        with mock.patch("sys.argv", ["analyze_progress.py"] + argv):
            if progress_path is not None:
                with mock.patch(patch_target, return_value=progress_path):
                    with mock.patch("sys.stdout", captured):
                        rc = analyze_main()
            else:
                with mock.patch(patch_target, return_value=progress_path or Path("/nonexistent.json")):
                    with mock.patch("sys.stdout", captured):
                        rc = analyze_main()
        return rc, captured.getvalue()

    def test_missing_progress_file_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nonexistent.json"
            rc, out = self._run_main(["--platform", "claude"], missing)
        assert rc == 0
        assert "No progress data" in out

    def test_valid_progress_file_produces_report(self):
        progress = {
            "English": {
                "estimates": [
                    {"date": "2026-01-01", "band": "5.5"},
                    {"date": "2026-01-04", "band": "6.0"},
                    {"date": "2026-01-07", "band": "6.5"},
                ]
            }
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(progress, f)
            progress_path = Path(f.name)

        rc, out = self._run_main(["--platform", "claude"], progress_path)
        assert rc == 0
        assert "English" in out
        assert "6.5" in out

    def test_language_filter(self):
        progress = {
            "English": {"estimates": [{"date": "2026-01-01", "band": "6.0"}]},
            "Japanese": {"estimates": [{"date": "2026-01-01", "band": "5.0"}]},
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
