"""Phase 1O: matched-budget multi-hotspot Walsh plateau repair experiment.

The frozen protocol lives in ``research/PHASE1O_PROTOCOL.md``.  This module has
no neural path and cannot enable the Neural Oracle.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import random
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from .cryptoshield import improved_transparency_order, is_bijective, validate_sbox
from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    evaluate_classical,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    structural_gate_count,
)
from .experiment_seeds import PHASE1O_DEV_SEEDS, validate_seed_registry
from .pareto import ITOAwareMetrics, non_dominated_sort, select_nsga2
from .phase1l import GA_CONFIG_KWARGS
from .phase1m import (
    CLASSICAL_BUDGET,
    GENERATIONS,
    ITO_NONINFERIORITY_TOLERANCE,
    PARENT_COUNT,
    POPULATION_SIZE,
    PROPOSALS_PER_GENERATION,
    PROPOSALS_PER_PARENT,
    SHORTLIST_SIZE,
    ClassicalEvaluationLedger,
    _cell_positions,
    _classical_to_ito,
    _initial_population,
    _maximum_du_cells,
    _metrics_dict,
    _population_digest,
    _ranked_population,
)
from .phase1n import (
    WalshHotspot,
    _run_bridge_arm as _run_phase1n_bridge_arm,
    _swap_walsh_delta,
    joint_du_walsh_swap_proposals,
    worst_walsh_hotspots,
)
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PlateauSwapScore:
    """Parent-local predicted effect of one swap on every tied worst Walsh peak."""

    plateau_size: int
    old_max_abs: int
    predicted_max_abs: int
    improved_count: int
    worsened_count: int
    total_abs_reduction: int


@dataclass(frozen=True, slots=True)
class MultiHotspotProposal:
    """One auditable DDT-anchored proposal scored over the full Walsh plateau."""

    sbox: SBox
    input_difference: int
    output_difference: int
    hotspot_count: int
    hotspot_positions: tuple[int, ...]
    plateau_size: int
    anchor_a: int
    anchor_b: int
    score: PlateauSwapScore
    fallback: bool = False


def walsh_maximum_plateau(sbox: Sequence[int]) -> tuple[WalshHotspot, ...]:
    """Return all non-trivial Walsh coefficients tied at the parent maximum."""

    return worst_walsh_hotspots(sbox)


def score_swap_on_walsh_plateau(
    sbox: Sequence[int],
    left: int,
    right: int,
    plateau: Sequence[WalshHotspot] | None = None,
) -> PlateauSwapScore:
    """Predict a swap's effect using exact two-position deltas on the parent plateau."""

    frozen = validate_sbox(sbox)
    if left == right or not (0 <= left < 256 and 0 <= right < 256):
        raise ValueError("swap endpoints must be distinct values in [0, 255]")
    active = tuple(plateau) if plateau is not None else walsh_maximum_plateau(frozen)
    if not active:
        raise ValueError("Walsh plateau must not be empty")

    old_abs = tuple(abs(item.coefficient) for item in active)
    old_max = max(old_abs)
    predicted: list[int] = []
    for item in active:
        delta = _swap_walsh_delta(
            frozen,
            left=left,
            right=right,
            input_mask=item.input_mask,
            output_mask=item.output_mask,
        )
        predicted.append(abs(item.coefficient + delta))

    return PlateauSwapScore(
        plateau_size=len(active),
        old_max_abs=old_max,
        predicted_max_abs=max(predicted),
        improved_count=sum(new < old for old, new in zip(old_abs, predicted)),
        worsened_count=sum(new > old for old, new in zip(old_abs, predicted)),
        total_abs_reduction=sum(old - new for old, new in zip(old_abs, predicted)),
    )


def _score_key(score: PlateauSwapScore) -> tuple[int, int, int, int]:
    return (
        -score.predicted_max_abs,
        score.improved_count,
        -score.worsened_count,
        score.total_abs_reduction,
    )


