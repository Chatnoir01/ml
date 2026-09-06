"""Central freshness check for Phase-2 evolutionary experiment seeds.

Phase-1 experiment seeds are the complete historical evolutionary registry before
Phase 2B. The registry is collected from the explicit ``*_SEEDS`` constants in
``experiment_seeds`` so later additions there automatically remain quarantined.
"""

from __future__ import annotations

from collections.abc import Iterable


def prior_evolution_seed_registry() -> tuple[int, ...]:
    from . import experiment_seeds

    values: set[int] = set()
    for name, block in vars(experiment_seeds).items():
        if not name.isupper() or not name.endswith("_SEEDS"):
            continue
        if isinstance(block, (tuple, list, set, frozenset)):
            values.update(int(value) for value in block)
    return tuple(sorted(values))


def phase2b_evolution_seeds_are_fresh(seeds: Iterable[int]) -> bool:
    frozen = tuple(int(value) for value in seeds)
    return (
        len(frozen) == 9
        and len(set(frozen)) == len(frozen)
        and set(frozen).isdisjoint(prior_evolution_seed_registry())
    )
