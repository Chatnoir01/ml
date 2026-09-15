"""Central provenance registry for Phase-2 evolutionary experiment seeds.

Phase-1 experiment seeds are the complete historical evolutionary registry before
Phase 2B. Later Phase-2 reservations are declared here before scientific execution
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

# Phase 2D bounded one-generation persistence experiment. Reserved publicly in
# issue #109 before implementation or scientific execution.
PHASE2D_RESERVED_EVOLUTION_SEEDS = (
    426011,
    426023,
    426037,
    426049,
    426061,
    426073,
    426089,
    426101,
    426113,
)

# Phase 2F minimal classical-band neural-pressure experiment. Reserved publicly
# in issue #115 before implementation or scientific execution.
PHASE2F_RESERVED_EVOLUTION_SEEDS = (
    526011,
    526023,
    526037,
    526049,
    526061,
    526073,
    526087,
    526099,
    526111,
)

# Phase 2G adaptive GA↔NN curriculum feedback experiment. Reserved publicly in
# issue #118 before implementation or scientific execution.
PHASE2G_RESERVED_EVOLUTION_SEEDS = (
    726011,
    726023,
    726037,
    726049,
    726061,
    726073,
    726087,
    726099,
    726113,
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


def phase2d_evolution_seeds_are_fresh(seeds: Iterable[int]) -> bool:
    """Validate exact identity, uniqueness and freshness of reserved Phase-2D seeds."""

    frozen = tuple(int(value) for value in seeds)
    return (
        frozen == PHASE2D_RESERVED_EVOLUTION_SEEDS
        and len(frozen) == 9
        and len(set(frozen)) == len(frozen)
        and set(frozen).isdisjoint(reserved_evolution_seed_registry_through_phase2b())
    )


def reserved_evolution_seed_registry_through_phase2d() -> tuple[int, ...]:
    """Return the complete evolutionary registry including Phase-2D reservation."""

    return tuple(
        sorted(
            {
                *reserved_evolution_seed_registry_through_phase2b(),
                *PHASE2D_RESERVED_EVOLUTION_SEEDS,
            }
        )
    )


def phase2f_evolution_seeds_are_fresh(seeds: Iterable[int]) -> bool:
    """Validate exact identity, uniqueness and freshness of reserved Phase-2F seeds."""

    frozen = tuple(int(value) for value in seeds)
    return (
        frozen == PHASE2F_RESERVED_EVOLUTION_SEEDS
        and len(frozen) == 9
        and len(set(frozen)) == len(frozen)
        and set(frozen).isdisjoint(reserved_evolution_seed_registry_through_phase2d())
    )


def reserved_evolution_seed_registry_through_phase2f() -> tuple[int, ...]:
    """Return the complete evolutionary registry including Phase-2F reservation."""

    return tuple(
        sorted(
            {
                *reserved_evolution_seed_registry_through_phase2d(),
                *PHASE2F_RESERVED_EVOLUTION_SEEDS,
            }
        )
    )


def phase2g_evolution_seeds_are_fresh(seeds: Iterable[int]) -> bool:
    """Validate exact identity, uniqueness and freshness of reserved Phase-2G seeds."""

    frozen = tuple(int(value) for value in seeds)
    return (
        frozen == PHASE2G_RESERVED_EVOLUTION_SEEDS
        and len(frozen) == 9
        and len(set(frozen)) == len(frozen)
        and set(frozen).isdisjoint(reserved_evolution_seed_registry_through_phase2f())
    )


def reserved_evolution_seed_registry_through_phase2g() -> tuple[int, ...]:
    """Return the complete evolutionary registry including Phase-2G reservation."""

    return tuple(
        sorted(
            {
                *reserved_evolution_seed_registry_through_phase2f(),
                *PHASE2G_RESERVED_EVOLUTION_SEEDS,
            }
        )
    )
