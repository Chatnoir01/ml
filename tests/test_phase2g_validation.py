"""RED contract for post-freeze Phase 2G held-out H validation.

Synthetic only. No real held-out training is performed here. The validation stage
must refuse all work until an intact 36-cell terminal freeze authorizes H, then
score each frozen terminal exactly once with 16 trainings per terminal.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from adversarial_sbox.phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2g_terminal_freeze import freeze_phase2g_terminals
from adversarial_sbox.phase2g_validation import validate_frozen_terminals
from adversarial_sbox.provenance import fingerprint_sbox


def _sha_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sbox(offset: int) -> list[int]:
    return list(range(offset, 256)) + list(range(offset))


def _cell(seed: int, arm: str, arm_index: int) -> dict[str, object]:
    sbox = _sbox((seed + arm_index) % 256)
    payload: dict[str, object] = {
        "phase": "2G",
        "seed": seed,
        "arm": arm,
        "classical_evaluations": 340,
        "checkpoint_trainings": 64,
        "initial_population_digest_sha256": hashlib.sha256(
            f"{seed}:matched-initial".encode("utf-8")
        ).hexdigest(),
        "checkpoints": [
            {
                "generation": generation,
                "training_count": 16,
                "training_receipt_sha256": hashlib.sha256(
                    f"{seed}:{arm}:{generation}:training".encode("utf-8")
                ).hexdigest(),
            }
            for generation in CHECKPOINT_GENERATIONS
        ],
        "terminal_selection_rule": "historical_classical_only",
        "terminal_fingerprint": fingerprint_sbox(sbox),
        "terminal_sbox": sbox,
        "terminal_classical": {
            "admissible": True,
            "nonlinearity": 104,
            "differential_uniformity": 4,
            "max_abs_lat": 32,
            "algebraic_degree": 7,
        },
    }
    payload["scientific_payload_sha256"] = _sha_payload(payload)
    return payload


def _freeze() -> dict[str, object]:
    cells = [
        _cell(seed, arm, arm_index)
        for seed in EVOLUTION_SEEDS
        for arm_index, arm in enumerate(ARMS)
    ]
    return freeze_phase2g_terminals(cells)


def _fake_score(candidate) -> dict[str, object]:
    sbox = tuple(candidate)
    fingerprint = fingerprint_sbox(sbox)
    payload: dict[str, object] = {
        "schema_version": 1,
        "purpose": "validation",
        "fingerprint": fingerprint,
        "training_count": 16,
        "neural_advantage": float((sbox[0] % 17) / 100.0),
    }
    payload["scientific_payload_sha256"] = _sha_payload(payload)
    return payload


def test_h_validation_scores_exact_36_frozen_terminals_once_and_counts_576() -> None:
    calls: list[str] = []

    def scorer(candidate):
        calls.append(fingerprint_sbox(candidate))
        return _fake_score(candidate)

    result = validate_frozen_terminals(_freeze(), score_terminal=scorer)

    assert result["phase"] == "2G-heldout-H-validation"
    assert result["terminal_freeze_sha256"] == _freeze()["terminal_freeze_sha256"]
    assert result["cell_count"] == 36
    assert result["heldout_training_count"] == 576
    assert result["heldout_accessed"] is True
    assert len(result["records"]) == 36
    assert len(calls) == len(set(calls)) == 36
    assert all(record["training_count"] == 16 for record in result["records"])
    assert all(len(record["scientific_payload_sha256"]) == 64 for record in result["records"])
    assert len(result["validation_sha256"]) == 64


def test_h_validation_is_deterministic_for_same_freeze_and_scores() -> None:
    frozen = _freeze()
    first = validate_frozen_terminals(frozen, score_terminal=_fake_score)
    second = validate_frozen_terminals(copy.deepcopy(frozen), score_terminal=_fake_score)
    assert first == second


def test_h_validation_fails_closed_before_any_score_call_on_bad_freeze() -> None:
    frozen = _freeze()
    frozen["terminal_freeze_sha256"] = "0" * 64
    calls = 0

    def scorer(candidate):
        nonlocal calls
        calls += 1
        return _fake_score(candidate)

    with pytest.raises(ValueError, match="terminal freeze"):
        validate_frozen_terminals(frozen, score_terminal=scorer)
    assert calls == 0


def test_h_validation_rejects_training_count_or_fingerprint_drift() -> None:
    frozen = _freeze()

    def bad_count(candidate):
        payload = _fake_score(candidate)
        payload["training_count"] = 15
        clean = {k: v for k, v in payload.items() if k != "scientific_payload_sha256"}
        payload["scientific_payload_sha256"] = _sha_payload(clean)
        return payload

    with pytest.raises(ValueError, match="training-count"):
        validate_frozen_terminals(frozen, score_terminal=bad_count)

    def bad_fingerprint(candidate):
        payload = _fake_score(candidate)
        payload["fingerprint"] = "wrong"
        clean = {k: v for k, v in payload.items() if k != "scientific_payload_sha256"}
        payload["scientific_payload_sha256"] = _sha_payload(clean)
        return payload

    with pytest.raises(ValueError, match="fingerprint"):
        validate_frozen_terminals(frozen, score_terminal=bad_fingerprint)
