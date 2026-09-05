"""ITO-aware multi-objective selection utilities.

This module is deliberately separate from :mod:`adversarial_sbox.evolution` so
historical ``constraint_distance`` and ``feasibility_first`` experiments remain
bit-for-bit reproducible.  All objective directions are normalized to
"higher is better" only for Pareto comparisons; no weighted scalar fitness is
introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence

from .cryptoshield import improved_transparency_order
from .evolution import ClassicalMetrics, evaluate_classical


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


def evaluate_with_ito(sbox: Sequence[int]) -> ITOAwareMetrics:
    """Evaluate all classical gates plus Improved Transparency Order.

    The classical evaluator is reused unchanged, then ITO is added as an
    independent objective.  This keeps the historical evaluation path intact.
    """

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
    """Fast-enough deterministic non-dominated sorting for research populations."""

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
    objective_count = len(objective_vector(metrics[indices[0]]))

    for objective_index in range(objective_count):
        ordered = sorted(
            indices,
            key=lambda index: (objective_vector(metrics[index])[objective_index], index),
        )
        minimum = objective_vector(metrics[ordered[0]])[objective_index]
        maximum = objective_vector(metrics[ordered[-1]])[objective_index]
        distances[ordered[0]] = math.inf
        distances[ordered[-1]] = math.inf

        span = maximum - minimum
        if span == 0:
            continue

        for position in range(1, len(ordered) - 1):
            index = ordered[position]
            if math.isinf(distances[index]):
                continue
            previous_value = objective_vector(metrics[ordered[position - 1]])[
                objective_index
            ]
            next_value = objective_vector(metrics[ordered[position + 1]])[
                objective_index
            ]
            distances[index] += (next_value - previous_value) / span

    return distances


def select_nsga2(
    metrics: Sequence[ITOAwareMetrics],
    count: int,
) -> tuple[int, ...]:
    """Select indices using non-dominated rank then crowding distance.

    Tie-breaking is deterministic: higher crowding wins, then lexicographically
    stronger objective vector, then lower original index.
    """

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
