"""Frozen scientific contract for Phase 2A-P R4 peak confirmation."""

from __future__ import annotations

import random
import statistics
from typing import Sequence

PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

ARCHITECTURE = "byte_tanh_mlp"
DEPTHS = (3, 4, 5)
DIFFERENCES = (0x00000001, 0x00000100)

DATASET_SEEDS = (
    74003, 74011, 74017, 74021, 74027, 74047, 74051, 74071, 74077, 74093,
    74101, 74131, 74143, 74149, 74161, 74167, 74179, 74189, 74197, 74201,
)
MODEL_SEEDS = (
    84011, 84017, 84029, 84037, 84047, 84053, 84059, 84061, 84067, 84083,
    84089, 84101, 84109, 84127, 84131, 84137, 84143, 84163, 84179, 84181,
)

PANEL_SIZE = 6
REPLICATES = 20
TRAININGS_PER_CELL = PANEL_SIZE * REPLICATES
TRAININGS_PER_DEPTH = TRAININGS_PER_CELL * len(DIFFERENCES)
TOTAL_TRAININGS = TRAININGS_PER_DEPTH * len(DEPTHS)

PERMUTATION_REPETITIONS = 20_000
PEAK_PERMUTATION_SEEDS = {(4, 3): 94043, (4, 5): 94045}
HETEROGENEITY_PERMUTATION_SEEDS = {3: 95003, 4: 95004, 5: 95005}
ALPHA_PER_SIDE = 0.025
EFFECT_RATIO_MAX = 0.75


def block_dispersion(block: Sequence[float]) -> float:
    if len(block) != PANEL_SIZE:
        raise ValueError("Phase 2A-P block must have frozen panel width")
    return float(statistics.pvariance(float(value) for value in block))


def candidate_means(blocks: Sequence[Sequence[float]]) -> list[float]:
    if not blocks:
        raise ValueError("at least one Phase 2A-P block is required")
    if any(len(block) != PANEL_SIZE for block in blocks):
        raise ValueError("Phase 2A-P blocks must have frozen panel width")
    return [
        float(sum(float(block[index]) for block in blocks) / len(blocks))
        for index in range(PANEL_SIZE)
    ]


def paired_block_peak_test(
    peak_blocks: Sequence[Sequence[float]],
    neighbor_blocks: Sequence[Sequence[float]],
    *,
    repetitions: int,
    seed: int,
) -> tuple[float, float, float, float, float]:
    """One-sided paired sign-flip test of larger blockwise dispersion at R4."""

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if len(peak_blocks) != len(neighbor_blocks) or not peak_blocks:
        raise ValueError("paired Phase 2A-P blocks must be non-empty and equal length")

    peak_disp = [block_dispersion(block) for block in peak_blocks]
    neighbor_disp = [block_dispersion(block) for block in neighbor_blocks]
    diffs = [left - right for left, right in zip(peak_disp, neighbor_disp)]
    observed = float(statistics.fmean(diffs))
    mean_peak = float(statistics.fmean(peak_disp))
    mean_neighbor = float(statistics.fmean(neighbor_disp))
    ratio = float(mean_neighbor / mean_peak) if mean_peak > 0.0 else float("inf")

    rng = random.Random(int(seed))
    exceedances = 0
    for _ in range(int(repetitions)):
        statistic = statistics.fmean(
            diff if rng.random() < 0.5 else -diff for diff in diffs
        )
        if statistic >= observed - 1e-18:
            exceedances += 1
    p_value = float((1 + exceedances) / (1 + int(repetitions)))
    return observed, p_value, mean_peak, mean_neighbor, ratio


def peak_side_pass(*, contrast: float, p_value: float, neighbor_over_r4: float) -> bool:
    return bool(
        float(contrast) > 0.0
        and float(p_value) < ALPHA_PER_SIDE
        and float(neighbor_over_r4) <= EFFECT_RATIO_MAX
    )


def classify_peak(*, requirements_pass: bool, side43_pass: bool, side45_pass: bool) -> str:
    if not bool(requirements_pass):
        return "phase2ap_inconclusive_prerequisite"
    if bool(side43_pass) and bool(side45_pass):
        return "phase2ap_r4_peak_supported"
    return "phase2ap_r4_peak_not_supported"
