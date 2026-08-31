import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1c import (
    CONFIRM_RESERVED_SEEDS,
    DEV_SEEDS,
    du_frontier_rank,
    run_development,
)


def test_phase1c_seed_sets_are_disjoint():
    assert not (set(DEV_SEEDS) & set(CONFIRM_RESERVED_SEEDS))


def test_du_gate_is_prioritized_before_higher_nl_outside_gate():
    constraints = HardConstraints()
    inside = ClassicalMetrics(98, 8, 60, 0.5, 7, "inside")
    outside = ClassicalMetrics(102, 10, 56, 0.5, 7, "outside")
    assert du_frontier_rank(inside, constraints) > du_frontier_rank(outside, constraints)


def test_nl_is_optimized_inside_du_frontier():
    constraints = HardConstraints()
    lower = ClassicalMetrics(98, 8, 60, 0.5, 7, "lower")
    target = ClassicalMetrics(100, 8, 64, 0.5, 7, "target")
    assert du_frontier_rank(target, constraints) > du_frontier_rank(lower, constraints)


def test_full_admissibility_remains_absolute():
    constraints = HardConstraints()
    admissible = ClassicalMetrics(100, 8, 64, 0.5, 7, "admissible")
    flashy_but_invalid = ClassicalMetrics(110, 10, 48, 0.5, 7, "invalid")
    assert du_frontier_rank(admissible, constraints) > du_frontier_rank(
        flashy_but_invalid, constraints
    )


def test_confirmation_seed_is_rejected_from_development():
    with pytest.raises(ValueError):
        run_development(
            seeds=(CONFIRM_RESERVED_SEEDS[0],),
            population_size=4,
            generations=1,
            elite_count=1,
            tournament_size=2,
            offspring_multiplier=1,
        )
