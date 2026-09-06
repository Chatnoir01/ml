from __future__ import annotations

from adversarial_sbox.phase2au_neural import (
    CELL_SPECS,
    PERMUTATION_REPETITIONS,
    REPLICATES,
    TRAININGS_PER_CELL,
    build_qualification_checks,
    consensus_scores,
    spearman_correlation,
)


def test_phase2au_neural_cell_contract_is_exact() -> None:
    assert CELL_SPECS == (
        ("bit_relu_mlp", 4, 0x00000001),
        ("bit_relu_mlp", 4, 0x00000100),
        ("byte_tanh_mlp", 4, 0x00000001),
        ("byte_tanh_mlp", 4, 0x00000100),
    )
    assert REPLICATES == 8
    assert TRAININGS_PER_CELL == 48
    assert PERMUTATION_REPETITIONS == 10_000


def test_consensus_score_is_unweighted_arithmetic_mean() -> None:
    bit = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
    byte = [0.30, 0.20, 0.10, 0.60, 0.50, 0.40]
    assert consensus_scores(bit, byte) == [0.20, 0.20, 0.20, 0.50, 0.50, 0.50]


def test_spearman_contract_is_stable() -> None:
    assert spearman_correlation([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]) == 1.0
    assert spearman_correlation([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]) == -1.0


def test_qualification_requires_every_frozen_phase2au_check() -> None:
    checks = build_qualification_checks(
        total_trainings=192,
        panel_revalidated=True,
        deterministic_receipts=True,
        neural_evolutionary_pressure=False,
        bit_p=0.01,
        byte_p=0.02,
        bit_range=0.02,
        byte_range=0.03,
        cross_arch_spearman=0.61,
        bit_signal=True,
        byte_signal=True,
        consensus_p=0.01,
        consensus_range=0.02,
        split_half_spearman=0.60,
    )
    assert all(checks.values())
    assert tuple(checks) == (
        "training_count_exact",
        "panel_revalidated",
        "deterministic_receipts",
        "no_neural_evolutionary_pressure",
        "bit_heterogeneity",
        "byte_heterogeneity",
        "bit_range",
        "byte_range",
        "cross_architecture_rank",
        "bit_signal",
        "byte_signal",
        "consensus_heterogeneity",
        "consensus_range",
        "split_half_consensus_rank",
    )


def test_qualification_thresholds_fail_closed_at_required_boundaries() -> None:
    base = dict(
        total_trainings=192,
        panel_revalidated=True,
        deterministic_receipts=True,
        neural_evolutionary_pressure=False,
        bit_p=0.01,
        byte_p=0.02,
        bit_range=0.015,
        byte_range=0.015,
        cross_arch_spearman=0.60,
        bit_signal=True,
        byte_signal=True,
        consensus_p=0.01,
        consensus_range=0.015,
        split_half_spearman=0.60,
    )
    assert all(build_qualification_checks(**base).values())

    bad = dict(base, cross_arch_spearman=0.599999)
    assert not build_qualification_checks(**bad)["cross_architecture_rank"]
    bad = dict(base, consensus_p=0.05)
    assert not build_qualification_checks(**bad)["consensus_heterogeneity"]
    bad = dict(base, split_half_spearman=0.599999)
    assert not build_qualification_checks(**bad)["split_half_consensus_rank"]
