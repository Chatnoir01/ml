"""Frozen scientific contract for Phase 2B first GA <- Neural Oracle pressure.

Phase 2B is deliberately one-way. The frozen 4-round Neural Oracle may influence
selection only after the protected primary classical security key. The Oracle is
not adapted from GA outcomes, so this module does not implement bidirectional
GA<->NN co-evolution.
"""

from __future__ import annotations

import hashlib
import itertools
import statistics
from typing import Sequence

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    constraint_violation,
    equivalent_random_budget,
    is_admissible,
)

PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
ARCHITECTURE = "byte_tanh_mlp"
DEPTH = 4
DIFFERENCES = (0x00000001, 0x00000100)
PAIR_COUNT = 8192
EXPECTED_TRAIN_SIZE = 5734
EXPECTED_VALIDATION_SIZE = 1228
EXPECTED_TEST_SIZE = 1230
PAIRED_REPLICATES = 8
TRAININGS_PER_ORACLE_SCORE = len(DIFFERENCES) * PAIRED_REPLICATES

EVOLUTION_SEEDS = (290003, 290017, 290029, 290041, 290057)

PRESSURE_DATASET_SEEDS = (
    276001,
    276011,
    276019,
    276037,
    276049,
    276067,
    276091,
    276109,
)
PRESSURE_MODEL_SEEDS = (
    286003,
    286019,
    286031,
    286043,
    286057,
    286069,
    286087,
    286103,
)
BLIND_DATASET_SEEDS = (
    277003,
    277019,
    277033,
    277051,
    277063,
    277079,
    277091,
    277111,
)
BLIND_MODEL_SEEDS = (
    287009,
    287021,
    287039,
    287051,
    287063,
    287081,
    287093,
    287107,
)

GA_CONFIG_KWARGS = {
    "population_size": 6,
    "generations": 5,
    "elite_count": 2,
    "tournament_size": 2,
    "mutation_swaps": 1,
    "crossover_rate": 0.0,
    "immigrant_fraction": 0.0,
    "offspring_multiplier": 1,
}
CLASSICAL_EVALUATIONS_PER_ARM = equivalent_random_budget(
    EvolutionConfig(seed=0, **GA_CONFIG_KWARGS)
)
ARM_NAMES = ("control", "neural", "sham")
CLASSICAL_EVALUATIONS_TOTAL = (
    len(EVOLUTION_SEEDS) * len(ARM_NAMES) * CLASSICAL_EVALUATIONS_PER_ARM
)
PRESSURE_NEURAL_TRAININGS = (
    len(EVOLUTION_SEEDS)
    * CLASSICAL_EVALUATIONS_PER_ARM
    * TRAININGS_PER_ORACLE_SCORE
)
BLIND_NEURAL_TRAININGS = (
    len(EVOLUTION_SEEDS) * len(ARM_NAMES) * TRAININGS_PER_ORACLE_SCORE
)
NEURAL_TRAININGS_TOTAL = PRESSURE_NEURAL_TRAININGS + BLIND_NEURAL_TRAININGS

PRIMARY_ALPHA = 0.05
PRIMARY_MEDIAN_DELTA_MIN = 0.02
PRIMARY_POSITIVE_PAIR_MIN = 4

if CLASSICAL_EVALUATIONS_PER_ARM != 26:
    raise RuntimeError("Phase 2B frozen classical arm budget drift")
if CLASSICAL_EVALUATIONS_TOTAL != 390:
    raise RuntimeError("Phase 2B frozen total classical budget drift")
if PRESSURE_NEURAL_TRAININGS != 2080:
    raise RuntimeError("Phase 2B pressure neural budget drift")
if BLIND_NEURAL_TRAININGS != 240:
    raise RuntimeError("Phase 2B blind neural budget drift")
if NEURAL_TRAININGS_TOTAL != 2320:
    raise RuntimeError("Phase 2B total neural budget drift")
if EXPECTED_TRAIN_SIZE + EXPECTED_VALIDATION_SIZE + EXPECTED_TEST_SIZE != PAIR_COUNT:
    raise RuntimeError("Phase 2B frozen split sizes do not sum to pair count")


