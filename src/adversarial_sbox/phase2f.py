"""Frozen Phase 2F contract for minimal classical-band neural pressure.

This module contains preregistered constants and pure ordering/verdict contracts.
Held-out Block X seeds live in ``phase2f_validation_seeds`` and are loaded only
through lazy aliases for post-freeze/provenance consumers.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any

from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    feasibility_rank,
    is_admissible,
    primary_security_key,
)
from .phase2_evolution_seed_registry import PHASE2F_RESERVED_EVOLUTION_SEEDS

ARCHITECTURE = "byte_tanh_mlp"
NUMPY_VERSION = "2.5.3"
DEPTH = 4
DIFFERENCES = (0x00000001, 0x00000100)
PAIR_COUNT = 8192
SPLIT_SIZES = (5734, 1228, 1230)

ARMS = ("C", "O0", "B1", "SB1")
EVOLUTION_SEEDS = PHASE2F_RESERVED_EVOLUTION_SEEDS

FITNESS_DATASET_SEEDS = (576003, 576017, 576031, 576043, 576059, 576071, 576083, 576097)
FITNESS_MODEL_SEEDS = (586009, 586021, 586033, 586047, 586061, 586073, 586087, 586099)

SHUFFLE_SEED_OFFSET = 10_000
CLASSICAL_BUDGET_PER_ARM_SEED = 340
EVOLUTION_GENERATIONS = 20
POPULATION_SIZE = 20
SHORTLIST_SIZE = 8
PARENT_COUNT = 4
PROPOSALS_PER_PARENT = 4
PROPOSALS_PER_GENERATION = 16
ORACLE_TRAININGS_PER_SCORE = len(DIFFERENCES) * len(FITNESS_DATASET_SEEDS)
ORACLE_SCORE_BUDGET_PER_ARM_SEED = 32
FITNESS_TRAININGS_PER_ARM_SEED = ORACLE_SCORE_BUDGET_PER_ARM_SEED * ORACLE_TRAININGS_PER_SCORE
TOTAL_FITNESS_TRAININGS = len(ARMS) * len(EVOLUTION_SEEDS) * FITNESS_TRAININGS_PER_ARM_SEED

B1_NL_RADIUS = 2
B1_DU_RADIUS = 2
B1_LAT_RADIUS = 2

SUPPORT_CHECKS = (
    "mechanism_activity_6_of_9",
    "b1_wins_o0_8_of_9",
    "paired_sign_p_lt_005",
    "mean_reduction_ge_002",
    "classical_non_degradation",
    "b1_wins_sb1_6_of_9",
    "b1_mean_lt_sb1_mean",
)

_LAZY_HELDOUT_NAMES = {
    "VALIDATION_DATASET_SEEDS",
    "VALIDATION_MODEL_SEEDS",
    "HELDOUT_TRAININGS_PER_TERMINAL",
    "TOTAL_HELDOUT_TRAININGS",
}


def __getattr__(name: str):
    if name in _LAZY_HELDOUT_NAMES:
        from . import phase2f_validation_seeds as heldout

        return getattr(heldout, name)
    raise AttributeError(name)


def in_b1_band(candidate: ClassicalMetrics, cutoff: ClassicalMetrics, constraints: HardConstraints) -> bool:
    """Return whether candidate is inside the exact preregistered B1 neighborhood."""

    return (
        is_admissible(candidate, constraints) == is_admissible(cutoff, constraints)
        and abs(int(candidate.nonlinearity) - int(cutoff.nonlinearity)) <= B1_NL_RADIUS
        and abs(int(candidate.differential_uniformity) - int(cutoff.differential_uniformity)) <= B1_DU_RADIUS
        and abs(int(candidate.max_linear_correlation) - int(cutoff.max_linear_correlation)) <= B1_LAT_RADIUS
        and int(candidate.algebraic_degree) == int(cutoff.algebraic_degree)
    )


def _historical_order(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    constraints: HardConstraints,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    indexed = list(enumerate(items))
    indexed.sort(
        key=lambda pair: (feasibility_rank(pair[1][1], constraints), pair[0]),
        reverse=True,
    )
    return [item for _index, item in indexed]


def _o0_order(
    historical: Sequence[tuple[Any, ClassicalMetrics, float]],
    constraints: HardConstraints,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    ordered: list[tuple[Any, ClassicalMetrics, float]] = []
    start = 0
    while start < len(historical):
        key = primary_security_key(historical[start][1], constraints)
        end = start + 1
        while end < len(historical) and primary_security_key(historical[end][1], constraints) == key:
            end += 1
        group = list(historical[start:end])
        group.sort(key=lambda item: float(item[2]))
        ordered.extend(group)
        start = end
    return ordered


def _contiguous_band_positions(
    historical: Sequence[tuple[Any, ClassicalMetrics, float]],
    *,
    cutoff_metrics: ClassicalMetrics,
    constraints: HardConstraints,
) -> list[int]:
    """Maximal contiguous B1-eligible run containing the cutoff reference."""

    matches = [
        index
        for index, item in enumerate(historical)
        if str(item[1].fingerprint) == str(cutoff_metrics.fingerprint)
    ]
    if len(matches) != 1:
        raise ValueError("Phase 2F cutoff reference fingerprint must occur exactly once")
    center = matches[0]
    if not in_b1_band(historical[center][1], cutoff_metrics, constraints):
        raise RuntimeError("Phase 2F cutoff reference is not self-eligible")

    left = center
    while left - 1 >= 0 and in_b1_band(historical[left - 1][1], cutoff_metrics, constraints):
        left -= 1
    right = center + 1
    while right < len(historical) and in_b1_band(historical[right][1], cutoff_metrics, constraints):
        right += 1
    return list(range(left, right))


def apply_phase2f_cutoff_order(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    *,
    constraints: HardConstraints,
    arm: str,
    cutoff_metrics: ClassicalMetrics,
    shuffle_rng: random.Random | None,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    """Apply the frozen pure Phase-2F cutoff ordering contract.

    C is historical feasibility order. O0 can reorder only exact protected-key
    groups. B1/SB1 can reorder only the contiguous B1 band containing the
    historical cutoff reference; no outside-band candidate can be crossed.
    """

    if arm not in ARMS:
        raise ValueError(f"unsupported Phase 2F arm {arm!r}")
    if arm == "SB1" and shuffle_rng is None:
        raise ValueError("SB1 requires one persistent shuffled-score RNG")

    historical = _historical_order(items, constraints)
    if arm == "C":
        return historical
    if arm == "O0":
        return _o0_order(historical, constraints)

    eligible_positions = _contiguous_band_positions(
        historical, cutoff_metrics=cutoff_metrics, constraints=constraints
    )
    if len(eligible_positions) < 2:
        return historical

    eligible = [historical[index] for index in eligible_positions]
    if arm == "B1":
        eligible.sort(key=lambda item: float(item[2]))
    else:
        assert shuffle_rng is not None
        assigned_scores = [float(item[2]) for item in eligible]
        shuffle_rng.shuffle(assigned_scores)
        decorated = list(zip(eligible, assigned_scores))
        decorated.sort(key=lambda pair: float(pair[1]))
        eligible = [item for item, _score in decorated]

    result = list(historical)
    for position, item in zip(eligible_positions, eligible):
        result[position] = item
    return result


def phase2f_verdict(prerequisites_pass: bool, checks: Mapping[str, bool]) -> str:
    if not bool(prerequisites_pass):
        return "phase2f_inconclusive_prerequisites"
    missing = [name for name in SUPPORT_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2F support checks: {', '.join(missing)}")
    if all(bool(checks[name]) for name in SUPPORT_CHECKS):
        return "phase2f_minimal_band_pressure_supported"
    return "phase2f_minimal_band_pressure_not_supported"
