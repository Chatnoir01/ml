"""RED contract for deterministic post-H Phase 2G aggregation.

Synthetic only: this test performs no neural training, evolution, or real held-out
H access. It freezes 36 synthetic full-provenance arm receipts, validates them
with an injected synthetic H scorer, and requires the exact frozen ten checks.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from adversarial_sbox.phase2g import (
    ARMS,
    EVOLUTION_SEEDS,
    SUPPORT_CHECKS,
    TOTAL_CHECKPOINT_TRAININGS,
    TOTAL_HELDOUT_TRAININGS,
    TOTAL_SCIENTIFIC_TRAININGS,
)
from adversarial_sbox.phase2g_aggregate import aggregate_phase2g_results
from adversarial_sbox.phase2g_terminal_freeze import freeze_phase2g_terminals
from adversarial_sbox.phase2g_validation import validate_frozen_terminals
from adversarial_sbox.provenance import fingerprint_sbox
from phase2g_full_fixture import make_full_cell, sha_text


def _canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _attach_sha(payload: dict, field: str = "scientific_payload_sha256") -> dict:
    clean = {key: value for key, value in payload.items() if key != field}
    payload[field] = hashlib.sha256(_canonical(clean)).hexdigest()
    return payload


def _terminal_classical(arm: str) -> dict:
    if arm == "A":
        return {
            "admissible": True,
            "nonlinearity": 109,
            "differential_uniformity": 4,
            "max_abs_lat": 29,
            "algebraic_degree": 7,
        }
    return {
        "admissible": True,
        "nonlinearity": 108,
        "differential_uniformity": 4,
        "max_abs_lat": 30,
        "algebraic_degree": 7,
    }


def _ordering_event(seed: int, arm: str) -> dict:
    first = sha_text(f"phase2g-band:{seed}:first")
    second = sha_text(f"phase2g-band:{seed}:second")
    group = [first, second]
    if arm == "F":
        assigned = {first: 0.10, second: 0.20}
    else:
        assigned = {first: 0.20, second: 0.10}
    entered = [second] if arm == "A" else []
    exited = [first] if arm == "A" else []
    return {
        "generation": 5,
        "stage": "survival",
        "cutoff": 20,
        "neural_selection_enabled": True,
        "boundary_opportunity": True,
        "b1_group": group,
        "scored_candidate_count": 2,
        "assigned_scores": assigned,
        "selected_before": [first],
        "selected_after": [second] if arm == "A" else [first],
        "entered": entered,
        "exited": exited,
        "score_caused_entered": entered,
        "cross_protected_key_membership_change": bool(arm == "A"),
    }


def _arm_result(seed_index: int, arm_index: int, seed: int, arm: str) -> dict:
    events = [_ordering_event(seed, arm)] if arm in {"A", "F"} else []
    return make_full_cell(
        seed=int(seed),
        arm=arm,
        arm_index=arm_index,
        terminal_offset=1 + (seed_index * len(ARMS)) + arm_index,
        terminal_classical=_terminal_classical(arm),
        selection_events=events,
    )


def _synthetic_inputs():
    arm_results = [
        _arm_result(seed_index, arm_index, int(seed), arm)
        for seed_index, seed in enumerate(EVOLUTION_SEEDS)
        for arm_index, arm in enumerate(ARMS)
    ]
    freeze = freeze_phase2g_terminals(arm_results)

    score_by_fingerprint = {}
    score_by_arm = {"A": 0.10, "F": 0.14, "S": 0.13, "C": 0.12}
    for result in arm_results:
        score_by_fingerprint[result["terminal_fingerprint"]] = score_by_arm[result["arm"]]

    def scorer(candidate):
        fingerprint = fingerprint_sbox(candidate)
        payload = {
            "purpose": "validation",
            "fingerprint": fingerprint,
            "training_count": 16,
            "neural_advantage": score_by_fingerprint[fingerprint],
        }
        return _attach_sha(payload)

    validation = validate_frozen_terminals(freeze, score_terminal=scorer)
    return arm_results, freeze, validation


def test_phase2g_aggregate_is_byte_deterministic_and_applies_exact_support_rule():
    arm_results, freeze, validation = _synthetic_inputs()

    first = aggregate_phase2g_results(
        arm_results=list(reversed(arm_results)),
        terminal_freeze=freeze,
        heldout_validation=validation,
    )
    second = aggregate_phase2g_results(
        arm_results=arm_results,
        terminal_freeze=freeze,
        heldout_validation=validation,
    )

    assert first == second
    assert _canonical(first) == _canonical(second)
    assert first["phase"] == "2G-aggregate"
    assert first["cell_count"] == 36
    assert first["checkpoint_training_count"] == TOTAL_CHECKPOINT_TRAININGS == 2304
    assert first["heldout_training_count"] == TOTAL_HELDOUT_TRAININGS == 576
    assert first["total_training_count"] == TOTAL_SCIENTIFIC_TRAININGS == 2880

    assert first["adaptation_activity"]["curriculum_changed_seed_count"] == 9
    assert first["adaptation_activity"]["score_ordering_changed_seed_count"] == 9
    assert first["adaptation_activity"]["passes"] is True
    assert first["mechanism_activity"]["cross_key_seed_count"] == 9
    assert first["mechanism_activity"]["passes"] is True

    assert first["heldout_comparisons"]["wins_vs_fixed"] == 9
    assert first["heldout_comparisons"]["sign_test_vs_fixed_p"] == pytest.approx(1 / 512)
    assert first["heldout_comparisons"]["mean_fixed_minus_adaptive"] == pytest.approx(0.04)
    assert first["heldout_comparisons"]["wins_vs_shuffled"] == 9
    assert first["heldout_comparisons"]["mean_adaptive"] < first["heldout_comparisons"]["mean_shuffled"]
    assert first["heldout_comparisons"]["wins_vs_control"] == 9
    assert first["heldout_comparisons"]["mean_adaptive"] < first["heldout_comparisons"]["mean_control"]

    assert first["classical_non_degradation"]["passing_seed_count"] == 9
    assert first["classical_non_degradation"]["passes"] is True
    assert tuple(first["support_checks"].keys()) == SUPPORT_CHECKS
    assert all(first["support_checks"].values())
    assert first["verdict"] == "phase2g_adaptive_coevolution_supported"

    stored = first["aggregate_sha256"]
    clean = {key: value for key, value in first.items() if key != "aggregate_sha256"}
    assert stored == hashlib.sha256(_canonical(clean)).hexdigest()


def test_phase2g_aggregate_fails_closed_if_validation_is_not_bound_to_freeze():
    arm_results, freeze, validation = _synthetic_inputs()
    tampered = json.loads(json.dumps(validation))
    tampered["terminal_freeze_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="freeze|validation|receipt|integrity"):
        aggregate_phase2g_results(
            arm_results=arm_results,
            terminal_freeze=freeze,
            heldout_validation=tampered,
        )
