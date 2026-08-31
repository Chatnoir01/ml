"""Deterministic classical genetic search over bijective 8x8 S-Boxes.

This module deliberately keeps the evolutionary machinery independent from any
neural model. Classical cryptographic properties are evaluated separately and
used as hard admissibility gates plus a lexicographic ranking signal.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from collections.abc import Callable, Iterable, Sequence

from .cryptoshield import (
    algebraic_degree,
    differential_uniformity,
    is_bijective,
    max_linear_correlation,
    nonlinearity,
    sac_score,
    validate_sbox,
)
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
Rank = tuple[float, ...]
Evaluator = Callable[[SBox], Rank]


@dataclass(frozen=True, slots=True)
class ClassicalMetrics:
    nonlinearity: int
    differential_uniformity: int
    max_linear_correlation: int
    sac_score: float
    algebraic_degree: int
    fingerprint: str


@dataclass(frozen=True, slots=True)
class HardConstraints:
    min_nonlinearity: int = 100
    max_differential_uniformity: int = 8
    max_linear_correlation: int = 64
    min_algebraic_degree: int = 6
    max_sac_deviation: float = 0.05

    def __post_init__(self) -> None:
        if not 0 <= self.min_nonlinearity <= 128:
            raise ValueError("min_nonlinearity must be in [0, 128]")
        if not 2 <= self.max_differential_uniformity <= 256:
            raise ValueError("max_differential_uniformity must be in [2, 256]")
        if not 0 <= self.max_linear_correlation <= 256:
            raise ValueError("max_linear_correlation must be in [0, 256]")
        if not 0 <= self.min_algebraic_degree <= 8:
            raise ValueError("min_algebraic_degree must be in [0, 8]")
        if not 0.0 <= self.max_sac_deviation <= 0.5:
            raise ValueError("max_sac_deviation must be in [0, 0.5]")


@dataclass(frozen=True, slots=True)
class EvolutionConfig:
    population_size: int = 32
    generations: int = 20
    elite_count: int = 4
    tournament_size: int = 4
    mutation_swaps: int = 2
    crossover_rate: float = 0.9
    seed: int = 0

    def __post_init__(self) -> None:
        if self.population_size < 4:
            raise ValueError("population_size must be >= 4")
        if self.generations < 1:
            raise ValueError("generations must be >= 1")
        if not 1 <= self.elite_count < self.population_size:
            raise ValueError("elite_count must be in [1, population_size)")
        if not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("tournament_size must be in [2, population_size]")
        if self.mutation_swaps < 1:
            raise ValueError("mutation_swaps must be >= 1")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class EvolutionResult:
    best_sbox: SBox
    best_rank: Rank
    best_rank_history: tuple[Rank, ...]
    evaluations: int


def evaluate_classical(sbox: Sequence[int]) -> ClassicalMetrics:
    """Compute the Phase-1 classical measurements for one S-Box."""

    frozen = validate_sbox(sbox)
    return ClassicalMetrics(
        nonlinearity=nonlinearity(frozen),
        differential_uniformity=differential_uniformity(frozen),
        max_linear_correlation=max_linear_correlation(frozen),
        sac_score=sac_score(frozen),
        algebraic_degree=algebraic_degree(frozen),
        fingerprint=fingerprint_sbox(frozen),
    )


def is_admissible(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    """Return whether all hard classical gates are satisfied."""

    return (
        metrics.nonlinearity >= constraints.min_nonlinearity
        and metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
        and abs(metrics.sac_score - 0.5) <= constraints.max_sac_deviation
    )


def constraint_violation(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> float:
    """Normalized distance from the hard admissibility region.

    Admissible candidates have exactly zero violation.  Infeasible candidates
    receive a positive score proportional to how far they miss each gate.  This
    gives the GA a direction toward feasibility without allowing a soft score to
    override the final hard constraints.
    """

    nl_denominator = max(1, constraints.min_nonlinearity)
    du_denominator = max(1, constraints.max_differential_uniformity)
    linear_denominator = max(1, constraints.max_linear_correlation)
    degree_denominator = max(1, constraints.min_algebraic_degree)
    sac_denominator = max(constraints.max_sac_deviation, 1e-12)

    nl_violation = max(0, constraints.min_nonlinearity - metrics.nonlinearity) / nl_denominator
    du_violation = max(
        0, metrics.differential_uniformity - constraints.max_differential_uniformity
    ) / du_denominator
    linear_violation = max(
        0, metrics.max_linear_correlation - constraints.max_linear_correlation
    ) / linear_denominator
    degree_violation = max(
        0, constraints.min_algebraic_degree - metrics.algebraic_degree
    ) / degree_denominator
    sac_violation = max(
        0.0, abs(metrics.sac_score - 0.5) - constraints.max_sac_deviation
    ) / sac_denominator

    return float(
        nl_violation
        + du_violation
        + linear_violation
        + degree_violation
        + sac_violation
    )


def classical_rank(metrics: ClassicalMetrics, constraints: HardConstraints) -> Rank:
    """Lexicographic rank, higher is better.

    The first coordinate remains the hard admissibility gate.  The second is the
    negative normalized constraint violation, which guides infeasible candidates
    toward the admissible region.  Remaining coordinates rank candidates only
    after feasibility distance is accounted for.
    """

    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        -constraint_violation(metrics, constraints),
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(-abs(metrics.sac_score - 0.5)),
        float(metrics.algebraic_degree),
    )


def make_classical_evaluator(
    constraints: HardConstraints,
) -> tuple[Evaluator, dict[SBox, ClassicalMetrics]]:
    """Build a cached classical evaluator and expose its metrics cache."""

    cache: dict[SBox, ClassicalMetrics] = {}

    def evaluator(sbox: SBox) -> Rank:
        metrics = cache.get(sbox)
        if metrics is None:
            metrics = evaluate_classical(sbox)
            cache[sbox] = metrics
        return classical_rank(metrics, constraints)

    return evaluator, cache


def random_sbox(rng: random.Random) -> SBox:
    values = list(range(256))
    rng.shuffle(values)
    return tuple(values)


def swap_mutation(parent: Sequence[int], rng: random.Random, *, swaps: int = 1) -> SBox:
    """Apply one or more swap mutations while preserving a permutation."""

    values = list(validate_sbox(parent))
    if not is_bijective(values):
        raise ValueError("swap_mutation requires a bijective parent")
    if swaps < 1:
        raise ValueError("swaps must be >= 1")
    for _ in range(swaps):
        left, right = rng.sample(range(256), 2)
        values[left], values[right] = values[right], values[left]
    return tuple(values)


def ordered_crossover(
    parent_a: Sequence[int], parent_b: Sequence[int], rng: random.Random
) -> SBox:
    """Permutation-preserving ordered crossover (OX)."""

    a = validate_sbox(parent_a)
    b = validate_sbox(parent_b)
    if not is_bijective(a) or not is_bijective(b):
        raise ValueError("ordered_crossover requires bijective parents")

    start, end = sorted(rng.sample(range(256), 2))
    child: list[int | None] = [None] * 256
    child[start:end] = a[start:end]
    used = set(a[start:end])

    fill_values = [value for value in b if value not in used]
    fill_index = 0
    for index in list(range(end, 256)) + list(range(0, start)):
        child[index] = fill_values[fill_index]
        fill_index += 1

    result = tuple(int(value) for value in child if value is not None)
    if len(result) != 256 or not is_bijective(result):
        raise RuntimeError("ordered crossover violated permutation invariant")
    return result


def _unique_population(population: Iterable[SBox]) -> list[SBox]:
    seen: set[SBox] = set()
    unique: list[SBox] = []
    for candidate in population:
        frozen = validate_sbox(candidate)
        if not is_bijective(frozen):
            raise ValueError("population contains a non-bijective S-Box")
        if frozen not in seen:
            seen.add(frozen)
            unique.append(frozen)
    return unique


def _tournament(
    ranked: list[tuple[SBox, Rank]], rng: random.Random, size: int
) -> SBox:
    contenders = rng.sample(ranked, size)
    return max(contenders, key=lambda item: item[1])[0]


def evolve_permutations(
    evaluator: Evaluator,
    config: EvolutionConfig,
    *,
    initial_population: Iterable[SBox] | None = None,
) -> EvolutionResult:
    """Run deterministic elitist GA over globally unique permutation candidates.

    Each distinct S-Box is evaluated at most once. Elites retain their previous
    ranks, while every child must be globally unseen. The resulting evaluation
    count therefore has a deterministic, directly comparable random-search
    budget.
    """

    rng = random.Random(config.seed)
    population = _unique_population(initial_population or ())
    while len(population) < config.population_size:
        candidate = random_sbox(rng)
        if candidate not in population:
            population.append(candidate)
    if len(population) > config.population_size:
        population = population[: config.population_size]

    seen_ever: set[SBox] = set(population)
    evaluations = 0
    history: list[Rank] = []

    def rank_new(items: list[SBox]) -> list[tuple[SBox, Rank]]:
        nonlocal evaluations
        ranked_items = [(candidate, evaluator(candidate)) for candidate in items]
        evaluations += len(items)
        ranked_items.sort(key=lambda item: item[1], reverse=True)
        return ranked_items

    ranked = rank_new(population)
    history.append(ranked[0][1])

    for _ in range(config.generations):
        elite_ranked = ranked[: config.elite_count]
        children: list[SBox] = []

        while len(children) < config.population_size - config.elite_count:
            parent_a = _tournament(ranked, rng, config.tournament_size)
            if rng.random() < config.crossover_rate:
                parent_b = _tournament(ranked, rng, config.tournament_size)
                child = ordered_crossover(parent_a, parent_b, rng)
            else:
                child = parent_a
            child = swap_mutation(child, rng, swaps=config.mutation_swaps)

            if child in seen_ever:
                continue
            seen_ever.add(child)
            children.append(child)

        ranked = elite_ranked + rank_new(children)
        ranked.sort(key=lambda item: item[1], reverse=True)
        history.append(ranked[0][1])

    return EvolutionResult(
        best_sbox=ranked[0][0],
        best_rank=ranked[0][1],
        best_rank_history=tuple(history),
        evaluations=evaluations,
    )


def random_search(evaluator: Evaluator, *, evaluations: int, seed: int) -> EvolutionResult:
    """Random-search baseline with an explicit unique evaluation budget."""

    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    rng = random.Random(seed)
    seen: set[SBox] = set()
    best_sbox: SBox | None = None
    best_rank: Rank | None = None
    history: list[Rank] = []

    while len(seen) < evaluations:
        candidate = random_sbox(rng)
        if candidate in seen:
            continue
        seen.add(candidate)
        rank = evaluator(candidate)
        if best_rank is None or rank > best_rank:
            best_sbox = candidate
            best_rank = rank
        history.append(best_rank)

    assert best_sbox is not None and best_rank is not None
    return EvolutionResult(
        best_sbox=best_sbox,
        best_rank=best_rank,
        best_rank_history=tuple(history),
        evaluations=evaluations,
    )


def equivalent_random_budget(config: EvolutionConfig) -> int:
    """Exact number of unique S-Box evaluations performed by one GA run."""

    children_per_generation = config.population_size - config.elite_count
    return config.population_size + config.generations * children_per_generation