def _baseline_score(plateau: Sequence[WalshHotspot]) -> PlateauSwapScore:
    maximum = max(abs(item.coefficient) for item in plateau)
    return PlateauSwapScore(len(plateau), maximum, maximum, 0, 0, 0)


def _wrap_fallback(parent: SBox, proposal, plateau: tuple[WalshHotspot, ...]) -> MultiHotspotProposal:
    score = score_swap_on_walsh_plateau(
        parent, proposal.anchor_a, proposal.anchor_b, plateau
    )
    return MultiHotspotProposal(
        sbox=proposal.sbox,
        input_difference=proposal.input_difference,
        output_difference=proposal.output_difference,
        hotspot_count=proposal.hotspot_count,
        hotspot_positions=proposal.hotspot_positions,
        plateau_size=len(plateau),
        anchor_a=proposal.anchor_a,
        anchor_b=proposal.anchor_b,
        score=score,
        fallback=True,
    )


def multihotspot_walsh_swap_proposals(
    sbox: Sequence[int],
    rng: random.Random,
    *,
    count: int,
) -> tuple[MultiHotspotProposal, ...]:
    """Generate unique DDT-anchored swaps that improve the full parent Walsh plateau.

    Candidate-wide post-swap metrics are never computed here.  The only candidate
    information used is the exact two-position Walsh delta implied by the swap.
    """

    frozen = validate_sbox(sbox)
    if not is_bijective(frozen):
        raise ValueError("multi-hotspot proposals require a bijective S-Box")
    if count < 1:
        raise ValueError("count must be >= 1")

    _maximum, cells, _table = _maximum_du_cells(frozen)
    positions_by_cell = {
        cell: _cell_positions(frozen, cell[0], cell[1]) for cell in cells
    }
    plateau = walsh_maximum_plateau(frozen)
    baseline = _baseline_score(plateau)
    baseline_key = _score_key(baseline)

    best_by_candidate: dict[SBox, MultiHotspotProposal] = {}
    attempts = max(512, count * 1024)
    for _ in range(attempts):
        input_difference, output_difference = rng.choice(cells)
        positions = positions_by_cell[(input_difference, output_difference)]
        if not positions:
            continue
        anchor_a = rng.choice(positions)
        anchor_b = rng.randrange(256)
        if anchor_a == anchor_b:
            continue
        score = score_swap_on_walsh_plateau(
            frozen, anchor_a, anchor_b, plateau
        )
        if _score_key(score) <= baseline_key or score.total_abs_reduction <= 0:
            continue
        values = list(frozen)
        values[anchor_a], values[anchor_b] = values[anchor_b], values[anchor_a]
        candidate = tuple(values)
        record = MultiHotspotProposal(
            sbox=candidate,
            input_difference=input_difference,
            output_difference=output_difference,
            hotspot_count=len(positions),
            hotspot_positions=positions,
            plateau_size=len(plateau),
            anchor_a=anchor_a,
            anchor_b=anchor_b,
            score=score,
            fallback=False,
        )
        previous = best_by_candidate.get(candidate)
        if previous is None or _score_key(record.score) > _score_key(previous.score):
            best_by_candidate[candidate] = record

    guided = sorted(
        best_by_candidate.values(),
        key=lambda item: (
            _score_key(item.score),
            -item.input_difference,
            -item.output_difference,
            -item.anchor_a,
            -item.anchor_b,
        ),
        reverse=True,
    )[:count]
    proposals = list(guided)
    seen = {item.sbox for item in proposals}

    while len(proposals) < count:
        needed = count - len(proposals)
        fallback_batch = joint_du_walsh_swap_proposals(frozen, rng, count=needed)
        added = 0
        for item in fallback_batch:
            if item.sbox in seen:
                continue
            wrapped = _wrap_fallback(frozen, item, plateau)
            seen.add(item.sbox)
            proposals.append(wrapped)
            added += 1
            if len(proposals) == count:
                break
        if added == 0:
            raise RuntimeError("unable to fill unique Phase 1O proposal batch")

    return tuple(proposals)