def protected_classical_key(
    metrics: ClassicalMetrics,
    constraints: HardConstraints,
) -> tuple[float, ...]:
    """Primary classical key that neural pressure is forbidden to override."""

    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(metrics.algebraic_degree),
    )


def classical_secondary_key(
    metrics: ClassicalMetrics,
    constraints: HardConstraints,
) -> tuple[float, ...]:
    return (
        -constraint_violation(metrics, constraints),
        float(-abs(metrics.sac_score - 0.5)),
    )


def sham_pressure_from_fingerprint(fingerprint: str) -> float:
    """Deterministic non-neural pseudo-pressure in [-1, 0)."""

    token = hashlib.sha256(str(fingerprint).encode("ascii")).digest()[:8]
    unit = int.from_bytes(token, "big") / float(2**64)
    return float(-unit)


def build_arm_rank(
    metrics: ClassicalMetrics,
    constraints: HardConstraints,
    *,
    arm: str,
    pressure_value: float = 0.0,
) -> tuple[float, ...]:
    """Build the exact Phase-2B lexicographic rank.

    The protected classical key is always first. The intervention component can
    therefore affect ordering only when two candidates have exactly the same
    protected primary classical key.
    """

    if arm not in ARM_NAMES:
        raise ValueError(f"unknown Phase 2B arm {arm!r}")
    if arm == "control":
        intervention = 0.0
    elif arm == "neural":
        intervention = -float(pressure_value)
    else:
        intervention = float(pressure_value)
    return (
        *protected_classical_key(metrics, constraints),
        intervention,
        *classical_secondary_key(metrics, constraints),
    )


def phase2b_neural_seed_registry() -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                *PRESSURE_DATASET_SEEDS,
                *PRESSURE_MODEL_SEEDS,
                *BLIND_DATASET_SEEDS,
                *BLIND_MODEL_SEEDS,
            }
        )
    )


def neural_seed_blocks_disjoint() -> bool:
    from .phase2_neural_seed_registry import prior_seed_registry_before_phase2b

    pressure = set(PRESSURE_DATASET_SEEDS) | set(PRESSURE_MODEL_SEEDS)
    blind = set(BLIND_DATASET_SEEDS) | set(BLIND_MODEL_SEEDS)
    prior = set(prior_seed_registry_before_phase2b())
    return pressure.isdisjoint(blind) and pressure.isdisjoint(prior) and blind.isdisjoint(prior)


def exact_paired_signflip_p(deltas: Sequence[float]) -> float:
    """Exact one-sided sign-flip p-value for positive mean paired improvement."""

    frozen = tuple(float(value) for value in deltas)
    if not frozen:
        raise ValueError("Phase 2B paired deltas must be non-empty")
    observed = statistics.fmean(frozen)
    assignments = 0
    exceedances = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(frozen)):
        statistic = statistics.fmean(sign * value for sign, value in zip(signs, frozen))
        assignments += 1
        if statistic >= observed - 1e-18:
            exceedances += 1
    return float(exceedances / assignments)


def primary_support_checks(paired_deltas: Sequence[float]) -> dict[str, bool]:
    frozen = tuple(float(value) for value in paired_deltas)
    if len(frozen) != len(EVOLUTION_SEEDS):
        raise ValueError("Phase 2B primary endpoint requires exactly five paired deltas")
    return {
        "paired_signflip_p": exact_paired_signflip_p(frozen) < PRIMARY_ALPHA,
        "mean_delta_positive": statistics.fmean(frozen) > 0.0,
        "median_delta_effect": statistics.median(frozen) >= PRIMARY_MEDIAN_DELTA_MIN,
        "positive_pair_count": sum(value > 0.0 for value in frozen) >= PRIMARY_POSITIVE_PAIR_MIN,
    }


def classify_phase2b(*, prerequisites_pass: bool, paired_deltas: Sequence[float]) -> str:
    if not bool(prerequisites_pass):
        return "phase2b_inconclusive_prerequisites"
    checks = primary_support_checks(paired_deltas)
    if all(checks.values()):
        return "phase2b_neural_pressure_supported"
    return "phase2b_neural_pressure_not_supported"
