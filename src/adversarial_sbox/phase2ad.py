"""Frozen scientific contract for Phase 2A-D neural depth attenuation."""

from __future__ import annotations

import random
import statistics
from typing import Sequence

PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

ARCHITECTURE = "byte_tanh_mlp"
DEPTHS = (3, 4, 5)
DIFFERENCES = (0x00000001, 0x00000100)

DATASET_SEEDS = (
    73009,
    73013,
    73019,
    73037,
    73039,
    73043,
    73061,
    73063,
    73079,
    73091,
)
MODEL_SEEDS = (
    83003,
    83009,
    83023,
    83047,
    83059,
    83063,
    83071,
    83077,
    83089,
    83101,
)

PANEL_SIZE = 6
REPLICATES = 10
TRAININGS_PER_CELL = PANEL_SIZE * REPLICATES
TRAININGS_PER_DEPTH = TRAININGS_PER_CELL * len(DIFFERENCES)
TOTAL_TRAININGS = TRAININGS_PER_DEPTH * len(DEPTHS)

PERMUTATION_REPETITIONS = 10_000
HETEROGENEITY_PERMUTATION_SEEDS = {
    3: 92103,
    4: 92104,
    5: 92105,
}
PRIMARY_PERMUTATION_SEED = 92045
SECONDARY_PERMUTATION_SEED = 92034
PRIMARY_ATTENUATION_RATIO_MAX = 0.75


def _candidate_means(blocks: Sequence[Sequence[float]]) -> list[float]:
    if not blocks:
        raise ValueError("at least one paired block is required")
    width = len(blocks[0])
    if width != PANEL_SIZE or any(len(block) != width for block in blocks):
        raise ValueError("Phase 2A-D blocks must all have frozen panel width")
    return [
        float(sum(float(block[index]) for block in blocks) / len(blocks))
        for index in range(width)
    ]


def between_candidate_variance(blocks: Sequence[Sequence[float]]) -> float:
    """Population variance of candidate mean neural advantages."""

    return float(statistics.pvariance(_candidate_means(blocks)))


def paired_dispersion_attenuation_p(
    left_blocks: Sequence[Sequence[float]],
    right_blocks: Sequence[Sequence[float]],
    *,
    repetitions: int,
    seed: int,
) -> tuple[float, float, float, float]:
    """One-sided paired randomization test for loss of between-candidate dispersion.

    Each row is one matched `(difference, replicate)` block and each column is a
    frozen S-box candidate. Under the null, the left/right depth labels are
    independently exchangeable within every candidate/block pair.
    """

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if len(left_blocks) != len(right_blocks) or not left_blocks:
        raise ValueError("paired depth blocks must be non-empty and equal length")

    left = [[float(value) for value in block] for block in left_blocks]
    right = [[float(value) for value in block] for block in right_blocks]
    if any(len(block) != PANEL_SIZE for block in left + right):
        raise ValueError("Phase 2A-D paired blocks must have frozen panel width")

    left_variance = between_candidate_variance(left)
    right_variance = between_candidate_variance(right)
    observed = float(left_variance - right_variance)

    rng = random.Random(int(seed))
    exceedances = 0
    for _ in range(int(repetitions)):
        perm_left: list[list[float]] = []
        perm_right: list[list[float]] = []
        for left_block, right_block in zip(left, right):
            left_row: list[float] = []
            right_row: list[float] = []
            for left_value, right_value in zip(left_block, right_block):
                if rng.random() < 0.5:
                    left_row.append(right_value)
                    right_row.append(left_value)
                else:
                    left_row.append(left_value)
                    right_row.append(right_value)
            perm_left.append(left_row)
            perm_right.append(right_row)
        statistic = between_candidate_variance(perm_left) - between_candidate_variance(
            perm_right
        )
        if statistic >= observed - 1e-18:
            exceedances += 1

    p_value = float((1 + exceedances) / (1 + int(repetitions)))
    return observed, p_value, left_variance, right_variance


def classify_depth_attenuation(
    *,
    requirements_pass: bool,
    delta45: float,
    p45: float,
    variance_ratio45: float,
) -> str:
    """Apply the exact Phase-2A-D classification frozen before execution."""

    if not bool(requirements_pass):
        return "phase2ad_inconclusive_baseline_or_provenance"
    supported = (
        float(delta45) > 0.0
        and float(p45) < 0.05
        and float(variance_ratio45) <= PRIMARY_ATTENUATION_RATIO_MAX
    )
    if supported:
        return "phase2ad_depth_attenuation_supported"
    return "phase2ad_depth_attenuation_not_supported"
