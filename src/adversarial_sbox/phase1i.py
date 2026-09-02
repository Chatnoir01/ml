"""Phase 1I accelerated fresh-population variable-neighborhood batch.

Every directed arm begins with the same deterministic fresh feasibility-first GA
prefix and then spends the remainder of an exact matched budget on a generalized
Phase-1H plateau-directed local neighborhood.  No historical S-box is injected.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import statistics
from typing import Any

from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    equivalent_random_budget,
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    make_classical_evaluator,
    primary_security_key,
)
from .experiment_seeds import PHASE1I_CONFIRM_RESERVED_SEEDS, PHASE1I_DEV_SEEDS
from .phase1e import cycle_mutation
from .phase1f import ga_config, repair_rank, structural_target
from .phase1h import (
    PlateauDiagnostics,
    build_plateau_diagnostics,
    projected_ddt_count,
    projected_lat_correlation,
)

SBox = tuple[int, ...]

TOTAL_BUDGET = 980
DISCOVERY_GENERATIONS = 13
FULL_GA_GENERATIONS = 30
BEAM_WIDTH = 8
BRIDGE_DU_CAP = 12
BRIDGE_CORR_CAP = 72
PANEL_MODE = "ties"
REPAIR_SEED_XOR = 0x1I1 if False else 0x1A1B1C1D  # stable integer salt

CONFIGURATIONS: dict[str, tuple[tuple[int, ...], int]] = {
    "c2_p96": ((2,), 96),
    "c3_p96": ((3,), 96),
    "c4_p32": ((4,), 32),
    "c4_p96": ((4,), 96),
    "c5_p96": ((5,), 96),
    "c6_p96": ((6,), 96),
    "c8_p96": ((8,), 96),
    "mix234_p96": ((2, 3, 4), 96),
    "mix456_p96": ((4, 5, 6), 96),
    "mix2468_p96": ((2, 4, 6, 8), 96),
}


@dataclass(frozen=True)
class LocalProposalScore:
    projected_lat_max: int
    projected_ddt_max: int
    lat_max_cells_reduced: int
    ddt_max_cells_reduced: int
    projected_lat_sum: int
    projected_ddt_sum: int
    order: int

    def ranking_key(self, *, parent_ddt_max: int) -> tuple[int, ...]:
        if parent_ddt_max > 8:
            return (
                self.projected_ddt_max,
                self.projected_lat_max,
                -self.ddt_max_cells_reduced,
                -self.lat_max_cells_reduced,
                self.projected_ddt_sum,
                self.projected_lat_sum,
                self.order,
            )
        return (
            self.projected_lat_max,
            self.projected_ddt_max,
            -self.lat_max_cells_reduced,
            -self.ddt_max_cells_reduced,
            self.projected_lat_sum,
            self.projected_ddt_sum,
            self.order,
        )


def bridge_region(metrics: ClassicalMetrics) -> bool:
    return (
        metrics.differential_uniformity <= BRIDGE_DU_CAP
        and metrics.max_linear_correlation <= BRIDGE_CORR_CAP
        and metrics.algebraic_degree >= 6
    )


def score_local_proposal(
    parent: SBox,
    child: SBox,
    diagnostics: PlateauDiagnostics,
    *,
    order: int,
) -> LocalProposalScore:
    changed = tuple(
        index
        for index, (left, right) in enumerate(zip(parent, child))
        if left != right
    )
    if len(changed) < 2:
        raise ValueError("Phase-1I proposals must change at least two positions")

    projected_lat = [
        abs(projected_lat_correlation(parent, child, changed, cell))
        for cell in diagnostics.lat_cells
    ]
    projected_ddt = [
        projected_ddt_count(parent, child, changed, cell)
        for cell in diagnostics.ddt_cells
    ]
    if not projected_lat or not projected_ddt:
        raise RuntimeError("plateau diagnostics unexpectedly produced an empty panel")

    return LocalProposalScore(
        projected_lat_max=max(projected_lat),
        projected_ddt_max=max(projected_ddt),
        lat_max_cells_reduced=sum(
            abs(cell.correlation) == diagnostics.lat_max
            and projected < diagnostics.lat_max
            for cell, projected in zip(diagnostics.lat_cells, projected_lat)
        ),
        ddt_max_cells_reduced=sum(
            cell.count == diagnostics.ddt_max and projected < diagnostics.ddt_max
            for cell, projected in zip(diagnostics.ddt_cells, projected_ddt)
        ),
        projected_lat_sum=sum(projected_lat),
        projected_ddt_sum=sum(projected_ddt),
        order=order,
    )


def _best_primary(
    cache: dict[SBox, ClassicalMetrics], constraints: HardConstraints
) -> tuple[SBox, ClassicalMetrics]:
    return max(
        cache.items(),
        key=lambda item: primary_security_key(item[1], constraints),
    )


def _summary_from_cache(
    cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    *,
    first_target_at: int | None,
    first_admissible_at: int | None,
) -> dict[str, Any]:
    best_sbox, best_metrics = _best_primary(cache, constraints)
    return {
        "best_sbox": list(best_sbox),
        "best_metrics": asdict(best_metrics),
        "best_primary_key": list(primary_security_key(best_metrics, constraints)),
        "found_structural_target": first_target_at is not None,
        "first_structural_target_at_evaluation": first_target_at,
        "found_admissible": first_admissible_at is not None,
        "first_admissible_at_evaluation": first_admissible_at,
        "unique_evaluations": len(cache),
    }


def _tracked_evaluator(
    constraints: HardConstraints,
) -> tuple[Any, dict[SBox, ClassicalMetrics], dict[str, int | None]]:
    evaluator, cache = make_classical_evaluator(
        constraints, ranking_mode="feasibility_first"
    )
    first: dict[str, int | None] = {"target": None, "admissible": None}

    def tracked(sbox: SBox):
        before = len(cache)
        rank = evaluator(sbox)
        if len(cache) != before:
            index = len(cache)
            metrics = cache[sbox]
            if first["target"] is None and structural_target(metrics, constraints):
                first["target"] = index
            if first["admissible"] is None and is_admissible(metrics, constraints):
                first["admissible"] = index
        return rank

    return tracked, cache, first


def _initial_archive(
    cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    *,
    beam_width: int,
) -> list[SBox]:
    eligible = [candidate for candidate, metrics in cache.items() if bridge_region(metrics)]
    eligible.sort(key=lambda candidate: repair_rank(cache[candidate], constraints), reverse=True)
    archive = eligible[:beam_width]
    if len(archive) < beam_width:
        remaining = [candidate for candidate in cache if candidate not in set(archive)]
        remaining.sort(
            key=lambda candidate: repair_rank(cache[candidate], constraints),
            reverse=True,
        )
        archive.extend(remaining[: beam_width - len(archive)])
    if not archive:
        raise RuntimeError("fresh discovery produced no candidate for repair archive")
    return archive


def directed_repair(
    *,
    evaluated_cache: dict[SBox, ClassicalMetrics],
    seed: int,
    evaluations: int,
    cycle_lengths: tuple[int, ...],
    proposal_pool: int,
    constraints: HardConstraints,
    first_target_at: int | None,
    first_admissible_at: int | None,
    beam_width: int = BEAM_WIDTH,
) -> dict[str, Any]:
    if evaluations < 1:
        raise ValueError("repair evaluations must be >= 1")
    if not cycle_lengths or any(length < 2 or length > 256 for length in cycle_lengths):
        raise ValueError("cycle_lengths must contain valid cycle sizes")
    if proposal_pool < 1:
        raise ValueError("proposal_pool must be >= 1")

    rng = random.Random(seed)
    seen: set[SBox] = set(evaluated_cache)
    archive = _initial_archive(evaluated_cache, constraints, beam_width=beam_width)
    diagnostics_cache: dict[SBox, PlateauDiagnostics] = {}

    archive_accepts = 0
    pools_generated = 0
    duplicate_proposals_skipped = 0
    pool_shortfalls = 0
    selected_reduce_lat_max = 0
    selected_reduce_ddt_max = 0
    selected_cycle_lengths: dict[int, int] = {length: 0 for length in cycle_lengths}

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        diagnostics = diagnostics_cache.get(parent)
        if diagnostics is None:
            diagnostics = build_plateau_diagnostics(parent, panel_mode=PANEL_MODE)
            diagnostics_cache[parent] = diagnostics

        proposals: list[tuple[SBox, LocalProposalScore, int]] = []
        proposal_seen: set[SBox] = set()
        attempts = 0
        attempt_limit = max(proposal_pool * 24, proposal_pool + 16)

        while len(proposals) < proposal_pool and attempts < attempt_limit:
            attempts += 1
            cycle_length = rng.choice(cycle_lengths)
            child, _fallback = cycle_mutation(
                parent,
                rng,
                cycle_length=cycle_length,
                anchor_indices=diagnostics.hotspot_indices,
            )
            if child in seen or child in proposal_seen:
                duplicate_proposals_skipped += 1
                continue
            proposal_seen.add(child)
            score = score_local_proposal(
                parent,
                child,
                diagnostics,
                order=len(proposals),
            )
            proposals.append((child, score, cycle_length))

        if not proposals:
            raise RuntimeError("unable to generate an unseen Phase-1I proposal")
        if len(proposals) < proposal_pool:
            pool_shortfalls += 1
        pools_generated += 1

        child, selected_score, selected_cycle = min(
            proposals,
            key=lambda item: item[1].ranking_key(
                parent_ddt_max=diagnostics.ddt_max
            ),
        )
        seen.add(child)
        selected_cycle_lengths[selected_cycle] = (
            selected_cycle_lengths.get(selected_cycle, 0) + 1
        )
        selected_reduce_lat_max += int(
            selected_score.projected_lat_max < diagnostics.lat_max
        )
        selected_reduce_ddt_max += int(
            selected_score.projected_ddt_max < diagnostics.ddt_max
        )

        metrics = evaluate_classical(child)
        evaluated_cache[child] = metrics
        completed += 1
        absolute_index = len(evaluated_cache)
        if first_target_at is None and structural_target(metrics, constraints):
            first_target_at = absolute_index
        if first_admissible_at is None and is_admissible(metrics, constraints):
            first_admissible_at = absolute_index

        if bridge_region(metrics):
            archive_accepts += 1
            archive.append(child)
            archive.sort(
                key=lambda candidate: repair_rank(
                    evaluated_cache[candidate], constraints
                ),
                reverse=True,
            )
            del archive[beam_width:]

    return {
        "evaluations": completed,
        "archive_accepts": archive_accepts,
        "archive_size": len(archive),
        "proposal_pools_generated": pools_generated,
        "duplicate_proposals_skipped": duplicate_proposals_skipped,
        "pool_shortfalls": pool_shortfalls,
        "selected_reduce_lat_max": selected_reduce_lat_max,
        "selected_reduce_ddt_max": selected_reduce_ddt_max,
        "selected_cycle_lengths": {
            str(key): value for key, value in sorted(selected_cycle_lengths.items())
        },
        "first_target_at": first_target_at,
        "first_admissible_at": first_admissible_at,
    }


def _run_directed(
    seed: int,
    *,
    cycle_lengths: tuple[int, ...],
    proposal_pool: int,
    constraints: HardConstraints,
) -> dict[str, Any]:
    evaluator, cache, first = _tracked_evaluator(constraints)
    discovery_config = ga_config(seed=seed, generations=DISCOVERY_GENERATIONS)
    discovery = evolve_permutations(evaluator, discovery_config)
    discovery_budget = equivalent_random_budget(discovery_config)
    if discovery.evaluations != discovery_budget or len(cache) != discovery_budget:
        raise RuntimeError("Phase-1I discovery budget accounting mismatch")

    repair_budget = TOTAL_BUDGET - discovery_budget
    repair = directed_repair(
        evaluated_cache=cache,
        seed=seed ^ REPAIR_SEED_XOR,
        evaluations=repair_budget,
        cycle_lengths=cycle_lengths,
        proposal_pool=proposal_pool,
        constraints=constraints,
        first_target_at=first["target"],
        first_admissible_at=first["admissible"],
    )
    if len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I directed arm did not consume exact budget")

    return {
        **_summary_from_cache(
            cache,
            constraints,
            first_target_at=repair["first_target_at"],
            first_admissible_at=repair["first_admissible_at"],
        ),
        "discovery_evaluations": discovery_budget,
        "repair_evaluations": repair_budget,
        "repair": repair,
    }


def _run_continued_ga(seed: int, *, constraints: HardConstraints) -> dict[str, Any]:
    evaluator, cache, first = _tracked_evaluator(constraints)
    config = ga_config(seed=seed, generations=FULL_GA_GENERATIONS)
    result = evolve_permutations(evaluator, config)
    expected = equivalent_random_budget(config)
    if expected != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I frozen comparator budget constant mismatch")
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1I comparator did not consume exact budget")
    return _summary_from_cache(
        cache,
        constraints,
        first_target_at=first["target"],
        first_admissible_at=first["admissible"],
    )


def _outcome(directed: dict[str, Any], comparator: dict[str, Any]) -> str:
    left = tuple(directed["best_primary_key"])
    right = tuple(comparator["best_primary_key"])
    return "directed" if left > right else "comparator" if left < right else "tie"


def run_development(
    *,
    configuration: str,
    seeds: tuple[int, ...] = PHASE1I_DEV_SEEDS,
) -> dict[str, Any]:
    if configuration not in CONFIGURATIONS:
        raise ValueError("configuration is not preregistered for Phase 1I")
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(PHASE1I_CONFIRM_RESERVED_SEEDS):
        raise ValueError("Phase-1I confirmation seeds cannot be used for development")

    cycle_lengths, proposal_pool = CONFIGURATIONS[configuration]
    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []

    for seed in seeds:
        directed = _run_directed(
            seed,
            cycle_lengths=cycle_lengths,
            proposal_pool=proposal_pool,
            constraints=constraints,
        )
        comparator = _run_continued_ga(seed, constraints=constraints)
        rows.append(
            {
                "seed": seed,
                "outcome": _outcome(directed, comparator),
                "directed": directed,
                "comparator": comparator,
            }
        )

    def median_metric(side: str, metric: str) -> float:
        return float(
            statistics.median(
                row[side]["best_metrics"][metric] for row in rows
            )
        )

    successful_first = [
        row["directed"]["first_admissible_at_evaluation"]
        for row in rows
        if row["directed"]["first_admissible_at_evaluation"] is not None
    ]

    summary = {
        "directed_admissible_runs": sum(
            row["directed"]["found_admissible"] for row in rows
        ),
        "comparator_admissible_runs": sum(
            row["comparator"]["found_admissible"] for row in rows
        ),
        "directed_target_runs": sum(
            row["directed"]["found_structural_target"] for row in rows
        ),
        "comparator_target_runs": sum(
            row["comparator"]["found_structural_target"] for row in rows
        ),
        "directed_wins": sum(row["outcome"] == "directed" for row in rows),
        "comparator_wins": sum(row["outcome"] == "comparator" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "median_nonlinearity_directed": median_metric("directed", "nonlinearity"),
        "median_du_directed": median_metric("directed", "differential_uniformity"),
        "median_max_corr_directed": median_metric("directed", "max_linear_correlation"),
        "median_nonlinearity_comparator": median_metric("comparator", "nonlinearity"),
        "median_du_comparator": median_metric("comparator", "differential_uniformity"),
        "median_max_corr_comparator": median_metric("comparator", "max_linear_correlation"),
        "median_first_admissible_evaluation": (
            float(statistics.median(successful_first)) if successful_first else None
        ),
        "archive_accepts": sum(
            row["directed"]["repair"]["archive_accepts"] for row in rows
        ),
        "selected_reduce_lat_max": sum(
            row["directed"]["repair"]["selected_reduce_lat_max"] for row in rows
        ),
        "selected_reduce_ddt_max": sum(
            row["directed"]["repair"]["selected_reduce_ddt_max"] for row in rows
        ),
        "duplicate_proposals_skipped": sum(
            row["directed"]["repair"]["duplicate_proposals_skipped"] for row in rows
        ),
        "pool_shortfalls": sum(
            row["directed"]["repair"]["pool_shortfalls"] for row in rows
        ),
    }

    eligible = (
        summary["directed_admissible_runs"] >= 2
        and summary["directed_target_runs"] >= 2
        and summary["directed_admissible_runs"]
        > summary["comparator_admissible_runs"]
    )
    summary["eligible_for_frozen_selection"] = eligible

    discovery_budget = equivalent_random_budget(
        ga_config(seed=0, generations=DISCOVERY_GENERATIONS)
    )
    return {
        "schema_version": 1,
        "experiment": "phase1i_fresh_population_vns_batch_development",
        "scientific_status": "fresh_population_development_not_gate1",
        "configuration": {
            "name": configuration,
            "cycle_lengths": list(cycle_lengths),
            "proposal_pool": proposal_pool,
            "panel_mode": PANEL_MODE,
            "beam_width": BEAM_WIDTH,
            "bridge_du_cap": BRIDGE_DU_CAP,
            "bridge_corr_cap": BRIDGE_CORR_CAP,
            "discovery_generations": DISCOVERY_GENERATIONS,
            "discovery_evaluations": discovery_budget,
            "repair_evaluations": TOTAL_BUDGET - discovery_budget,
            "total_evaluations_each_arm": TOTAL_BUDGET,
            "seeds": list(seeds),
        },
        "reserved_confirmation_seeds": list(PHASE1I_CONFIRM_RESERVED_SEEDS),
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", choices=tuple(CONFIGURATIONS), required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1I_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1i-dev.json"))
    args = parser.parse_args()
    result = run_development(
        configuration=args.configuration,
        seeds=tuple(args.seeds),
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
