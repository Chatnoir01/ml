import pytest

from adversarial_sbox.pareto import (
    ITOAwareMetrics,
    dominates,
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
