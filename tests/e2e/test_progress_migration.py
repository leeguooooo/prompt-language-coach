"""Regression tests for progress-file schema migration and merge.

Covers:
- Legacy date-only records still load and sort correctly.
- Legacy records from different platforms with identical (date, estimate, text)
  collapse (one session written to multiple mirrors).
- Same-day distinct timestamp records stay separate after merge.
- Mixed legacy + new records survive a round-trip through _merge_estimates.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.manage_language_coach import _merge_estimates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "progress"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_legacy_date_only_merge_is_lossless_within_one_file():
    legacy = _load("legacy_date_only.json")["English"]["estimates"]
    merged = _merge_estimates([], legacy)
    assert [m["date"] for m in merged] == ["2026-04-13", "2026-04-14", "2026-04-15"]
    assert merged[-1].get("text") == "First paragraph from my essay"


def test_legacy_records_dedupe_when_same_across_mirrors():
    # Simulate the same 3 records written to two platform mirrors. After merge
    # we should have 3 rows, not 6.
    legacy = _load("legacy_date_only.json")["English"]["estimates"]
    merged = _merge_estimates(legacy, list(legacy))
    assert len(merged) == 3


def test_new_timestamped_same_day_sessions_stay_distinct():
    current = _load("new_timestamped.json")["English"]["estimates"]
    merged = _merge_estimates([], current)
    # 3 sessions on the same date — must not collapse.
    dates = [m["date"] for m in merged]
    assert dates == ["2026-04-18", "2026-04-18", "2026-04-18"]
    estimates = [m["estimate"] for m in merged]
    assert estimates == ["5.5", "6.0", "6.0"]


def test_new_timestamped_dedupes_bit_identical_cross_mirror_writes():
    current = _load("new_timestamped.json")["English"]["estimates"]
    # Same 3 records written to 2 mirrors. Expect 3, not 6, after merge.
    merged = _merge_estimates(current, list(current))
    assert len(merged) == 3
    texts = [m.get("text") for m in merged]
    assert texts == ["morning practice", "afternoon practice", "evening review"]


def test_legacy_plus_new_mixed_round_trip_preserves_everything():
    legacy = _load("legacy_date_only.json")["English"]["estimates"]
    new = _load("new_timestamped.json")["English"]["estimates"]
    merged = _merge_estimates(legacy, new)
    # 3 legacy dates + 3 same-day new timestamps = 6 rows
    assert len(merged) == 6
    # Timestamp-ordered ascending — old date-only rows come first (their key
    # resolves to the date string), new timestamps sort later within 2026-04-18.
    ordered_keys = [m.get("timestamp") or m["date"] for m in merged]
    assert ordered_keys == sorted(ordered_keys)


def test_japanese_currentBand_legacy_key_round_trips_on_load():
    # _merge_estimates itself only handles estimates list. Verify it tolerates
    # the legacy `band` field (older schema) and surfaces it as estimate.
    legacy = _load("legacy_date_only.json")["Japanese"]["estimates"]
    merged = _merge_estimates([], legacy)
    assert [m["date"] for m in merged] == ["2026-04-15", "2026-04-16"]
    # Our merge projects legacy `band` values through to `estimate`
    for row in merged:
        assert row.get("estimate") == "N5"
