from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1c_benchmark import (
    balanced_primary_key,
    structural_violation_profile,
)


def _metrics(*, nl, du, corr=60, degree=7, sac=0.5, name="x"):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint=name,
    )


def test_balanced_key_rejects_large_du_regression_hidden_by_nl_gain():
    constraints = HardConstraints()
    high_nl_bad_du = _metrics(nl=98, du=12, name="high-nl-bad-du")
    lower_nl_better_du = _metrics(nl=96, du=10, corr=64, name="balanced")

    assert balanced_primary_key(lower_nl_better_du, constraints) > balanced_primary_key(
        high_nl_bad_du, constraints
    )


def test_balanced_key_prefers_nl_gain_when_du_bottleneck_is_equal():
    constraints = HardConstraints()
    better = _metrics(nl=98, du=10, name="better")
    worse = _metrics(nl=96, du=10, corr=64, name="worse")

    assert balanced_primary_key(better, constraints) > balanced_primary_key(
        worse, constraints
    )


def test_candidate_at_du_gate_beats_candidate_farther_from_du_gate():
    constraints = HardConstraints()
    near = _metrics(nl=98, du=8, name="near")
    farther = _metrics(nl=100, du=10, name="farther")

    assert balanced_primary_key(near, constraints) > balanced_primary_key(
        farther, constraints
    )
    assert max(structural_violation_profile(near, constraints)) == 0.02
    assert max(structural_violation_profile(farther, constraints)) == 0.25


def test_structural_profile_is_zero_inside_all_structural_gates():
    constraints = HardConstraints()
    strong = _metrics(nl=112, du=4, corr=32, degree=7, name="strong")
    assert structural_violation_profile(strong, constraints) == (0.0, 0.0, 0.0, 0.0)
