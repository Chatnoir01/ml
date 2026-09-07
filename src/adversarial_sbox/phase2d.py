"""Frozen Phase 2D contract for bounded one-generation neural persistence.

This module contains only preregistered constants and pure ordering/state-machine
contracts. It does not run the scientific experiment or load held-out Block W.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .evolution import ClassicalMetrics, HardConstraints, primary_security_key
from .phase2_evolution_seed_registry import PHASE2D_RESERVED_EVOLUTION_SEEDS

ARCHITECTURE = "byte_tanh_mlp"
DEPTH = 4
DIFFERENCES = (0x00000001, 0x00000100)
PAIR_COUNT = 8192
SPLIT_SIZES = (5734, 1228, 1230)

ARMS = ("C", "O0", "OP1", "SP1")
EVOLUTION_SEEDS = PHASE2D_RESERVED_EVOLUTION_SEEDS

FITNESS_DATASET_SEEDS = (
    376003,
    376017,
    376031,
    376043,
    376057,
    376069,
    376081,
    376093,
)
FITNESS_MODEL_SEEDS = (
    386009,
    386021,
    386033,
    386047,
    386059,
    386071,
    386087,
    386099,
)
VALIDATION_DATASET_SEEDS = (
    476003,
    476017,
    476029,
    476043,
    476057,
    476071,
    476083,
    476099,
)
VALIDATION_MODEL_SEEDS = (
    486007,
    486019,
    486031,
    486043,
    486061,
    486073,
    486091,
    486103,
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
FITNESS_TRAININGS_PER_ARM_SEED = ORACLE_SCORE_BUDGET_PER_ARM_SEED * ORACLE_TRAININGS_PER_SCORE
TOTAL_FITNESS_TRAININGS = len(ARMS) * len(EVOLUTION_SEEDS) * FITNESS_TRAININGS_PER_ARM_SEED
HELDOUT_TRAININGS_PER_TERMINAL = len(DIFFERENCES) * len(VALIDATION_DATASET_SEEDS)
TOTAL_HELDOUT_TRAININGS = len(ARMS) * len(EVOLUTION_SEEDS) * HELDOUT_TRAININGS_PER_TERMINAL

SUPPORT_CHECKS = (
    "mechanism_transmission_6_of_9",
    "op1_wins_o0_8_of_9",
    "paired_sign_p_lt_005",
    "mean_reduction_ge_002",
    "classical_non_degradation",
    "op1_wins_sp1_6_of_9",
    "op1_mean_lt_sp1_mean",
)


@dataclass(slots=True)
class PersistenceLedger:
    """One-generation, one-stage persistence tags.

    Tags created at generation g / stage s become active only at generation g+1
    for the same stage s. They are sets, so duplicate creation never stacks. Once
    that next-generation stage is finished, all matching tags expire regardless
    of whether they changed selection.
    """

    _tags: dict[tuple[int, str], set[str]] = field(default_factory=dict)

    def create(self, *, fingerprint: str, generation: int, stage: str) -> None:
        if stage not in {"shortlist", "survival"}:
            raise ValueError(f"unsupported persistence stage {stage!r}")
        key = (int(generation) + 1, str(stage))
        self._tags.setdefault(key, set()).add(str(fingerprint))

    def create_from_membership_change(
        self,
        *,
        generation: int,
        stage: str,
        entered: Sequence[str],
        ordering_changed: bool,
    ) -> None:
        if not ordering_changed:
            return
        for fingerprint in entered:
            self.create(fingerprint=str(fingerprint), generation=generation, stage=stage)

    def active(self, *, generation: int, stage: str) -> frozenset[str]:
        return frozenset(self._tags.get((int(generation), str(stage)), set()))

    def finish_stage(self, *, generation: int, stage: str) -> None:
        self._tags.pop((int(generation), str(stage)), None)

    def snapshot(self) -> dict[str, list[str]]:
        return {
            f"{generation}:{stage}": sorted(values)
            for (generation, stage), values in sorted(self._tags.items())
        }


def _group_by_protected_key(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    constraints: HardConstraints,
) -> list[list[tuple[Any, ClassicalMetrics, float]]]:
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


def apply_phase2d_order(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    *,
    constraints: HardConstraints,
    arm: str,
    active_tags: set[str] | frozenset[str],
    shuffle_rng: random.Random | None,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    """Apply the pure Phase-2D within-protected-key ordering contract.

    Protected classical key is always primary. C preserves historical order inside
    equal-key groups. O0 prefers lower real neural advantage. OP1 first prefers an
    active one-generation persistence tag, then lower real neural advantage. SP1
    uses the same tag priority but destroys candidate-score association with one
    caller-owned persistent shuffled RNG stream.
    """

    if arm not in ARMS:
        raise ValueError(f"unsupported Phase 2D arm {arm!r}")
    if arm == "SP1" and shuffle_rng is None:
        raise ValueError("SP1 requires one persistent shuffled-score RNG")

    tags = {str(value) for value in active_tags}
    ordered: list[tuple[Any, ClassicalMetrics, float]] = []
    for group in _group_by_protected_key(items, constraints):
        if len(group) < 2 or arm == "C":
            ordered.extend(group)
            continue
        if arm == "O0":
            ordered.extend(sorted(group, key=lambda item: float(item[2])))
            continue

        if arm == "OP1":
            ordered.extend(
                sorted(
                    group,
                    key=lambda item: (
                        0 if str(item[0]) in tags else 1,
                        float(item[2]),
                    ),
                )
            )
            continue

        scores = [float(item[2]) for item in group]
        assert shuffle_rng is not None
        shuffle_rng.shuffle(scores)
        decorated = list(zip(group, scores))
        decorated.sort(
            key=lambda pair: (
                0 if str(pair[0][0]) in tags else 1,
                float(pair[1]),
            )
        )
        ordered.extend(item for item, _assigned_score in decorated)

    return ordered


def phase2d_verdict(prerequisites_pass: bool, checks: Mapping[str, bool]) -> str:
    if not bool(prerequisites_pass):
        return "phase2d_inconclusive_prerequisites"
    missing = [name for name in SUPPORT_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2D support checks: {', '.join(missing)}")
    if all(bool(checks[name]) for name in SUPPORT_CHECKS):
        return "phase2d_bounded_persistence_supported"
    return "phase2d_bounded_persistence_not_supported"
