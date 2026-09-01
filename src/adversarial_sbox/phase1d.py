"""Phase 1D warm-start continuation from the verified Phase-1B DU=8 candidate.

This experiment does not test global fresh-population search superiority. It asks a
narrower question: once a historically reproduced S-Box reaches the DU<=8
frontier, can an adaptive frontier-preserving local search raise NL from 98 to
>=100 without losing the other hard structural constraints?
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
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    make_classical_evaluator,
    swap_mutation,
)

SBox = tuple[int, ...]
EXPECTED_PHASE1B_FINGERPRINT = (
    "d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc"
)
DEV_SEEDS = (701, 709, 719, 727, 733)
CONFIRM_RESERVED_SEEDS = (809, 811, 821, 823, 827, 829, 839, 853, 857)


def reproduce_phase1b_frontier_candidate() -> tuple[SBox, ClassicalMetrics]:
    """Re-run the frozen Phase-1B seed/config and verify the historical receipt."""

    constraints = HardConstraints()
    evaluator, cache = make_classical_evaluator(
        constraints, ranking_mode="feasibility_first"
    )
    result = evolve_permutations(
        evaluator,
        EvolutionConfig(
            population_size=12,
            generations=8,
            elite_count=2,
            tournament_size=3,
            mutation_swaps=3,
            crossover_rate=0.0,
            immigrant_fraction=0.0,
            offspring_multiplier=3,
            seed=307,
        ),
    )
    metrics = cache[result.best_sbox]
    expected = (98, 8, 60, 7, EXPECTED_PHASE1B_FINGERPRINT)
    observed = (
        metrics.nonlinearity,
        metrics.differential_uniformity,
        metrics.max_linear_correlation,
        metrics.algebraic_degree,
        metrics.fingerprint,
    )
    if observed != expected:
        raise RuntimeError(
            "historical Phase-1B candidate reproduction failed: "
            f"expected={expected!r}, observed={observed!r}"
        )
    return result.best_sbox, metrics


def _frontier_ok(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def continuation_rank(
    metrics: ClassicalMetrics, constraints: HardConstraints
) -> tuple[float, ...]:
    """Rank warm-start candidates without permitting DU/linear/degree regression."""

    return (
        1.0 if is_admissible(metrics, constraints) else 0.0,
        1.0 if _frontier_ok(metrics, constraints) else 0.0,
        float(metrics.nonlinearity),
        float(-metrics.differential_uniformity),
        float(-metrics.max_linear_correlation),
        float(metrics.algebraic_degree),
        float(-abs(metrics.sac_score - 0.5)),
    )


def _evaluate_cached(
    candidate: SBox,
    cache: dict[SBox, ClassicalMetrics],
) -> ClassicalMetrics:
    metrics = cache.get(candidate)
    if metrics is None:
        metrics = evaluate_classical(candidate)
        cache[candidate] = metrics
    return metrics


def adaptive_frontier_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    beam_width: int,
    mutation_swaps: int,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Adaptive beam search whose archive only admits structural-frontier states."""

    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    if beam_width < 1:
        raise ValueError("beam_width must be >= 1")
    if mutation_swaps < 1:
        raise ValueError("mutation_swaps must be >= 1")
    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must already satisfy the structural frontier")

    rng = random.Random(seed)
    cache: dict[SBox, ClassicalMetrics] = {start: start_metrics}
    seen: set[SBox] = {start}
    archive: list[SBox] = [start]
    best = start
    best_metrics = start_metrics
    accepted_frontier = 0
    found_at: int | None = 0 if is_admissible(start_metrics, constraints) else None

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        child = swap_mutation(parent, rng, swaps=mutation_swaps)
        if child in seen:
            continue
        seen.add(child)
        metrics = _evaluate_cached(child, cache)
        completed += 1

        if _frontier_ok(metrics, constraints):
            accepted_frontier += 1
            archive.append(child)
            archive.sort(
                key=lambda candidate: continuation_rank(cache[candidate], constraints),
                reverse=True,
            )
            del archive[beam_width:]

        if continuation_rank(metrics, constraints) > continuation_rank(
            best_metrics, constraints
        ):
            best = child
            best_metrics = metrics
        if found_at is None and is_admissible(metrics, constraints):
            found_at = completed

    return {
        "best_sbox": list(best),
        "best_metrics": asdict(best_metrics),
        "best_rank": list(continuation_rank(best_metrics, constraints)),
        "frontier_accepts": accepted_frontier,
        "found_admissible": found_at is not None,
        "found_at_evaluation": found_at,
        "evaluations": completed,
    }