def _proposal_audit_digest(records: Sequence[MultiHotspotProposal]) -> str:
    serializable = [
        {
            "input_difference": item.input_difference,
            "output_difference": item.output_difference,
            "hotspot_count": item.hotspot_count,
            "plateau_size": item.plateau_size,
            "anchor_a": item.anchor_a,
            "anchor_b": item.anchor_b,
            "fallback": item.fallback,
            "score": {
                "old_max_abs": item.score.old_max_abs,
                "predicted_max_abs": item.score.predicted_max_abs,
                "improved_count": item.score.improved_count,
                "worsened_count": item.score.worsened_count,
                "total_abs_reduction": item.score.total_abs_reduction,
            },
            "fingerprint": fingerprint_sbox(item.sbox),
        }
        for item in records
    ]
    blob = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _collect_unique_batch(
    parents: Sequence[SBox],
    rng: random.Random,
    *,
    seen_ever: set[SBox],
) -> tuple[list[SBox], list[MultiHotspotProposal]]:
    batch: list[SBox] = []
    audit: list[MultiHotspotProposal] = []
    parent_index = 0
    stalled = 0
    while len(batch) < PROPOSALS_PER_GENERATION:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(batch))
        generated = multihotspot_walsh_swap_proposals(parent, rng, count=needed)
        added = 0
        for record in generated:
            if record.sbox in seen_ever:
                continue
            seen_ever.add(record.sbox)
            batch.append(record.sbox)
            audit.append(record)
            added += 1
            if len(batch) == PROPOSALS_PER_GENERATION:
                break
        stalled = stalled + 1 if added == 0 else 0
        if stalled > 512:
            raise RuntimeError("unable to generate globally unique Phase 1O proposals")
    return batch, audit


def _to_classical(metrics: ITOAwareMetrics) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=metrics.nonlinearity,
        differential_uniformity=metrics.differential_uniformity,
        max_linear_correlation=metrics.max_linear_correlation,
        sac_score=metrics.sac_score,
        algebraic_degree=metrics.algebraic_degree,
        fingerprint=metrics.fingerprint,
    )


def _run_multihotspot_arm(
    initial: tuple[SBox, ...], *, seed: int, initial_digest: str
) -> dict[str, Any]:
    constraints = HardConstraints()
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    rng = random.Random(seed)
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    audit_records: list[MultiHotspotProposal] = []

    for candidate in population:
        ledger.evaluate(candidate)

    def with_ito(candidate: SBox) -> ITOAwareMetrics:
        cached = ito_cache.get(candidate)
        if cached is None:
            cached = ITOAwareMetrics.from_classical(
                ledger.evaluate(candidate),
                improved_transparency_order_value=improved_transparency_order(candidate),
            )
            ito_cache[candidate] = cached
        return cached

    for _generation in range(GENERATIONS):
        ranked = _ranked_population(population, ledger, constraints)
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_metrics = tuple(with_ito(candidate) for candidate in shortlist)
        parent_indices = select_nsga2(shortlist_metrics, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in parent_indices)
        proposals, audit = _collect_unique_batch(parents, rng, seen_ever=seen_ever)
        audit_records.extend(audit)
        for proposal in proposals:
            ledger.evaluate(proposal)
        population = _ranked_population(
            [*population, *proposals], ledger, constraints
        )[:POPULATION_SIZE]

    if ledger.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Phase 1O budget drift: {ledger.evaluations} != {CLASSICAL_BUDGET}"
        )

    ranked = _ranked_population(population, ledger, constraints)
    final_shortlist = tuple(ranked[:SHORTLIST_SIZE])
    final_metrics = tuple(with_ito(candidate) for candidate in final_shortlist)
    front_indices = non_dominated_sort(final_metrics)[0]
    terminal = tuple(final_metrics[index] for index in front_indices)
    best = max(
        terminal,
        key=lambda item: feasibility_rank(_to_classical(item), constraints),
    )
    protected = sum(
        item.nonlinearity >= 100
        and item.max_linear_correlation <= 64
        and item.algebraic_degree >= 6
        for item in terminal
    )
    joint = sum(
        item.differential_uniformity <= 8
        and item.nonlinearity >= 100
        and item.max_linear_correlation <= 64
        and item.algebraic_degree >= 6
        for item in terminal
    )

    return {
        "proposal_mode": "multihotspot",
        "terminal_set_size": len(terminal),
        "best_du": min(item.differential_uniformity for item in terminal),
        "du8_count": sum(item.differential_uniformity <= 8 for item in terminal),
        "protected_classical_count": protected,
        "joint_target_count": joint,
        "hard_admissible_count": sum(
            is_admissible(_to_classical(item), constraints) for item in terminal
        ),
        "structural_target_count": sum(
            structural_gate_count(_to_classical(item), constraints) == 4
            for item in terminal
        ),
        "min_ito": min(item.improved_transparency_order for item in terminal),
        "best_feasibility_metrics": _metrics_dict(best),
        "terminal_metrics": [_metrics_dict(item) for item in terminal],
        "classical_evaluations": ledger.evaluations,
        "ito_evaluations": len(ito_cache),
        "initial_population_digest_sha256": initial_digest,
        "proposal_audit_sha256": _proposal_audit_digest(audit_records),
        "multihotspot_guided_proposals": sum(not item.fallback for item in audit_records),
        "fallback_proposals": sum(item.fallback for item in audit_records),
    }


