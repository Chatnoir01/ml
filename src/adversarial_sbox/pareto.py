"""ITO-aware multi-objective selection and staged evolutionary search.

This module is deliberately separate from :mod:`adversarial_sbox.evolution` so
historical ``constraint_distance`` and ``feasibility_first`` experiments remain
bit-for-bit reproducible. All objective directions are normalized to
"higher is better" only for Pareto comparisons; no weighted scalar fitness is
introduced.

ITO is substantially more expensive than the classical gates. The staged search
therefore evaluates every candidate classically, shortlists by the frozen
feasibility-first policy, and spends ITO evaluations only on that shortlist.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
import math
import random

from .cryptoshield import improved_transparency_order, is_bijective, validate_sbox
from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    evaluate_classical,
    feasibility_rank,
    ordered_crossover,
    random_sbox,
    swap_mutation,
)

SBox = tuple[int, ...]
ClassicalEvaluator = Callable[[Sequence[int]], ClassicalMetrics]
ITOEvaluator = Callable[[Sequence[int]], float]


@dataclass(frozen=True, slots=True)
class ITOAwareMetrics:
    nonlinearity: int
    differential_uniformity: int
    max_linear_correlation: int
    sac_score: float
    algebraic_degree: int
    improved_transparency_order: float
    fingerprint: str

    @classmethod
    def from_classical(
        cls,
        metrics: ClassicalMetrics,
        *,
        improved_transparency_order_value: float,
    ) -> "ITOAwareMetrics":
        return cls(
            nonlinearity=metrics.nonlinearity,
            differential_uniformity=metrics.differential_uniformity,
            max_linear_correlation=metrics.max_linear_correlation,
            sac_score=metrics.sac_score,
            algebraic_degree=metrics.algebraic_degree,
            improved_transparency_order=float(improved_transparency_order_value),
            fingerprint=metrics.fingerprint,
        )


@dataclass(frozen=True, slots=True)
class StagedParetoConfig:
    """Configuration for the optional staged ITO-aware evolutionary path."""

    population_size: int = 12
    generations: int = 4
    shortlist_size: int = 6
    parent_count: int = 4
    mutation_swaps: int = 2
    crossover_rate: float = 0.5
    seed: int = 0

    def __post_init__(self) -> None:
        if self.population_size < 4:
            raise ValueError("population_size must be >= 4")
        if self.generations < 1:
            raise ValueError("generations must be >= 1")
        if not 2 <= self.shortlist_size <= self.population_size:
            raise ValueError("shortlist_size must be in [2, population_size]")
        if not 2 <= self.parent_count <= self.shortlist_size:
            raise ValueError("parent_count must be in [2, shortlist_size]")
        if self.mutation_swaps < 1:
            raise ValueError("mutation_swaps must be >= 1")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class StagedParetoResult:
    pareto_sboxes: tuple[SBox, ...]
    pareto_metrics: tuple[ITOAwareMetrics, ...]
    classical_evaluations: int
    ito_evaluations: int
    front_size_history: tuple[int, ...]


def evaluate_with_ito(sbox: Sequence[int]) -> ITOAwareMetrics:
    """Evaluate all classical gates plus Improved Transparency Order."""

    classical = evaluate_classical(sbox)
    ito = improved_transparency_order(sbox)
    return ITOAwareMetrics.from_classical(
        classical,
        improved_transparency_order_value=ito,
    )


def objective_vector(metrics: ITOAwareMetrics) -> tuple[float, ...]:
    """Return Pareto objectives normalized so every axis is maximized."""

    return (
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(-metrics.improved_transparency_order),
        float(-abs(metrics.sac_score - 0.5)),
        float(metrics.algebraic_degree),
    )


def dominates(left: ITOAwareMetrics, right: ITOAwareMetrics) -> bool:
    """Return whether ``left`` strictly Pareto-dominates ``right``."""

    left_vector = objective_vector(left)
    right_vector = objective_vector(right)
    return all(a >= b for a, b in zip(left_vector, right_vector)) and any(
        a > b for a, b in zip(left_vector, right_vector)
    )


def non_dominated_sort(
    metrics: Sequence[ITOAwareMetrics],
) -> tuple[tuple[int, ...], ...]:
    """Deterministic non-dominated sorting for research-sized populations."""

    count = len(metrics)
    dominates_sets: list[list[int]] = [[] for _ in range(count)]
    domination_counts = [0] * count
    first_front: list[int] = []

    for left in range(count):
        for right in range(left + 1, count):
            if dominates(metrics[left], metrics[right]):
                dominates_sets[left].append(right)
                domination_counts[right] += 1
            elif dominates(metrics[right], metrics[left]):
                dominates_sets[right].append(left)
                domination_counts[left] += 1

    for index, domination_count in enumerate(domination_counts):
        if domination_count == 0:
            first_front.append(index)

    fronts: list[tuple[int, ...]] = []
    current = tuple(first_front)
    while current:
        fronts.append(current)
        next_front: list[int] = []
        for winner in current:
            for loser in dominates_sets[winner]:
                domination_counts[loser] -= 1
                if domination_counts[loser] == 0:
                    next_front.append(loser)
        current = tuple(sorted(next_front))

    return tuple(fronts)


def crowding_distance(
    metrics: Sequence[ITOAwareMetrics],
    front: Sequence[int],
) -> dict[int, float]:
    """Compute standard NSGA-II crowding distance for one front."""

    indices = tuple(front)
    if not indices:
        return {}
    if len(indices) <= 2:
        return {index: math.inf for index in indices}

    distances = {index: 0.0 for index in indices}
    vectors = {index: objective_vector(metrics[index]) for index in indices}
    objective_count = len(vectors[indices[0]])

    for objective_index in range(objective_count):
        ordered = sorted(
            indices,
            key=lambda index: (vectors[index][objective_index], index),
        )
        minimum = vectors[ordered[0]][objective_index]
        maximum = vectors[ordered[-1]][objective_index]
        span = maximum - minimum
        if span == 0:
            continue

        distances[ordered[0]] = math.inf
        distances[ordered[-1]] = math.inf
        for position in range(1, len(ordered) - 1):
            index = ordered[position]
            if math.isinf(distances[index]):
                continue
            previous_value = vectors[ordered[position - 1]][objective_index]
            next_value = vectors[ordered[position + 1]][objective_index]
            distances[index] += (next_value - previous_value) / span

    return distances


def select_nsga2(
    metrics: Sequence[ITOAwareMetrics],
    count: int,
) -> tuple[int, ...]:
    """Select indices using non-dominated rank then crowding distance."""

    if count < 0 or count > len(metrics):
        raise ValueError("count must be in [0, len(metrics)]")
    if count == 0:
        return ()

    selected: list[int] = []
    for front in non_dominated_sort(metrics):
        remaining = count - len(selected)
        if remaining <= 0:
            break
        if len(front) <= remaining:
            selected.extend(front)
            continue

        distances = crowding_distance(metrics, front)
        ordered = sorted(
            front,
            key=lambda index: (
                distances[index],
                objective_vector(metrics[index]),
                -index,
            ),
            reverse=True,
        )
        selected.extend(ordered[:remaining])
        break

    return tuple(selected)


def evolve_staged_pareto(
    config: StagedParetoConfig,
    *,
    constraints: HardConstraints | None = None,
    initial_population: Iterable[Sequence[int]] | None = None,
    classical_evaluator: ClassicalEvaluator = evaluate_classical,
    ito_evaluator: ITOEvaluator = improved_transparency_order,
) -> StagedParetoResult:
    """Run a deterministic classical-prefiltered, ITO-aware Pareto search.

    Every unique candidate receives a classical evaluation. Only the top
    ``shortlist_size`` candidates under the already-frozen feasibility-first
    ordering receive the expensive ITO metric. Parent selection inside that
    shortlist is then Pareto/NSGA-II, so ITO is never collapsed into an
    arbitrary scalar weight. New offspring are globally unique within the run,
    making classical and ITO evaluation counts auditable.
    """

    frozen_constraints = constraints or HardConstraints()
    rng = random.Random(config.seed)
    classical_cache: dict[SBox, ClassicalMetrics] = {}
    ito_cache: dict[SBox, ITOAwareMetrics] = {}

    def freeze(candidate: Sequence[int]) -> SBox:
        value = validate_sbox(candidate)
        if not is_bijective(value):
            raise ValueError("staged Pareto search requires bijective S-Boxes")
        return value

    population: list[SBox] = []
    seen_ever: set[SBox] = set()
    for candidate in initial_population or ():
        frozen = freeze(candidate)
        if frozen not in seen_ever:
            seen_ever.add(frozen)
            population.append(frozen)
        if len(population) == config.population_size:
            break

    while len(population) < config.population_size:
        candidate = random_sbox(rng)
        if candidate not in seen_ever:
            seen_ever.add(candidate)
            population.append(candidate)

    def classical(candidate: SBox) -> ClassicalMetrics:
        cached = classical_cache.get(candidate)
        if cached is None:
            cached = classical_evaluator(candidate)
            classical_cache[candidate] = cached
        return cached

    def with_ito(candidate: SBox) -> ITOAwareMetrics:
        cached = ito_cache.get(candidate)
        if cached is None:
            cached = ITOAwareMetrics.from_classical(
                classical(candidate),
                improved_transparency_order_value=ito_evaluator(candidate),
            )
            ito_cache[candidate] = cached
        return cached

    def shortlist(current: Sequence[SBox]) -> tuple[SBox, ...]:
        ranked = sorted(
            current,
            key=lambda candidate: (
                feasibility_rank(classical(candidate), frozen_constraints),
                candidate,
            ),
            reverse=True,
        )
        return tuple(ranked[: config.shortlist_size])

    history: list[int] = []
    for _ in range(config.generations):
        shortlisted = shortlist(population)
        shortlisted_metrics = tuple(with_ito(candidate) for candidate in shortlisted)
        history.append(len(non_dominated_sort(shortlisted_metrics)[0]))
        parents = tuple(
            shortlisted[index]
            for index in select_nsga2(shortlisted_metrics, config.parent_count)
        )

        next_population = list(parents)
        next_seen = set(next_population)
        while len(next_population) < config.population_size:
            parent_a = rng.choice(parents)
            if rng.random() < config.crossover_rate:
                parent_b = rng.choice(parents)
                child = ordered_crossover(parent_a, parent_b, rng)
            else:
                child = parent_a
            child = swap_mutation(child, rng, swaps=config.mutation_swaps)
            if child in next_seen or child in seen_ever:
                continue
            next_seen.add(child)
            seen_ever.add(child)
            next_population.append(child)
        population = next_population

    final_shortlist = shortlist(population)
    final_metrics = tuple(with_ito(candidate) for candidate in final_shortlist)
    final_front = non_dominated_sort(final_metrics)[0]

    return StagedParetoResult(
        pareto_sboxes=tuple(final_shortlist[index] for index in final_front),
        pareto_metrics=tuple(final_metrics[index] for index in final_front),
        classical_evaluations=len(classical_cache),
        ito_evaluations=len(ito_cache),
        front_size_history=tuple(history),
    )
