"""Frozen identity and verdict contract for Phase 2G adaptive GA↔NN research.

This module contains only preregistered constants, seed expansion, budget identity,
and fail-closed verdict semantics. It does not implement checkpoint training,
adaptive scoring, evolution, held-out validation, or scientific execution.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .phase2_evolution_seed_registry import PHASE2G_RESERVED_EVOLUTION_SEEDS

ARMS = ("C", "F", "A", "S")
CHECKPOINT_GENERATIONS = (0, 5, 10, 15)
EVOLUTION_SEEDS = PHASE2G_RESERVED_EVOLUTION_SEEDS

TRAINING_DATASET_BASE_SEEDS = (
    776003,
    776017,
    776031,
    776043,
    776059,
    776071,
    776083,
    776097,
)

TRAINING_MODEL_BASE_SEEDS = (
    786009,
    786021,
    786033,
    786047,
    786061,
    786073,
    786087,
    786101,
)

SCORING_DATASET_BASE_SEEDS = (
    796003,
    796017,
    796029,
    796043,
    796057,
    796071,
    796083,
    796099,
)

HELDOUT_DATASET_SEEDS = (
    876003,
    876017,
    876029,
    876043,
    876057,
    876071,
    876083,
    876099,
)

HELDOUT_MODEL_SEEDS = (
    886007,
    886019,
    886031,
    886043,
    886061,
    886073,
    886091,
    886103,
)

CHECKPOINTS_PER_CELL = len(CHECKPOINT_GENERATIONS)
TRAININGS_PER_CHECKPOINT = 16
CHECKPOINT_TRAININGS_PER_CELL = CHECKPOINTS_PER_CELL * TRAININGS_PER_CHECKPOINT
ARM_SEED_CELLS = len(ARMS) * len(EVOLUTION_SEEDS)
TOTAL_CHECKPOINT_TRAININGS = ARM_SEED_CELLS * CHECKPOINT_TRAININGS_PER_CELL
TOTAL_HELDOUT_TRAININGS = ARM_SEED_CELLS * 16
TOTAL_SCIENTIFIC_TRAININGS = TOTAL_CHECKPOINT_TRAININGS + TOTAL_HELDOUT_TRAININGS

SUPPORT_CHECKS = (
    "adaptation_activity",
    "mechanism_activity",
    "wins_vs_fixed",
    "sign_test_vs_fixed",
    "effect_size_vs_fixed",
    "classical_non_degradation",
    "wins_vs_shuffled",
    "mean_vs_shuffled",
    "wins_vs_control",
    "mean_vs_control",
)


def expanded_checkpoint_seed_block(base: Iterable[int], checkpoint: int) -> tuple[int, ...]:
    """Expand a preregistered checkpoint base block using exact +1000*c semantics."""

    if checkpoint not in range(len(CHECKPOINT_GENERATIONS)):
        raise ValueError(f"invalid Phase-2G checkpoint index {checkpoint!r}")
    frozen = tuple(int(value) for value in base)
    return tuple(value + (1000 * checkpoint) for value in frozen)


def phase2g_verdict(prerequisites_ok: bool, checks: Mapping[str, bool]) -> str:
    """Return the exact preregistered Phase-2G verdict, failing closed."""

    if tuple(checks.keys()) != SUPPORT_CHECKS:
        raise ValueError("Phase-2G support checks must match the frozen ordered contract")

    if not prerequisites_ok or not bool(checks["adaptation_activity"]):
        return "phase2g_inconclusive_prerequisites"

    if all(bool(checks[name]) for name in SUPPORT_CHECKS):
        return "phase2g_adaptive_coevolution_supported"

    return "phase2g_adaptive_coevolution_not_supported"
