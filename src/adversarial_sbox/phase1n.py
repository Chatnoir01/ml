"""Phase 1N: matched-budget joint DU / nonlinearity bridge experiment.

The scientific protocol is frozen in ``research/PHASE1N_PROTOCOL.md``. This
module contains no neural code and cannot enable the neural oracle.
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

from .cryptoshield import (
    improved_transparency_order,
    is_bijective,
    linear_approximation_table,
    validate_sbox,
)
from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    structural_gate_count,
)
from .experiment_seeds import PHASE1N_DEV_SEEDS, validate_seed_registry
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
    du_hotspot_swap_proposals,
)

SBox = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class WalshHotspot:
    """One current maximum-absolute Walsh coefficient for a nonzero component."""

    input_mask: int
    output_mask: int
    coefficient: int


@dataclass(frozen=True, slots=True)
class JointDUWalshProposal:
    """Auditable one-swap proposal anchored on DU and guided by Walsh structure."""

    sbox: SBox
    input_difference: int
    output_difference: int
    hotspot_count: int
    hotspot_positions: tuple[int, ...]
    input_mask: int
    output_mask: int
    old_walsh_coefficient: int
    predicted_walsh_delta: int
    anchor_a: int
    anchor_b: int
    fallback: bool = False


def _parity(value: int) -> int:
    return value.bit_count() & 1


def worst_walsh_hotspots(sbox: Sequence[int]) -> tuple[WalshHotspot, ...]:
    """Return every worst absolute Walsh coefficient for nonzero output masks."""

    frozen = validate_sbox(sbox)
    table = linear_approximation_table(frozen)
    best = max(
        abs(table[input_mask][output_mask])
        for input_mask in range(256)
        for output_mask in range(1, 256)
    )
    return tuple(
        WalshHotspot(input_mask, output_mask, table[input_mask][output_mask])
        for input_mask in range(256)
        for output_mask in range(1, 256)
        if abs(table[input_mask][output_mask]) == best
    )


def _walsh_term(input_mask: int, output_mask: int, x: int, y: int) -> int:
    bit = _parity(input_mask & x) ^ _parity(output_mask & y)
    return 1 if bit == 0 else -1


def _swap_walsh_delta(
    sbox: SBox,
    *,
    left: int,
    right: int,
    input_mask: int,
    output_mask: int,
) -> int:
    left_value = sbox[left]
    right_value = sbox[right]
    old_sum = _walsh_term(input_mask, output_mask, left, left_value) + _walsh_term(
        input_mask, output_mask, right, right_value
    )
    new_sum = _walsh_term(input_mask, output_mask, left, right_value) + _walsh_term(
        input_mask, output_mask, right, left_value
    )
    return new_sum - old_sum


def _swap_at(sbox: SBox, left: int, right: int) -> SBox:
    values = list(sbox)
    values[left], values[right] = values[right], values[left]
    return tuple(values)


def joint_du_walsh_swap_proposals(
    sbox: Sequence[int],
    rng: random.Random,
    *,
    count: int,
) -> tuple[JointDUWalshProposal, ...]:
    """Generate unique DU-hotspot swaps predicted to reduce a worst Walsh peak.

    Only the parent S-box's DDT/Walsh structure is used for proposal geometry.
    No proposed candidate receives a post-swap classical, ITO, or neural score
    here; callers must charge any inspected candidate through the full ledger.
    """

    frozen = validate_sbox(sbox)
    if not is_bijective(frozen):
        raise ValueError("joint DU/Walsh proposals require a bijective S-Box")
    if count < 1:
        raise ValueError("count must be >= 1")

    maximum, cells, _table = _maximum_du_cells(frozen)
    positions_by_cell = {
        cell: _cell_positions(frozen, cell[0], cell[1]) for cell in cells
    }
    walsh_hotspots = worst_walsh_hotspots(frozen)
    if not walsh_hotspots:
        raise RuntimeError("no non-trivial Walsh hotspot found")

    proposals: list[JointDUWalshProposal] = []
    seen: set[SBox] = set()
    attempts = 0
    max_attempts = max(512, count * 1024)

    while len(proposals) < count and attempts < max_attempts:
        attempts += 1
        input_difference, output_difference = rng.choice(cells)
        positions = positions_by_cell[(input_difference, output_difference)]
        if not positions:
            continue
        anchor_a = rng.choice(positions)
        anchor_b = rng.randrange(256)
        if anchor_b == anchor_a:
            continue

        walsh = rng.choice(walsh_hotspots)
        delta = _swap_walsh_delta(
            frozen,
            left=anchor_a,
            right=anchor_b,
            input_mask=walsh.input_mask,
            output_mask=walsh.output_mask,
        )
        if delta == 0:
            continue
        if abs(walsh.coefficient + delta) >= abs(walsh.coefficient):
            continue

        candidate = _swap_at(frozen, anchor_a, anchor_b)
        if candidate == frozen or candidate in seen:
            continue
        seen.add(candidate)
        proposals.append(
            JointDUWalshProposal(
                sbox=candidate,
                input_difference=input_difference,
                output_difference=output_difference,
                hotspot_count=len(positions),
                hotspot_positions=positions,
                input_mask=walsh.input_mask,
                output_mask=walsh.output_mask,
                old_walsh_coefficient=walsh.coefficient,
                predicted_walsh_delta=delta,
                anchor_a=anchor_a,
                anchor_b=anchor_b,
                fallback=False,
            )
        )

    # Frozen fallback is the Phase-1M hotspot operator. It does not receive any
    # hidden candidate score; metadata records the parent Walsh context only.
    while len(proposals) < count:
        needed = count - len(proposals)
        fallback_batch = du_hotspot_swap_proposals(frozen, rng, count=needed)
        added = 0
        for fallback in fallback_batch:
            if fallback.sbox in seen:
                continue
            walsh = rng.choice(walsh_hotspots)
            delta = _swap_walsh_delta(
                frozen,
                left=fallback.anchor_a,
                right=fallback.anchor_b,
                input_mask=walsh.input_mask,
                output_mask=walsh.output_mask,
            )
            seen.add(fallback.sbox)
            proposals.append(
                JointDUWalshProposal(
                    sbox=fallback.sbox,
                    input_difference=fallback.input_difference,
                    output_difference=fallback.output_difference,
                    hotspot_count=fallback.hotspot_count,
                    hotspot_positions=fallback.hotspot_positions,
                    input_mask=walsh.input_mask,
                    output_mask=walsh.output_mask,
                    old_walsh_coefficient=walsh.coefficient,
                    predicted_walsh_delta=delta,
                    anchor_a=fallback.anchor_a,
                    anchor_b=fallback.anchor_b,
                    fallback=True,
                )
            )
            added += 1
            if len(proposals) == count:
                break
        if added == 0:
            raise RuntimeError("unable to generate enough unique joint proposals")

    return tuple(proposals)


def _proposal_audit_digest(records: Sequence[JointDUWalshProposal]) -> str:
    serializable = [
        {
            "input_difference": record.input_difference,
            "output_difference": record.output_difference,
            "hotspot_count": record.hotspot_count,
            "input_mask": record.input_mask,
            "output_mask": record.output_mask,
            "old_walsh_coefficient": record.old_walsh_coefficient,
            "predicted_walsh_delta": record.predicted_walsh_delta,
            "anchor_a": record.anchor_a,
            "anchor_b": record.anchor_b,
            "fallback": record.fallback,
            "fingerprint": record.sbox,
        }
        for record in records
    ]
    blob = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _collect_unique_batch(
    parents: Sequence[SBox],
    rng: random.Random,
    *,
    mode: str,
    seen_ever: set[SBox],
) -> tuple[list[SBox], list[JointDUWalshProposal]]:
    if mode not in {"joint", "hotspot"}:
        raise ValueError(f"unknown proposal mode: {mode}")

    batch: list[SBox] = []
    audit: list[JointDUWalshProposal] = []
    parent_index = 0
    stalled_rounds = 0

    while len(batch) < PROPOSALS_PER_GENERATION:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(batch))

        if mode == "joint":
            generated = joint_du_walsh_swap_proposals(parent, rng, count=needed)
        else:
            hotspot_only = du_hotspot_swap_proposals(parent, rng, count=needed)
            parent_walsh = worst_walsh_hotspots(parent)
            generated = tuple(
                JointDUWalshProposal(
                    sbox=proposal.sbox,
                    input_difference=proposal.input_difference,
                    output_difference=proposal.output_difference,
                    hotspot_count=proposal.hotspot_count,
                    hotspot_positions=proposal.hotspot_positions,
                    input_mask=parent_walsh[0].input_mask,
                    output_mask=parent_walsh[0].output_mask,
                    old_walsh_coefficient=parent_walsh[0].coefficient,
                    predicted_walsh_delta=_swap_walsh_delta(
                        parent,
                        left=proposal.anchor_a,
                        right=proposal.anchor_b,
                        input_mask=parent_walsh[0].input_mask,
                        output_mask=parent_walsh[0].output_mask,
                    ),
                    anchor_a=proposal.anchor_a,
                    anchor_b=proposal.anchor_b,
                    fallback=True,
                )
                for proposal in hotspot_only
            )

        added = 0
        for record in generated:
            candidate = record.sbox
            if candidate in seen_ever:
                continue
            seen_ever.add(candidate)
            batch.append(candidate)
            if mode == "joint":
                audit.append(record)
            added += 1
            if len(batch) == PROPOSALS_PER_GENERATION:
                break

        if added == 0:
            stalled_rounds += 1
        else:
            stalled_rounds = 0
        if stalled_rounds > 512:
            raise RuntimeError("unable to generate enough globally unique proposals")

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


def _run_bridge_arm(
    initial: tuple[SBox, ...],
    *,
    seed: int,
    mode: str,
    initial_digest: str,
) -> dict[str, Any]:
    constraints = HardConstraints()
    from .evolution import evaluate_classical

    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    rng = random.Random(seed)
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    audit_records: list[JointDUWalshProposal] = []

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

        proposals, audit = _collect_unique_batch(
            parents,
            rng,
            mode=mode,
            seen_ever=seen_ever,
        )
        audit_records.extend(audit)
        for proposal in proposals:
            ledger.evaluate(proposal)

        population = _ranked_population(
            [*population, *proposals], ledger, constraints
        )[:POPULATION_SIZE]

    if ledger.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Phase 1N {mode} budget drift: {ledger.evaluations} != {CLASSICAL_BUDGET}"
        )

    ranked = _ranked_population(population, ledger, constraints)
    final_shortlist = tuple(ranked[:SHORTLIST_SIZE])
    final_metrics = tuple(with_ito(candidate) for candidate in final_shortlist)
    final_front_indices = non_dominated_sort(final_metrics)[0]
    terminal_metrics = tuple(final_metrics[index] for index in final_front_indices)

    best = max(
        terminal_metrics,
        key=lambda item: feasibility_rank(_to_classical(item), constraints),
    )
    protected = sum(
        item.nonlinearity >= 100
        and item.max_linear_correlation <= 64
        and item.algebraic_degree >= 6
        for item in terminal_metrics
    )
    joint = sum(
        item.differential_uniformity <= 8
        and item.nonlinearity >= 100
        and item.max_linear_correlation <= 64
        and item.algebraic_degree >= 6
        for item in terminal_metrics
    )
    hard_count = sum(
        is_admissible(_to_classical(item), constraints) for item in terminal_metrics
    )
    structural_count = sum(
        structural_gate_count(_to_classical(item), constraints) == 4
        for item in terminal_metrics
    )

    return {
        "proposal_mode": mode,
        "terminal_set_size": len(terminal_metrics),
        "best_du": min(item.differential_uniformity for item in terminal_metrics),
        "du8_count": sum(item.differential_uniformity <= 8 for item in terminal_metrics),
        "protected_classical_count": protected,
        "joint_target_count": joint,
        "hard_admissible_count": hard_count,
        "structural_target_count": structural_count,
        "min_ito": min(item.improved_transparency_order for item in terminal_metrics),
        "best_feasibility_metrics": _metrics_dict(best),
        "terminal_metrics": [_metrics_dict(item) for item in terminal_metrics],
        "classical_evaluations": ledger.evaluations,
        "ito_evaluations": len(ito_cache),
        "initial_population_digest_sha256": initial_digest,
        "proposal_audit_sha256": _proposal_audit_digest(audit_records),
        "joint_guided_proposals": sum(not record.fallback for record in audit_records),
        "fallback_proposals": sum(record.fallback for record in audit_records),
    }


def _run_seed_once(seed: int) -> dict[str, Any]:
    constraints = HardConstraints()
    initial = _initial_population(seed)
    digest = _population_digest(initial)

    arm_a = _run_bridge_arm(
        initial,
        seed=seed,
        mode="joint",
        initial_digest=digest,
    )
    arm_b = _run_bridge_arm(
        initial,
        seed=seed,
        mode="hotspot",
        initial_digest=digest,
    )

    ga_config = EvolutionConfig(seed=seed, **GA_CONFIG_KWARGS)
    ga_evaluator, ga_cache = make_classical_evaluator(
        constraints,
        ranking_mode="feasibility_first",
    )
    arm_c_result = evolve_permutations(
        ga_evaluator,
        ga_config,
        initial_population=initial,
    )
    if arm_c_result.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Phase 1N historical comparator budget drift: {arm_c_result.evaluations}"
        )
    arm_c_classical = ga_cache[arm_c_result.best_sbox]
    arm_c_ito = _classical_to_ito(arm_c_classical, arm_c_result.best_sbox)

    return {
        "phase": "1N",
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
    """Execute one registered Phase-1N development seed with deterministic rerun."""

    validate_seed_registry()
    if seed not in PHASE1N_DEV_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase 1N development seed")

    first = _run_seed_once(seed)
    second = _run_seed_once(seed)
    first_bytes = _canonical_payload(first)
    second_bytes = _canonical_payload(second)
    if first_bytes != second_bytes:
        raise RuntimeError("Phase 1N fixed-seed scientific payload is not deterministic")

    return {
        **first,
        "scientific_payload_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "deterministic_payload_match": True,
    }


def aggregate_development(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Apply every frozen Phase-1N development gate to exactly five results."""

    if len(results) != 5:
        raise ValueError("Phase 1N development requires exactly five seed results")

    joint_a = sum(item["arm_a"]["joint_target_count"] for item in results)
    joint_b = sum(item["arm_b"]["joint_target_count"] for item in results)
    joint_seed_successes_a = sum(
        item["arm_a"]["joint_target_count"] > 0 for item in results
    )

    du8_seed_successes_a = sum(item["arm_a"]["du8_count"] > 0 for item in results)
    du8_seed_successes_b = sum(item["arm_b"]["du8_count"] > 0 for item in results)
    best_du_a = [item["arm_a"]["best_du"] for item in results]
    best_du_b = [item["arm_b"]["best_du"] for item in results]
    median_best_du_a = median(best_du_a)
    median_best_du_b = median(best_du_b)
    best_du_wins = sum(a < b for a, b in zip(best_du_a, best_du_b))
    best_du_losses = sum(a > b for a, b in zip(best_du_a, best_du_b))
    best_du_ties = len(results) - best_du_wins - best_du_losses

    protected_a = sum(item["arm_a"]["protected_classical_count"] for item in results)
    protected_b = sum(item["arm_b"]["protected_classical_count"] for item in results)
    median_min_ito_a = median(item["arm_a"]["min_ito"] for item in results)
    median_min_ito_b = median(item["arm_b"]["min_ito"] for item in results)

    budgets_exact = all(
        item[arm]["classical_evaluations"] == CLASSICAL_BUDGET
        for item in results
        for arm in ("arm_a", "arm_b", "arm_c")
    )
    same_initial_population = all(
        item["initial_population_digest_sha256"]
        == item["arm_a"]["initial_population_digest_sha256"]
        == item["arm_b"]["initial_population_digest_sha256"]
        == item["arm_c"]["initial_population_digest_sha256"]
        for item in results
    )
    deterministic_rerun = all(
        item.get("deterministic_payload_match", False) for item in results
    )
    declared_seeds = tuple(sorted(item["seed"] for item in results))
    seed_registry_exact = declared_seeds == tuple(sorted(PHASE1N_DEV_SEEDS))
    neural_blocked = all(not item.get("neural_oracle_executed", False) for item in results)

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
            median_min_ito_a
            <= median_min_ito_b + ITO_NONINFERIORITY_TOLERANCE
        ),
        "exact_classical_budgets": budgets_exact,
        "same_initial_population": same_initial_population,
        "deterministic_rerun": deterministic_rerun,
        "fresh_seed_registry_exact": seed_registry_exact,
        "neural_oracle_blocked": neural_blocked,
    }
    passed = all(checks.values())

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
        "verdict": "phase1n_dev_pass" if passed else "phase1n_dev_fail",
    }


def aggregate_files(paths: Sequence[Path]) -> dict[str, Any]:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    aggregate = aggregate_development(results)
    return {"per_seed": results, **aggregate}


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
        payload = (
            runs[0]
            if len(runs) == 1
            else {"per_seed": runs, **aggregate_development(runs)}
        )

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
