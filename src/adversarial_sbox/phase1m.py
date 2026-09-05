"""Phase 1M: matched-budget DU-hotspot bridge experiment.

The scientific protocol is frozen in ``research/PHASE1M_PROTOCOL.md``.  This
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
from typing import Any, Callable, Iterable, Sequence

from .cryptoshield import (
    differential_distribution_table,
    improved_transparency_order,
    is_bijective,
    validate_sbox,
)
from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    evaluate_classical,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    random_sbox,
    structural_gate_count,
)
from .experiment_seeds import PHASE1M_DEV_SEEDS, validate_seed_registry
from .pareto import ITOAwareMetrics, non_dominated_sort, select_nsga2
from .phase1l import GA_CONFIG_KWARGS
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
ClassicalEvaluator = Callable[[Sequence[int]], ClassicalMetrics]

CLASSICAL_BUDGET = 340
ITO_NONINFERIORITY_TOLERANCE = 0.02
POPULATION_SIZE = 20
SHORTLIST_SIZE = 8
PARENT_COUNT = 4
PROPOSALS_PER_PARENT = 4
PROPOSALS_PER_GENERATION = PARENT_COUNT * PROPOSALS_PER_PARENT
GENERATIONS = (CLASSICAL_BUDGET - POPULATION_SIZE) // PROPOSALS_PER_GENERATION

if POPULATION_SIZE + GENERATIONS * PROPOSALS_PER_GENERATION != CLASSICAL_BUDGET:
    raise RuntimeError("Phase 1M frozen budget does not divide exactly")


@dataclass(frozen=True, slots=True)
class DUHotspotProposal:
    """One auditable bijective swap proposal anchored on a maximum-DDT hotspot."""

    sbox: SBox
    input_difference: int
    output_difference: int
    hotspot_count: int
    hotspot_positions: tuple[int, ...]
    anchor_a: int
    anchor_b: int
    fallback: bool = False


class ClassicalEvaluationLedger:
    """Cache full classical evaluations and enforce an exact unique-evaluation cap."""

    def __init__(self, evaluator: ClassicalEvaluator, *, budget: int) -> None:
        if budget < 1:
            raise ValueError("budget must be >= 1")
        self._evaluator = evaluator
        self._budget = int(budget)
        self._cache: dict[SBox, ClassicalMetrics] = {}

    @property
    def evaluations(self) -> int:
        return len(self._cache)

    @property
    def remaining(self) -> int:
        return self._budget - self.evaluations

    @property
    def cache(self) -> dict[SBox, ClassicalMetrics]:
        return self._cache

    def evaluate(self, sbox: Sequence[int]) -> ClassicalMetrics:
        frozen = validate_sbox(sbox)
        if not is_bijective(frozen):
            raise ValueError("classical ledger requires bijective S-Boxes")
        cached = self._cache.get(frozen)
        if cached is not None:
            return cached
        if self.evaluations >= self._budget:
            raise RuntimeError("classical evaluation budget exhausted")
        metrics = self._evaluator(frozen)
        self._cache[frozen] = metrics
        return metrics


def _maximum_du_cells(sbox: SBox) -> tuple[int, tuple[tuple[int, int], ...], list[list[int]]]:
    table = differential_distribution_table(sbox)
    maximum = max(max(row) for row in table[1:])
    cells = tuple(
        (input_difference, output_difference)
        for input_difference in range(1, 256)
        for output_difference, count in enumerate(table[input_difference])
        if count == maximum
    )
    if not cells:
        raise RuntimeError("no non-trivial maximum-DU cell found")
    return maximum, cells, table


def _cell_positions(sbox: SBox, input_difference: int, output_difference: int) -> tuple[int, ...]:
    return tuple(
        x
        for x in range(256)
        if sbox[x] ^ sbox[x ^ input_difference] == output_difference
    )


def _swap_at(sbox: SBox, left: int, right: int) -> SBox:
    values = list(sbox)
    values[left], values[right] = values[right], values[left]
    return tuple(values)


def du_hotspot_swap_proposals(
    sbox: Sequence[int],
    rng: random.Random,
    *,
    count: int,
) -> tuple[DUHotspotProposal, ...]:
    """Generate unique one-swap proposals anchored on maximum-DU DDT cells.

    Proposal generation itself performs no full CryptoShield or ITO evaluation.
    The caller is responsible for charging every proposal it chooses to inspect.
    """

    frozen = validate_sbox(sbox)
    if not is_bijective(frozen):
        raise ValueError("DU hotspot proposals require a bijective S-Box")
    if count < 1:
        raise ValueError("count must be >= 1")

    maximum, cells, _table = _maximum_du_cells(frozen)
    positions_by_cell = {
        cell: _cell_positions(frozen, cell[0], cell[1]) for cell in cells
    }
    if any(len(positions) != maximum for positions in positions_by_cell.values()):
        raise RuntimeError("DDT hotspot position count does not match maximum cell")

    proposals: list[DUHotspotProposal] = []
    seen: set[SBox] = set()
    attempts = 0
    max_attempts = max(64, count * 64)

    while len(proposals) < count and attempts < max_attempts:
        attempts += 1
        input_difference, output_difference = rng.choice(cells)
        positions = positions_by_cell[(input_difference, output_difference)]
        if len(positions) < 2:
            continue
        anchor_a, anchor_b = rng.sample(positions, 2)
        candidate = _swap_at(frozen, anchor_a, anchor_b)
        if candidate == frozen or candidate in seen:
            continue
        seen.add(candidate)
        proposals.append(
            DUHotspotProposal(
                sbox=candidate,
                input_difference=input_difference,
                output_difference=output_difference,
                hotspot_count=len(positions),
                hotspot_positions=positions,
                anchor_a=anchor_a,
                anchor_b=anchor_b,
                fallback=False,
            )
        )

    # A maximum cell can be narrow enough that hotspot/hotspot pairs are exhausted.
    # Preserve one hotspot anchor and widen only the second swap endpoint.
    while len(proposals) < count:
        input_difference, output_difference = rng.choice(cells)
        positions = positions_by_cell[(input_difference, output_difference)]
        anchor_a = rng.choice(positions)
        anchor_b = rng.randrange(256)
        if anchor_b == anchor_a:
            continue
        candidate = _swap_at(frozen, anchor_a, anchor_b)
        if candidate == frozen or candidate in seen:
            continue
        seen.add(candidate)
        proposals.append(
            DUHotspotProposal(
                sbox=candidate,
                input_difference=input_difference,
                output_difference=output_difference,
                hotspot_count=len(positions),
                hotspot_positions=positions,
                anchor_a=anchor_a,
                anchor_b=anchor_b,
                fallback=True,
            )
        )

    return tuple(proposals)


def _random_swap_proposals(sbox: SBox, rng: random.Random, *, count: int) -> tuple[SBox, ...]:
    proposals: list[SBox] = []
    seen: set[SBox] = set()
    while len(proposals) < count:
        left, right = rng.sample(range(256), 2)
        candidate = _swap_at(sbox, left, right)
        if candidate in seen:
            continue
        seen.add(candidate)
        proposals.append(candidate)
    return tuple(proposals)


def _initial_population(seed: int) -> tuple[SBox, ...]:
    rng = random.Random(seed)
    population: list[SBox] = []
    seen: set[SBox] = set()
    while len(population) < POPULATION_SIZE:
        candidate = random_sbox(rng)
        if candidate in seen:
            continue
        seen.add(candidate)
        population.append(candidate)
    return tuple(population)


def _population_digest(population: Sequence[Sequence[int]]) -> str:
    payload = "\n".join(fingerprint_sbox(candidate) for candidate in population)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _to_classical(metrics: ITOAwareMetrics) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=metrics.nonlinearity,
        differential_uniformity=metrics.differential_uniformity,
        max_linear_correlation=metrics.max_linear_correlation,
        sac_score=metrics.sac_score,
        algebraic_degree=metrics.algebraic_degree,
        fingerprint=metrics.fingerprint,
    )


def _metrics_dict(metrics: ITOAwareMetrics) -> dict[str, Any]:
    return {
        "nonlinearity": metrics.nonlinearity,
        "differential_uniformity": metrics.differential_uniformity,
        "max_linear_correlation": metrics.max_linear_correlation,
        "sac_score": metrics.sac_score,
        "algebraic_degree": metrics.algebraic_degree,
        "improved_transparency_order": metrics.improved_transparency_order,
        "fingerprint": metrics.fingerprint,
    }


def _classical_to_ito(metrics: ClassicalMetrics, sbox: SBox) -> ITOAwareMetrics:
    return ITOAwareMetrics.from_classical(
        metrics,
        improved_transparency_order_value=improved_transparency_order(sbox),
    )


def _ranked_population(
    population: Iterable[SBox],
    ledger: ClassicalEvaluationLedger,
    constraints: HardConstraints,
) -> list[SBox]:
    return sorted(
        population,
        key=lambda candidate: (
            feasibility_rank(ledger.evaluate(candidate), constraints),
            candidate,
        ),
        reverse=True,
    )


def _proposal_audit_digest(records: Sequence[DUHotspotProposal]) -> str:
    serializable = [
        {
            "input_difference": record.input_difference,
            "output_difference": record.output_difference,
            "hotspot_count": record.hotspot_count,
            "anchor_a": record.anchor_a,
            "anchor_b": record.anchor_b,
            "fallback": record.fallback,
            "fingerprint": fingerprint_sbox(record.sbox),
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
) -> tuple[list[SBox], list[DUHotspotProposal]]:
    if mode not in {"hotspot", "random"}:
        raise ValueError(f"unknown proposal mode: {mode}")

    batch: list[SBox] = []
    audit: list[DUHotspotProposal] = []
    parent_index = 0
    stalled_rounds = 0

    while len(batch) < PROPOSALS_PER_GENERATION:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(batch))

        if mode == "hotspot":
            generated = du_hotspot_swap_proposals(parent, rng, count=needed)
            pairs = [(proposal.sbox, proposal) for proposal in generated]
        else:
            generated_random = _random_swap_proposals(parent, rng, count=needed)
            pairs = [(candidate, None) for candidate in generated_random]

        added = 0
        for candidate, record in pairs:
            if candidate in seen_ever:
                continue
            seen_ever.add(candidate)
            batch.append(candidate)
            if record is not None:
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


def _run_bridge_arm(
    initial: tuple[SBox, ...],
    *,
    seed: int,
    mode: str,
    initial_digest: str,
) -> dict[str, Any]:
    constraints = HardConstraints()
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    rng = random.Random(seed)
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    audit_records: list[DUHotspotProposal] = []

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
            f"Phase 1M {mode} budget drift: {ledger.evaluations} != {CLASSICAL_BUDGET}"
        )

    ranked = _ranked_population(population, ledger, constraints)
    final_shortlist = tuple(ranked[:SHORTLIST_SIZE])
    final_metrics = tuple(with_ito(candidate) for candidate in final_shortlist)
    final_front_indices = non_dominated_sort(final_metrics)[0]
    terminal_sboxes = tuple(final_shortlist[index] for index in final_front_indices)
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
        "hard_admissible_count": hard_count,
        "structural_target_count": structural_count,
        "min_ito": min(item.improved_transparency_order for item in terminal_metrics),
        "best_feasibility_metrics": _metrics_dict(best),
        "terminal_metrics": [_metrics_dict(item) for item in terminal_metrics],
        "classical_evaluations": ledger.evaluations,
        "ito_evaluations": len(ito_cache),
        "initial_population_digest_sha256": initial_digest,
        "proposal_audit_sha256": _proposal_audit_digest(audit_records),
        "hotspot_proposals": len(audit_records),
        "fallback_proposals": sum(record.fallback for record in audit_records),
    }


def _run_seed_once(seed: int) -> dict[str, Any]:
    constraints = HardConstraints()
    initial = _initial_population(seed)
    digest = _population_digest(initial)

    arm_a = _run_bridge_arm(
        initial,
        seed=seed,
        mode="hotspot",
        initial_digest=digest,
    )
    arm_b = _run_bridge_arm(
        initial,
        seed=seed,
        mode="random",
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
            f"Phase 1M historical comparator budget drift: {arm_c_result.evaluations}"
        )
    arm_c_classical = ga_cache[arm_c_result.best_sbox]
    arm_c_ito = _classical_to_ito(arm_c_classical, arm_c_result.best_sbox)

    return {
        "phase": "1M",
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
    """Execute one registered Phase-1M development seed with a deterministic rerun."""

    validate_seed_registry()
    if seed not in PHASE1M_DEV_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase 1M development seed")

    first = _run_seed_once(seed)
    second = _run_seed_once(seed)
    first_bytes = _canonical_payload(first)
    second_bytes = _canonical_payload(second)
    deterministic_match = first_bytes == second_bytes
    if not deterministic_match:
        raise RuntimeError("Phase 1M fixed-seed scientific payload is not deterministic")

    return {
        **first,
        "scientific_payload_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "deterministic_payload_match": True,
    }


def aggregate_development(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Apply every frozen Phase-1M development gate to exactly five seed results."""

    if len(results) != 5:
        raise ValueError("Phase 1M development requires exactly five seed results")

    du8_a = sum(item["arm_a"]["du8_count"] for item in results)
    du8_b = sum(item["arm_b"]["du8_count"] for item in results)
    du8_seed_successes_a = sum(item["arm_a"]["du8_count"] > 0 for item in results)

    best_du_a = [item["arm_a"]["best_du"] for item in results]
    best_du_b = [item["arm_b"]["best_du"] for item in results]
    median_best_du_a = median(best_du_a)
    median_best_du_b = median(best_du_b)
    best_du_wins = sum(a < b for a, b in zip(best_du_a, best_du_b))
    best_du_losses = sum(a > b for a, b in zip(best_du_a, best_du_b))
    best_du_ties = len(results) - best_du_wins - best_du_losses
    best_du_robust = (
        median_best_du_a < median_best_du_b
        or (
            median_best_du_a == median_best_du_b
            and best_du_wins > best_du_losses
        )
    )

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
    seed_registry_exact = declared_seeds == tuple(sorted(PHASE1M_DEV_SEEDS))
    neural_blocked = all(not item.get("neural_oracle_executed", False) for item in results)

    checks = {
        "du8_aggregate_advantage": du8_a > du8_b,
        "du8_seed_successes_ge_3": du8_seed_successes_a >= 3,
        "best_du_robustness": best_du_robust,
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
            "du8_count_a": du8_a,
            "du8_count_b": du8_b,
            "du8_seed_successes_a": du8_seed_successes_a,
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
        "verdict": "phase1m_dev_pass" if passed else "phase1m_dev_fail",
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
