"""Phase-1C balanced-feasibility evolutionary benchmark.

This experiment is deliberately separate from the historical Phase-1/1B ranking
modes. It balances normalized structural hard-gate violations so that an
improvement in nonlinearity cannot hide a large regression in differential
uniformity. SAC remains a secondary search tie-break unless full hard
admissibility is reached.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics
from typing import Any, Iterable, Sequence

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    constraint_violation,
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    random_search,
    structural_gate_count,
)
from .experiment_seeds import DEV_V3_SEEDS

SBox = tuple[int, ...]
Rank = tuple[float, ...]


def structural_violation_profile(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> tuple[float, float, float, float]:
    """Normalized violations for NL, DU, linear correlation and degree."""

    nl = max(0, constraints.min_nonlinearity - metrics.nonlinearity) / max(
        1, constraints.min_nonlinearity
    )
    du = max(
        0, metrics.differential_uniformity - constraints.max_differential_uniformity
    ) / max(1, constraints.max_differential_uniformity)
    linear = max(
        0, metrics.max_linear_correlation - constraints.max_linear_correlation
    ) / max(1, constraints.max_linear_correlation)
    degree = max(
        0, constraints.min_algebraic_degree - metrics.algebraic_degree
    ) / max(1, constraints.min_algebraic_degree)
    return (float(nl), float(du), float(linear), float(degree))


def balanced_primary_key(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> tuple[float, ...]:
    """Scientific V3 comparison key; excludes SAC except via full admissibility.

    Higher is better. After full admissibility and structural gate count, the key
    minimizes the worst normalized structural violation, then total structural
    violation. Raw metrics only break remaining ties.
    """

    violations = structural_violation_profile(metrics, constraints)
    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        float(structural_gate_count(metrics, constraints)),
        float(-max(violations)),
        float(-sum(violations)),
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(metrics.algebraic_degree),
    )


def balanced_search_rank(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> Rank:
    """V3 search rank: balanced primary key plus only secondary SAC guidance."""

    return balanced_primary_key(metrics, constraints) + (
        float(-abs(metrics.sac_score - 0.5)),
    )


def make_balanced_evaluator(
    constraints: HardConstraints,
) -> tuple[Any, dict[SBox, ClassicalMetrics]]:
    cache: dict[SBox, ClassicalMetrics] = {}

    def evaluator(sbox: SBox) -> Rank:
        metrics = cache.get(sbox)
        if metrics is None:
            metrics = evaluate_classical(sbox)
            cache[sbox] = metrics
        return balanced_search_rank(metrics, constraints)

    return evaluator, cache


def _median(values: Iterable[float]) -> float:
    return float(statistics.median(list(values)))


def _metrics_dict(metrics: ClassicalMetrics) -> dict[str, Any]:
    return asdict(metrics)


def _structurally_admissible(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> bool:
    return structural_gate_count(metrics, constraints) == 4


def _dual_nl_du_gate(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.nonlinearity >= constraints.min_nonlinearity
        and metrics.differential_uniformity <= constraints.max_differential_uniformity
    )


def run_phase1c_benchmark(
    *,
    seeds: Sequence[int] = DEV_V3_SEEDS,
    population_size: int = 12,
    generations: int = 8,
    elite_count: int = 2,
    tournament_size: int = 3,
    mutation_swaps: int = 1,
    crossover_rate: float = 0.0,
    immigrant_fraction: float = 0.0,
    offspring_multiplier: int = 3,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one seed is required")
    constraints = constraints or HardConstraints()

    rows: list[dict[str, Any]] = []
    outcomes = {"ga": 0, "random": 0, "tie": 0}
    rank_outcomes = {"ga": 0, "random": 0, "tie": 0}

    for seed in seeds:
        config = EvolutionConfig(
            population_size=population_size,
            generations=generations,
            elite_count=elite_count,
            tournament_size=tournament_size,
            mutation_swaps=mutation_swaps,
            crossover_rate=crossover_rate,
            immigrant_fraction=immigrant_fraction,
            offspring_multiplier=offspring_multiplier,
            seed=int(seed),
        )

        ga_evaluator, ga_cache = make_balanced_evaluator(constraints)
        ga = evolve_permutations(ga_evaluator, config)

        random_evaluator, random_cache = make_balanced_evaluator(constraints)
        baseline = random_search(
            random_evaluator,
            evaluations=ga.evaluations,
            seed=int(seed) ^ 0x5A5A5A5A,
        )

        ga_metrics = ga_cache[ga.best_sbox]
        random_metrics = random_cache[baseline.best_sbox]
        ga_primary = balanced_primary_key(ga_metrics, constraints)
        random_primary = balanced_primary_key(random_metrics, constraints)

        if ga_primary > random_primary:
            outcome = "ga"
        elif ga_primary < random_primary:
            outcome = "random"
        else:
            outcome = "tie"
        outcomes[outcome] += 1

        if ga.best_rank > baseline.best_rank:
            rank_outcome = "ga"
        elif ga.best_rank < baseline.best_rank:
            rank_outcome = "random"
        else:
            rank_outcome = "tie"
        rank_outcomes[rank_outcome] += 1

        ga_profile = structural_violation_profile(ga_metrics, constraints)
        random_profile = structural_violation_profile(random_metrics, constraints)

        rows.append(
            {
                "seed": int(seed),
                "outcome": outcome,
                "rank_outcome": rank_outcome,
                "evaluation_budget_each": ga.evaluations,
                "ga": {
                    "sbox": list(ga.best_sbox),
                    "metrics": _metrics_dict(ga_metrics),
                    "balanced_primary_key": list(ga_primary),
                    "rank": list(ga.best_rank),
                    "structural_violation_profile": list(ga_profile),
                    "max_structural_violation": max(ga_profile),
                    "total_structural_violation": sum(ga_profile),
                    "constraint_violation": constraint_violation(ga_metrics, constraints),
                    "history": [list(rank) for rank in ga.best_rank_history],
                },
                "random": {
                    "sbox": list(baseline.best_sbox),
                    "metrics": _metrics_dict(random_metrics),
                    "balanced_primary_key": list(random_primary),
                    "rank": list(baseline.best_rank),
                    "structural_violation_profile": list(random_profile),
                    "max_structural_violation": max(random_profile),
                    "total_structural_violation": sum(random_profile),
                    "constraint_violation": constraint_violation(
                        random_metrics, constraints
                    ),
                },
            }
        )

    def metrics(side: str, name: str) -> list[float]:
        return [float(row[side]["metrics"][name]) for row in rows]

    ga_admissible = sum(
        is_admissible(ClassicalMetrics(**row["ga"]["metrics"]), constraints)
        for row in rows
    )
    random_admissible = sum(
        is_admissible(ClassicalMetrics(**row["random"]["metrics"]), constraints)
        for row in rows
    )
    ga_structural = sum(
        _structurally_admissible(
            ClassicalMetrics(**row["ga"]["metrics"]), constraints
        )
        for row in rows
    )
    random_structural = sum(
        _structurally_admissible(
            ClassicalMetrics(**row["random"]["metrics"]), constraints
        )
        for row in rows
    )
    ga_dual = sum(
        _dual_nl_du_gate(ClassicalMetrics(**row["ga"]["metrics"]), constraints)
        for row in rows
    )
    random_dual = sum(
        _dual_nl_du_gate(
            ClassicalMetrics(**row["random"]["metrics"]), constraints
        )
        for row in rows
    )

    if outcomes["ga"] > outcomes["random"]:
        preliminary = "ga_ahead"
    elif outcomes["random"] > outcomes["ga"]:
        preliminary = "random_ahead"
    else:
        preliminary = "inconclusive"

    return {
        "schema_version": 1,
        "experiment": "phase1c_balanced_feasibility_vs_equal_budget_random",
        "scientific_status": "development_not_confirmation",
        "configuration": {
            "seeds": [int(seed) for seed in seeds],
            "population_size": population_size,
            "generations": generations,
            "elite_count": elite_count,
            "tournament_size": tournament_size,
            "mutation_swaps": mutation_swaps,
            "crossover_rate": crossover_rate,
            "immigrant_fraction": immigrant_fraction,
            "offspring_multiplier": offspring_multiplier,
            "comparison_key": "balanced_primary_key_v1",
            "search_rank": "balanced_feasibility_v1",
            "constraints": asdict(constraints),
        },
        "summary": {
            "ga_wins": outcomes["ga"],
            "random_wins": outcomes["random"],
            "ties": outcomes["tie"],
            "rank_ga_wins": rank_outcomes["ga"],
            "rank_random_wins": rank_outcomes["random"],
            "rank_ties": rank_outcomes["tie"],
            "preliminary_verdict": preliminary,
            "admissible_ga": ga_admissible,
            "admissible_random": random_admissible,
            "structural_admissible_ga": ga_structural,
            "structural_admissible_random": random_structural,
            "dual_nl_du_gate_ga": ga_dual,
            "dual_nl_du_gate_random": random_dual,
            "median_max_structural_violation_ga": _median(
                row["ga"]["max_structural_violation"] for row in rows
            ),
            "median_max_structural_violation_random": _median(
                row["random"]["max_structural_violation"] for row in rows
            ),
            "median_total_structural_violation_ga": _median(
                row["ga"]["total_structural_violation"] for row in rows
            ),
            "median_total_structural_violation_random": _median(
                row["random"]["total_structural_violation"] for row in rows
            ),
            "median_constraint_violation_ga": _median(
                row["ga"]["constraint_violation"] for row in rows
            ),
            "median_constraint_violation_random": _median(
                row["random"]["constraint_violation"] for row in rows
            ),
            "median_nonlinearity_ga": _median(metrics("ga", "nonlinearity")),
            "median_nonlinearity_random": _median(metrics("random", "nonlinearity")),
            "median_differential_uniformity_ga": _median(
                metrics("ga", "differential_uniformity")
            ),
            "median_differential_uniformity_random": _median(
                metrics("random", "differential_uniformity")
            ),
            "median_max_linear_correlation_ga": _median(
                metrics("ga", "max_linear_correlation")
            ),
            "median_max_linear_correlation_random": _median(
                metrics("random", "max_linear_correlation")
            ),
        },
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1c-benchmark.json"))
    parser.add_argument("--mutation-swaps", type=int, default=1)
    parser.add_argument("--population-size", type=int, default=12)
    parser.add_argument("--generations", type=int, default=8)
    parser.add_argument("--elite-count", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=3)
    parser.add_argument("--crossover-rate", type=float, default=0.0)
    parser.add_argument("--immigrant-fraction", type=float, default=0.0)
    parser.add_argument("--offspring-multiplier", type=int, default=3)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEV_V3_SEEDS))
    args = parser.parse_args()

    result = run_phase1c_benchmark(
        seeds=tuple(args.seeds),
        mutation_swaps=args.mutation_swaps,
        population_size=args.population_size,
        generations=args.generations,
        elite_count=args.elite_count,
        tournament_size=args.tournament_size,
        crossover_rate=args.crossover_rate,
        immigrant_fraction=args.immigrant_fraction,
        offspring_multiplier=args.offspring_multiplier,
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