def direct_neighborhood_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    mutation_swaps: int,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Equal-budget non-adaptive comparator: mutate only the original DU=8 state."""

    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must already satisfy the structural frontier")

    rng = random.Random(seed)
    seen: set[SBox] = {start}
    best = start
    best_metrics = start_metrics
    frontier_accepts = 0
    found_at: int | None = 0 if is_admissible(start_metrics, constraints) else None
    completed = 0

    while completed < evaluations:
        child = swap_mutation(start, rng, swaps=mutation_swaps)
        if child in seen:
            continue
        seen.add(child)
        metrics = evaluate_classical(child)
        completed += 1
        if _frontier_ok(metrics, constraints):
            frontier_accepts += 1
        if continuation_rank(metrics, constraints) > continuation_rank(
            best_metrics, constraints
        ):
            best = child
            best_metrics = metrics
        if found_at is None and is_admissible(metrics, constraints):
            found_at = completed

    return {
        "best_sbox": list(best),
        "best_metrics": asdict(best_metrics),
        "best_rank": list(continuation_rank(best_metrics, constraints)),
        "frontier_accepts": frontier_accepts,
        "found_admissible": found_at is not None,
        "found_at_evaluation": found_at,
        "evaluations": completed,
    }


def run_development(
    *,
    seeds: tuple[int, ...] = DEV_SEEDS,
    evaluations: int = 600,
    beam_width: int = 8,
    mutation_swaps: int = 1,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(CONFIRM_RESERVED_SEEDS):
        raise ValueError("confirmation seeds cannot be used for development")

    constraints = HardConstraints()
    start, start_metrics = reproduce_phase1b_frontier_candidate()
    rows: list[dict[str, Any]] = []

    for seed in seeds:
        adaptive = adaptive_frontier_search(
            start,
            seed=seed,
            evaluations=evaluations,
            beam_width=beam_width,
            mutation_swaps=mutation_swaps,
            constraints=constraints,
        )
        direct = direct_neighborhood_search(
            start,
            seed=seed ^ 0x1D1D1D1D,
            evaluations=evaluations,
            mutation_swaps=mutation_swaps,
            constraints=constraints,
        )
        adaptive_key = tuple(adaptive["best_rank"])
        direct_key = tuple(direct["best_rank"])
        outcome = "adaptive" if adaptive_key > direct_key else "direct" if adaptive_key < direct_key else "tie"
        rows.append({"seed": seed, "outcome": outcome, "adaptive": adaptive, "direct": direct})

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "adaptive_wins": sum(row["outcome"] == "adaptive" for row in rows),
        "direct_wins": sum(row["outcome"] == "direct" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "adaptive_admissible_runs": sum(row["adaptive"]["found_admissible"] for row in rows),
        "direct_admissible_runs": sum(row["direct"]["found_admissible"] for row in rows),
        "adaptive_nl100_du8_runs": sum(
            row["adaptive"]["best_metrics"]["nonlinearity"] >= 100
            and row["adaptive"]["best_metrics"]["differential_uniformity"] <= 8
            for row in rows
        ),
        "direct_nl100_du8_runs": sum(
            row["direct"]["best_metrics"]["nonlinearity"] >= 100
            and row["direct"]["best_metrics"]["differential_uniformity"] <= 8
            for row in rows
        ),
        "median_nonlinearity_adaptive": median("adaptive", "nonlinearity"),
        "median_nonlinearity_direct": median("direct", "nonlinearity"),
        "median_du_adaptive": median("adaptive", "differential_uniformity"),
        "median_du_direct": median("direct", "differential_uniformity"),
        "median_max_corr_adaptive": median("adaptive", "max_linear_correlation"),
        "median_max_corr_direct": median("direct", "max_linear_correlation"),
    }

    return {
        "schema_version": 1,
        "experiment": "phase1d_frontier_continuation_development",
        "scientific_status": "warm_start_development_not_global_gate1",
        "historical_start": {"sbox": list(start), "metrics": asdict(start_metrics)},
        "reserved_confirmation_seeds": list(CONFIRM_RESERVED_SEEDS),
        "configuration": {
            "seeds": list(seeds),
            "evaluations_each": evaluations,
            "beam_width": beam_width,
            "mutation_swaps": mutation_swaps,
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1d-dev.json"))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEV_SEEDS))
    parser.add_argument("--evaluations", type=int, default=600)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--mutation-swaps", type=int, default=1)
    args = parser.parse_args()
    result = run_development(
        seeds=tuple(args.seeds),
        evaluations=args.evaluations,
        beam_width=args.beam_width,
        mutation_swaps=args.mutation_swaps,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
