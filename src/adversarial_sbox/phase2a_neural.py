"""Pure statistical contracts for Phase 2A Neural Oracle qualification.

No neural training is executed by importing this module. The scientific runner is
added only after the preregistered six-candidate panel is committed.
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Iterable, Sequence

from .phase2a import (
    CHALLENGER_ARCHITECTURE,
    CHALLENGER_DIFFERENCES,
    CHALLENGER_ROUNDS,
    DATASET_SEEDS,
    ORACLE_ARCHITECTURE,
    ORACLE_DIFFERENCES,
    ORACLE_ROUNDS,
    PANEL_SIZE,
    TOTAL_TRAININGS,
)

CELL_SPECS = (
    ("oracle", ORACLE_ROUNDS, ORACLE_DIFFERENCES[0], ORACLE_ARCHITECTURE),
    ("oracle", ORACLE_ROUNDS, ORACLE_DIFFERENCES[1], ORACLE_ARCHITECTURE),
    (
        "challenger",
        CHALLENGER_ROUNDS,
        CHALLENGER_DIFFERENCES[0],
        CHALLENGER_ARCHITECTURE,
    ),
    (
        "challenger",
        CHALLENGER_ROUNDS,
        CHALLENGER_DIFFERENCES[1],
        CHALLENGER_ARCHITECTURE,
    ),
)

REPLICATES = len(DATASET_SEEDS)
TRAININGS_PER_CELL = PANEL_SIZE * REPLICATES
PERMUTATION_REPETITIONS = 10000
ORACLE_PERMUTATION_SEED = 930101
CHALLENGER_PERMUTATION_SEED = 930201


def _mean(values: Iterable[float]) -> float:
    frozen = [float(value) for value in values]
    if not frozen:
        raise ValueError("cannot compute mean of an empty sequence")
    return float(sum(frozen) / len(frozen))


def _variance_of_candidate_means(blocks: Sequence[Sequence[float]]) -> float:
    if not blocks:
        raise ValueError("at least one block is required")
    width = len(blocks[0])
    if width < 2 or any(len(block) != width for block in blocks):
        raise ValueError("all blocks must have the same candidate width >= 2")
    sums = [0.0] * width
    for block in blocks:
        for index, value in enumerate(block):
            sums[index] += float(value)
    means = [total / len(blocks) for total in sums]
    return float(statistics.pvariance(means))


def blocked_heterogeneity_p(
    blocks: Sequence[Sequence[float]], *, repetitions: int, seed: int
) -> tuple[float, float]:
    """Deterministic blocked permutation test for any fixed candidate width."""

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    frozen = [[float(value) for value in block] for block in blocks]
    observed = _variance_of_candidate_means(frozen)
    width = len(frozen[0])
    rng = random.Random(int(seed))
    exceedances = 0
    for _ in range(int(repetitions)):
        sums = [0.0] * width
        for block in frozen:
            shuffled = list(block)
            rng.shuffle(shuffled)
            for index, value in enumerate(shuffled):
                sums[index] += value
        means = [total / len(frozen) for total in sums]
        statistic = statistics.pvariance(means)
        if statistic >= observed - 1e-18:
            exceedances += 1
    return float(observed), float((1 + exceedances) / (1 + int(repetitions)))


def _average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: float(values[index]))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        value = float(values[order[cursor]])
        while end < len(order) and float(values[order[end]]) == value:
            end += 1
        average_rank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = average_rank
        cursor = end
    return ranks


def spearman_correlation(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman correlation requires equal sequences of length >= 2")
    x = _average_ranks(left)
    y = _average_ranks(right)
    mean_x = _mean(x)
    mean_y = _mean(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denom_x = math.sqrt(sum((a - mean_x) ** 2 for a in x))
    denom_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
    if denom_x == 0.0 or denom_y == 0.0:
        return 0.0
    value = numerator / (denom_x * denom_y)
    if abs(value - 1.0) < 1e-15:
        return 1.0
    if abs(value + 1.0) < 1e-15:
        return -1.0
    return float(value)


def build_qualification_checks(
    *,
    total_trainings: int,
    panel_revalidated: bool,
    oracle_p: float,
    challenger_p: float,
    oracle_range: float,
    challenger_range: float,
    spearman: float,
    oracle_signal: bool,
    challenger_signal: bool,
    deterministic_receipts: bool,
) -> dict[str, bool]:
    """Apply the exact Phase-2A thresholds frozen before neural execution."""

    return {
        "training_count_exact": int(total_trainings) == TOTAL_TRAININGS,
        "panel_revalidated": bool(panel_revalidated),
        "oracle_heterogeneity": float(oracle_p) < 0.05,
        "challenger_heterogeneity": float(challenger_p) < 0.05,
        "oracle_range": float(oracle_range) >= 0.015,
        "challenger_range": float(challenger_range) >= 0.015,
        "rank_replication": float(spearman) >= 0.60,
        "oracle_signal": bool(oracle_signal),
        "challenger_signal": bool(challenger_signal),
        "deterministic_receipts": bool(deterministic_receipts),
    }
