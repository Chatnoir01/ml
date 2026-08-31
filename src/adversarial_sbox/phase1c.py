"""Phase 1C: target the DU<=8 frontier, then raise nonlinearity.

This is development-only research code. Confirmation seeds are declared here but
must not be consumed by this module. Equal-budget random search uses the same
ranking objective so the comparison remains fair.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics
from typing import Any

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    constraint_violation,
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    primary_security_key,
    random_search,
)

DEV_SEEDS = (503, 509, 521, 523, 541)
CONFIRM_RESERVED_SEEDS = (601, 607, 613, 617, 619, 631, 641, 643, 647)


def du_frontier_rank(metrics: ClassicalMetrics, constraints: HardConstraints) -> tuple[float, ...]:
    """Rank the exact Phase-1C search target.

    The DU hard gate is entered first. Once inside DU<=8, NL becomes the dominant
    coordinate, so NL=100/DU=8 outranks NL=98/DU=8. Linear correlation and degree
    remain protected before aggregate/SAC tie-breakers. Full admissibility is
    always absolute.
    """

    du_gate = metrics.differential_uniformity <= constraints.max_differential_uniformity
    linear_gate = metrics.max_linear_correlation <= constraints.max_linear_correlation
    degree_gate = metrics.algebraic_degree >= constraints.min_algebraic_degree
    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        1.0 if du_gate else 0.0,
        float(metrics.nonlinearity),
        1.0 if linear_gate else 0.0,
        float(-metrics.max_linear_correlation),
        1.0 if degree_gate else 0.0,
        float(metrics.algebraic_degree),
        float(-metrics.differential_uniformity),
        -constraint_violation(metrics, constraints),
        float(-abs(metrics.sac_score - 0.5)),
    )


def make_du_frontier_evaluator(constraints: HardConstraints):
    cache: dict[tuple[int, ...], ClassicalMetrics] = {}

    def evaluator(sbox: tuple[int, ...]) -> tuple[float, ...]:
        metrics = cache.get(sbox)
        if metrics is None:
            metrics = evaluate_classical(sbox)
            cache[sbox] = metrics
        return du_frontier_rank(metrics, constraints)

    return evaluator, cache


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def _near_frontier(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.nonlinearity >= constraints.min_nonlinearity - 2
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def run_development(
    *,
    seeds: tuple[int, ...] = DEV_SEEDS,
    population_size: int = 14,
    generations: int = 10,
    elite_count: int = 2,
    tournament_size: int = 3,
    mutation_swaps: int = 3,
    crossover_rate: float = 0.0,
    immigrant_fraction: float = 0.0,
    offspring_multiplier: int = 4,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(CONFIRM_RESERVED_SEEDS):
        raise ValueError("confirmation seeds cannot be used for development")
    constraints = constraints or HardConstraints()

    rows: list[dict[str, Any]] = []
    best_overall: tuple[tuple[float, ...], tuple[int, ...], ClassicalMetrics, int] | None = None

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
        ga_eval, ga_cache = make_du_frontier_evaluator(constraints)
        ga = evolve_permutations(ga_eval, config)
        ga_metrics = ga_cache[ga.best_sbox]

        random_eval, random_cache = make_du_frontier_evaluator(constraints)
        baseline = random_search(
            random_eval,
            evaluations=ga.evaluations,
            seed=seed ^ 0x6C6C6C6C,
        )
        random_metrics = random_cache[baseline.best_sbox]

        ga_primary = primary_security_key(ga_metrics, constraints)
        random_primary = primary_security_key(random_metrics, constraints)
        if ga_primary > random_primary:
            outcome = "ga"
        elif ga_primary < random_primary:
            outcome = "random"
        else:
            outcome = "tie"

        rank = du_frontier_rank(ga_metrics, constraints)
        if best_overall is None or rank > best_overall[0]:
            best_overall = (rank, ga.best_sbox, ga_metrics, seed)

        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "evaluation_budget_each": ga.evaluations,
                "ga": {
                    "metrics": asdict(ga_metrics),
                    "rank": list(rank),
                    "constraint_violation": constraint_violation(ga_metrics, constraints),
                    "admissible": is_admissible(ga_metrics, constraints),
                    "du_frontier": ga_metrics.differential_uniformity <= constraints.max_differential_uniformity,
                    "near_frontier": _near_frontier(ga_metrics, constraints),
                    "sbox": list(ga.best_sbox),
                },
                "random": {
                    "metrics": asdict(random_metrics),
                    "rank": list(du_frontier_rank(random_metrics, constraints)),
                    "constraint_violation": constraint_violation(random_metrics, constraints),
                    "admissible": is_admissible(random_metrics, constraints),
                    "du_frontier": random_metrics.differential_uniformity <= constraints.max_differential_uniformity,
                    "near_frontier": _near_frontier(random_metrics, constraints),
                },
            }
        )

    assert best_overall is not None
    _, best_sbox, best_metrics, best_seed = best_overall
    ga_wins = sum(row["outcome"] == "ga" for row in rows)
    random_wins = sum(row["outcome"] == "random" for row in rows)
    ties = len(rows) - ga_wins - random_wins

    summary = {
        "ga_wins": ga_wins,
        "random_wins": random_wins,
        "ties": ties,
        "admissible_ga": sum(row["ga"]["admissible"] for row in rows),
        "admissible_random": sum(row["random"]["admissible"] for row in rows),
        "du_frontier_ga": sum(row["ga"]["du_frontier"] for row in rows),
        "du_frontier_random": sum(row["random"]["du_frontier"] for row in rows),
        "near_frontier_ga": sum(row["ga"]["near_frontier"] for row in rows),
        "near_frontier_random": sum(row["random"]["near_frontier"] for row in rows),
        "median_nonlinearity_ga": _median([row["ga"]["metrics"]["nonlinearity"] for row in rows]),
        "median_nonlinearity_random": _median([row["random"]["metrics"]["nonlinearity"] for row in rows]),
        "median_differential_uniformity_ga": _median([row["ga"]["metrics"]["differential_uniformity"] for row in rows]),
        "median_differential_uniformity_random": _median([row["random"]["metrics"]["differential_uniformity"] for row in rows]),
        "median_max_linear_correlation_ga": _median([row["ga"]["metrics"]["max_linear_correlation"] for row in rows]),
        "median_max_linear_correlation_random": _median([row["random"]["metrics"]["max_linear_correlation"] for row in rows]),
        "best_ga_seed": best_seed,
        "best_ga_metrics": asdict(best_metrics),
        "best_ga_sbox": list(best_sbox),
    }

    return {
        "schema_version": 1,
        "experiment": "phase1c_du_frontier_development",
        "scientific_status": "development_only_not_confirmatory",
        "reserved_confirmation_seeds": list(CONFIRM_RESERVED_SEEDS),
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
            "ranking_mode": "du_frontier_v1",
            "constraints": asdict(constraints),
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1c-dev.json"))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEV_SEEDS))
    parser.add_argument("--population-size", type=int, default=14)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--elite-count", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=3)
    parser.add_argument("--mutation-swaps", type=int, default=3)
    parser.add_argument("--crossover-rate", type=float, default=0.0)
    parser.add_argument("--immigrant-fraction", type=float, default=0.0)
    parser.add_argument("--offspring-multiplier", type=int, default=4)
    args = parser.parse_args()

    result = run_development(
        seeds=tuple(args.seeds),
        population_size=args.population_size,
        generations=args.generations,
        elite_count=args.elite_count,
        tournament_size=args.tournament_size,
        mutation_swaps=args.mutation_swaps,
        crossover_rate=args.crossover_rate,
        immigrant_fraction=args.immigrant_fraction,
        offspring_multiplier=args.offspring_multiplier,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
