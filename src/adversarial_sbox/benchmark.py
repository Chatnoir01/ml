"""Reproducible Phase-1 benchmark: classical GA versus equal-budget random search.

The benchmark never turns an experimental outcome into a test failure. It
records losses and ties. Scientific wins are based only on primary classical
security metrics; secondary SAC/tie-break improvements are reported separately.
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
    evolve_permutations,
    is_admissible,
    make_classical_evaluator,
    primary_security_key,
    random_search,
)

CI_SEEDS = (11, 23, 37, 53, 71)


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
    offspring_multiplier: int = 1,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Run matched-budget GA/random experiments and return JSON-ready evidence."""

    if not seeds:
        raise ValueError("at least one seed is required")
    constraints = constraints or HardConstraints()

    rows: list[dict[str, Any]] = []
    ga_wins = random_wins = ties = 0
    ga_rank_wins = random_rank_wins = rank_ties = 0

    for seed in seeds:
        config = EvolutionConfig(
            population_size=population_size,
            generations=generations,
            elite_count=elite_count,
            tournament_size=tournament_size,
            mutation_swaps=mutation_swaps,
            crossover_rate=crossover_rate,
            offspring_multiplier=offspring_multiplier,
            seed=seed,
        )

        ga_evaluator, ga_cache = make_classical_evaluator(constraints)
        ga = evolve_permutations(ga_evaluator, config)

        random_evaluator, random_cache = make_classical_evaluator(constraints)
        baseline = random_search(
            random_evaluator,
            evaluations=ga.evaluations,
            seed=seed ^ 0x5A5A5A5A,
        )

        ga_metrics = ga_cache[ga.best_sbox]
        random_metrics = random_cache[baseline.best_sbox]
        ga_primary = primary_security_key(ga_metrics, constraints)
        random_primary = primary_security_key(random_metrics, constraints)

        if ga_primary > random_primary:
            outcome = "ga"
            ga_wins += 1
        elif ga_primary < random_primary:
            outcome = "random"
            random_wins += 1
        else:
            outcome = "tie"
            ties += 1

        if ga.best_rank > baseline.best_rank:
            rank_outcome = "ga"
            ga_rank_wins += 1
        elif ga.best_rank < baseline.best_rank:
            rank_outcome = "random"
            random_rank_wins += 1
        else:
            rank_outcome = "tie"
            rank_ties += 1

        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "rank_outcome": rank_outcome,
                "evaluation_budget_each": ga.evaluations,
                "ga": {
                    "primary_security_key": list(ga_primary),
                    "rank": list(ga.best_rank),
                    "metrics": _metrics_dict(ga_metrics),
                    "history": [list(rank) for rank in ga.best_rank_history],
                },
                "random": {
                    "primary_security_key": list(random_primary),
                    "rank": list(baseline.best_rank),
                    "metrics": _metrics_dict(random_metrics),
                },
            }
        )

    ga_nl = [row["ga"]["metrics"]["nonlinearity"] for row in rows]
    random_nl = [row["random"]["metrics"]["nonlinearity"] for row in rows]
    ga_du = [row["ga"]["metrics"]["differential_uniformity"] for row in rows]
    random_du = [row["random"]["metrics"]["differential_uniformity"] for row in rows]
    ga_lat = [row["ga"]["metrics"]["max_linear_correlation"] for row in rows]
    random_lat = [row["random"]["metrics"]["max_linear_correlation"] for row in rows]
    ga_admissible = sum(
        is_admissible(ga_cache_row, constraints)
        for ga_cache_row in (
            ClassicalMetrics(**row["ga"]["metrics"]) for row in rows
        )
    )
    random_admissible = sum(
        is_admissible(random_cache_row, constraints)
        for random_cache_row in (
            ClassicalMetrics(**row["random"]["metrics"]) for row in rows
        )
    )

    if ga_wins > random_wins:
        preliminary = "ga_ahead"
    elif random_wins > ga_wins:
        preliminary = "random_ahead"
    else:
        preliminary = "inconclusive"

    return {
        "schema_version": 2,
        "experiment": "phase1_ga_vs_equal_budget_random",
        "scientific_status": "preliminary_not_gate1",
        "outcome_definition": "admissibility_then_NL_then_DU_then_max_linear_correlation_then_degree",
        "configuration": {
            "seeds": list(seeds),
            "population_size": population_size,
            "generations": generations,
            "elite_count": elite_count,
            "tournament_size": tournament_size,
            "mutation_swaps": mutation_swaps,
            "crossover_rate": crossover_rate,
            "offspring_multiplier": offspring_multiplier,
            "constraints": asdict(constraints),
        },
        "summary": {
            "ga_wins": ga_wins,
            "random_wins": random_wins,
            "ties": ties,
            "preliminary_verdict": preliminary,
            "ga_rank_wins": ga_rank_wins,
            "random_rank_wins": random_rank_wins,
            "rank_ties": rank_ties,
            "admissible_ga": ga_admissible,
            "admissible_random": random_admissible,
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
    parser.add_argument("--offspring-multiplier", type=int, default=1)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=list(CI_SEEDS),
        help="deterministic experiment seeds",
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
        offspring_multiplier=args.offspring_multiplier,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
