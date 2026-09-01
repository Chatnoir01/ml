"""Phase 1E spectral/DDT-guided continuation on the verified DU=8 frontier.

This is a defensive/academic toy S-Box search experiment. It does not target or
claim compromise of deployed cryptosystems. The experiment asks whether a
structurally guided permutation operator can cross the observed NL=98 plateau
while preserving the classical DU/linear/degree frontier.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import statistics
from typing import Any, Sequence

from .cryptoshield import is_bijective, validate_sbox
from .evolution import ClassicalMetrics, HardConstraints, evaluate_classical, is_admissible
from .experiment_seeds import DEV_PHASE1E_SEEDS, CONFIRM_PHASE1E_RESERVED_SEEDS
from .phase1d import (
    adaptive_frontier_search,
    continuation_rank,
    reproduce_phase1b_frontier_candidate,
)

SBox = tuple[int, ...]
GUIDE_MODES = ("spectral", "ddt", "hybrid")


@dataclass(frozen=True, slots=True)
class StructuralGuide:
    walsh_input_mask: int
    walsh_output_mask: int
    walsh_correlation: int
    walsh_bad_positions: tuple[int, ...]
    ddt_input_difference: int
    ddt_output_difference: int
    ddt_count: int
    ddt_hot_positions: tuple[int, ...]


def _parity(value: int) -> int:
    return value.bit_count() & 1


def _fwht(values: list[int]) -> list[int]:
    out = values[:]
    width = 1
    while width < len(out):
        step = width * 2
        for start in range(0, len(out), step):
            for offset in range(width):
                left_index = start + offset
                right_index = left_index + width
                left = out[left_index]
                right = out[right_index]
                out[left_index] = left + right
                out[right_index] = left - right
        width = step
    return out


def worst_walsh_hotspot(sbox: Sequence[int]) -> tuple[int, int, int]:
    """Return the (input mask, output mask, signed correlation) limiting NL."""

    values = validate_sbox(sbox)
    best_abs = -1
    best = (0, 1, 0)
    for output_mask in range(1, 256):
        signs = [
            1 if _parity(output_mask & values[x]) == 0 else -1
            for x in range(256)
        ]
        spectrum = _fwht(signs)
        for input_mask, correlation in enumerate(spectrum):
            absolute = abs(correlation)
            if absolute > best_abs:
                best_abs = absolute
                best = (input_mask, output_mask, correlation)
    return best


def worst_ddt_hotspot(sbox: Sequence[int]) -> tuple[int, int, int]:
    """Return the highest non-trivial DDT cell without materializing the full table."""

    values = validate_sbox(sbox)
    best_count = -1
    best = (1, 0, 0)
    for input_difference in range(1, 256):
        counts = [0] * 256
        for x in range(256):
            counts[values[x] ^ values[x ^ input_difference]] += 1
        for output_difference, count in enumerate(counts):
            if count > best_count:
                best_count = count
                best = (input_difference, output_difference, count)
    return best


def build_structural_guide(sbox: Sequence[int]) -> StructuralGuide:
    values = validate_sbox(sbox)
    a, b, correlation = worst_walsh_hotspot(values)
    correlation_sign = 1 if correlation >= 0 else -1
    walsh_bad = []
    for x in range(256):
        contribution = 1 if _parity(a & x) == _parity(b & values[x]) else -1
        if contribution == correlation_sign:
            walsh_bad.append(x)

    dx, dy, count = worst_ddt_hotspot(values)
    ddt_hot = [
        x
        for x in range(256)
        if values[x] ^ values[x ^ dx] == dy
    ]
    return StructuralGuide(
        walsh_input_mask=a,
        walsh_output_mask=b,
        walsh_correlation=correlation,
        walsh_bad_positions=tuple(walsh_bad),
        ddt_input_difference=dx,
        ddt_output_difference=dy,
        ddt_count=count,
        ddt_hot_positions=tuple(ddt_hot),
    )


def _walsh_contribution(values: Sequence[int], a: int, b: int, x: int, *, swapped: tuple[int, int] | None = None) -> int:
    output = values[x]
    if swapped is not None:
        left, right = swapped
        if x == left:
            output = values[right]
        elif x == right:
            output = values[left]
    return 1 if _parity(a & x) == _parity(b & output) else -1


def walsh_pair_improvement(sbox: Sequence[int], guide: StructuralGuide, left: int, right: int) -> int:
    values = validate_sbox(sbox)
    old_pair = (
        _walsh_contribution(values, guide.walsh_input_mask, guide.walsh_output_mask, left)
        + _walsh_contribution(values, guide.walsh_input_mask, guide.walsh_output_mask, right)
    )
    new_pair = (
        _walsh_contribution(
            values,
            guide.walsh_input_mask,
            guide.walsh_output_mask,
            left,
            swapped=(left, right),
        )
        + _walsh_contribution(
            values,
            guide.walsh_input_mask,
            guide.walsh_output_mask,
            right,
            swapped=(left, right),
        )
    )
    new_correlation = guide.walsh_correlation - old_pair + new_pair
    return abs(guide.walsh_correlation) - abs(new_correlation)


def ddt_pair_improvement(sbox: Sequence[int], guide: StructuralGuide, left: int, right: int) -> int:
    """Exact change in the current worst DDT cell caused by one output swap."""

    values = validate_sbox(sbox)
    dx = guide.ddt_input_difference
    dy = guide.ddt_output_difference
    affected = {left, right, left ^ dx, right ^ dx}

    def output_at(index: int, swapped: bool) -> int:
        if not swapped:
            return values[index]
        if index == left:
            return values[right]
        if index == right:
            return values[left]
        return values[index]

    old_count = 0
    new_count = 0
    for x in affected:
        if output_at(x, False) ^ output_at(x ^ dx, False) == dy:
            old_count += 1
        if output_at(x, True) ^ output_at(x ^ dx, True) == dy:
            new_count += 1
    return old_count - new_count


def _pair_key(
    mode: str,
    spectral_improvement: int,
    ddt_improvement: int,
) -> tuple[int, ...]:
    if mode == "spectral":
        return (spectral_improvement, ddt_improvement)
    if mode == "ddt":
        return (ddt_improvement, spectral_improvement)
    if mode == "hybrid":
        return (
            1 if ddt_improvement >= 0 else 0,
            spectral_improvement,
            ddt_improvement,
        )
    raise ValueError(f"unknown guide mode: {mode}")


def guided_mutation(
    parent: Sequence[int],
    rng: random.Random,
    *,
    guide: StructuralGuide,
    mode: str,
    proposal_pairs: int,
    swaps: int,
) -> tuple[SBox, dict[str, int]]:
    """Choose a swap using local LAT/DDT diagnostics, then optionally add swaps."""

    values = list(validate_sbox(parent))
    if not is_bijective(values):
        raise ValueError("guided_mutation requires a bijective parent")
    if mode not in GUIDE_MODES:
        raise ValueError(f"unknown guide mode: {mode}")
    if proposal_pairs < 1:
        raise ValueError("proposal_pairs must be >= 1")
    if swaps < 1:
        raise ValueError("swaps must be >= 1")

    if mode == "spectral":
        anchor_pool = guide.walsh_bad_positions
    elif mode == "ddt":
        anchor_pool = guide.ddt_hot_positions
    else:
        anchor_pool = tuple(sorted(set(guide.walsh_bad_positions) | set(guide.ddt_hot_positions)))
    if not anchor_pool:
        anchor_pool = tuple(range(256))

    best_pair: tuple[int, int] | None = None
    best_key: tuple[int, ...] | None = None
    best_proxy = (0, 0)
    sampled: set[tuple[int, int]] = set()
    attempts = 0
    max_attempts = max(proposal_pairs * 20, 100)
    while len(sampled) < proposal_pairs and attempts < max_attempts:
        attempts += 1
        left = rng.choice(anchor_pool)
        right = rng.randrange(256)
        if left == right:
            continue
        pair = (left, right) if left < right else (right, left)
        if pair in sampled:
            continue
        sampled.add(pair)
        spectral = walsh_pair_improvement(values, guide, *pair)
        ddt = ddt_pair_improvement(values, guide, *pair)
        key = _pair_key(mode, spectral, ddt)
        if best_key is None or key > best_key:
            best_key = key
            best_pair = pair
            best_proxy = (spectral, ddt)

    if best_pair is None:
        left, right = rng.sample(range(256), 2)
        best_pair = (left, right)
        best_proxy = (
            walsh_pair_improvement(values, guide, left, right),
            ddt_pair_improvement(values, guide, left, right),
        )

    left, right = best_pair
    values[left], values[right] = values[right], values[left]
    for _ in range(swaps - 1):
        left, right = rng.sample(range(256), 2)
        values[left], values[right] = values[right], values[left]

    return tuple(values), {
        "spectral_proxy_improvement": best_proxy[0],
        "ddt_proxy_improvement": best_proxy[1],
    }


def _frontier_ok(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def guided_frontier_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    mode: str,
    proposal_pairs: int,
    swaps: int,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    """Adaptive hill-climb using hotspot-guided permutation proposals."""

    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must satisfy the structural frontier")

    rng = random.Random(seed)
    seen: set[SBox] = {start}
    current = start
    current_metrics = start_metrics
    current_guide = build_structural_guide(current)
    best = start
    best_metrics = start_metrics
    accepted_steps = 0
    frontier_candidates = 0
    positive_spectral_proposals = 0
    nonworse_ddt_proposals = 0
    found_at: int | None = 0 if is_admissible(start_metrics, constraints) else None

    completed = 0
    while completed < evaluations:
        child, proxy = guided_mutation(
            current,
            rng,
            guide=current_guide,
            mode=mode,
            proposal_pairs=proposal_pairs,
            swaps=swaps,
        )
        if child in seen:
            continue
        seen.add(child)
        metrics = evaluate_classical(child)
        completed += 1
        positive_spectral_proposals += proxy["spectral_proxy_improvement"] > 0
        nonworse_ddt_proposals += proxy["ddt_proxy_improvement"] >= 0

        if _frontier_ok(metrics, constraints):
            frontier_candidates += 1
            if continuation_rank(metrics, constraints) > continuation_rank(
                current_metrics, constraints
            ):
                current = child
                current_metrics = metrics
                current_guide = build_structural_guide(current)
                accepted_steps += 1

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
        "found_admissible": found_at is not None,
        "found_at_evaluation": found_at,
        "evaluations": completed,
        "accepted_steps": accepted_steps,
        "frontier_candidates": frontier_candidates,
        "positive_spectral_proposals": positive_spectral_proposals,
        "nonworse_ddt_proposals": nonworse_ddt_proposals,
    }


def run_development(
    *,
    seeds: tuple[int, ...] = DEV_PHASE1E_SEEDS,
    evaluations: int = 480,
    mode: str = "hybrid",
    proposal_pairs: int = 64,
    swaps: int = 1,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(CONFIRM_PHASE1E_RESERVED_SEEDS):
        raise ValueError("Phase-1E confirmation seeds cannot be used for development")
    if mode not in GUIDE_MODES:
        raise ValueError(f"unknown guide mode: {mode}")

    constraints = HardConstraints()
    start, start_metrics = reproduce_phase1b_frontier_candidate()
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        guided = guided_frontier_search(
            start,
            seed=seed,
            evaluations=evaluations,
            mode=mode,
            proposal_pairs=proposal_pairs,
            swaps=swaps,
            constraints=constraints,
        )
        unguided = adaptive_frontier_search(
            start,
            seed=seed ^ 0x1E1E1E1E,
            evaluations=evaluations,
            beam_width=8,
            mutation_swaps=swaps,
            constraints=constraints,
        )
        guided_key = tuple(guided["best_rank"])
        unguided_key = tuple(unguided["best_rank"])
        outcome = (
            "guided"
            if guided_key > unguided_key
            else "unguided"
            if guided_key < unguided_key
            else "tie"
        )
        rows.append(
            {"seed": seed, "outcome": outcome, "guided": guided, "unguided": unguided}
        )

    def median(side: str, metric: str) -> float:
        return float(
            statistics.median(row[side]["best_metrics"][metric] for row in rows)
        )

    summary = {
        "guided_wins": sum(row["outcome"] == "guided" for row in rows),
        "unguided_wins": sum(row["outcome"] == "unguided" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "guided_admissible_runs": sum(row["guided"]["found_admissible"] for row in rows),
        "unguided_admissible_runs": sum(row["unguided"]["found_admissible"] for row in rows),
        "guided_nl100_du8_runs": sum(
            row["guided"]["best_metrics"]["nonlinearity"] >= 100
            and row["guided"]["best_metrics"]["differential_uniformity"] <= 8
            for row in rows
        ),
        "unguided_nl100_du8_runs": sum(
            row["unguided"]["best_metrics"]["nonlinearity"] >= 100
            and row["unguided"]["best_metrics"]["differential_uniformity"] <= 8
            for row in rows
        ),
        "median_nonlinearity_guided": median("guided", "nonlinearity"),
        "median_nonlinearity_unguided": median("unguided", "nonlinearity"),
        "median_du_guided": median("guided", "differential_uniformity"),
        "median_du_unguided": median("unguided", "differential_uniformity"),
        "median_max_corr_guided": median("guided", "max_linear_correlation"),
        "median_max_corr_unguided": median("unguided", "max_linear_correlation"),
    }
    return {
        "schema_version": 1,
        "experiment": "phase1e_spectral_ddt_guided_development",
        "scientific_status": "warm_start_operator_development_not_global_gate1",
        "historical_start": {"sbox": list(start), "metrics": asdict(start_metrics)},
        "reserved_confirmation_seeds": list(CONFIRM_PHASE1E_RESERVED_SEEDS),
        "configuration": {
            "seeds": list(seeds),
            "evaluations_each": evaluations,
            "mode": mode,
            "proposal_pairs": proposal_pairs,
            "swaps": swaps,
            "unguided_comparator": {"beam_width": 8, "mutation_swaps": swaps},
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1e-dev.json"))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEV_PHASE1E_SEEDS))
    parser.add_argument("--evaluations", type=int, default=480)
    parser.add_argument("--mode", choices=GUIDE_MODES, default="hybrid")
    parser.add_argument("--proposal-pairs", type=int, default=64)
    parser.add_argument("--swaps", type=int, default=1)
    args = parser.parse_args()
    result = run_development(
        seeds=tuple(args.seeds),
        evaluations=args.evaluations,
        mode=args.mode,
        proposal_pairs=args.proposal_pairs,
        swaps=args.swaps,
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
