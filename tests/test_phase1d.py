import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1d import (
    CONFIRM_RESERVED_SEEDS,
    DEV_SEEDS,
    continuation_rank,
    run_development,
)


def test_phase1d_seed_sets_are_disjoint():
    assert not (set(DEV_SEEDS) & set(CONFIRM_RESERVED_SEEDS))


def test_continuation_rank_preserves_du_frontier_before_nl_gain():
    constraints = HardConstraints()
    frontier = ClassicalMetrics(98, 8, 60, 0.5, 7, "frontier")
    higher_nl_but_du_regression = ClassicalMetrics(102, 10, 56, 0.5, 7, "regress")
    assert continuation_rank(frontier, constraints) > continuation_rank(
        higher_nl_but_du_regression, constraints
    )


def test_continuation_rank_rewards_nl100_inside_frontier():
    constraints = HardConstraints()
    start = ClassicalMetrics(98, 8, 60, 0.5, 7, "start")
    target = ClassicalMetrics(100, 8, 60, 0.5, 7, "target")
    assert continuation_rank(target, constraints) > continuation_rank(start, constraints)


def test_full_admissibility_remains_absolute():
    constraints = HardConstraints()
    admissible = ClassicalMetrics(100, 8, 64, 0.5, 7, "ok")
    non_admissible = ClassicalMetrics(110, 10, 48, 0.5, 7, "bad-du")
    assert continuation_rank(admissible, constraints) > continuation_rank(
        non_admissible, constraints
    )


def test_confirmation_seed_is_rejected_from_development_before_reproduction():
    with pytest.raises(ValueError):
        run_development(seeds=(CONFIRM_RESERVED_SEEDS[0],), evaluations=1)
