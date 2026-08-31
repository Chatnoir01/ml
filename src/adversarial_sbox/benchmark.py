"""Reproducible Phase-1 benchmark: evolutionary search vs equal-budget random.

Historical callers keep ``comparison_mode='rank'`` and
``ranking_mode='constraint_distance'`` by default. New experiments may opt into
primary-security outcomes and versioned search rankings without changing old
experiment semantics.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics
from typing import Any, Iterable

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    constraint_violation,
    evolve_permutations,
    is_admissible,
    make_classical_evaluator,
    primary_security_key,
    random_search,
)

CI_SEEDS = (11, 23, 37, 53, 71)
COMPARISON_MODES = ("rank", "primary")


def _metrics_dict(metrics: ClassicalMetrics) -> dict[str, Any]:
    return asdict(metrics)


def _median(values: Iterable[float]) -> float:
    materialized = list(values)
    return float(statistics.median(materialized))


def run_benchmark(
    *,
    seeds: tuple[int, ...] = CI_SEEDS,
    population_size: int = 8,
    generations: int = 3,
    elite_count: int = 2,
    tournament_size: int = 2,
    mutation_swaps: int = 1,
    crossover_rate: float = 0.9,
    immigrant_fraction: float = 0.0,
    offspring_multiplier: int = 1,
    ranking_mode: str = "constraint_distance",
    comparison_mode: str = "rank",
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Run matched-budget GA/random experiments and return JSON-ready evidence."""

    if not seeds:
        raise ValueError("at least one seed is required")
    if comparison_mode not in COMPARISON_MODES:
        raise ValueError(f"unknown comparison_mode: {comparison_mode}")
    constraints = constraints or HardConstraints()

    rows: list[dict[str, Any]] = []
    selected_counts = {"ga": 0, "random": 0, "tie": 0}
    primary_counts = {"ga": 0, "random": 0, "tie": 0}
    rank_counts = {"ga": 0, "random": 0, "tie": 0}

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
            seed=seed,
        )

        ga_evaluator, ga_cache = make_classical_evaluator(
            constraints, ranking_mode=ranking_mode
        )
        ga = evolve_permutations(ga_evaluator, config)

        random_evaluator, random_cache = make_classical_evaluator(
            constraints, ranking_mode=ranking_mode
        )
        baseline = random_search(
            random_evaluator,
            evaluations=ga.evaluations,
            seed=seed ^ 0x5A5A5A5A,
        )

        ga_metrics = ga_cache[ga.best_sbox]
        random_metrics = random_cache[baseline.best_sbox]
        ga_primary = primary_security_key(ga_metrics, constraints)
        random_primary = primary_security_key(random_metrics, constraints)

        if ga.best_rank > baseline.best_rank:
            rank_outcome = "ga"
        elif ga.best_rank < baseline.best_rank:
            rank_outcome = "random"
        else:
            rank_outcome = "tie"
        rank_counts[rank_outcome] += 1

        if ga_primary > random_primary:
            primary_outcome = "ga"
        elif ga_primary < random_primary:
            primary_outcome = "random"
        else:
            primary_outcome = "tie"
        primary_counts[primary_outcome] += 1

        outcome = rank_outcome if comparison_mode == "rank" else primary_outcome
        selected_counts[outcome] += 1

        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "primary_outcome": primary_outcome,
                "rank_outcome": rank_outcome,
                "evaluation_budget_each": ga.evaluations,
                "ga": {
                    "primary_security_key": list(ga_primary),
                    "rank": list(ga.best_rank),
                    "metrics": _metrics_dict(ga_metrics),
                    "constraint_violation": constraint_violation(ga_metrics, constraints),
                    "history": [list(rank) for rank in ga.best_rank_history],
                },
                "random": {
                    "primary_security_key": list(random_primary),
                    "rank": list(baseline.best_rank),
                    "metrics": _metrics_dict(random_metrics),
                    "constraint_violation": constraint_violation(
                        random_metrics, constraints
                    ),
                },
            }
        )

    ga_nl = [row["ga"]["metrics"]["nonlinearity"] for row in rows]
    random_nl = [row["random"]["metrics"]["nonlinearity"] for row in rows]
    ga_du = [row["ga"]["metrics"]["differential_uniformity"] for row in rows]
    random_du = [row["random"]["metrics"]["differential_uniformity"] for row in rows]
    ga_lat = [row["ga"]["metrics"]["max_linear_correlation"] for row in rows]
    random_lat = [row["random"]["metrics"]["max_linear_correlation"] for row in rows]
    ga_violation = [row["ga"]["constraint_violation"] for row in rows]
    random_violation = [row["random"]["constraint_violation"] for row in rows]
    ga_admissible = sum(
        is_admissible(ClassicalMetrics(**row["ga"]["metrics"]), constraints)
        for row in rows
    )
    random_admissible = sum(
        is_admissible(ClassicalMetrics(**row["random"]["metrics"]), constraints)
        for row in rows
    )

    if selected_counts["ga"] > selected_counts["random"]:
        preliminary = "ga_ahead"
    elif selected_counts["random"] > selected_counts["ga"]:
        preliminary = "random_ahead"
    else:
        preliminary = "inconclusive"

    return {
        "schema_version": 3,
        "experiment": "phase1_ga_vs_equal_budget_random",
        "scientific_status": "preliminary_not_gate1",
        "comparison_mode": comparison_mode,
        "ranking_mode": ranking_mode,
        "configuration": {
            "seeds": list(seeds),
            "population_size": population_size,
            "generations": generations,
            "elite_count": elite_count,
            "tournament_size": tournament_size,
            "mutation_swaps": mutation_swaps,
            "crossover_rate": crossover_rate,
            "immigrant_fraction": immigrant_fraction,
            "offspring_multiplier": offspring_multiplier,
            "ranking_mode": ranking_mode,
            "comparison_mode": comparison_mode,
            "constraints": asdict(constraints),
        },
        "summary": {
            "ga_wins": selected_counts["ga"],
            "random_wins": selected_counts["random"],
            "ties": selected_counts["tie"],
            "preliminary_verdict": preliminary,
            "primary_ga_wins": primary_counts["ga"],
            "primary_random_wins": primary_counts["random"],
            "primary_ties": primary_counts["tie"],
            "rank_ga_wins": rank_counts["ga"],
            "rank_random_wins": rank_counts["random"],
            "rank_ties": rank_counts["tie"],
            "admissible_ga": ga_admissible,
            "admissible_random": random_admissible,
            "median_constraint_violation_ga": _median(ga_violation),
            "median_constraint_violation_random": _median(random_violation),
            "median_nonlinearity_ga": _median(ga_nl),
            "median_nonlinearity_random": _median(random_nl),
            "median_differential_uniformity_ga": _median(ga_du),
            "median_differential_uniformity_random": _median(random_du),
            "median_max_linear_correlation_ga": _median(ga_lat),
            "median_max_linear_correlation_random": _median(random_lat),
        },
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1-benchmark.json"))
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--elite-count", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--mutation-swaps", type=int, default=1)
    parser.add_argument("--crossover-rate", type=float, default=0.9)
    parser.add_argument("--immigrant-fraction", type=float, default=0.0)
    parser.add_argument("--offspring-multiplier", type=int, default=1)
    parser.add_argument(
        "--ranking-mode",
        choices=("constraint_distance", "feasibility_first"),
        default="constraint_distance",
    )
    parser.add_argument(
        "--comparison-mode", choices=COMPARISON_MODES, default="rank"
    )
    parser.add_argument(
        "--seeds", type=int, nargs="+", default=list(CI_SEEDS)
    )
    args = parser.parse_args()

    result = run_benchmark(
        seeds=tuple(args.seeds),
        population_size=args.population_size,
        generations=args.generations,
        elite_count=args.elite_count,
        tournament_size=args.tournament_size,
        mutation_swaps=args.mutation_swaps,
        crossover_rate=args.crossover_rate,
        immigrant_fraction=args.immigrant_fraction,
        offspring_multiplier=args.offspring_multiplier,
        ranking_mode=args.ranking_mode,
        comparison_mode=args.comparison_mode,
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
