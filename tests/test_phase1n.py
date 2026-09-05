import random

import pytest

from adversarial_sbox.cryptoshield import is_bijective
from adversarial_sbox.experiment_seeds import (
    PHASE1N_CONFIRM_RESERVED_SEEDS,
    PHASE1N_DEV_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1m import CLASSICAL_BUDGET as PHASE1M_CLASSICAL_BUDGET
from adversarial_sbox.phase1n import (
    CLASSICAL_BUDGET,
    ITO_NONINFERIORITY_TOLERANCE,
    aggregate_development,
    joint_du_walsh_swap_proposals,
    run_seed,
    worst_walsh_hotspots,
)


def test_phase1n_seed_registry_is_frozen_and_disjoint():
    validate_seed_registry()
    assert PHASE1N_DEV_SEEDS == (2309, 2311, 2333, 2339, 2341)
    assert PHASE1N_CONFIRM_RESERVED_SEEDS == (
        2401,
        2411,
        2417,
        2423,
        2437,
        2441,
        2447,
        2459,
        2467,
    )


def test_phase1n_budget_and_ito_guard_match_frozen_phase1m_budget():
    assert CLASSICAL_BUDGET == 340
    assert PHASE1M_CLASSICAL_BUDGET == 340
    assert ITO_NONINFERIORITY_TOLERANCE == pytest.approx(0.02)


def test_worst_walsh_hotspots_exclude_trivial_pair_and_match_max_abs():
    sbox = tuple(range(256))
    hotspots = worst_walsh_hotspots(sbox)

    assert hotspots
    max_abs = abs(hotspots[0].coefficient)
    assert max_abs == 256
    assert all(abs(item.coefficient) == max_abs for item in hotspots)
    assert all(item.output_mask != 0 for item in hotspots)
    assert all(not (item.input_mask == 0 and item.output_mask == 0) for item in hotspots)


def test_joint_proposals_are_bijective_deterministic_unique_and_auditable():
    sbox = tuple(range(256))

    left = joint_du_walsh_swap_proposals(sbox, random.Random(13579), count=8)
    right = joint_du_walsh_swap_proposals(sbox, random.Random(13579), count=8)

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
        assert proposal.output_mask != 0
        if not proposal.fallback:
            guided += 1
            assert proposal.predicted_walsh_delta != 0
            assert abs(proposal.old_walsh_coefficient + proposal.predicted_walsh_delta) < abs(
                proposal.old_walsh_coefficient
            )
    assert guided >= 1


def test_joint_operator_rejects_non_bijective_input():
    with pytest.raises(ValueError, match="bijective"):
        joint_du_walsh_swap_proposals(
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
        "phase": "1N",
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


def test_phase1n_aggregate_requires_every_frozen_gate():
    passing = [_seed_payload(seed=seed) for seed in PHASE1N_DEV_SEEDS]
    result = aggregate_development(passing)
    assert result["verdict"] == "phase1n_dev_pass"
    assert all(result["development_checks"].values())

    only_one_joint_seed = [
        _seed_payload(seed=seed, joint_a=(1 if index == 0 else 0))
        for index, seed in enumerate(PHASE1N_DEV_SEEDS)
    ]
    result = aggregate_development(only_one_joint_seed)
    assert result["development_checks"]["joint_seed_successes_ge_2"] is False
    assert result["verdict"] == "phase1n_dev_fail"

    hidden_budget = passing.copy()
    hidden_budget[0] = {
        **hidden_budget[0],
        "arm_a": {**hidden_budget[0]["arm_a"], "classical_evaluations": 341},
    }
    assert aggregate_development(hidden_budget)["verdict"] == "phase1n_dev_fail"


def test_phase1n_run_rejects_unregistered_seed_before_work():
    with pytest.raises(ValueError, match="Phase 1N development seed"):
        run_seed(99991)
