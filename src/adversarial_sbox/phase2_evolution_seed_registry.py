"""Central provenance registry for Phase-2 evolutionary experiment seeds.

Phase-1 experiment seeds are the complete historical evolutionary registry before
Phase 2B. Phase-2B seeds are explicitly reserved here before scientific execution
so later phases can quarantine them without relying on scattered local constants.
"""

from __future__ import annotations

from collections.abc import Iterable

PHASE2B_RESERVED_EVOLUTION_SEEDS = (
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


def prior_evolution_seed_registry() -> tuple[int, ...]:
    """Return every explicitly registered evolutionary seed predating Phase 2B."""

    from . import experiment_seeds

    values: set[int] = set()
    for name, block in vars(experiment_seeds).items():
        if not name.isupper() or not name.endswith("_SEEDS"):
            continue
        if isinstance(block, (tuple, list, set, frozenset)):
            values.update(int(value) for value in block)
    return tuple(sorted(values))


def phase2b_evolution_seeds_are_fresh(seeds: Iterable[int]) -> bool:
    """Validate exact identity, uniqueness and freshness of frozen Phase-2B seeds."""

    frozen = tuple(int(value) for value in seeds)
    return (
        frozen == PHASE2B_RESERVED_EVOLUTION_SEEDS
        and len(frozen) == 9
        and len(set(frozen)) == len(frozen)
        and set(frozen).isdisjoint(prior_evolution_seed_registry())
    )


def reserved_evolution_seed_registry_through_phase2b() -> tuple[int, ...]:
    """Return historical evolutionary seeds plus the explicit Phase-2B reservation."""

    return tuple(
        sorted(
            {
                *prior_evolution_seed_registry(),
                *PHASE2B_RESERVED_EVOLUTION_SEEDS,
            }
        )
    )