def _run_seed_once(seed: int) -> dict[str, Any]:
    constraints = HardConstraints()
    initial = _initial_population(seed)
    digest = _population_digest(initial)
    arm_a = _run_multihotspot_arm(initial, seed=seed, initial_digest=digest)
    arm_b = _run_phase1n_bridge_arm(
        initial, seed=seed, mode="joint", initial_digest=digest
    )

    ga_config = EvolutionConfig(seed=seed, **GA_CONFIG_KWARGS)
    ga_evaluator, ga_cache = make_classical_evaluator(
        constraints, ranking_mode="feasibility_first"
    )
    arm_c_result = evolve_permutations(
        ga_evaluator, ga_config, initial_population=initial
    )
    if arm_c_result.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError("Phase 1O historical comparator budget drift")
    arm_c_classical = ga_cache[arm_c_result.best_sbox]
    arm_c_ito = _classical_to_ito(arm_c_classical, arm_c_result.best_sbox)

    return {
        "phase": "1O",
        "seed": seed,
        "initial_population_digest_sha256": digest,
        "arm_a": arm_a,
        "arm_b": arm_b,
        "arm_c": {
            "best_feasibility_metrics": _metrics_dict(arm_c_ito),
            "hard_admissible_count": int(is_admissible(arm_c_classical, constraints)),
            "structural_target_count": int(
                structural_gate_count(arm_c_classical, constraints) == 4
            ),
            "classical_evaluations": arm_c_result.evaluations,
            "ito_evaluations": 1,
            "initial_population_digest_sha256": digest,
        },
        "neural_oracle_executed": False,
    }


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_seed(seed: int) -> dict[str, Any]:
    validate_seed_registry()
    if seed not in PHASE1O_DEV_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase 1O development seed")
    first = _run_seed_once(seed)
    second = _run_seed_once(seed)
    first_bytes = _canonical_payload(first)
    if first_bytes != _canonical_payload(second):
        raise RuntimeError("Phase 1O fixed-seed scientific payload is not deterministic")
    return {
        **first,
        "scientific_payload_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "deterministic_payload_match": True,
    }


