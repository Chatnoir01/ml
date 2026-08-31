"""Reproducible Phase-1 benchmark: classical GA versus equal-budget random search.

The benchmark never turns an experimental outcome into a test failure.  It
records the result, including losses and ties, so negative evidence is retained.
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
    make_classical_evaluator,
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
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Run matched-budget GA/random experiments and return JSON-ready evidence."""

    if not seeds:
        raise ValueError("at least one seed is required")
    constraints = constraints or HardConstraints()

    rows: list[dict[str, Any]] = []
    ga_wins = random_wins = ties = 0

    for seed in seeds:
        config = EvolutionConfig(
            population_size=population_size,
            generations=generations,
            elite_count=elite_count,
            tournament_size=tournament_size,
            mutation_swaps=mutation_swaps,
            crossover_rate=crossover_rate,
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

        if ga.best_rank > baseline.best_rank:
            outcome = "ga"
            ga_wins += 1
        elif ga.best_rank < baseline.best_rank:
            outcome = "random"
            random_wins += 1
        else:
            outcome = "tie"
            ties += 1

        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "evaluation_budget_each": ga.evaluations,
                "ga": {
                    "rank": list(ga.best_rank),
                    "metrics": _metrics_dict(ga_metrics),
                    "history": [list(rank) for rank in ga.best_rank_history],
                },
                "random": {
                    "rank": list(baseline.best_rank),
                    "metrics": _metrics_dict(random_metrics),
                },
            }
        )

    ga_nl = [row["ga"]["metrics"]["nonlinearity"] for row in rows]
    random_nl = [row["random"]["metrics"]["nonlinearity"] for row in rows]
    ga_du = [row["ga"]["metrics"]["differential_uniformity"] for row in rows]
    random_du = [row["random"]["metrics"]["differential_uniformity"] for row in rows]

    # This is intentionally named preliminary: Gate 1 requires a larger repeated
    # experiment and statistical analysis, not merely a majority of five runs.
    if ga_wins > random_wins:
        preliminary = "ga_ahead"
    elif random_wins > ga_wins:
        preliminary = "random_ahead"
    else:
        preliminary = "inconclusive"

    return {
        "schema_version": 1,
        "experiment": "phase1_ga_vs_equal_budget_random",
        "scientific_status": "preliminary_not_gate1",
        "configuration": {
            "seeds": list(seeds),
            "population_size": population_size,
            "generations": generations,
            "elite_count": elite_count,
            "tournament_size": tournament_size,
            "mutation_swaps": mutation_swaps,
            "crossover_rate": crossover_rate,
            "constraints": asdict(constraints),
        },
        "summary": {
            "ga_wins": ga_wins,
            "random_wins": random_wins,
            "ties": ties,
            "preliminary_verdict": preliminary,
            "median_nonlinearity_ga": _median(ga_nl),
            "median_nonlinearity_random": _median(random_nl),
            "median_differential_uniformity_ga": _median(ga_du),
            "median_differential_uniformity_random": _median(random_du),
        },
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1-benchmark.json"))
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--generations", type=int, default=3)
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
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
