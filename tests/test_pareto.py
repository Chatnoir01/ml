import pytest

from adversarial_sbox.evolution import ClassicalMetrics
from adversarial_sbox.pareto import (
    ITOAwareMetrics,
    StagedParetoConfig,
    dominates,
    evolve_staged_pareto,
    non_dominated_sort,
    objective_vector,
    select_nsga2,
)


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


def test_objective_vector_has_security_direction_normalized_to_higher_is_better():
    metrics = _m(104, 6, 48, 6.5, sac=0.49, degree=7)
    assert objective_vector(metrics) == pytest.approx(
        (104.0, -6.0, -48.0, -6.5, -0.01, 7.0)
    )


def test_strict_pareto_dominance_requires_no_regression_and_one_improvement():
    stronger = _m(104, 6, 48, 6.4, fingerprint="strong")
    weaker = _m(102, 8, 56, 6.9, fingerprint="weak")
    tradeoff = _m(106, 10, 48, 6.2, fingerprint="tradeoff")

    assert dominates(stronger, weaker)
    assert not dominates(weaker, stronger)
    assert not dominates(stronger, tradeoff)
    assert not dominates(tradeoff, stronger)


def test_non_dominated_sort_keeps_tradeoffs_on_first_front():
    weak = _m(100, 10, 64, 7.0, fingerprint="weak")
    balanced = _m(104, 8, 56, 6.8, fingerprint="balanced")
    low_ito = _m(102, 8, 56, 6.2, fingerprint="low-ito")
    high_nl = _m(106, 10, 56, 6.8, fingerprint="high-nl")

    fronts = non_dominated_sort((weak, balanced, low_ito, high_nl))

    assert set(fronts[0]) == {1, 2, 3}
    assert fronts[1] == (0,)


def test_nsga2_selection_is_deterministic_and_preserves_first_front_before_dominated():
    metrics = (
        _m(100, 10, 64, 7.0, fingerprint="weak"),
        _m(104, 8, 56, 6.8, fingerprint="balanced"),
        _m(102, 8, 56, 6.2, fingerprint="low-ito"),
        _m(106, 10, 56, 6.8, fingerprint="high-nl"),
    )

    first = select_nsga2(metrics, 3)
    second = select_nsga2(metrics, 3)

    assert first == second
    assert set(first) == {1, 2, 3}


def _fake_classical(sbox):
    checksum = sum((index ^ value) & 0xFF for index, value in enumerate(sbox))
    return ClassicalMetrics(
        nonlinearity=96 + checksum % 9,
        differential_uniformity=8 + 2 * (sbox[0] % 3),
        max_linear_correlation=52 + 4 * (sbox[1] % 4),
        sac_score=0.5 + ((sbox[2] % 5) - 2) / 1000.0,
        algebraic_degree=6 + sbox[3] % 2,
        fingerprint=f"fake-{checksum}-{sbox[0]}-{sbox[1]}",
    )


def _fake_ito(sbox):
    return 6.0 + ((sbox[4] * 257 + sbox[5]) % 1000) / 1000.0


def test_staged_pareto_search_is_deterministic_and_caps_expensive_ito_work():
    config = StagedParetoConfig(
        population_size=8,
        generations=2,
        shortlist_size=4,
        parent_count=2,
        mutation_swaps=2,
        crossover_rate=0.5,
        seed=31415,
    )

    first = evolve_staged_pareto(
        config,
        classical_evaluator=_fake_classical,
        ito_evaluator=_fake_ito,
    )
    second = evolve_staged_pareto(
        config,
        classical_evaluator=_fake_classical,
        ito_evaluator=_fake_ito,
    )

    assert first == second
    assert first.pareto_sboxes
    assert len(first.pareto_sboxes) == len(first.pareto_metrics)
    assert first.classical_evaluations > first.ito_evaluations
    assert first.ito_evaluations <= config.shortlist_size * (config.generations + 1)
    assert len(first.front_size_history) == config.generations


def test_staged_pareto_config_rejects_shortlist_larger_than_population():
    with pytest.raises(ValueError, match="shortlist_size"):
        StagedParetoConfig(population_size=8, shortlist_size=9)