def aggregate_development(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(results) != 5:
        raise ValueError("Phase 1O development requires exactly five seed results")

    joint_a = sum(item["arm_a"]["joint_target_count"] for item in results)
    joint_b = sum(item["arm_b"]["joint_target_count"] for item in results)
    joint_seed_successes_a = sum(item["arm_a"]["joint_target_count"] > 0 for item in results)
    du8_seed_successes_a = sum(item["arm_a"]["du8_count"] > 0 for item in results)
    du8_seed_successes_b = sum(item["arm_b"]["du8_count"] > 0 for item in results)
    best_du_a = [item["arm_a"]["best_du"] for item in results]
    best_du_b = [item["arm_b"]["best_du"] for item in results]
    best_du_wins = sum(a < b for a, b in zip(best_du_a, best_du_b))
    best_du_losses = sum(a > b for a, b in zip(best_du_a, best_du_b))
    best_du_ties = len(results) - best_du_wins - best_du_losses
    median_best_du_a = median(best_du_a)
    median_best_du_b = median(best_du_b)
    protected_a = sum(item["arm_a"]["protected_classical_count"] for item in results)
    protected_b = sum(item["arm_b"]["protected_classical_count"] for item in results)
    median_min_ito_a = median(item["arm_a"]["min_ito"] for item in results)
    median_min_ito_b = median(item["arm_b"]["min_ito"] for item in results)

    checks = {
        "joint_aggregate_advantage": joint_a > joint_b,
        "joint_seed_successes_ge_2": joint_seed_successes_a >= 2,
        "du_bridge_nonregression": (
            du8_seed_successes_a >= du8_seed_successes_b
            and best_du_wins >= best_du_losses
        ),
        "median_best_du_nonregression": median_best_du_a <= median_best_du_b,
        "classical_protection": protected_a >= protected_b,
        "ito_noninferiority": (
            median_min_ito_a <= median_min_ito_b + ITO_NONINFERIORITY_TOLERANCE
        ),
        "exact_classical_budgets": all(
            item[arm]["classical_evaluations"] == CLASSICAL_BUDGET
            for item in results
            for arm in ("arm_a", "arm_b", "arm_c")
        ),
        "same_initial_population": all(
            item["initial_population_digest_sha256"]
            == item["arm_a"]["initial_population_digest_sha256"]
            == item["arm_b"]["initial_population_digest_sha256"]
            == item["arm_c"]["initial_population_digest_sha256"]
            for item in results
        ),
        "deterministic_rerun": all(
            item.get("deterministic_payload_match", False) for item in results
        ),
        "fresh_seed_registry_exact": tuple(sorted(item["seed"] for item in results))
        == tuple(sorted(PHASE1O_DEV_SEEDS)),
        "neural_oracle_blocked": all(
            not item.get("neural_oracle_executed", False) for item in results
        ),
    }

    return {
        "summary": {
            "joint_target_count_a": joint_a,
            "joint_target_count_b": joint_b,
            "joint_seed_successes_a": joint_seed_successes_a,
            "du8_seed_successes_a": du8_seed_successes_a,
            "du8_seed_successes_b": du8_seed_successes_b,
            "median_best_du_a": median_best_du_a,
            "median_best_du_b": median_best_du_b,
            "best_du_wins": best_du_wins,
            "best_du_losses": best_du_losses,
            "best_du_ties": best_du_ties,
            "protected_classical_count_a": protected_a,
            "protected_classical_count_b": protected_b,
            "median_min_ito_a": median_min_ito_a,
            "median_min_ito_b": median_min_ito_b,
        },
        "development_checks": checks,
        "verdict": "phase1o_dev_pass" if all(checks.values()) else "phase1o_dev_fail",
    }


def aggregate_files(paths: Sequence[Path]) -> dict[str, Any]:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    return {"per_seed": results, **aggregate_development(results)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aggregate-files", type=Path, nargs="+")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.aggregate_files:
        payload = aggregate_files(args.aggregate_files)
    else:
        if not args.seeds:
            raise SystemExit("--seeds is required unless --aggregate-files is used")
        runs = [run_seed(seed) for seed in args.seeds]
        payload = runs[0] if len(runs) == 1 else {"per_seed": runs, **aggregate_development(runs)}
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
