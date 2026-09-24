from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2h_evidence import build_evidence_manifest
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


def _manifest(raw: list[dict]) -> dict:
    return build_evidence_manifest(
        raw,
        parent_commit=PARENT_PHASE2G_COMMIT,
        parent_aggregate_sha256=PARENT_AGGREGATE_SHA256,
    )


def _inputs() -> list[dict]:
    out = []
    for seed in EVOLUTION_SEEDS:
        out.append(_receipt(int(seed), "A", adaptive=True))
        out.append(_receipt(int(seed), "F", adaptive=False))
    return out


def test_phase2h_is_deterministic_and_parent_bound() -> None:
    raw = _inputs()
    first = diagnose_phase2g_receipts(
        raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(raw),
    )
    reversed_raw = list(reversed(copy.deepcopy(raw)))
    second = diagnose_phase2g_receipts(
        reversed_raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(reversed_raw),
    )
    assert first == second
    assert first["parent_phase2g_commit"] == PARENT_PHASE2G_COMMIT
    assert len(first["diagnostic_sha256"]) == 64


def test_phase2h_fails_closed_on_wrong_parent() -> None:
    with pytest.raises(ValueError, match="parent aggregate"):
        diagnose_phase2g_receipts(_inputs(), phase2g_aggregate_sha256="0" * 64, evidence_manifest=_manifest(_inputs()))


def test_phase2h_requires_all_primary_cells() -> None:
    raw = _inputs()
    manifest = _manifest(raw)
    raw.pop()
    with pytest.raises(ValueError, match="incomplete Phase-2H input evidence"):
        diagnose_phase2g_receipts(
            raw,
            phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
            evidence_manifest=manifest,
        )


def test_phase2h_reports_unavailable_evidence_instead_of_inventing_it() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(),
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(_inputs()),
    )
    assert result["availability"]["forgetting_matrix"] is False
    assert result["availability"]["candidate_level_classical_distortion"] is True


def test_phase2h_detects_adaptive_drift_and_rank_change() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(),
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(_inputs()),
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_curriculum"]["changed_from_initial_count"] == 3
        assert row["F_curriculum"]["changed_from_initial_count"] == 0
        assert row["A_vs_F_rank"]["different_order_count"] == 1
        assert row["A_mechanism"]["score_caused_entry_event_count"] == 1


def test_phase2h_recurrence_does_not_call_movement_cycling() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(),
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(_inputs()),
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_recurrence"]["exact_curriculum_digest_recurrence"] is False
        assert row["F_recurrence"]["exact_curriculum_digest_recurrence"] is True


def test_phase2h_classical_distortion_fails_closed_without_ledger_rows() -> None:
    result = diagnose_phase2g_receipts(
        _inputs(),
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(_inputs()),
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_classical_distortion"]["paired_membership_changes"] == 0


def test_diagnostics_refuse_to_run_without_frozen_manifest() -> None:
    with pytest.raises(ValueError, match="requires a frozen evidence manifest"):
        diagnose_phase2g_receipts([], phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256)


def test_phase2h_h2_distinguishes_drift_from_cycling() -> None:
    raw = _inputs()
    result = diagnose_phase2g_receipts(
        raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(raw),
    )
    for seed in EVOLUTION_SEEDS:
        row = result["diagnostics"][str(int(seed))]
        assert row["A_H2_motion"]["classification"] == "drift_without_recurrence_or_rank_reversal"
        assert row["A_H2_motion"]["cycling_supported_by_receipts"] is False
        assert row["F_H2_motion"]["classification"] == "exact_recurrence_without_rank_reversal"
        assert row["F_H2_motion"]["cycling_supported_by_receipts"] is False


def test_phase2h_h2_requires_actual_rank_direction_reversal() -> None:
    raw = _inputs()
    adaptive = next(item for item in raw if item["arm"] == "A")
    adaptive["selection_events"].append({
        "generation": 10,
        "stage": "survivor",
        "neural_selection_enabled": True,
        "boundary_opportunity": True,
        "b1_group": ["a", "b", "c"],
        "scored_candidate_count": 3,
        "assigned_scores": {"a": 0.05, "b": 0.2, "c": 0.3},
        "cross_protected_key_membership_change": True,
        "score_caused_entered": ["a"],
    })
    result = diagnose_phase2g_receipts(
        raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(raw),
    )
    row = result["diagnostics"][str(int(adaptive["seed"]))]
    assert row["A_rank_reversal"]["true_rank_reversal_observed"] is True
    assert row["A_rank_reversal"]["pairwise_reversal_count"] >= 1
    # Rank reversal alone is still insufficient for a cycling claim.
    assert row["A_H2_motion"]["cycling_supported_by_receipts"] is False


def test_phase2h_never_promotes_checkpoint_ordering_to_causality() -> None:
    raw = _inputs()
    result = diagnose_phase2g_receipts(
        raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(raw),
    )
    causal = result["causal_interpretation"]
    assert causal["causal_claim_supported"] is False
    assert "observational" in causal["reason"]
    summary = result["A_vs_F_ordering_summary"]
    assert (
        summary["single_signal_first_count"]
        + summary["checkpoint_tie_count"]
        + summary["unresolved_count"]
        == len(EVOLUTION_SEEDS)
    )
    assert set(summary["claims"]) == {str(int(seed)) for seed in EVOLUTION_SEEDS}


def test_phase2h_mechanism_verdict_is_conservative_and_phase2g_immutable() -> None:
    raw = _inputs()
    result = diagnose_phase2g_receipts(
        raw,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=_manifest(raw),
    )
    assert result["mechanism_verdict"] == "phase2h_drift_without_cycling_evidence"
    basis = result["mechanism_verdict_basis"]
    assert basis["cycling_seed_count"] == 0
    assert basis["rank_reversal_seed_count"] == 0
    assert basis["A_motion_classification_counts"] == {
        "drift_without_recurrence_or_rank_reversal": len(EVOLUTION_SEEDS)
    }
    assert basis["scope"] == "receipt_level_diagnostics_only"
    assert basis["does_not_modify_phase2g_verdict"] is True
