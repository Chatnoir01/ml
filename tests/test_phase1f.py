import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints, equivalent_random_budget
from adversarial_sbox.experiment_seeds import PHASE1F_CONFIRM_RESERVED_SEEDS, PHASE1F_DEV_SEEDS
from adversarial_sbox.phase1f import (
    DISCOVERY_SPLITS,
    FULL_GA_GENERATIONS,
    TOTAL_BUDGET,
    bridge_region,
    ga_config,
    repair_rank,
    run_development,
    structural_target,
)


def metrics(*, nl=98, du=8, corr=60, degree=7, sac=0.5):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint="x",
    )


def test_phase1f_seed_sets_are_disjoint():
    assert set(PHASE1F_DEV_SEEDS).isdisjoint(PHASE1F_CONFIRM_RESERVED_SEEDS)


def test_preregistered_budget_splits_are_exact():
    assert equivalent_random_budget(ga_config(seed=0, generations=FULL_GA_GENERATIONS)) == TOTAL_BUDGET
    for generations in DISCOVERY_SPLITS.values():
        discovery = equivalent_random_budget(ga_config(seed=0, generations=generations))
        assert discovery < TOTAL_BUDGET
        assert discovery + (TOTAL_BUDGET - discovery) == TOTAL_BUDGET


def test_bridge_region_is_broad_but_structural_target_is_strict():
    constraints = HardConstraints()
    near = metrics(nl=98, du=10, corr=60, degree=7)
    target = metrics(nl=100, du=8, corr=60, degree=7)
    outside = metrics(nl=100, du=12, corr=60, degree=7)
    assert bridge_region(near, constraints)
    assert not structural_target(near, constraints)
    assert structural_target(target, constraints)
    assert not bridge_region(outside, constraints)


def test_repair_rank_prefers_structural_target_over_near_frontier():
    constraints = HardConstraints()
    near = metrics(nl=102, du=10, corr=60, degree=7)
    target = metrics(nl=100, du=8, corr=64, degree=7)
    assert repair_rank(target, constraints) > repair_rank(near, constraints)


def test_repair_rank_keeps_full_admissibility_absolute():
    constraints = HardConstraints()
    admissible = metrics(nl=100, du=8, corr=64, degree=6, sac=0.5)
    inadmissible = metrics(nl=112, du=8, corr=32, degree=7, sac=0.6)
    assert repair_rank(admissible, constraints) > repair_rank(inadmissible, constraints)


def test_confirmation_seed_is_rejected_before_any_experiment():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(discovery_generations=10, seeds=(PHASE1F_CONFIRM_RESERVED_SEEDS[0],))
