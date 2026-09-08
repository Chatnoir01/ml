"""RED-first checks for pre-Block-X CLI artifact checksum validation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase2f.py"
spec = importlib.util.spec_from_file_location("phase2f_cli", SCRIPT)
assert spec is not None and spec.loader is not None
phase2f_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase2f_cli)


def _seal(payload: dict, field: str) -> dict:
    clean = {key: value for key, value in payload.items() if key != field}
    payload[field] = hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def _pair():
    run = {
        "schema_version": 1,
        "phase": "2F",
        "seed": 526011,
        "arm": "C",
        "terminal_fingerprint": "terminal-fp",
        "terminal_sbox": [0, 1, 2],
        "terminal_classical": {"fingerprint": "terminal-fp"},
        "selection_events": [],
    }
    _seal(run, "scientific_payload_sha256")
    freeze = {
        "schema_version": 1,
        "phase": "2F-terminal-freeze",
        "cell_count": 36,
        "prerequisites": {"pass": True},
        "terminals": [
            {
                "seed": 526011,
                "arm": "C",
                "terminal_fingerprint": "terminal-fp",
                "terminal_sbox": [0, 1, 2],
                "arm_payload_sha256": run["scientific_payload_sha256"],
            }
        ],
    }
    _seal(freeze, "terminal_freeze_sha256")
    return run, freeze


def test_valid_sealed_arm_and_freeze_are_accepted():
    run, freeze = _pair()
    phase2f_cli._require_terminal_freeze(run, freeze)


def test_tampered_freeze_manifest_fails_before_block_x():
    run, freeze = _pair()
    freeze["cell_count"] = 35
    with pytest.raises(SystemExit):
        phase2f_cli._require_terminal_freeze(run, freeze)


def test_tampered_arm_payload_fails_before_block_x_even_if_terminal_is_unchanged():
    run, freeze = _pair()
    run["selection_events"] = [{"tampered": True}]
    with pytest.raises(SystemExit):
        phase2f_cli._require_terminal_freeze(run, freeze)
