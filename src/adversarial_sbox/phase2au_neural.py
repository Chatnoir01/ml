"""Pure statistical contracts for Phase 2A-U.

Importing this module executes no neural training and exposes no evolutionary
feedback path. The scientific runner is added only after this contract is GREEN.
"""

from __future__ import annotations

from typing import Sequence

from .phase2a_neural import blocked_heterogeneity_p, spearman_correlation
from .phase2au import (
    ARCHITECTURES,
    DATASET_SEEDS,
    DIFFERENCES,
    PANEL_SIZE,
    PERMUTATIONS,
    ROUNDS,
    TOTAL_NEURAL_TRAININGS,
)

CELL_SPECS = (
    (ARCHITECTURES[0], ROUNDS, DIFFERENCES[0]),
    (ARCHITECTURES[0], ROUNDS, DIFFERENCES[1]),
    (ARCHITECTURES[1], ROUNDS, DIFFERENCES[0]),
    (ARCHITECTURES[1], ROUNDS, DIFFERENCES[1]),
)
REPLICATES = len(DATASET_SEEDS)
TRAININGS_PER_CELL = PANEL_SIZE * REPLICATES
PERMUTATION_REPETITIONS = PERMUTATIONS


def consensus_scores(
    bit_scores: Sequence[float], byte_scores: Sequence[float]
) -> list[float]:
    """Frozen unweighted consensus candidate score."""

    if len(bit_scores) != PANEL_SIZE or len(byte_scores) != PANEL_SIZE:
        raise ValueError(f"consensus requires exactly {PANEL_SIZE} scores per architecture")
    return [
        (float(bit) + float(byte)) / 2.0
        for bit, byte in zip(bit_scores, byte_scores)
    ]


def build_qualification_checks(
    *,
    total_trainings: int,
    panel_revalidated: bool,
    deterministic_receipts: bool,
    neural_evolutionary_pressure: bool,
    bit_p: float,
    byte_p: float,
    bit_range: float,
    byte_range: float,
    cross_arch_spearman: float,
    bit_signal: bool,
    byte_signal: bool,
    consensus_p: float,
    consensus_range: float,
    split_half_spearman: float,
) -> dict[str, bool]:
    """Apply the exact preregistered Phase-2A-U thresholds."""

    return {
        "training_count_exact": int(total_trainings) == TOTAL_NEURAL_TRAININGS,
        "panel_revalidated": bool(panel_revalidated),
        "deterministic_receipts": bool(deterministic_receipts),
        "no_neural_evolutionary_pressure": not bool(neural_evolutionary_pressure),
        "bit_heterogeneity": float(bit_p) < 0.05,
        "byte_heterogeneity": float(byte_p) < 0.05,
        "bit_range": float(bit_range) >= 0.015,
        "byte_range": float(byte_range) >= 0.015,
        "cross_architecture_rank": float(cross_arch_spearman) >= 0.60,
        "bit_signal": bool(bit_signal),
        "byte_signal": bool(byte_signal),
        "consensus_heterogeneity": float(consensus_p) < 0.05,
        "consensus_range": float(consensus_range) >= 0.015,
        "split_half_consensus_rank": float(split_half_spearman) >= 0.60,
    }


__all__ = [
    "CELL_SPECS",
    "PERMUTATION_REPETITIONS",
    "REPLICATES",
    "TRAININGS_PER_CELL",
    "blocked_heterogeneity_p",
    "build_qualification_checks",
    "consensus_scores",
    "spearman_correlation",
]
