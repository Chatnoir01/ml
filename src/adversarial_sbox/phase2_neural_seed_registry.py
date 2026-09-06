"""Central provenance registry for frozen/executed Phase-2 neural seeds.

This module is intentionally lazy: phase modules are imported inside functions so
historical contracts can query the registry without creating circular imports.
"""

from __future__ import annotations

from typing import Iterable

SeedBlock = tuple[str, tuple[int, ...], tuple[int, ...]]


def _freeze(values: Iterable[int]) -> tuple[int, ...]:
    return tuple(int(value) for value in values)


def prior_blocks_before_phase2au() -> tuple[SeedBlock, ...]:
    """Every frozen/executed Phase-2 neural registry predating Phase 2A-U."""

    from .phase2a import DATASET_SEEDS as A_DATASET, MODEL_SEEDS as A_MODEL
    from .phase2ad import DATASET_SEEDS as AD_DATASET, MODEL_SEEDS as AD_MODEL
    from .phase2ap import DATASET_SEEDS as AP_DATASET, MODEL_SEEDS as AP_MODEL
    from .phase2ar import DATASET_SEEDS as AR_DATASET, MODEL_SEEDS as AR_MODEL
    from .phase2as import DATASET_SEEDS as AS_DATASET, MODEL_SEEDS as AS_MODEL
    from .phase2at import DATASET_SEEDS as AT_DATASET, MODEL_SEEDS as AT_MODEL

    return (
        ("phase2a", _freeze(A_DATASET), _freeze(A_MODEL)),
        ("phase2ad", _freeze(AD_DATASET), _freeze(AD_MODEL)),
        ("phase2ap", _freeze(AP_DATASET), _freeze(AP_MODEL)),
        ("phase2ar", _freeze(AR_DATASET), _freeze(AR_MODEL)),
        ("phase2as", _freeze(AS_DATASET), _freeze(AS_MODEL)),
        ("phase2at", _freeze(AT_DATASET), _freeze(AT_MODEL)),
    )


def phase2au_blocks() -> tuple[SeedBlock, ...]:
    from .phase2au import (
        BLOCK_A_DATASET_SEEDS,
        BLOCK_A_MODEL_SEEDS,
        BLOCK_B_DATASET_SEEDS,
        BLOCK_B_MODEL_SEEDS,
    )

    return (
        ("phase2au-A", _freeze(BLOCK_A_DATASET_SEEDS), _freeze(BLOCK_A_MODEL_SEEDS)),
        ("phase2au-B", _freeze(BLOCK_B_DATASET_SEEDS), _freeze(BLOCK_B_MODEL_SEEDS)),
    )


def phase2au2_blocks() -> tuple[SeedBlock, ...]:
    """Frozen U2 requalification blocks, including the Phase-2B fitness block."""

    from .phase2au2 import (
        BLOCK_A_DATASET_SEEDS,
        BLOCK_A_MODEL_SEEDS,
        BLOCK_B_DATASET_SEEDS,
        BLOCK_B_MODEL_SEEDS,
    )

    return (
        ("phase2au2-A", _freeze(BLOCK_A_DATASET_SEEDS), _freeze(BLOCK_A_MODEL_SEEDS)),
        ("phase2au2-B", _freeze(BLOCK_B_DATASET_SEEDS), _freeze(BLOCK_B_MODEL_SEEDS)),
    )


def phase2b_reserved_blocks() -> tuple[SeedBlock, ...]:
    """Fresh Phase-2B terminal-validation block reserved before execution."""

    from .phase2b import VALIDATION_DATASET_SEEDS, VALIDATION_MODEL_SEEDS

    return (
        (
            "phase2b-validation-V",
            _freeze(VALIDATION_DATASET_SEEDS),
            _freeze(VALIDATION_MODEL_SEEDS),
        ),
    )


def seed_union(blocks: Iterable[SeedBlock]) -> tuple[int, ...]:
    values: set[int] = set()
    for _name, dataset_seeds, model_seeds in blocks:
        values.update(dataset_seeds)
        values.update(model_seeds)
    return tuple(sorted(values))


def prior_seed_registry_before_phase2au() -> tuple[int, ...]:
    return seed_union(prior_blocks_before_phase2au())


def prior_seed_registry_before_phase2au2() -> tuple[int, ...]:
    return seed_union((*prior_blocks_before_phase2au(), *phase2au_blocks()))


def prior_seed_registry_before_phase2b() -> tuple[int, ...]:
    """Complete frozen/executed neural registry before Phase-2B validation seeds."""

    return seed_union(
        (*prior_blocks_before_phase2au(), *phase2au_blocks(), *phase2au2_blocks())
    )


def complete_seed_registry_through_phase2b() -> tuple[int, ...]:
    """Complete registry including the reserved Phase-2B held-out Block V."""

    return seed_union(
        (
            *prior_blocks_before_phase2au(),
            *phase2au_blocks(),
            *phase2au2_blocks(),
            *phase2b_reserved_blocks(),
        )
    )


def overlap_with_prior(
    dataset_seeds: Iterable[int],
    model_seeds: Iterable[int],
    *,
    before: str,
) -> tuple[int, ...]:
    candidate = {int(value) for value in dataset_seeds} | {
        int(value) for value in model_seeds
    }
    if before == "phase2au":
        prior = set(prior_seed_registry_before_phase2au())
    elif before == "phase2au2":
        prior = set(prior_seed_registry_before_phase2au2())
    elif before == "phase2b":
        prior = set(prior_seed_registry_before_phase2b())
    else:
        raise ValueError(f"unsupported Phase-2 provenance boundary {before!r}")
    return tuple(sorted(candidate & prior))


def registry_is_disjoint(
    dataset_seeds: Iterable[int],
    model_seeds: Iterable[int],
    *,
    before: str,
) -> bool:
    return not overlap_with_prior(dataset_seeds, model_seeds, before=before)
