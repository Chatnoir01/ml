"""Fail-closed curriculum freezing for preregistered Phase 2G checkpoints.

This module performs no neural training, inference, or evolution. It only validates
and canonically freezes the exact 20-candidate curriculum source required by the
Phase-2G protocol before a checkpoint model is ever allowed to consume it.
"""

from __future__ import annotations

from collections.abc import Sequence

from .cryptoshield import validate_sbox
from .phase2g import ARMS, CHECKPOINT_GENERATIONS
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
POPULATION_SIZE = 20


def _freeze_population(population: Sequence[Sequence[int]], *, role: str) -> tuple[SBox, ...]:
    if len(population) != POPULATION_SIZE:
        raise ValueError(f"Phase-2G {role} population must contain exactly 20 candidates")

    frozen = tuple(validate_sbox(candidate) for candidate in population)
    if len(set(frozen)) != POPULATION_SIZE:
        raise ValueError(f"Phase-2G {role} population must contain 20 unique candidates")

    return tuple(sorted(frozen, key=fingerprint_sbox))


def freeze_checkpoint_curriculum(
    *,
    arm: str,
    checkpoint_generation: int,
    initial_population: Sequence[Sequence[int]],
    current_population: Sequence[Sequence[int]],
) -> tuple[SBox, ...]:
    """Return the exact canonical curriculum mandated for one Phase-2G checkpoint.

    F is frozen to the seed's initial population at every checkpoint. C, A and S
    consume the exact current population. Both inputs are validated fail-closed so
    malformed, duplicate, or wrong-size populations cannot silently enter model
    training later.
    """

    if arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {arm!r}")
    if int(checkpoint_generation) not in CHECKPOINT_GENERATIONS:
        raise ValueError(
            f"generation {checkpoint_generation!r} is not a frozen Phase-2G checkpoint"
        )

    frozen_initial = _freeze_population(initial_population, role="initial")
    frozen_current = _freeze_population(current_population, role="current")

    return frozen_initial if arm == "F" else frozen_current
