"""Red-first contracts for the Phase-2A neural qualification runner/analysis."""

from adversarial_sbox.phase2a_neural import (
    CELL_SPECS,
    PERMUTATION_REPETITIONS,
    TOTAL_TRAININGS,
    TRAININGS_PER_CELL,
    blocked_heterogeneity_p,
    build_qualification_checks,
    spearman_correlation,
)


def test_phase2a_neural_factorial_contract():
    assert CELL_SPECS == (
        ("oracle", 4, 0x00000001, "bit_relu_mlp"),
        ("oracle", 4, 0x00000100, "bit_relu_mlp"),
        ("challenger", 5, 0x00010000, "byte_tanh_mlp"),
        ("challenger", 5, 0x01000000, "byte_tanh_mlp"),
    )
    assert TRAININGS_PER_CELL == 30
    assert TOTAL_TRAININGS == 120
    assert PERMUTATION_REPETITIONS == 10000


def test_blocked_heterogeneity_supports_six_candidates_and_is_deterministic():
    blocks = [
        [0.01, 0.03, 0.05, 0.07, 0.09, 0.11],
        [0.02, 0.04, 0.06, 0.08, 0.10, 0.12],
        [0.00, 0.02, 0.04, 0.06, 0.08, 0.10],
        [0.01, 0.04, 0.05, 0.08, 0.09, 0.12],
    ]
    first = blocked_heterogeneity_p(blocks, repetitions=500, seed=930001)
    second = blocked_heterogeneity_p(blocks, repetitions=500, seed=930001)
    assert first == second
    statistic, p_value = first
    assert statistic > 0.0
    assert 0.0 < p_value <= 1.0


def test_phase2a_spearman_replication_contract():
    assert spearman_correlation([1, 2, 3, 4, 5, 6], [10, 20, 30, 40, 50, 60]) == 1.0
    assert spearman_correlation([1, 2, 3, 4, 5, 6], [60, 50, 40, 30, 20, 10]) == -1.0


def test_build_qualification_checks_uses_frozen_thresholds():
    passing = build_qualification_checks(
        total_trainings=120,
        panel_revalidated=True,
        oracle_p=0.049,
        challenger_p=0.01,
        oracle_range=0.015,
        challenger_range=0.02,
        spearman=0.60,
        oracle_signal=True,
        challenger_signal=True,
        deterministic_receipts=True,
    )
    assert all(passing.values())

    failing = build_qualification_checks(
        total_trainings=120,
        panel_revalidated=True,
        oracle_p=0.05,
        challenger_p=0.01,
        oracle_range=0.015,
        challenger_range=0.02,
        spearman=0.60,
        oracle_signal=True,
        challenger_signal=True,
        deterministic_receipts=True,
    )
    assert failing["oracle_heterogeneity"] is False
