"""Phase 1H plateau-directed warm-start operator experiment.

The full classical fitness budget is kept equal to the existing strict combined
cycle-4 comparator.  Phase 1H differs only in proposal selection: several cycle-4
children are generated cheaply and ranked by exact local projections on the
current LAT/DDT plateau before one child receives a full CryptoShield evaluation.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import statistics
from typing import Any, Literal

from .cryptoshield import differential_distribution_table, linear_approximation_table
from .evolution import ClassicalMetrics, HardConstraints, evaluate_classical, is_admissible
from .experiment_seeds import PHASE1H_CONFIRM_RESERVED_SEEDS, PHASE1H_DEV_SEEDS
from .phase1d import (
    EXPECTED_PHASE1B_FINGERPRINT,
    _frontier_ok,
    continuation_rank,
    reproduce_phase1b_frontier_candidate,
)
from .phase1e import cycle_mutation, guided_adaptive_search

SBox = tuple[int, ...]
PanelMode = Literal["ties", "band"]


@dataclass(frozen=True)
class LatCell:
    input_mask: int
    output_mask: int
    correlation: int


@dataclass(frozen=True)
class DdtCell:
    input_difference: int
    output_difference: int
    count: int


@dataclass(frozen=True)
class PlateauDiagnostics:
    lat_max: int
    ddt_max: int
    lat_cells: tuple[LatCell, ...]
    ddt_cells: tuple[DdtCell, ...]
    hotspot_indices: tuple[int, ...]


@dataclass(frozen=True)
class ProposalScore:
    projected_lat_max: int
    projected_ddt_max: int
    lat_max_cells_reduced: int
    ddt_max_cells_reduced: int
    projected_lat_sum: int
    projected_ddt_sum: int
    order: int

    def ranking_key(self) -> tuple[int, ...]:
        return (
            self.projected_lat_max,
            self.projected_ddt_max,
            -self.lat_max_cells_reduced,
            -self.ddt_max_cells_reduced,
            self.projected_lat_sum,
            self.projected_ddt_sum,
            self.order,
        )


def _parity(value: int) -> int:
    return value.bit_count() & 1


def _lat_contribution(sbox: SBox, x: int, input_mask: int, output_mask: int) -> int:
    return 1 if _parity(input_mask & x) == _parity(output_mask & sbox[x]) else -1


def build_plateau_diagnostics(
    sbox: SBox,
    *,
    panel_mode: PanelMode,
) -> PlateauDiagnostics:
    """Build the frozen LAT/DDT panel and hotspot union for one evaluated parent."""

    if panel_mode not in ("ties", "band"):
        raise ValueError(f"unsupported panel mode: {panel_mode}")

    lat = linear_approximation_table(sbox)
    lat_max = max(
        abs(lat[a][b])
        for a in range(256)
        for b in range(256)
        if not (a == 0 and b == 0)
    )
    lat_threshold = lat_max if panel_mode == "ties" else max(0, lat_max - 4)
    lat_cells = tuple(
        LatCell(a, b, lat[a][b])
        for a in range(256)
        for b in range(256)
        if not (a == 0 and b == 0) and abs(lat[a][b]) >= lat_threshold
    )

    ddt = differential_distribution_table(sbox)
    ddt_max = max(max(row) for row in ddt[1:])
    ddt_threshold = ddt_max if panel_mode == "ties" else max(0, ddt_max - 2)
    ddt_cells = tuple(
        DdtCell(dx, dy, ddt[dx][dy])
        for dx in range(1, 256)
        for dy in range(256)
        if ddt[dx][dy] >= ddt_threshold
    )

    hot: set[int] = set()
    for cell in lat_cells:
        if abs(cell.correlation) != lat_max:
            continue
        support_sign = 1 if cell.correlation > 0 else -1
        for x in range(256):
            if _lat_contribution(sbox, x, cell.input_mask, cell.output_mask) == support_sign:
                hot.add(x)

    for cell in ddt_cells:
        if cell.count != ddt_max:
            continue
        dx = cell.input_difference
        dy = cell.output_difference
        for x in range(256):
            if sbox[x] ^ sbox[x ^ dx] == dy:
                hot.add(x)
                hot.add(x ^ dx)

    if not hot:
        hot.update(range(256))

    return PlateauDiagnostics(
        lat_max=lat_max,
        ddt_max=ddt_max,
        lat_cells=lat_cells,
        ddt_cells=ddt_cells,
        hotspot_indices=tuple(sorted(hot)),
    )


def projected_lat_correlation(
    parent: SBox,
    child: SBox,
    changed_indices: tuple[int, ...],
    cell: LatCell,
) -> int:
    """Exact new correlation for one existing LAT cell after a local permutation."""

    correlation = cell.correlation
    for x in changed_indices:
        old = _lat_contribution(parent, x, cell.input_mask, cell.output_mask)
        new = _lat_contribution(child, x, cell.input_mask, cell.output_mask)
        correlation += new - old
    return correlation


def projected_ddt_count(
    parent: SBox,
    child: SBox,
    changed_indices: tuple[int, ...],
    cell: DdtCell,
) -> int:
    """Exact new count for one existing DDT cell after a local permutation."""

    dx = cell.input_difference
    dy = cell.output_difference
    affected: set[int] = set()
    for index in changed_indices:
        affected.add(index)
        affected.add(index ^ dx)

    count = cell.count
    for x in affected:
        old = 1 if parent[x] ^ parent[x ^ dx] == dy else 0
        new = 1 if child[x] ^ child[x ^ dx] == dy else 0
        count += new - old
    return count


def score_proposal(
    parent: SBox,
    child: SBox,
    diagnostics: PlateauDiagnostics,
    *,
    order: int,
) -> ProposalScore:
    changed = tuple(index for index, (left, right) in enumerate(zip(parent, child)) if left != right)
    if len(changed) != 4:
        raise ValueError("Phase-1H proposals must be exact cycle-4 mutations")

    projected_lat = [
        abs(projected_lat_correlation(parent, child, changed, cell))
        for cell in diagnostics.lat_cells
    ]
    projected_ddt = [
        projected_ddt_count(parent, child, changed, cell)
        for cell in diagnostics.ddt_cells
    ]

    lat_reduced = sum(
        abs(cell.correlation) == diagnostics.lat_max and projected < diagnostics.lat_max
        for cell, projected in zip(diagnostics.lat_cells, projected_lat)
    )
    ddt_reduced = sum(
        cell.count == diagnostics.ddt_max and projected < diagnostics.ddt_max
        for cell, projected in zip(diagnostics.ddt_cells, projected_ddt)
    )

    return ProposalScore(
        projected_lat_max=max(projected_lat),
        projected_ddt_max=max(projected_ddt),
        lat_max_cells_reduced=lat_reduced,
        ddt_max_cells_reduced=ddt_reduced,
        projected_lat_sum=sum(projected_lat),
        projected_ddt_sum=sum(projected_ddt),
        order=order,
    )


def structural_target(metrics: ClassicalMetrics, constraints: HardConstraints) -> bool:
    return (
        metrics.nonlinearity >= constraints.min_nonlinearity
        and metrics.differential_uniformity <= constraints.max_differential_uniformity
        and metrics.max_linear_correlation <= constraints.max_linear_correlation
        and metrics.algebraic_degree >= constraints.min_algebraic_degree
    )


def plateau_directed_search(
    start: SBox,
    *,
    seed: int,
    evaluations: int,
    proposal_pool: int,
    panel_mode: PanelMode,
    beam_width: int = 8,
    constraints: HardConstraints | None = None,
) -> dict[str, Any]:
    if evaluations < 1:
        raise ValueError("evaluations must be >= 1")
    if proposal_pool < 1:
        raise ValueError("proposal_pool must be >= 1")
    if beam_width < 1:
        raise ValueError("beam_width must be >= 1")

    constraints = constraints or HardConstraints()
    start_metrics = evaluate_classical(start)
    if not _frontier_ok(start_metrics, constraints):
        raise ValueError("warm-start candidate must satisfy the structural frontier")

    rng = random.Random(seed)
    metrics_cache: dict[SBox, ClassicalMetrics] = {start: start_metrics}
    diagnostics_cache: dict[SBox, PlateauDiagnostics] = {}
    seen: set[SBox] = {start}
    archive: list[SBox] = [start]
    best = start
    best_metrics = start_metrics

    frontier_accepts = 0
    proposal_pools_generated = 0
    duplicate_proposals_skipped = 0
    pool_shortfalls = 0
    selected_lat_max_deltas: list[int] = []
    selected_ddt_max_deltas: list[int] = []
    selected_reduce_lat_cell = 0
    selected_reduce_ddt_cell = 0
    selected_reduce_lat_max = 0
    target_at: int | None = None
    admissible_at: int | None = None

    completed = 0
    while completed < evaluations:
        parent = rng.choice(archive)
        diagnostics = diagnostics_cache.get(parent)
        if diagnostics is None:
            diagnostics = build_plateau_diagnostics(parent, panel_mode=panel_mode)
            diagnostics_cache[parent] = diagnostics

        proposals: list[tuple[SBox, ProposalScore]] = []
        proposal_seen: set[SBox] = set()
        attempts = 0
        attempt_limit = max(proposal_pool * 20, proposal_pool + 10)
        while len(proposals) < proposal_pool and attempts < attempt_limit:
            attempts += 1
            child, _fallback = cycle_mutation(
                parent,
                rng,
                cycle_length=4,
                anchor_indices=diagnostics.hotspot_indices,
            )
            if child in seen or child in proposal_seen:
                duplicate_proposals_skipped += 1
                continue
            proposal_seen.add(child)
            score = score_proposal(parent, child, diagnostics, order=len(proposals))
            proposals.append((child, score))

        if not proposals:
            raise RuntimeError("unable to generate an unseen Phase-1H proposal")
        if len(proposals) < proposal_pool:
            pool_shortfalls += 1

        proposal_pools_generated += 1
        child, selected_score = min(proposals, key=lambda item: item[1].ranking_key())
        seen.add(child)

        selected_lat_max_deltas.append(selected_score.projected_lat_max - diagnostics.lat_max)
        selected_ddt_max_deltas.append(selected_score.projected_ddt_max - diagnostics.ddt_max)
        selected_reduce_lat_cell += int(selected_score.lat_max_cells_reduced > 0)
        selected_reduce_ddt_cell += int(selected_score.ddt_max_cells_reduced > 0)
        selected_reduce_lat_max += int(selected_score.projected_lat_max < diagnostics.lat_max)

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

        if target_at is None and structural_target(metrics, constraints):
            target_at = completed
        if admissible_at is None and is_admissible(metrics, constraints):
            admissible_at = completed

    return {
        "best_sbox": list(best),
        "best_metrics": asdict(best_metrics),
        "best_rank": list(continuation_rank(best_metrics, constraints)),
        "frontier_accepts": frontier_accepts,
        "found_target": target_at is not None,
        "found_target_at_evaluation": target_at,
        "found_admissible": admissible_at is not None,
        "found_admissible_at_evaluation": admissible_at,
        "evaluations": completed,
        "proposal_pools_generated": proposal_pools_generated,
        "duplicate_proposals_skipped": duplicate_proposals_skipped,
        "pool_shortfalls": pool_shortfalls,
        "selected_lat_max_deltas": selected_lat_max_deltas,
        "selected_ddt_max_deltas": selected_ddt_max_deltas,
        "selected_reduce_lat_cell": selected_reduce_lat_cell,
        "selected_reduce_ddt_cell": selected_reduce_ddt_cell,
        "selected_reduce_lat_max": selected_reduce_lat_max,
    }


def run_development(
    *,
    proposal_pool: int,
    panel_mode: PanelMode,
    seeds: tuple[int, ...] = PHASE1H_DEV_SEEDS,
    evaluations: int = 600,
    beam_width: int = 8,
) -> dict[str, Any]:
    if proposal_pool not in (32, 96):
        raise ValueError("proposal_pool is not preregistered for Phase 1H")
    if panel_mode not in ("ties", "band"):
        raise ValueError("panel_mode is not preregistered for Phase 1H")
    if not seeds:
        raise ValueError("at least one development seed is required")
    if set(seeds) & set(PHASE1H_CONFIRM_RESERVED_SEEDS):
        raise ValueError("Phase-1H confirmation seeds cannot be used for development")

    start, start_metrics = reproduce_phase1b_frontier_candidate()
    if start_metrics.fingerprint != EXPECTED_PHASE1B_FINGERPRINT:
        raise RuntimeError("Phase-1H warm-start fingerprint mismatch")

    constraints = HardConstraints()
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        directed = plateau_directed_search(
            start,
            seed=seed,
            evaluations=evaluations,
            proposal_pool=proposal_pool,
            panel_mode=panel_mode,
            beam_width=beam_width,
            constraints=constraints,
        )
        comparator = guided_adaptive_search(
            start,
            seed=seed ^ 0x1A1A1A1A,
            evaluations=evaluations,
            beam_width=beam_width,
            cycle_length=4,
            guidance="combined",
            constraints=constraints,
        )
        directed_key = tuple(directed["best_rank"])
        comparator_key = tuple(comparator["best_rank"])
        outcome = (
            "directed"
            if directed_key > comparator_key
            else "comparator"
            if directed_key < comparator_key
            else "tie"
        )
        rows.append(
            {
                "seed": seed,
                "outcome": outcome,
                "directed": directed,
                "comparator": comparator,
            }
        )

    def median(side: str, metric: str) -> float:
        return float(statistics.median(row[side]["best_metrics"][metric] for row in rows))

    summary = {
        "directed_wins": sum(row["outcome"] == "directed" for row in rows),
        "comparator_wins": sum(row["outcome"] == "comparator" for row in rows),
        "ties": sum(row["outcome"] == "tie" for row in rows),
        "directed_target_runs": sum(row["directed"]["found_target"] for row in rows),
        "comparator_target_runs": sum(row["comparator"]["found_target"] for row in rows),
        "directed_admissible_runs": sum(row["directed"]["found_admissible"] for row in rows),
        "comparator_admissible_runs": sum(row["comparator"]["found_admissible"] for row in rows),
        "median_nonlinearity_directed": median("directed", "nonlinearity"),
        "median_nonlinearity_comparator": median("comparator", "nonlinearity"),
        "median_du_directed": median("directed", "differential_uniformity"),
        "median_du_comparator": median("comparator", "differential_uniformity"),
        "median_max_corr_directed": median("directed", "max_linear_correlation"),
        "median_max_corr_comparator": median("comparator", "max_linear_correlation"),
        "selected_reduce_lat_max": sum(row["directed"]["selected_reduce_lat_max"] for row in rows),
        "selected_reduce_lat_cell": sum(row["directed"]["selected_reduce_lat_cell"] for row in rows),
        "selected_reduce_ddt_cell": sum(row["directed"]["selected_reduce_ddt_cell"] for row in rows),
        "duplicate_proposals_skipped": sum(row["directed"]["duplicate_proposals_skipped"] for row in rows),
        "pool_shortfalls": sum(row["directed"]["pool_shortfalls"] for row in rows),
    }

    config_name = f"{'ties' if panel_mode == 'ties' else 'band'}_p{proposal_pool}"
    return {
        "schema_version": 1,
        "experiment": "phase1h_plateau_directed_development",
        "scientific_status": "warm_start_operator_development_not_global_gate1",
        "historical_start": {"sbox": list(start), "metrics": asdict(start_metrics)},
        "reserved_confirmation_seeds": list(PHASE1H_CONFIRM_RESERVED_SEEDS),
        "configuration": {
            "name": config_name,
            "panel_mode": panel_mode,
            "proposal_pool": proposal_pool,
            "cycle_length": 4,
            "beam_width": beam_width,
            "evaluations_each": evaluations,
            "seeds": list(seeds),
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-pool", type=int, required=True)
    parser.add_argument("--panel-mode", choices=("ties", "band"), required=True)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--evaluations", type=int, default=600)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PHASE1H_DEV_SEEDS))
    parser.add_argument("--output", type=Path, default=Path("phase1h-dev.json"))
    args = parser.parse_args()
    result = run_development(
        proposal_pool=args.proposal_pool,
        panel_mode=args.panel_mode,
        seeds=tuple(args.seeds),
        evaluations=args.evaluations,
        beam_width=args.beam_width,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
