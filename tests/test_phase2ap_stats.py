"""Synthetic tests for the frozen Phase 2A-P blockwise statistics."""

from adversarial_sbox.phase2ap import (
    ALPHA_PER_SIDE,
    EFFECT_RATIO_MAX,
    block_dispersion,
    paired_block_peak_test,
    peak_side_pass,
)


def _scaled_blocks(scale: float, count: int = 40) -> list[list[float]]:
    base = (-3.0, -2.0, -1.0, 1.0, 2.0, 3.0)
    return [[scale * value + index * 1e-6 for value in base] for index in range(count)]


def test_block_dispersion_is_population_variance():
    assert block_dispersion([0, 0, 0, 2, 2, 2]) == 1.0


def test_paired_peak_test_is_deterministic_and_detects_strong_peak():
    peak = _scaled_blocks(1.0)
    neighbor = _scaled_blocks(0.2)
    first = paired_block_peak_test(peak, neighbor, repetitions=20_000, seed=94043)
    second = paired_block_peak_test(peak, neighbor, repetitions=20_000, seed=94043)
    assert first == second

    contrast, p_value, mean_peak, mean_neighbor, ratio = first
    assert contrast > 0.0
    assert mean_peak > mean_neighbor
    assert p_value < ALPHA_PER_SIDE
    assert ratio <= EFFECT_RATIO_MAX
    assert peak_side_pass(
        contrast=contrast,
        p_value=p_value,
        neighbor_over_r4=ratio,
    )


def test_peak_side_requires_all_frozen_conditions():
    assert not peak_side_pass(contrast=-0.1, p_value=0.001, neighbor_over_r4=0.5)
    assert not peak_side_pass(contrast=0.1, p_value=ALPHA_PER_SIDE, neighbor_over_r4=0.5)
    assert not peak_side_pass(contrast=0.1, p_value=0.001, neighbor_over_r4=EFFECT_RATIO_MAX + 1e-9)
