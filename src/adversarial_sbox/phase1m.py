"""Phase 1M: fresh-population DDT-first plateau repair experiment.

The scientific protocol is frozen in ``research/PHASE1M_PROTOCOL.md`` before
implementation and before any Phase-1M scientific execution.  The experiment
changes one mechanism relative to Phase 1I: local proposal ordering gives DDT
reduction priority after a non-regressing LAT guard.  No neural code is used.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import glob
import hashlib
import json
from pathlib import Path
import random
from statistics import median
from typing import Any, Callable, Sequence

from .cryptoshield import improved_transparency_order
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
)
from .experiment_seeds import (
    PHASE1M_CONFIRM_RESERVED_SEEDS,
    PHASE1M_DEV_SEEDS,
    validate_seed_registry,
)
from .phase1e import cycle_mutation
from .phase1h import (
    ProposalScore,
    build_plateau_diagnostics,
    score_proposal,
    structural_target,
)
from .phase1i import fresh_plateau_repair
from .provenance import fingerprint_sbox

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
REPAIR_SEED_XOR = 0x2D2D2D2D


def ga_config(*, seed: int, generations: int) -> EvolutionConfig:
    """Return the frozen Phase-1M GA configuration."""

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


def validate_frozen_design() -> None:
    """Fail closed if any preregistered budget or seed invariant drifts."""

    validate_seed_registry()
    discovery = equivalent_random_budget(
        ga_config(seed=0, generations=DISCOVERY_GENERATIONS)
    )
    total = equivalent_random_budget(ga_config(seed=0, generations=FULL_GA_GENERATIONS))
    if discovery != DISCOVERY_BUDGET:
        raise RuntimeError(
            f"Phase-1M discovery budget drift: {discovery} != {DISCOVERY_BUDGET}"
        )
    if total != TOTAL_BUDGET:
        raise RuntimeError(f"Phase-1M total budget drift: {total} != {TOTAL_BUDGET}")
    if DISCOVERY_BUDGET + REPAIR_BUDGET != TOTAL_BUDGET:
        raise RuntimeError("Phase-1M split does not equal total budget")
    if ARCHIVE_WIDTH != 8 or PROPOSAL_POOL != 96 or CYCLE_LENGTH != 4:
        raise RuntimeError("Phase-1M frozen repair constants drifted")
    if PANEL_MODE != "ties":
        raise RuntimeError("Phase-1M panel mode drifted")


validate_frozen_design()


def ddt_first_ranking_key(
    score: ProposalScore,
    *,
    current_lat_max: int,
) -> tuple[int, ...]:
    """Frozen DDT-first proposal key with a hard lexicographic LAT guard.

    A proposal that does not increase the current LAT maximum always outranks one
    that does.  Inside that guard class, projected DDT maximum and DDT plateau
    destruction are primary.  This is the only scientific mechanism changed from
    the historical Phase-1I repair selector.
    """

    lat_guard_violation = max(0, score.projected_lat_max - current_lat_max)
    return (
        lat_guard_violation,
        score.projected_ddt_max,
        -score.ddt_max_cells_reduced,
        score.projected_ddt_sum,
        score.projected_lat_max,
        -score.lat_max_cells_reduced,
        score.projected_lat_sum,
        score.order,
    )


def _first_index(
    cache: dict[SBox, ClassicalMetrics],
    predicate: Callable[[ClassicalMetrics], bool],
) -> int | None:
    for index, metrics in enumerate(cache.values(), start=1):
        if predicate(metrics):
            return index
    return None


def _best_from_cache(
    cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
) -> tuple[SBox, ClassicalMetrics]:
    if not cache:
        raise ValueError("cannot select from an empty Phase-1M cache")
    return max(cache.items(), key=lambda item: feasibility_rank(item[1], constraints))


def _cache_digest(cache: dict[SBox, ClassicalMetrics]) -> str:
    payload = "\n".join(fingerprint_sbox(candidate) for candidate in cache)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _cache_summary(
    cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
) -> dict[str, Any]:
    best_sbox, best_metrics = _best_from_cache(cache, constraints)
    du8_at = _first_index(
        cache,
        lambda metrics: metrics.differential_uniformity <= constraints.max_differential_uniformity,
    )
    target_at = _first_index(cache, lambda metrics: structural_target(metrics, constraints))
    admissible_at = _first_index(cache, lambda metrics: is_admissible(metrics, constraints))
    return {
        "best_sbox": list(best_sbox),
        "best_fingerprint": best_metrics.fingerprint,
        "best_metrics": asdict(best_metrics),
        "best_rank": list(feasibility_rank(best_metrics, constraints)),
        "posthoc_ito": improved_transparency_order(best_sbox),
        "found_du8": du8_at is not None,
        "found_du8_at_evaluation": du8_at,
        "found_structural_target": target_at is not None,
        "found_structural_target_at_evaluation": target_at,
        "found_admissible": admissible_at is not None,
        "found_admissible_at_evaluation": admissible_at,
        "unique_evaluations": len(cache),
        "cache_digest_sha256": _cache_digest(cache),
    }


def ddt_first_repair(
    *,
    seed: int,
    evaluations: int,
    evaluated_cache: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints | None = None,
    archive_width: int = ARCHIVE_WIDTH,
    proposal_pool: int = PROPOSAL_POOL,
    panel_mode: str = PANEL_MODE,
) -> dict[str, Any]:
    """Spend exact new full evaluations using the preregistered DDT-first key."""

    if evaluations < 0:
        raise ValueError("evaluations must be >= 0")
    if not evaluated_cache:
        raise ValueError("DDT-first repair requires a non-empty discovery cache")
    if archive_width < 1:
        raise ValueError("archive_width must be >= 1")
    if proposal_pool < 1:
        raise ValueError("proposal_pool must be >= 1")
    if panel_mode != "ties":
        raise ValueError("Phase-1M DDT-first repair uses the frozen ties panel")

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
    selected_reduce_ddt_max = 0
    selected_reduce_ddt_cell = 0
    selected_reduce_lat_max = 0
    selected_reduce_lat_cell = 0
    selected_lat_guard_violations = 0
    selected_ddt_max_deltas: list[int] = []
    selected_lat_max_deltas: list[int] = []

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        diagnostics = diagnostics_cache.get(parent)
        if diagnostics is None:
            diagnostics = build_plateau_diagnostics(parent, panel_mode=panel_mode)
            diagnostics_cache[parent] = diagnostics

        proposals: list[tuple[SBox, ProposalScore, bool]] = []
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
            score = score_proposal(parent, child, diagnostics, order=len(proposals))
            proposals.append((child, score, fallback))

        if len(proposals) != proposal_pool:
            raise RuntimeError(
                f"Phase-1M proposal pool shortfall: {len(proposals)} != {proposal_pool}"
            )

        proposal_pools_generated += 1
        child, selected_score, selected_fallback = min(
            proposals,
            key=lambda item: ddt_first_ranking_key(
                item[1],
                current_lat_max=diagnostics.lat_max,
            ),
        )
        seen.add(child)
        hotspot_fallbacks += int(selected_fallback)

        ddt_delta = selected_score.projected_ddt_max - diagnostics.ddt_max
        lat_delta = selected_score.projected_lat_max - diagnostics.lat_max
        selected_ddt_max_deltas.append(ddt_delta)
        selected_lat_max_deltas.append(lat_delta)
        selected_reduce_ddt_max += int(ddt_delta < 0)
        selected_reduce_ddt_cell += int(selected_score.ddt_max_cells_reduced > 0)
        selected_reduce_lat_max += int(lat_delta < 0)
        selected_reduce_lat_cell += int(selected_score.lat_max_cells_reduced > 0)
        selected_lat_guard_violations += int(lat_delta > 0)

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
        "selected_reduce_ddt_max": selected_reduce_ddt_max,
        "selected_reduce_ddt_cell": selected_reduce_ddt_cell,
        "selected_reduce_lat_max": selected_reduce_lat_max,
        "selected_reduce_lat_cell": selected_reduce_lat_cell,
        "selected_lat_guard_violations": selected_lat_guard_violations,
        "selected_ddt_max_deltas": selected_ddt_max_deltas,
        "selected_lat_max_deltas": selected_lat_max_deltas,
    }


def _historical_repair_payload(repair: dict[str, Any]) -> dict[str, Any]:
    """Normalize Phase-1I diagnostics for direct comparison with Arm A."""

    lat_deltas = [int(value) for value in repair["selected_lat_max_deltas"]]
    ddt_deltas = [int(value) for value in repair["selected_ddt_max_deltas"]]
    return {
        **repair,
        "selected_reduce_ddt_max": sum(value < 0 for value in ddt_deltas),
        "selected_lat_guard_violations": sum(value > 0 for value in lat_deltas),
    }


def _run_discovery(
    seed: int,
    *,
    constraints: HardConstraints,
) -> dict[SBox, ClassicalMetrics]:
    evaluator, cache = make_classical_evaluator(
        constraints,
        ranking_mode="feasibility_first",
    )
    result = evolve_permutations(
        evaluator,
        ga_config(seed=seed, generations=DISCOVERY_GENERATIONS),
    )
    if result.evaluations != DISCOVERY_BUDGET or len(cache) != DISCOVERY_BUDGET:
        raise RuntimeError("Phase-1M discovery evaluation accounting mismatch")
    return cache


def _run_continued_ga(
    seed: int,
    *,
    constraints: HardConstraints,
) -> dict[str, Any]:
    evaluator, cache = make_classical_evaluator(
        constraints,
        ranking_mode="feasibility_first",
    )
    result = evolve_permutations(
        evaluator,
        ga_config(seed=seed, generations=FULL_GA_GENERATIONS),
    )
    if result.evaluations != TOTAL_BUDGET or len(cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1M continued-GA arm did not consume exact budget")
    return _cache_summary(cache, constraints)


def _outcome(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_rank = tuple(left["best_rank"])
    right_rank = tuple(right["best_rank"])
    if left_rank > right_rank:
        return "a_win"
    if left_rank < right_rank:
        return "a_loss"
    return "tie"


def run_seed(seed: int) -> dict[str, Any]:
    """Execute the three frozen Phase-1M arms for one development seed."""

    validate_frozen_design()
    if seed not in PHASE1M_DEV_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase-1M development seed")

    constraints = HardConstraints()
    discovery_cache = _run_discovery(seed, constraints=constraints)
    discovery_digest = _cache_digest(discovery_cache)
    discovery_best, discovery_metrics = _best_from_cache(discovery_cache, constraints)

    arm_a_cache = dict(discovery_cache)
    arm_b_cache = dict(discovery_cache)

    arm_a_repair = ddt_first_repair(
        seed=seed ^ REPAIR_SEED_XOR,
        evaluations=REPAIR_BUDGET,
        evaluated_cache=arm_a_cache,
        constraints=constraints,
        archive_width=ARCHIVE_WIDTH,
        proposal_pool=PROPOSAL_POOL,
        panel_mode=PANEL_MODE,
    )
    arm_b_repair_raw = fresh_plateau_repair(
        seed=seed ^ REPAIR_SEED_XOR,
        evaluations=REPAIR_BUDGET,
        evaluated_cache=arm_b_cache,
        constraints=constraints,
        archive_width=ARCHIVE_WIDTH,
        proposal_pool=PROPOSAL_POOL,
        panel_mode=PANEL_MODE,
    )

    if len(arm_a_cache) != TOTAL_BUDGET or len(arm_b_cache) != TOTAL_BUDGET:
        raise RuntimeError("Phase-1M repair arm did not consume exact total budget")

    arm_a = _cache_summary(arm_a_cache, constraints)
    arm_a["repair"] = arm_a_repair
    arm_b = _cache_summary(arm_b_cache, constraints)
    arm_b["repair"] = _historical_repair_payload(arm_b_repair_raw)
    arm_c = _run_continued_ga(seed, constraints=constraints)

    return {
        "phase": "1M",
        "seed": seed,
        "discovery": {
            "best_fingerprint": discovery_metrics.fingerprint,
            "best_metrics": asdict(discovery_metrics),
            "best_sbox_fingerprint_check": fingerprint_sbox(discovery_best),
            "cache_digest_sha256": discovery_digest,
            "unique_evaluations": len(discovery_cache),
        },
        "arm_a": arm_a,
        "arm_b": arm_b,
        "arm_c": arm_c,
        "a_vs_b": _outcome(arm_a, arm_b),
        "neural_oracle_executed": False,
        "historical_warm_start_loaded": False,
        "phase1l_terminal_loaded": False,
    }


def build_development_payload(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate frozen five-seed Phase-1M development evidence."""

    if not rows:
        raise ValueError("Phase-1M development rows cannot be empty")
    ordered = sorted(rows, key=lambda row: int(row["seed"]))
    seeds = tuple(int(row["seed"]) for row in ordered)

    def med(side: str, field: str) -> float:
        if field == "posthoc_ito":
            return float(median(float(row[side][field]) for row in ordered))
        return float(
            median(float(row[side]["best_metrics"][field]) for row in ordered)
        )

    summary = {
        "a_admissible_runs": sum(row["arm_a"]["found_admissible"] for row in ordered),
        "b_admissible_runs": sum(row["arm_b"]["found_admissible"] for row in ordered),
        "c_admissible_runs": sum(row["arm_c"]["found_admissible"] for row in ordered),
        "a_structural_target_runs": sum(
            row["arm_a"]["found_structural_target"] for row in ordered
        ),
        "b_structural_target_runs": sum(
            row["arm_b"]["found_structural_target"] for row in ordered
        ),
        "c_structural_target_runs": sum(
            row["arm_c"]["found_structural_target"] for row in ordered
        ),
        "a_wins_vs_b": sum(row["a_vs_b"] == "a_win" for row in ordered),
        "a_losses_vs_b": sum(row["a_vs_b"] == "a_loss" for row in ordered),
        "ties_vs_b": sum(row["a_vs_b"] == "tie" for row in ordered),
        "median_du_a": med("arm_a", "differential_uniformity"),
        "median_du_b": med("arm_b", "differential_uniformity"),
        "median_du_c": med("arm_c", "differential_uniformity"),
        "median_nonlinearity_a": med("arm_a", "nonlinearity"),
        "median_nonlinearity_b": med("arm_b", "nonlinearity"),
        "median_max_corr_a": med("arm_a", "max_linear_correlation"),
        "median_max_corr_b": med("arm_b", "max_linear_correlation"),
        "median_ito_a": med("arm_a", "posthoc_ito"),
        "median_ito_b": med("arm_b", "posthoc_ito"),
        "median_ito_c": med("arm_c", "posthoc_ito"),
    }

    checks = {
        "a_admissible_at_least_3": summary["a_admissible_runs"] >= 3,
        "a_structural_at_least_3": summary["a_structural_target_runs"] >= 3,
        "a_admissible_gt_b": summary["a_admissible_runs"] > summary["b_admissible_runs"],
        "a_structural_gt_b": summary["a_structural_target_runs"] > summary["b_structural_target_runs"],
        "a_wins_gt_losses_b": summary["a_wins_vs_b"] > summary["a_losses_vs_b"],
        "median_du_a_at_most_8": summary["median_du_a"] <= 8,
        "median_nonlinearity_a_at_least_100": summary["median_nonlinearity_a"] >= 100,
        "median_max_corr_a_at_most_60": summary["median_max_corr_a"] <= 60,
        "median_ito_a_not_worse_than_b": summary["median_ito_a"] <= summary["median_ito_b"],
        "exact_budget_all_arms": all(
            row[side]["unique_evaluations"] == TOTAL_BUDGET
            for row in ordered
            for side in ("arm_a", "arm_b", "arm_c")
        ),
        "fresh_seed_registry_exact": seeds == PHASE1M_DEV_SEEDS,
        "reserved_confirmation_seeds_unused": not (
            set(seeds) & set(PHASE1M_CONFIRM_RESERVED_SEEDS)
        ),
        "neural_oracle_blocked": all(
            not row["neural_oracle_executed"] for row in ordered
        ),
        "no_historical_warm_start": all(
            not row["historical_warm_start_loaded"] for row in ordered
        ),
        "no_phase1l_terminal_loaded": all(
            not row["phase1l_terminal_loaded"] for row in ordered
        ),
    }

    development_pass = all(checks.values())
    return {
        "schema_version": 1,
        "experiment": "phase1m_ddt_first_fresh_population_repair_development",
        "configuration": {
            "development_seeds": list(PHASE1M_DEV_SEEDS),
            "reserved_confirmation_seeds": list(PHASE1M_CONFIRM_RESERVED_SEEDS),
            "discovery_generations": DISCOVERY_GENERATIONS,
            "discovery_evaluations": DISCOVERY_BUDGET,
            "repair_evaluations": REPAIR_BUDGET,
            "total_evaluations_each_arm": TOTAL_BUDGET,
            "archive_width": ARCHIVE_WIDTH,
            "proposal_pool": PROPOSAL_POOL,
            "cycle_length": CYCLE_LENGTH,
            "panel_mode": PANEL_MODE,
            "repair_seed_xor": REPAIR_SEED_XOR,
        },
        "summary": summary,
        "development_checks": checks,
        "per_seed": ordered,
        "verdict": "phase1m_dev_pass" if development_pass else "phase1m_dev_fail",
    }


def _write_payload(payload: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def _load_aggregate_files(patterns: Sequence[str]) -> list[dict[str, Any]]:
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(sorted(glob.glob(pattern)))
    if not paths:
        raise ValueError("no Phase-1M aggregate files matched")
    return [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--aggregate-files", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.aggregate_files:
        if args.seeds:
            parser.error("--seeds and --aggregate-files are mutually exclusive")
        payload = build_development_payload(_load_aggregate_files(args.aggregate_files))
        _write_payload(payload, args.output)
        return

    if not args.seeds:
        parser.error("provide --seeds or --aggregate-files")

    rows = [run_seed(seed) for seed in args.seeds]
    payload: dict[str, Any]
    if len(rows) == 1:
        payload = rows[0]
    else:
        payload = build_development_payload(rows)
    _write_payload(payload, args.output)


if __name__ == "__main__":
    main()
