"""Frozen Phase 2B contract for first one-way GA <- Neural Oracle pressure.

This module contains only preregistered constants and pure selection/statistical
contracts. It does not train a neural model and does not authorize scientific
execution. The execution gate remains issue #98. Issue #101 freezes the ex-ante
matched Oracle scoring budget before any scientific Phase-2B run.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any

from .evolution import ClassicalMetrics, HardConstraints, primary_security_key

ARCHITECTURE = "byte_tanh_mlp"
DEPTH = 4
DIFFERENCES = (0x00000001, 0x00000100)
PAIR_COUNT = 8192
SPLIT_SIZES = (5734, 1228, 1230)

EVOLUTION_SEEDS = (
    326011,
    326023,
    326033,
    326047,
    326051,
    326063,
    326071,
    326087,
    326099,
)

FITNESS_DATASET_SEEDS = (
    176003,
    176017,
    176029,
    176041,
    176057,
    176069,
    176081,
    176093,
)
FITNESS_MODEL_SEEDS = (
    186007,
    186019,
    186031,
    186043,
    186061,
    186073,
    186091,
    186103,
)

VALIDATION_DATASET_SEEDS = (
    276003,
    276017,
    276029,
    276041,
    276053,
    276067,
    276079,
    276091,
)
VALIDATION_MODEL_SEEDS = (
    286007,
    286019,
    286031,
    286043,
    286057,
    286069,
    286081,
    286103,
)

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
FITNESS_TRAININGS_PER_ARM_SEED = (
    ORACLE_SCORE_BUDGET_PER_ARM_SEED * ORACLE_TRAININGS_PER_SCORE
)

SUPPORT_CHECKS = (
    "o_wins_c_8_of_9",
    "paired_sign_p_lt_005",
    "mean_reduction_ge_002",
    "classical_non_degradation",
    "o_wins_s_6_of_9",
    "o_reduction_gt_s_reduction",
)


def _group_by_protected_key(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    constraints: HardConstraints,
) -> list[list[tuple[Any, ClassicalMetrics, float]]]:
    """Group candidates after deterministic descending protected-key ordering."""

    indexed = list(enumerate(items))
    indexed.sort(
        key=lambda pair: primary_security_key(pair[1][1], constraints),
        reverse=True,
    )
    groups: list[list[tuple[Any, ClassicalMetrics, float]]] = []
    active_key: tuple[float, ...] | None = None
    for _index, item in indexed:
        key = primary_security_key(item[1], constraints)
        if active_key is None or key != active_key:
            groups.append([])
            active_key = key
        groups[-1].append(item)
    return groups


def apply_oracle_tiebreak(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    *,
    constraints: HardConstraints,
    mode: str,
    shuffle_seed: int,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    """Apply Phase-2B ordering without allowing cross-key neural compensation.

    Every item is ``(candidate_id, classical_metrics, oracle_score)``. Protected
    classical keys are always ordered first. Neural information can only reorder
    candidates *inside* one exact protected-key group.

    ``control`` preserves the input ordering inside each exact-key group.
    ``oracle`` prefers lower real neural advantage.
    ``shuffled`` deterministically permutes score assignment inside each group
    before ordering, preserving score distribution but destroying association.
    """

    if mode not in {"control", "oracle", "shuffled"}:
        raise ValueError(f"unsupported Phase 2B arm mode {mode!r}")
    groups = _group_by_protected_key(items, constraints)
    rng = random.Random(int(shuffle_seed))
    ordered: list[tuple[Any, ClassicalMetrics, float]] = []

    for group in groups:
        if len(group) < 2 or mode == "control":
            ordered.extend(group)
            continue
        if mode == "oracle":
            ordered.extend(sorted(group, key=lambda item: float(item[2])))
            continue

        scores = [float(item[2]) for item in group]
        rng.shuffle(scores)
        decorated = list(zip(group, scores))
        decorated.sort(key=lambda pair: pair[1])
        ordered.extend(item for item, _assigned_score in decorated)

    return ordered


def phase2b_verdict(prerequisites_pass: bool, checks: Mapping[str, bool]) -> str:
    """Apply the exact preregistered Phase-2B support rule."""

    if not bool(prerequisites_pass):
        return "phase2b_inconclusive_prerequisites"
    missing = [name for name in SUPPORT_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2B support checks: {', '.join(missing)}")
    if all(bool(checks[name]) for name in SUPPORT_CHECKS):
        return "phase2b_oracle_pressure_supported"
    return "phase2b_oracle_pressure_not_supported"
