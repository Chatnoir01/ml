import random

import pytest

from adversarial_sbox.cryptoshield import is_bijective
from adversarial_sbox.experiment_seeds import (
    PHASE1O_CONFIRM_RESERVED_SEEDS,
    PHASE1O_DEV_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1n import CLASSICAL_BUDGET as PHASE1N_CLASSICAL_BUDGET
from adversarial_sbox.phase1o import (
    CLASSICAL_BUDGET,
    ITO_NONINFERIORITY_TOLERANCE,
    aggregate_development,
    multihotspot_walsh_swap_proposals,
    run_seed,
    score_swap_on_walsh_plateau,
    walsh_maximum_plateau,
)


def test_phase1o_seed_registry_is_frozen_and_disjoint():
    validate_seed_registry()
    assert PHASE1O_DEV_SEEDS == (2503, 2521, 2531, 2539, 2543)
    assert PHASE1O_CONFIRM_RESERVED_SEEDS == (
        2609,
        2617,
        2621,
        2633,
        2647,
        2657,
        2663,
        2671,
        2683,
    )


def test_phase1o_budget_and_ito_guard_match_frozen_phase1n_geometry():
    assert CLASSICAL_BUDGET == 340
    assert PHASE1N_CLASSICAL_BUDGET == 340
    assert ITO_NONINFERIORITY_TOLERANCE == pytest.approx(0.02)


def test_walsh_maximum_plateau_contains_every_tied_parent_maximum():
    sbox = tuple(range(256))
    plateau = walsh_maximum_plateau(sbox)

    assert plateau
    assert abs(plateau[0].coefficient) == 256
    assert all(abs(item.coefficient) == 256 for item in plateau)
    assert all(item.output_mask != 0 for item in plateau)
    # Identity has one perfect correlation for every nonzero output component.
    assert len(plateau) == 255


def test_plateau_swap_score_uses_all_tied_maxima_and_is_deterministic():
    sbox = tuple(range(256))
    plateau = walsh_maximum_plateau(sbox)

    left = score_swap_on_walsh_plateau(sbox, 0, 1, plateau)
    right = score_swap_on_walsh_plateau(sbox, 0, 1, plateau)

    assert left == right
    assert left.plateau_size == len(plateau)
    assert left.old_max_abs == 256
    assert left.predicted_max_abs <= 256
    assert left.improved_count >= 1
    assert left.worsened_count == 0
    assert left.total_abs_reduction > 0


def test_multihotspot_proposals_are_bijective_deterministic_unique_and_auditable():
    sbox = tuple(range(256))

    left = multihotspot_walsh_swap_proposals(sbox, random.Random(24680), count=8)
    right = multihotspot_walsh_swap_proposals(sbox, random.Random(24680), count=8)

    assert left == right
    assert len(left) == 8
    assert len({proposal.sbox for proposal in left}) == 8

    guided = 0
    for proposal in left:
        assert is_bijective(proposal.sbox)
        assert proposal.sbox != sbox
        assert 1 <= proposal.input_difference <= 255
        assert proposal.hotspot_count >= 2
        assert proposal.anchor_a in proposal.hotspot_positions
        assert proposal.anchor_a != proposal.anchor_b
        assert proposal.plateau_size >= 1
        if not proposal.fallback:
            guided += 1
            assert proposal.score.improved_count >= 1
            assert proposal.score.predicted_max_abs <= proposal.score.old_max_abs
            assert proposal.score.total_abs_reduction > 0
    assert guided >= 1


def test_multihotspot_operator_rejects_non_bijective_input():
    with pytest.raises(ValueError, match="bijective"):
        multihotspot_walsh_swap_proposals(
            tuple(0 for _ in range(256)), random.Random(1), count=2
        )


def _seed_payload(
    *,
    seed: int,
    joint_a: int = 1,
    joint_b: int = 0,
    du8_a: int = 1,
    du8_b: int = 0,
    best_du_a: int = 8,
    best_du_b: int = 10,
    protected_a: int = 2,
    protected_b: int = 1,
    min_ito_a: float = 6.84,
    min_ito_b: float = 6.85,
    digest: str = "same",
):
    return {
        "phase": "1O",
        "seed": seed,
        "initial_population_digest_sha256": digest,
        "arm_a": {
            "joint_target_count": joint_a,
            "du8_count": du8_a,
            "best_du": best_du_a,
            "protected_classical_count": protected_a,
            "min_ito": min_ito_a,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_b": {
            "joint_target_count": joint_b,
            "du8_count": du8_b,
            "best_du": best_du_b,
            "protected_classical_count": protected_b,
            "min_ito": min_ito_b,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_c": {
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "deterministic_payload_match": True,
        "neural_oracle_executed": False,
    }


def test_phase1o_aggregate_requires_every_frozen_gate():
    passing = [_seed_payload(seed=seed) for seed in PHASE1O_DEV_SEEDS]
    result = aggregate_development(passing)
    assert result["verdict"] == "phase1o_dev_pass"
    assert all(result["development_checks"].values())

    no_joint_advantage = [
        _seed_payload(seed=seed, joint_a=0, joint_b=0)
        for seed in PHASE1O_DEV_SEEDS
    ]
    result = aggregate_development(no_joint_advantage)
    assert result["development_checks"]["joint_aggregate_advantage"] is False
    assert result["development_checks"]["joint_seed_successes_ge_2"] is False
    assert result["verdict"] == "phase1o_dev_fail"

    hidden_budget = passing.copy()
    hidden_budget[0] = {
        **hidden_budget[0],
        "arm_a": {**hidden_budget[0]["arm_a"], "classical_evaluations": 341},
    }
    assert aggregate_development(hidden_budget)["verdict"] == "phase1o_dev_fail"


def test_phase1o_run_rejects_unregistered_seed_before_work():
    with pytest.raises(ValueError, match="Phase 1O development seed"):
        run_seed(99991)
