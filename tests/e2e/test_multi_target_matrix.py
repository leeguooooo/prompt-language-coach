"""Parametrized matrix covering per-target propagation across every mutating
command × the three `targets[]` shapes we care about:

- `empty`        — single-target mode (no targets[] list).
- `single`       — one target entry.
- `multi`        — two target entries.

Each scenario seeds a config, invokes a single command, and asserts that
top-level and every target entry stay in lockstep for every per-target key.
"""
from __future__ import annotations

import argparse
import copy

import pytest

from scripts.manage_language_coach import _PER_TARGET_SYNCED_KEYS, apply_command

BASE_CONFIG = {
    "nativeLanguage": "Chinese",
    "targetLanguage": "English",
    "goal": "everyday",
    "mode": "everyday",
    "style": "teaching",
    "responseLanguage": "native",
    "enabled": True,
    "scoringFocus": "both",
    "targetEstimate": "",
    "currentLevel": "",
    "vocabFocus": False,
    "version": 1,
}


def _make_config(shape: str) -> dict:
    config = copy.deepcopy(BASE_CONFIG)
    if shape == "empty":
        config["targets"] = []
    elif shape == "single":
        config["targets"] = [
            {"targetLanguage": "English", **{k: config[k] for k in _PER_TARGET_SYNCED_KEYS}},
        ]
    elif shape == "multi":
        config["targets"] = [
            {"targetLanguage": "English", **{k: config[k] for k in _PER_TARGET_SYNCED_KEYS}},
            {"targetLanguage": "Japanese", **{k: config[k] for k in _PER_TARGET_SYNCED_KEYS}},
        ]
    else:
        raise ValueError(shape)
    return config


# (command, value, per-target keys we expect to end up mirroring top-level)
COMMAND_CASES = [
    ("style", "concise", ("style",)),
    ("response", "target", ("responseLanguage",)),
    ("goal", "scored", ("goal", "mode")),
    ("mode", "scored-writing", ("mode", "goal")),
    ("mode", "scored-speaking", ("mode", "goal")),
    ("mode", "everyday", ("mode", "goal")),
    ("estimate", "6.5", ("targetEstimate",)),
    ("band", "7.0", ("targetEstimate",)),
    ("focus", "speaking", ("scoringFocus",)),
    ("practice-focus", "writing", ("scoringFocus",)),
    ("level", "高中生水平", ("currentLevel",)),
    ("vocab", "on", ("vocabFocus",)),
    ("vocab", "off", ("vocabFocus",)),
]

SHAPES = ["empty", "single", "multi"]


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize(("command", "value", "synced_keys"), COMMAND_CASES)
def test_command_keeps_top_level_and_targets_in_sync(shape, command, value, synced_keys):
    config = _make_config(shape)
    args = argparse.Namespace(command=command, value=value)

    result = apply_command(config, args)
    assert result is not None, f"{command} did not return a status message"

    targets = config.get("targets") or []
    for target in targets:
        for key in synced_keys:
            assert target[key] == config[key], (
                f"after `{command} {value}` with shape={shape}, "
                f"target {target.get('targetLanguage')!r} key {key!r} "
                f"= {target[key]!r} but top-level = {config[key]!r}"
            )


@pytest.mark.parametrize("shape", SHAPES)
def test_goal_everyday_forces_mode_everyday_on_all_targets(shape):
    config = _make_config(shape)
    config["goal"] = "scored"
    config["mode"] = "scored-writing"
    for target in config.get("targets") or []:
        target["goal"] = "scored"
        target["mode"] = "scored-writing"

    apply_command(config, argparse.Namespace(command="goal", value="everyday"))
    assert config["mode"] == "everyday"
    for target in config.get("targets") or []:
        assert target["mode"] == "everyday"
        assert target["goal"] == "everyday"


def test_target_command_empty_shape_updates_top_level():
    config = _make_config("empty")
    apply_command(config, argparse.Namespace(command="target", value="Korean"))
    assert config["targetLanguage"] == "Korean"


def test_target_command_multi_shape_promotes_existing_profile():
    config = _make_config("multi")
    apply_command(config, argparse.Namespace(command="target", value="Japanese"))
    assert config["targetLanguage"] == "Japanese"
    assert config["targets"][0]["targetLanguage"] == "Japanese"


def test_target_command_multi_shape_does_not_silently_add_unknown_language():
    config = _make_config("multi")
    original_langs = [t["targetLanguage"] for t in config["targets"]]
    apply_command(config, argparse.Namespace(command="target", value="Korean"))
    assert config["targetLanguage"] == "Korean"
    # targets[] must NOT be mutated
    assert [t["targetLanguage"] for t in config["targets"]] == original_langs
