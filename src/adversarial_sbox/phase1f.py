"""Phase 1F fresh-population feasibility-first search with guided local repair.

Phase 1F does not use the historical warm-start candidate. Each memetic run starts
from a fresh random population, spends a preregistered prefix of its exact budget
on feasibility-first evolution, then spends the remaining budget on the frozen
Phase-1E combined-cycle4 hotspot repair operator. Equal-budget continued-GA and
random-search controls are evaluated on the same development seeds.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
import statistics
from typing import Any

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    equivalent_random_budget,
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    make_classical_evaluator,
    primary_security_key,
    random_search,
    structural_gate_count,
)
from .experiment_seeds import PHASE1F_CONFIRM_RESERVED_SEEDS, PHASE1F_DEV_SEEDS
from .phase1e import cycle_mutation, hotspot_indices

SBox = tuple[int, ...]

TOTAL_BUDGET = 788
FULL_GA_GENERATIONS = 24
DISCOVERY_SPLITS = {
    "bridge10_c4": 10,
    "bridge13_c4": 13,
    "bridge16_c4": 16,
}
BEAM_WIDTH = 8
CYCLE_LENGTH = 4


def ga_config(*, seed: int, generations: int) -> EvolutionConfig:
    return EvolutionConfig(
        population_size=20,
        generations=generations,
        elite_count=4,
        tournament_size=3,
        mutation_swaps=3,
        crossover_rate=0.0,
        immigrant_fraction=0.10,
        offspring_multiplier=2,
        seed=seed,
    )


def structural_target(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.nonlinearity >= constraints.min_nonlinearity
        and metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def bridge_region(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    """Broad local-repair region preregistered for Phase 1F."""

    return (
        metrics.differential_uniformity <= 10
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def repair_rank(metrics: ClassicalMetrics, constraints: HardConstraints) -> tuple[float, ...]:
    """Search rank for the bridge stage; SAC is a final tie-breaker only."""

    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        1.0 if structural_target(metrics, constraints) else 0.0,
        float(structural_gate_count(metrics, constraints)),
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(metrics.algebraic_degree),
        float(-abs(metrics.sac_score - 0.5)),
    )


def _best_primary(
    cache: dict[SBox, ClassicalMetrics], constraints: HardConstraints
) -> tuple[SBox, ClassicalMetrics]:
    if not cache:
        raise ValueError("cannot select from an empty evaluation cache")
    return max(
        cache.items(),
        key=lambda item: primary_security_key(item[1], constraints),
    )


def _cache_summary(cache: dict[SBox, ClassicalMetrics], constraints: HardConstraints) -> dict[str, Any]:
    best_sbox, best_metrics = _best_primary(cache, constraints)
    return {
        "best_sbox": list(best_sbox),
        "best_metrics": asdict(best_metrics),
        "best_primary_key": list(primary_security_key(best_metrics, constraints)),
        "found_structural_target": any(structural_target(m, constraints) for m in cache.values()),
        "found_admissible": any(is_admissible(m, constraints) for m in cache.values()),
        "unique_evaluations": len(cache),
    }


def guided_bridge_repair(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    evaluated_cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints | None = None,
    beam_width: int = BEAM_WIDTH,
    cycle_length: int = CYCLE_LENGTH,
) -> dict[str, Any]:
    """Spend exactly ``evaluations`` new unique evaluations on combined-cycle repair."""

    if evaluations < 0:
        raise ValueError("evaluations must be >= 0")
    if beam_width < 1:
        raise ValueError("beam_width must be >= 1")
    constraints = constraints or HardConstraints()
    if start not in evaluated_cache:
        raise ValueError("repair start must already be present in the discovery cache")

    rng = random.Random(seed)
    seen: set[SBox] = set(evaluated_cache)
    hotspot_cache: dict[SBox, tuple[int, ...]] = {}
    archive: list[SBox] = [start]
    frontier_accepts = 0
    hotspot_fallbacks = 0
    completed = 0

    while completed < evaluations:
        parent = rng.choice(archive)
        anchors = hotspot_cache.get(parent)
        if anchors is None:
            anchors = hotspot_indices(parent, "combined")
            hotspot_cache[parent] = anchors
        child, fallback = cycle_mutation(
            parent,
            rng,
            cycle_length=cycle_length,
            anchor_indices=anchors,
        )
        if child in seen:
            continue
        seen.add(child)
        hotspot_fallbacks += int(fallback)

        metrics = evaluate_classical(child)
        evaluated_cache[child] = metrics
        completed += 1

        if bridge_region(metrics, constraints):
            frontier_accepts += 1
            archive.append(child)
            archive.sort(
                key=lambda candidate: repair_rank(evaluated_cache[candidate], constraints),
                reverse=True,
            )
            del archive[beam_width:]

    return {
        "evaluations": completed,
        "frontier_accepts": frontier_accepts,
        "hotspot_fallbacks": hotspot_fallbacks,
        "archive_size": len(archive),
    }


def _run_memetic(seed: int, *, discovery_generations: int, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    config = ga_config(seed=seed, generations=discovery_generations)
    discovery = evolve_permutations(evaluator, config)
    expected_discovery = equivalent_random_budget(config)
    if discovery.evaluations != expected_discovery or len(cache) != expected_discovery:
        raise RuntimeError("discovery evaluation accounting mismatch")

    repair_evaluations = TOTAL_BUDGET - expected_discovery
    if repair_evaluations < 0:
        raise RuntimeError("discovery budget exceeds Phase-1F total budget")
    repair = guided_bridge_repair(
        discovery.best_sbox,
        seed=seed ^ 0x1F1F1F1F,
        evaluations=repair_evaluations,
        evaluated_cache=cache,
        constraints=constraints,
    )
    if len(cache) != TOTAL_BUDGET:
        raise RuntimeError("memetic arm did not consume exactly the frozen budget")

    return {
        **_cache_summary(cache, constraints),
        "discovery_evaluations": expected_discovery,
        "repair_evaluations": repair_evaluations,
        "repair": repair,
    }


def _run_continued_ga(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    config = ga_config(seed=seed, generations=FULL_GA_GENERATIONS)
    result = evolve_permutations(evaluator, config)
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("continued-GA arm did not consume exactly the frozen budget")
    return _cache_summary(cache, constraints)


def _run_random(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    result = random_search(
        evaluator,
        evaluations=TOTAL_BUDGET,
        seed=seed ^ 0x5A17F00D,
    )
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("random arm did not consume exactly the frozen budget")
    return _cache_summary(cache, constraints)


def _outcome(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_key = tuple(left["best_primary_key"])
    right_key = tuple(right["best_primary_key"])
    return "memetic" if left_key > right_key else "other" if left_key < right_key else "tie"


def run_development(
    *,
    discovery_generations: int,
    seeds: tuple[int, ...] = PHASE1F_DEV_SEEDS,
) -> dict[str, Any]:
    if discovery_generations not in set(DISCOVERY_SPLITS.values()):
        raise ValueError("discovery_generations is not a preregistered Phase-1F split")
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(PHASE1F_CONFIRM_RESERVED_SEEDS):
        raise ValueError("Phase-1F confirmation seeds cannot be used for development")

    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []

    for seed in seeds:
        memetic = _run_memetic(seed, discovery_generations=discovery_generations, constraints=constraints)
        continued_ga = _run_continued_ga(seed, constraints=constraints)
        random_control = _run_random(seed, constraints=constraints)
        rows.append(
            {
                "seed": seed,
                "memetic_vs_ga": _outcome(memetic, continued_ga),
                "memetic_vs_random": _outcome(memetic, random_control),
                "memetic": memetic,
                "continued_ga": continued_ga,
                "random": random_control,
            }
        )

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "memetic_admissible_runs": sum(row["memetic"]["found_admissible"] for row in rows),
        "ga_admissible_runs": sum(row["continued_ga"]["found_admissible"] for row in rows),
        "random_admissible_runs": sum(row["random"]["found_admissible"] for row in rows),
        "memetic_target_runs": sum(row["memetic"]["found_structural_target"] for row in rows),
        "ga_target_runs": sum(row["continued_ga"]["found_structural_target"] for row in rows),
        "random_target_runs": sum(row["random"]["found_structural_target"] for row in rows),
        "memetic_wins_vs_ga": sum(row["memetic_vs_ga"] == "memetic" for row in rows),
        "memetic_losses_vs_ga": sum(row["memetic_vs_ga"] == "other" for row in rows),
        "ties_vs_ga": sum(row["memetic_vs_ga"] == "tie" for row in rows),
        "memetic_wins_vs_random": sum(row["memetic_vs_random"] == "memetic" for row in rows),
        "memetic_losses_vs_random": sum(row["memetic_vs_random"] == "other" for row in rows),
        "ties_vs_random": sum(row["memetic_vs_random"] == "tie" for row in rows),
        "median_nonlinearity_memetic": median("memetic", "nonlinearity"),
        "median_du_memetic": median("memetic", "differential_uniformity"),
        "median_max_corr_memetic": median("memetic", "max_linear_correlation"),
        "median_nonlinearity_ga": median("continued_ga", "nonlinearity"),
        "median_du_ga": median("continued_ga", "differential_uniformity"),
        "median_max_corr_ga": median("continued_ga", "max_linear_correlation"),
        "median_nonlinearity_random": median("random", "nonlinearity"),
        "median_du_random": median("random", "differential_uniformity"),
        "median_max_corr_random": median("random", "max_linear_correlation"),
    }

    split_name = next(name for name, value in DISCOVERY_SPLITS.items() if value == discovery_generations)
    discovery_budget = equivalent_random_budget(ga_config(seed=0, generations=discovery_generations))
    return {
        "schema_version": 1,
        "experiment": "phase1f_fresh_population_guided_bridge_development",
        "scientific_status": "fresh_population_development_not_gate1",
        "reserved_confirmation_seeds": list(PHASE1F_CONFIRM_RESERVED_SEEDS),
        "configuration": {
            "name": split_name,
            "discovery_generations": discovery_generations,
            "discovery_evaluations": discovery_budget,
            "repair_evaluations": TOTAL_BUDGET - discovery_budget,
            "total_evaluations_each_arm": TOTAL_BUDGET,
            "beam_width": BEAM_WIDTH,
            "guidance": "combined",
            "cycle_length": CYCLE_LENGTH,
            "seeds": list(seeds),
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery-generations", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1F_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1f-dev.json"))
    args = parser.parse_args()
    result = run_development(
        discovery_generations=args.discovery_generations,
        seeds=tuple(args.seeds),
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
