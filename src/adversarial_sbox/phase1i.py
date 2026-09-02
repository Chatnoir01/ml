"""Phase 1I fresh-population transfer of the Phase-1H proposal selector.

Every scientific run begins from a fresh GA population.  No historical S-box is
loaded as a parent or archive member.  After a frozen 16-generation discovery
prefix, the transfer arm uses the Phase-1H exact local plateau projection to
pre-screen cycle-4 proposals while charging only full CryptoShield evaluations to
the matched evidence budget.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
import statistics
from typing import Any, Callable

from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    equivalent_random_budget,
    evaluate_classical,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    random_search,
)
from .experiment_seeds import PHASE1I_CONFIRM_RESERVED_SEEDS, PHASE1I_DEV_SEEDS
from .phase1e import cycle_mutation
from .phase1h import build_plateau_diagnostics, score_proposal, structural_target

SBox = tuple[int, ...]

DISCOVERY_GENERATIONS = 16
FULL_GA_GENERATIONS = 50
TOTAL_BUDGET = 1620
DISCOVERY_BUDGET = 532
REPAIR_BUDGET = 1088
ARCHIVE_WIDTH = 8
PROPOSAL_POOL = 96
CYCLE_LENGTH = 4
PANEL_MODE = "ties"
REPAIR_SEED_XOR = 0x1F1F1F1F
RANDOM_SEED_XOR = 0x5A17F00D


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


def _validate_frozen_budgets() -> None:
    discovery = equivalent_random_budget(ga_config(seed=0, generations=DISCOVERY_GENERATIONS))
    total = equivalent_random_budget(ga_config(seed=0, generations=FULL_GA_GENERATIONS))
    if discovery != DISCOVERY_BUDGET:
        raise RuntimeError(f"Phase-1I discovery budget drift: {discovery} != {DISCOVERY_BUDGET}")
    if total != TOTAL_BUDGET:
        raise RuntimeError(f"Phase-1I total budget drift: {total} != {TOTAL_BUDGET}")
    if DISCOVERY_BUDGET + REPAIR_BUDGET != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I split does not equal total budget")


_validate_frozen_budgets()


def _best_from_cache(
    cache: dict[SBox, ClassicalMetrics], constraints: HardConstraints
) -> tuple[SBox, ClassicalMetrics]:
    if not cache:
        raise ValueError("cannot select from an empty cache")
    return max(cache.items(), key=lambda item: feasibility_rank(item[1], constraints))


def _first_index(
    cache: dict[SBox, ClassicalMetrics],
    predicate: Callable[[ClassicalMetrics], bool],
) -> int | None:
    for index, metrics in enumerate(cache.values(), start=1):
        if predicate(metrics):
            return index
    return None


def _cache_summary(
    cache: dict[SBox, ClassicalMetrics], constraints: HardConstraints
) -> dict[str, Any]:
    best_sbox, best_metrics = _best_from_cache(cache, constraints)
    target_at = _first_index(cache, lambda metrics: structural_target(metrics, constraints))
    admissible_at = _first_index(cache, lambda metrics: is_admissible(metrics, constraints))
    return {
        "best_sbox": list(best_sbox),
        "best_metrics": asdict(best_metrics),
        "best_rank": list(feasibility_rank(best_metrics, constraints)),
        "found_structural_target": target_at is not None,
        "found_structural_target_at_evaluation": target_at,
        "found_admissible": admissible_at is not None,
        "found_admissible_at_evaluation": admissible_at,
        "unique_evaluations": len(cache),
    }


def fresh_plateau_repair(
    *,
    seed: int,
    evaluations: int,
    evaluated_cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints | None = None,
    archive_width: int = ARCHIVE_WIDTH,
    proposal_pool: int = PROPOSAL_POOL,
    panel_mode: str = PANEL_MODE,
) -> dict[str, Any]:
    """Spend exactly ``evaluations`` new full evaluations from a fresh cache.

    This helper intentionally accepts smaller widths/pools for unit tests.  The
    scientific runner below hard-freezes the preregistered Phase-1I constants.
    """

    if evaluations < 0:
        raise ValueError("evaluations must be >= 0")
    if not evaluated_cache:
        raise ValueError("fresh repair requires a non-empty discovery cache")
    if archive_width < 1:
        raise ValueError("archive_width must be >= 1")
    if proposal_pool < 1:
        raise ValueError("proposal_pool must be >= 1")
    if panel_mode != "ties":
        raise ValueError("Phase-1I transfer uses the frozen ties panel")

    constraints = constraints or HardConstraints()
    rng = random.Random(seed)
    seen: set[SBox] = set(evaluated_cache)
    diagnostics_cache: dict[SBox, Any] = {}

    archive = sorted(
        evaluated_cache,
        key=lambda candidate: feasibility_rank(evaluated_cache[candidate], constraints),
        reverse=True,
    )[:archive_width]

    proposal_pools_generated = 0
    duplicate_proposals_skipped = 0
    hotspot_fallbacks = 0
    selected_reduce_lat_max = 0
    selected_reduce_lat_cell = 0
    selected_reduce_ddt_cell = 0
    selected_lat_max_deltas: list[int] = []
    selected_ddt_max_deltas: list[int] = []

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        diagnostics = diagnostics_cache.get(parent)
        if diagnostics is None:
            diagnostics = build_plateau_diagnostics(parent, panel_mode="ties")
            diagnostics_cache[parent] = diagnostics

        proposals: list[tuple[SBox, Any, bool]] = []
        proposal_seen: set[SBox] = set()
        attempts = 0
        attempt_limit = max(proposal_pool * 30, proposal_pool + 20)
        while len(proposals) < proposal_pool and attempts < attempt_limit:
            attempts += 1
            child, fallback = cycle_mutation(
                parent,
                rng,
                cycle_length=CYCLE_LENGTH,
                anchor_indices=diagnostics.hotspot_indices,
            )
            if child in seen or child in proposal_seen:
                duplicate_proposals_skipped += 1
                continue
            proposal_seen.add(child)
            score = score_proposal(
                parent,
                child,
                diagnostics,
                order=len(proposals),
            )
            proposals.append((child, score, fallback))

        if len(proposals) != proposal_pool:
            raise RuntimeError(
                f"Phase-1I proposal pool shortfall: {len(proposals)} != {proposal_pool}"
            )

        proposal_pools_generated += 1
        child, selected_score, selected_fallback = min(
            proposals,
            key=lambda item: item[1].ranking_key(),
        )
        seen.add(child)
        hotspot_fallbacks += int(selected_fallback)
        selected_reduce_lat_max += int(
            selected_score.projected_lat_max < diagnostics.lat_max
        )
        selected_reduce_lat_cell += int(selected_score.lat_max_cells_reduced > 0)
        selected_reduce_ddt_cell += int(selected_score.ddt_max_cells_reduced > 0)
        selected_lat_max_deltas.append(selected_score.projected_lat_max - diagnostics.lat_max)
        selected_ddt_max_deltas.append(selected_score.projected_ddt_max - diagnostics.ddt_max)

        metrics = evaluate_classical(child)
        evaluated_cache[child] = metrics
        completed += 1

        archive.append(child)
        archive.sort(
            key=lambda candidate: feasibility_rank(evaluated_cache[candidate], constraints),
            reverse=True,
        )
        del archive[archive_width:]

    return {
        "evaluations": completed,
        "proposal_pools_generated": proposal_pools_generated,
        "duplicate_proposals_skipped": duplicate_proposals_skipped,
        "hotspot_fallbacks": hotspot_fallbacks,
        "archive_size": len(archive),
        "selected_reduce_lat_max": selected_reduce_lat_max,
        "selected_reduce_lat_cell": selected_reduce_lat_cell,
        "selected_reduce_ddt_cell": selected_reduce_ddt_cell,
        "selected_lat_max_deltas": selected_lat_max_deltas,
        "selected_ddt_max_deltas": selected_ddt_max_deltas,
    }


def _run_transfer(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    discovery_config = ga_config(seed=seed, generations=DISCOVERY_GENERATIONS)
    discovery = evolve_permutations(evaluator, discovery_config)
    if discovery.evaluations != DISCOVERY_BUDGET or len(cache) != DISCOVERY_BUDGET:
        raise RuntimeError("Phase-1I discovery evaluation accounting mismatch")

    discovery_summary = _cache_summary(cache, constraints)
    repair = fresh_plateau_repair(
        seed=seed ^ REPAIR_SEED_XOR,
        evaluations=REPAIR_BUDGET,
        evaluated_cache=cache,
        constraints=constraints,
        archive_width=ARCHIVE_WIDTH,
        proposal_pool=PROPOSAL_POOL,
        panel_mode=PANEL_MODE,
    )
    if len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I transfer arm did not consume exact total budget")

    return {
        **_cache_summary(cache, constraints),
        "discovery": discovery_summary,
        "discovery_evaluations": DISCOVERY_BUDGET,
        "repair_evaluations": REPAIR_BUDGET,
        "repair": repair,
    }


def _run_continued_ga(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    config = ga_config(seed=seed, generations=FULL_GA_GENERATIONS)
    result = evolve_permutations(evaluator, config)
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I continued-GA arm did not consume exact budget")
    return _cache_summary(cache, constraints)


def _run_random(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(constraints, ranking_mode="feasibility_first")
    result = random_search(
        evaluator,
        evaluations=TOTAL_BUDGET,
        seed=seed ^ RANDOM_SEED_XOR,
    )
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I random arm did not consume exact budget")
    return _cache_summary(cache, constraints)


def _outcome(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_rank = tuple(left["best_rank"])
    right_rank = tuple(right["best_rank"])
    return "transfer" if left_rank > right_rank else "other" if left_rank < right_rank else "tie"


def run_development(
    *,
    seeds: tuple[int, ...] = PHASE1I_DEV_SEEDS,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one Phase-1I development seed is required")
    if set(seeds) & set(PHASE1I_CONFIRM_RESERVED_SEEDS):
        raise ValueError("Phase-1I confirmation seeds cannot be used for development")

    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        transfer = _run_transfer(seed, constraints=constraints)
        continued_ga = _run_continued_ga(seed, constraints=constraints)
        random_control = _run_random(seed, constraints=constraints)
        rows.append(
            {
                "seed": seed,
                "transfer_vs_ga": _outcome(transfer, continued_ga),
                "transfer_vs_random": _outcome(transfer, random_control),
                "transfer": transfer,
                "continued_ga": continued_ga,
                "random": random_control,
            }
        )

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "transfer_admissible_runs": sum(row["transfer"]["found_admissible"] for row in rows),
        "ga_admissible_runs": sum(row["continued_ga"]["found_admissible"] for row in rows),
        "random_admissible_runs": sum(row["random"]["found_admissible"] for row in rows),
        "transfer_target_runs": sum(row["transfer"]["found_structural_target"] for row in rows),
        "ga_target_runs": sum(row["continued_ga"]["found_structural_target"] for row in rows),
        "random_target_runs": sum(row["random"]["found_structural_target"] for row in rows),
        "transfer_wins_vs_ga": sum(row["transfer_vs_ga"] == "transfer" for row in rows),
        "transfer_losses_vs_ga": sum(row["transfer_vs_ga"] == "other" for row in rows),
        "ties_vs_ga": sum(row["transfer_vs_ga"] == "tie" for row in rows),
        "transfer_wins_vs_random": sum(row["transfer_vs_random"] == "transfer" for row in rows),
        "transfer_losses_vs_random": sum(row["transfer_vs_random"] == "other" for row in rows),
        "ties_vs_random": sum(row["transfer_vs_random"] == "tie" for row in rows),
        "median_nonlinearity_transfer": median("transfer", "nonlinearity"),
        "median_du_transfer": median("transfer", "differential_uniformity"),
        "median_max_corr_transfer": median("transfer", "max_linear_correlation"),
        "median_nonlinearity_ga": median("continued_ga", "nonlinearity"),
        "median_du_ga": median("continued_ga", "differential_uniformity"),
        "median_max_corr_ga": median("continued_ga", "max_linear_correlation"),
        "median_nonlinearity_random": median("random", "nonlinearity"),
        "median_du_random": median("random", "differential_uniformity"),
        "median_max_corr_random": median("random", "max_linear_correlation"),
    }

    checks = {
        "transfer_admissible_at_least_2": summary["transfer_admissible_runs"] >= 2,
        "transfer_target_at_least_2": summary["transfer_target_runs"] >= 2,
        "transfer_admissible_gt_ga": summary["transfer_admissible_runs"] > summary["ga_admissible_runs"],
        "transfer_target_gt_ga": summary["transfer_target_runs"] > summary["ga_target_runs"],
        "transfer_wins_gt_losses_ga": summary["transfer_wins_vs_ga"] > summary["transfer_losses_vs_ga"],
        "median_nonlinearity_at_least_98": summary["median_nonlinearity_transfer"] >= 98,
        "median_du_at_most_8": summary["median_du_transfer"] <= 8,
        "median_max_corr_at_most_60": summary["median_max_corr_transfer"] <= 60,
        "exact_budget_all_arms": all(
            row[side]["unique_evaluations"] == TOTAL_BUDGET
            for row in rows
            for side in ("transfer", "continued_ga", "random")
        ),
    }
    development_pass = all(checks.values())

    return {
        "schema_version": 1,
        "experiment": "phase1i_fresh_population_plateau_transfer_development",
        "scientific_status": "fresh_population_development_not_gate1",
        "configuration": {
            "seeds": list(seeds),
            "reserved_confirmation_seeds": list(PHASE1I_CONFIRM_RESERVED_SEEDS),
            "discovery_generations": DISCOVERY_GENERATIONS,
            "discovery_evaluations": DISCOVERY_BUDGET,
            "repair_evaluations": REPAIR_BUDGET,
            "total_evaluations_each_arm": TOTAL_BUDGET,
            "continued_ga_generations": FULL_GA_GENERATIONS,
            "archive_width": ARCHIVE_WIDTH,
            "proposal_pool": PROPOSAL_POOL,
            "cycle_length": CYCLE_LENGTH,
            "panel_mode": PANEL_MODE,
            "ranking_mode": "feasibility_first",
            "warm_start": False,
        },
        "summary": summary,
        "development_checks": checks,
        "verdict": "fresh_transfer_dev_pass" if development_pass else "fresh_transfer_dev_fail",
        "global_gate1": "red",
        "neural_oracle": "blocked",
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1I_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1i-dev.json"))
    args = parser.parse_args()
    result = run_development(seeds=tuple(args.seeds))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "verdict": result["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
