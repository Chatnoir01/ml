from adversarial_sbox.experiment_seeds import (
    PHASE1L_CONFIRM_RESERVED_SEEDS,
    PHASE1L_DEV_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1l import (
    CLASSICAL_BUDGET,
    GA_GENERATIONS,
    PARETO_GENERATIONS,
    POPULATION_SIZE,
    aggregate_development,
    pareto_set_coverage,
)
from adversarial_sbox.pareto import ITOAwareMetrics


def _m(nl, du, corr, ito, sac=0.5, degree=7, fingerprint="x"):
    return ITOAwareMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        improved_transparency_order=ito,
        fingerprint=fingerprint,
    )


def test_phase1l_seed_registry_is_frozen_and_disjoint():
    validate_seed_registry()
    assert PHASE1L_DEV_SEEDS == (1901, 1907, 1913, 1931, 1933)
    assert PHASE1L_CONFIRM_RESERVED_SEEDS == (
        2003,
        2011,
        2017,
        2027,
        2029,
        2039,
        2053,
        2063,
        2069,
    )


def test_phase1l_matched_classical_budget_is_exactly_340():
    assert POPULATION_SIZE == 20
    assert PARETO_GENERATIONS == 20
    assert GA_GENERATIONS == 10
    assert CLASSICAL_BUDGET == 340


def test_pareto_set_coverage_is_directional_and_weight_free():
    strong = _m(104, 6, 48, 6.3, fingerprint="strong")
    tradeoff = _m(106, 10, 48, 6.1, fingerprint="tradeoff")
    weak = _m(100, 10, 64, 7.0, fingerprint="weak")

    assert pareto_set_coverage((strong, tradeoff), (weak,)) == 1.0
    assert pareto_set_coverage((weak,), (strong, tradeoff)) == 0.0


def test_aggregate_development_requires_every_frozen_gate():
    passing_seed = {
        "coverage_a_b": 0.75,
        "coverage_b_a": 0.25,
        "arm_a": {
            "min_ito": 6.20,
            "hard_admissible_count": 1,
            "structural_target_count": 1,
            "classical_evaluations": 340,
        },
        "arm_b": {
            "min_ito": 6.50,
            "hard_admissible_count": 0,
            "structural_target_count": 0,
            "classical_evaluations": 340,
        },
        "arm_c": {"classical_evaluations": 340},
    }
    result = aggregate_development([passing_seed] * 5)
    assert result["verdict"] == "phase1l_dev_pass"

    failing = dict(passing_seed)
    failing["coverage_a_b"] = 0.0
    failing["coverage_b_a"] = 1.0
    result = aggregate_development([failing] + [passing_seed] * 4)
    assert result["summary"]["coverage_losses"] == 1

    broken_budget = {
        **passing_seed,
        "arm_c": {"classical_evaluations": 339},
    }
    result = aggregate_development([broken_budget] + [passing_seed] * 4)
    assert result["verdict"] == "phase1l_dev_fail"
