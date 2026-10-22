"""Strict H2 recurrence/reversal diagnostics, using synthetic receipts only."""

from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2h import _recurrence, _rank_reversals


def _arm(*, missing: bool = False) -> dict:
    checkpoints = []
    for generation, tokens in (
        (0, ("a", "b")),
        (5, ("c", "d")),
        (10, ("a", "b")),
        (15, ("e", "f")),
    ):
        row = {
            "generation": generation,
            "curriculum_digest_sha256": f"{generation + 1:064x}",
            "curriculum_fingerprints": list(tokens),
            "population_after_fingerprints": list(tokens),
        }
        checkpoints.append(row)
    if missing:
        for row in checkpoints:
            row.pop("curriculum_fingerprints")
            row.pop("population_after_fingerprints")
    return {"checkpoints": checkpoints, "selection_events": []}


def _event(*, generation: int, stage: str, reversed_order: bool = False) -> dict:
    return {
        "generation": generation,
        "stage": stage,
        "b1_group": ["a", "b"],
        "scored_candidate_count": 2,
        "assigned_scores": (
            {"a": 0.3, "b": 0.1}
            if reversed_order else {"a": 0.1, "b": 0.3}
        ),
    }


def test_h2_matrix_covers_all_six_pairs_with_explicit_fingerprint_recurrence() -> None:
    result = _recurrence(_arm())
    matrix = result["checkpoint_fingerprint_recurrence_matrix"]
    assert result["checkpoint_pair_count"] == 6
    assert result["curriculum_pairs_comparable"] == 6
    assert result["population_pairs_comparable"] == 6
    assert len(result["nonadjacent_checkpoint_overlap"]) == 3
    row = next(x for x in matrix if (x["left_generation"], x["right_generation"]) == (0, 10))
    assert row["adjacent"] is False
    assert row["curriculum_identical"] is True
    assert row["curriculum_jaccard"] == 1.0
    assert row["curriculum_shared_fingerprint_count"] == 2
    adjacent = next(x for x in matrix if (x["left_generation"], x["right_generation"]) == (0, 5))
    assert adjacent["curriculum_identical"] is False
    assert adjacent["curriculum_jaccard"] == 0.0


def test_missing_checkpoint_sets_cannot_be_false_perfect_jaccard() -> None:
    result = _recurrence(_arm(missing=True))
    assert result["checkpoint_pair_count"] == 6
    assert result["curriculum_pairs_comparable"] == 0
    assert result["population_pairs_comparable"] == 0
    assert all(row["curriculum_jaccard"] is None for row in result["checkpoint_fingerprint_recurrence_matrix"])
    assert all(row["population_identical"] is None for row in result["checkpoint_fingerprint_recurrence_matrix"])
    assert result["exact_curriculum_digest_recurrence"] is False


def test_duplicate_or_malformed_checkpoint_fingerprint_refuses_comparison() -> None:
    arm = _arm()
    arm["checkpoints"][0]["curriculum_fingerprints"] = ["a", "a"]
    with pytest.raises(ValueError, match="duplicate curriculum_fingerprints"):
        _recurrence(arm)
    arm = _arm()
    arm["checkpoints"][0]["population_after_fingerprints"] = "a"
    with pytest.raises(ValueError, match="malformed population_after_fingerprints"):
        _recurrence(arm)


def test_same_generation_across_selection_stages_is_not_temporal_reversal() -> None:
    arm = {"selection_events": [
        _event(generation=5, stage="shortlist"),
        _event(generation=5, stage="survivor", reversed_order=True),
    ]}
    result = _rank_reversals(arm)
    assert result["pairwise_reversal_count"] == 0
    assert result["true_rank_reversal_observed"] is False


def test_only_same_stage_observations_at_distinct_generations_can_reverse() -> None:
    arm = {"selection_events": [
        _event(generation=5, stage="shortlist"),
        _event(generation=10, stage="survivor", reversed_order=True),
        _event(generation=15, stage="shortlist", reversed_order=True),
    ]}
    result = _rank_reversals(arm)
    assert result["true_rank_reversal_observed"] is True
    assert result["pairwise_reversal_count"] == 1
    assert result["pairwise_reversals"][0]["stage"] == "shortlist"
    assert [x["generation"] for x in result["pairwise_reversals"][0]["observations"]] == [5, 15]


def test_same_stage_same_generation_conflict_is_ambiguous_not_reversal() -> None:
    arm = {"selection_events": [
        _event(generation=5, stage="survivor"),
        _event(generation=5, stage="survivor", reversed_order=True),
        _event(generation=10, stage="survivor", reversed_order=True),
    ]}
    result = _rank_reversals(arm)
    assert result["true_rank_reversal_observed"] is False
    assert result["ambiguous_pair_stage_count"] == 1
    assert result["ambiguous_pairs"][0]["conflicting_generations"] == [5]


def test_event_order_does_not_modify_temporal_results() -> None:
    events = [
        _event(generation=5, stage="survivor"),
        _event(generation=10, stage="survivor", reversed_order=True),
        _event(generation=15, stage="shortlist"),
    ]
    first = _rank_reversals({"selection_events": events})
    second = _rank_reversals({"selection_events": list(reversed(copy.deepcopy(events)))})
    assert first == second
