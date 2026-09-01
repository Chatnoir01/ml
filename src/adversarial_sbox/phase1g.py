"""Phase 1G annealed escape from the verified NL=98 / DU=8 frontier.

This is warm-start mechanism development, not global Gate-1 evidence. It keeps the
Phase-1E combined hotspot cycle-4 proposal operator fixed and changes only the
acceptance policy: bounded temporary off-frontier states may be accepted through a
deterministic-seed simulated-annealing rule, with resets to the best frontier state.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any

from .evolution import ClassicalMetrics, HardConstraints, evaluate_classical, is_admissible
from .experiment_seeds import PHASE1G_CONFIRM_RESERVED_SEEDS, PHASE1G_DEV_SEEDS
from .phase1d import (
    EXPECTED_PHASE1B_FINGERPRINT,
    _frontier_ok,
    continuation_rank,
    reproduce_phase1b_frontier_candidate,
)
from .phase1e import cycle_mutation, guided_adaptive_search, hotspot_indices

SBox = tuple[int, ...]


def structural_target(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.nonlinearity >= constraints.min_nonlinearity
        and metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def escape_score(metrics: ClassicalMetrics) -> float:
    """Frozen Phase-1G scalar used only for temporary-state acceptance."""

    return float(
        metrics.nonlinearity
        - 2 * max(0, metrics.differential_uniformity - 8)
        - 0.25 * max(0, metrics.max_linear_correlation - 64)
    )


def excursion_eligible(
    metrics: ClassicalMetrics,
    *,
    du_cap: int,
    corr_cap: int,
    constraints: HardConstraints,
) -> bool:
    return (
        metrics.algebraic_degree >= constraints.min_algebraic_degree
        and metrics.differential_uniformity <= du_cap
        and metrics.max_linear_correlation <= corr_cap
    )


def _temperature(*, completed: int, evaluations: int, start: float, end: float) -> float:
    if evaluations <= 1:
        return float(end)
    fraction = (completed - 1) / (evaluations - 1)
    return float(start + (end - start) * fraction)


def annealed_escape_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    du_cap: int,
    corr_cap: int,
    t_start: float,
    t_end: float,
    reset_after: int,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    if du_cap < 8:
        raise ValueError("du_cap must be >= 8")
    if corr_cap < 64:
        raise ValueError("corr_cap must be >= 64")
    if t_start <= 0 or t_end <= 0:
        raise ValueError("temperatures must be positive")
    if reset_after < 1:
        raise ValueError("reset_after must be >= 1")

    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must satisfy the structural frontier")

    rng = random.Random(seed)
    seen: set[SBox] = {start}
    metrics_cache: dict[SBox, ClassicalMetrics] = {start: start_metrics}
    hotspot_cache: dict[SBox, tuple[int, ...]] = {}

    current = start
    current_metrics = start_metrics
    best_frontier = start
    best_frontier_metrics = start_metrics

    accepted = 0
    accepted_off_frontier = 0
    frontier_returns = 0
    forced_resets = 0
    accepted_since_frontier = 0
    max_accepted_du = start_metrics.differential_uniformity
    max_accepted_corr = start_metrics.max_linear_correlation

    target_at: int | None = None
    admissible_at: int | None = None

    completed = 0
    while completed < evaluations:
        anchors = hotspot_cache.get(current)
        if anchors is None:
            anchors = hotspot_indices(current, "combined")
            hotspot_cache[current] = anchors

        child, _ = cycle_mutation(
            current,
            rng,
            cycle_length=4,
            anchor_indices=anchors,
        )
        if child in seen:
            continue
        seen.add(child)

        metrics = metrics_cache.get(child)
        if metrics is None:
            metrics = evaluate_classical(child)
            metrics_cache[child] = metrics
        completed += 1

        if target_at is None and structural_target(metrics, constraints):
            target_at = completed
        if admissible_at is None and is_admissible(metrics, constraints):
            admissible_at = completed

        if _frontier_ok(metrics, constraints):
            if continuation_rank(metrics, constraints) > continuation_rank(
                best_frontier_metrics, constraints
            ):
                best_frontier = child
                best_frontier_metrics = metrics

        if not excursion_eligible(
            metrics,
            du_cap=du_cap,
            corr_cap=corr_cap,
            constraints=constraints,
        ):
            continue

        temperature = _temperature(
            completed=completed,
            evaluations=evaluations,
            start=t_start,
            end=t_end,
        )
        delta = escape_score(metrics) - escape_score(current_metrics)
        accept = delta >= 0.0
        if not accept:
            probability = math.exp(delta / max(temperature, 1e-12))
            accept = rng.random() < probability

        if not accept:
            continue

        was_frontier = _frontier_ok(current_metrics, constraints)
        now_frontier = _frontier_ok(metrics, constraints)
        current = child
        current_metrics = metrics
        accepted += 1
        max_accepted_du = max(max_accepted_du, metrics.differential_uniformity)
        max_accepted_corr = max(max_accepted_corr, metrics.max_linear_correlation)

        if now_frontier:
            if not was_frontier:
                frontier_returns += 1
            accepted_since_frontier = 0
        else:
            accepted_off_frontier += 1
            accepted_since_frontier += 1

        if accepted_since_frontier >= reset_after:
            current = best_frontier
            current_metrics = best_frontier_metrics
            forced_resets += 1
            accepted_since_frontier = 0

    return {
        "best_sbox": list(best_frontier),
        "best_metrics": asdict(best_frontier_metrics),
        "best_rank": list(continuation_rank(best_frontier_metrics, constraints)),
        "found_target": target_at is not None,
        "found_target_at_evaluation": target_at,
        "found_admissible": admissible_at is not None,
        "found_admissible_at_evaluation": admissible_at,
        "accepted_proposals": accepted,
        "accepted_off_frontier": accepted_off_frontier,
        "frontier_returns": frontier_returns,
        "forced_resets": forced_resets,
        "max_accepted_du": max_accepted_du,
        "max_accepted_corr": max_accepted_corr,
        "final_current_metrics": asdict(current_metrics),
        "evaluations": completed,
    }


def run_development(
    *,
    du_cap: int,
    corr_cap: int,
    t_start: float,
    t_end: float,
    reset_after: int,
    seeds: tuple[int, ...] = PHASE1G_DEV_SEEDS,
    evaluations: int = 600,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(PHASE1G_CONFIRM_RESERVED_SEEDS):
        raise ValueError("confirmation seeds cannot be used for development")

    start, start_metrics = reproduce_phase1b_frontier_candidate()
    if start_metrics.fingerprint != EXPECTED_PHASE1B_FINGERPRINT:
        raise RuntimeError("Phase-1G warm-start fingerprint mismatch")

    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []

    for seed in seeds:
        annealed = annealed_escape_search(
            start,
            seed=seed,
            evaluations=evaluations,
            du_cap=du_cap,
            corr_cap=corr_cap,
            t_start=t_start,
            t_end=t_end,
            reset_after=reset_after,
            constraints=constraints,
        )
        strict = guided_adaptive_search(
            start,
            seed=seed,
            evaluations=evaluations,
            beam_width=8,
            cycle_length=4,
            guidance="combined",
            constraints=constraints,
        )

        annealed_key = tuple(annealed["best_rank"])
        strict_key = tuple(strict["best_rank"])
        outcome = (
            "annealed"
            if annealed_key > strict_key
            else "strict"
            if annealed_key < strict_key
            else "tie"
        )
        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "annealed": annealed,
                "strict": strict,
            }
        )

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "annealed_wins": sum(row["outcome"] == "annealed" for row in rows),
        "strict_wins": sum(row["outcome"] == "strict" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "annealed_target_runs": sum(row["annealed"]["found_target"] for row in rows),
        "strict_target_runs": sum(row["strict"]["found_target"] for row in rows),
        "annealed_admissible_runs": sum(
            row["annealed"]["found_admissible"] for row in rows
        ),
        "strict_admissible_runs": sum(row["strict"]["found_admissible"] for row in rows),
        "median_nonlinearity_annealed": median("annealed", "nonlinearity"),
        "median_nonlinearity_strict": median("strict", "nonlinearity"),
        "median_du_annealed": median("annealed", "differential_uniformity"),
        "median_du_strict": median("strict", "differential_uniformity"),
        "median_max_corr_annealed": median("annealed", "max_linear_correlation"),
        "median_max_corr_strict": median("strict", "max_linear_correlation"),
        "accepted_off_frontier": sum(
            row["annealed"]["accepted_off_frontier"] for row in rows
        ),
        "frontier_returns": sum(row["annealed"]["frontier_returns"] for row in rows),
        "forced_resets": sum(row["annealed"]["forced_resets"] for row in rows),
    }

    return {
        "schema_version": 1,
        "experiment": "phase1g_annealed_escape_development",
        "scientific_status": "warm_start_mechanism_development_not_global_gate1",
        "historical_start": {"sbox": list(start), "metrics": asdict(start_metrics)},
        "reserved_confirmation_seeds": list(PHASE1G_CONFIRM_RESERVED_SEEDS),
        "configuration": {
            "guidance": "combined",
            "cycle_length": 4,
            "strict_beam_width": 8,
            "du_cap": du_cap,
            "corr_cap": corr_cap,
            "t_start": t_start,
            "t_end": t_end,
            "reset_after": reset_after,
            "evaluations_each": evaluations,
            "seeds": list(seeds),
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--du-cap", type=int, required=True)
    parser.add_argument("--corr-cap", type=int, required=True)
    parser.add_argument("--t-start", type=float, required=True)
    parser.add_argument("--t-end", type=float, required=True)
    parser.add_argument("--reset-after", type=int, required=True)
    parser.add_argument("--evaluations", type=int, default=600)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1G_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1g-dev.json"))
    args = parser.parse_args()

    result = run_development(
        du_cap=args.du_cap,
        corr_cap=args.corr_cap,
        t_start=args.t_start,
        t_end=args.t_end,
        reset_after=args.reset_after,
        seeds=tuple(args.seeds),
        evaluations=args.evaluations,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
