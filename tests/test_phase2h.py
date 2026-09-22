from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2h import (
    PARENT_AGGREGATE_SHA256,
    PARENT_PHASE2G_COMMIT,
    diagnose_phase2g_receipts,
)


def _receipt(seed: int, arm: str, *, adaptive: bool) -> dict:
    checkpoints = []
    for generation in CHECKPOINT_GENERATIONS:
        token = generation if adaptive else 0
        checkpoints.append(
            {
                "generation": generation,
                "training_count": 16,
                "training_receipt_sha256": ("%064x" % (seed + generation + 1)),
                "curriculum_digest_sha256": ("%064x" % (seed + token + 1000)),
            }
        )
    group = ["a", "b", "c"]
    return {
        "phase": "2G",
        "seed": seed,
        "arm": arm,
        "checkpoints": checkpoints,
        "selection_events": [
            {
                "generation": 5,
                "stage": "survivor",
                "neural_selection_enabled": True,
                "boundary_opportunity": True,
                "b1_group": group,
                "scored_candidate_count": 3,
                "assigned_scores": (
                    {"a": 0.3, "b": 0.1, "c": 0.2}
                    if adaptive
                    else {"a": 0.1, "b": 0.2, "c": 0.3}
                ),
                "cross_protected_key_membership_change": adaptive,
                "score_caused_entered": ["b"] if adaptive else [],
            }
        ],
    }


def _inputs() -> list[dict]:
    out = []
    for seed in EVOLUTION_SEEDS:
        out.append(_receipt(int(seed), "A", adaptive=True))
        out.append(_receipt(int(seed), "F", adaptive=False))
    return out


def test_phase2h_is_deterministic_and_parent_bound() -> None:
    raw = _inputs()
    first = diagnose_phase2g_receipts(raw, phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256)
    second = diagnose_phase2g_receipts(
        list(reversed(copy.deepcopy(raw))),
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
    )
    assert first == second
    assert first["parent_phase2g_commit"] == PARENT_PHASE2G_COMMIT
    assert len(first["diagnostic_sha256"]) == 64


def test_phase2h_fails_closed_on_wrong_parent() -> None:
    with pytest.raises(ValueError, match="parent aggregate"):
        diagnose_phase2g_receipts(_inputs(), phase2g_aggregate_sha256="0" * 64)


def test_phase2h_requires_all_primary_cells() -> None:
    raw = _inputs()
    raw.pop()
    with pytest.raises(ValueError, match="missing primary"):
        diagnose_phase2g_receipts(raw, phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256)


def test_phase2h_reports_unavailable_evidence_instead_of_inventing_it() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(), phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256
    )
    assert result["availability"]["forgetting_matrix"] is False
    assert result["availability"]["candidate_level_classical_distortion"] is True


def test_phase2h_detects_adaptive_drift_and_rank_change() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(), phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_curriculum"]["changed_from_initial_count"] == 3
        assert row["F_curriculum"]["changed_from_initial_count"] == 0
        assert row["A_vs_F_rank"]["different_order_count"] == 1
        assert row["A_mechanism"]["score_caused_entry_event_count"] == 1


def test_phase2h_recurrence_does_not_call_movement_cycling() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(), phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_recurrence"]["exact_curriculum_digest_recurrence"] is False
        assert row["F_recurrence"]["exact_curriculum_digest_recurrence"] is True


def test_phase2h_classical_distortion_fails_closed_without_ledger_rows() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(), phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_classical_distortion"]["paired_membership_changes"] == 0
