"""Phase 1E hotspot-guided warm-start operator experiment.

This is not global Gate-1 evidence. It compares hotspot-guided adaptive cycle
mutations against an equal-budget unguided adaptive comparator, both starting from
the exact verified Phase-1B DU=8 frontier candidate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
import statistics
from typing import Any, Literal

from .cryptoshield import differential_distribution_table, linear_approximation_table
from .evolution import ClassicalMetrics, HardConstraints, evaluate_classical, is_admissible
from .experiment_seeds import PHASE1E_CONFIRM_RESERVED_SEEDS, PHASE1E_DEV_SEEDS
from .phase1d import (
    EXPECTED_PHASE1B_FINGERPRINT,
    _frontier_ok,
    continuation_rank,
    reproduce_phase1b_frontier_candidate,
)

SBox = tuple[int, ...]
GuidanceMode = Literal["ddt", "lat", "combined"]


def _parity(value: int) -> int:
    return value.bit_count() & 1


def ddt_hotspot_indices(sbox: SBox) -> tuple[int, ...]:
    """Return inputs participating in the lexicographically first max DDT cell."""

    table = differential_distribution_table(sbox)
    maximum = max(max(row) for row in table[1:])
    selected: tuple[int, int] | None = None
    for dx in range(1, 256):
        for dy, count in enumerate(table[dx]):
            if count == maximum:
                selected = (dx, dy)
                break
        if selected is not None:
            break
    if selected is None:
        return ()
    dx, dy = selected
    hot: set[int] = set()
    for x in range(256):
        if sbox[x] ^ sbox[x ^ dx] == dy:
            hot.add(x)
            hot.add(x ^ dx)
    return tuple(sorted(hot))


def lat_hotspot_indices(sbox: SBox) -> tuple[int, ...]:
    """Return inputs supporting the lexicographically first max-|LAT| cell."""

    table = linear_approximation_table(sbox)
    maximum = 0
    selected: tuple[int, int, int] | None = None
    for input_mask in range(256):
        for output_mask in range(256):
            if input_mask == 0 and output_mask == 0:
                continue
            correlation = table[input_mask][output_mask]
            magnitude = abs(correlation)
            if magnitude > maximum:
                maximum = magnitude
                selected = (input_mask, output_mask, correlation)
    if selected is None or maximum == 0:
        return ()

    input_mask, output_mask, correlation = selected
    support_sign = 1 if correlation > 0 else -1
    hot: list[int] = []
    for x in range(256):
        contribution = 1 if _parity(input_mask & x) == _parity(output_mask & sbox[x]) else -1
        if contribution == support_sign:
            hot.append(x)
    return tuple(hot)


def hotspot_indices(sbox: SBox, guidance: GuidanceMode) -> tuple[int, ...]:
    if guidance == "ddt":
        return ddt_hotspot_indices(sbox)
    if guidance == "lat":
        return lat_hotspot_indices(sbox)
    if guidance == "combined":
        return tuple(sorted(set(ddt_hotspot_indices(sbox)) | set(lat_hotspot_indices(sbox))))
    raise ValueError(f"unsupported guidance mode: {guidance}")


def cycle_mutation(
    sbox: SBox,
    rng: random.Random,
    *,
    cycle_length: int,
    anchor_indices: tuple[int, ...] | None = None,
) -> tuple[SBox, bool]:
    """Rotate values across distinct indices; optionally force one hotspot anchor."""

    if cycle_length < 2 or cycle_length > len(sbox):
        raise ValueError("cycle_length must be in [2, len(sbox)]")

    fallback = not anchor_indices
    if anchor_indices:
        anchor = rng.choice(anchor_indices)
        remaining = [idx for idx in range(len(sbox)) if idx != anchor]
        indices = [anchor, *rng.sample(remaining, cycle_length - 1)]
    else:
        indices = rng.sample(range(len(sbox)), cycle_length)

    out = list(sbox)
    values = [out[idx] for idx in indices]
    rotated = [values[-1], *values[:-1]]
    for idx, value in zip(indices, rotated):
        out[idx] = value
    return tuple(out), fallback


def _adaptive_cycle_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    beam_width: int,
    cycle_length: int,
    guidance: GuidanceMode | None,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    if beam_width < 1:
        raise ValueError("beam_width must be >= 1")
    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must satisfy structural frontier")

    rng = random.Random(seed)
    metrics_cache: dict[SBox, ClassicalMetrics] = {start: start_metrics}
    hotspot_cache: dict[SBox, tuple[int, ...]] = {}
    seen: set[SBox] = {start}
    archive: list[SBox] = [start]
    best = start
    best_metrics = start_metrics
    frontier_accepts = 0
    hotspot_fallbacks = 0
    target_at: int | None = None
    admissible_at: int | None = 0 if is_admissible(start_metrics, constraints) else None

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        anchors: tuple[int, ...] | None = None
        if guidance is not None:
            anchors = hotspot_cache.get(parent)
            if anchors is None:
                anchors = hotspot_indices(parent, guidance)
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
        hotspot_fallbacks += int(fallback and guidance is not None)

        metrics = metrics_cache.get(child)
        if metrics is None:
            metrics = evaluate_classical(child)
            metrics_cache[child] = metrics
        completed += 1

        if _frontier_ok(metrics, constraints):
            frontier_accepts += 1
            archive.append(child)
            archive.sort(
                key=lambda candidate: continuation_rank(metrics_cache[candidate], constraints),
                reverse=True,
            )
            del archive[beam_width:]

        if continuation_rank(metrics, constraints) > continuation_rank(best_metrics, constraints):
            best = child
            best_metrics = metrics

        if target_at is None and metrics.nonlinearity >= 100 and metrics.differential_uniformity <= 8:
            target_at = completed
        if admissible_at is None and is_admissible(metrics, constraints):
            admissible_at = completed

    return {
        "best_sbox": list(best),
        "best_metrics": asdict(best_metrics),
        "best_rank": list(continuation_rank(best_metrics, constraints)),
        "frontier_accepts": frontier_accepts,
        "hotspot_fallbacks": hotspot_fallbacks,
        "found_target": target_at is not None,
        "found_target_at_evaluation": target_at,
        "found_admissible": admissible_at is not None,
        "found_admissible_at_evaluation": admissible_at,
        "evaluations": completed,
    }


def guided_adaptive_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    beam_width: int,
    cycle_length: int,
    guidance: GuidanceMode,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    return _adaptive_cycle_search(
        start,
        seed=seed,
        evaluations=evaluations,
        beam_width=beam_width,
        cycle_length=cycle_length,
        guidance=guidance,
        constraints=constraints,
    )


def unguided_adaptive_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    beam_width: int,
    cycle_length: int,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    return _adaptive_cycle_search(
        start,
        seed=seed,
        evaluations=evaluations,
        beam_width=beam_width,
        cycle_length=cycle_length,
        guidance=None,
        constraints=constraints,
    )


def run_development(
    *,
    guidance: GuidanceMode,
    cycle_length: int,
    seeds: tuple[int, ...] = PHASE1E_DEV_SEEDS,
    evaluations: int = 600,
    beam_width: int = 8,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(PHASE1E_CONFIRM_RESERVED_SEEDS):
        raise ValueError("confirmation seeds cannot be used for development")

    start, start_metrics = reproduce_phase1b_frontier_candidate()
    if start_metrics.fingerprint != EXPECTED_PHASE1B_FINGERPRINT:
        raise RuntimeError("Phase-1E warm-start fingerprint mismatch")
    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []

    for seed in seeds:
        guided = guided_adaptive_search(
            start,
            seed=seed,
            evaluations=evaluations,
            beam_width=beam_width,
            cycle_length=cycle_length,
            guidance=guidance,
            constraints=constraints,
        )
        unguided = unguided_adaptive_search(
            start,
            seed=seed ^ 0x1E1E1E1E,
            evaluations=evaluations,
            beam_width=beam_width,
            cycle_length=cycle_length,
            constraints=constraints,
        )
        guided_key = tuple(guided["best_rank"])
        unguided_key = tuple(unguided["best_rank"])
        outcome = "guided" if guided_key > unguided_key else "unguided" if guided_key < unguided_key else "tie"
        rows.append({"seed": seed, "outcome": outcome, "guided": guided, "unguided": unguided})

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "guided_wins": sum(row["outcome"] == "guided" for row in rows),
        "unguided_wins": sum(row["outcome"] == "unguided" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "guided_target_runs": sum(row["guided"]["found_target"] for row in rows),
        "unguided_target_runs": sum(row["unguided"]["found_target"] for row in rows),
        "guided_admissible_runs": sum(row["guided"]["found_admissible"] for row in rows),
        "unguided_admissible_runs": sum(row["unguided"]["found_admissible"] for row in rows),
        "median_nonlinearity_guided": median("guided", "nonlinearity"),
        "median_nonlinearity_unguided": median("unguided", "nonlinearity"),
        "median_du_guided": median("guided", "differential_uniformity"),
        "median_du_unguided": median("unguided", "differential_uniformity"),
        "median_max_corr_guided": median("guided", "max_linear_correlation"),
        "median_max_corr_unguided": median("unguided", "max_linear_correlation"),
        "hotspot_fallbacks": sum(row["guided"]["hotspot_fallbacks"] for row in rows),
    }

    return {
        "schema_version": 1,
        "experiment": "phase1e_hotspot_guided_development",
        "scientific_status": "warm_start_operator_development_not_global_gate1",
        "historical_start": {"sbox": list(start), "metrics": asdict(start_metrics)},
        "reserved_confirmation_seeds": list(PHASE1E_CONFIRM_RESERVED_SEEDS),
        "configuration": {
            "guidance": guidance,
            "cycle_length": cycle_length,
            "beam_width": beam_width,
            "evaluations_each": evaluations,
            "seeds": list(seeds),
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guidance", choices=("ddt", "lat", "combined"), required=True)
    parser.add_argument("--cycle-length", type=int, required=True)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--evaluations", type=int, default=600)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1E_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1e-dev.json"))
    args = parser.parse_args()
    result = run_development(
        guidance=args.guidance,
        cycle_length=args.cycle_length,
        seeds=tuple(args.seeds),
        evaluations=args.evaluations,
        beam_width=args.beam_width,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
