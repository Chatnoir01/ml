"""Phase 1L: fresh-population ITO-aware Pareto development experiment.

The protocol is frozen in ``research/PHASE1L_PROTOCOL.md`` before scientific
execution. This module contains no neural code and cannot enable the neural
oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from .cryptoshield import improved_transparency_order
from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    equivalent_random_budget,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    random_sbox,
    structural_gate_count,
)
from .experiment_seeds import PHASE1L_DEV_SEEDS, validate_seed_registry
from .pareto import (
    ITOAwareMetrics,
    StagedParetoConfig,
    dominates,
    evolve_staged_pareto,
)
from .provenance import fingerprint_sbox

POPULATION_SIZE = 20
PARETO_GENERATIONS = 20
GA_GENERATIONS = 10
SHORTLIST_SIZE = 8
PARENT_COUNT = 4
MUTATION_SWAPS = 3
CROSSOVER_RATE = 0.0
CLASSICAL_BUDGET = 340
NEUTRAL_ITO = 0.0

PARETO_CONFIG_KWARGS = {
    "population_size": POPULATION_SIZE,
    "generations": PARETO_GENERATIONS,
    "shortlist_size": SHORTLIST_SIZE,
    "parent_count": PARENT_COUNT,
    "mutation_swaps": MUTATION_SWAPS,
    "crossover_rate": CROSSOVER_RATE,
}

GA_CONFIG_KWARGS = {
    "population_size": POPULATION_SIZE,
    "generations": GA_GENERATIONS,
    "elite_count": 4,
    "tournament_size": 3,
    "mutation_swaps": MUTATION_SWAPS,
    "crossover_rate": CROSSOVER_RATE,
    "immigrant_fraction": 0.10,
    "offspring_multiplier": 2,
}


def _classical_budget_checks() -> None:
    pareto_budget = POPULATION_SIZE + PARETO_GENERATIONS * (
        POPULATION_SIZE - PARENT_COUNT
    )
    ga_budget = equivalent_random_budget(EvolutionConfig(seed=0, **GA_CONFIG_KWARGS))
    if pareto_budget != CLASSICAL_BUDGET or ga_budget != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Phase 1L frozen budget drift: pareto={pareto_budget}, ga={ga_budget}"
        )


_classical_budget_checks()


def _to_classical(metrics: ITOAwareMetrics) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=metrics.nonlinearity,
        differential_uniformity=metrics.differential_uniformity,
        max_linear_correlation=metrics.max_linear_correlation,
        sac_score=metrics.sac_score,
        algebraic_degree=metrics.algebraic_degree,
        fingerprint=metrics.fingerprint,
    )


def _with_actual_ito(metrics: ITOAwareMetrics, sbox: Sequence[int]) -> ITOAwareMetrics:
    return ITOAwareMetrics(
        nonlinearity=metrics.nonlinearity,
        differential_uniformity=metrics.differential_uniformity,
        max_linear_correlation=metrics.max_linear_correlation,
        sac_score=metrics.sac_score,
        algebraic_degree=metrics.algebraic_degree,
        improved_transparency_order=improved_transparency_order(sbox),
        fingerprint=metrics.fingerprint,
    )


def _from_classical_with_actual_ito(
    metrics: ClassicalMetrics, sbox: Sequence[int]
) -> ITOAwareMetrics:
    return ITOAwareMetrics.from_classical(
        metrics,
        improved_transparency_order_value=improved_transparency_order(sbox),
    )


def pareto_set_coverage(
    left: Sequence[ITOAwareMetrics], right: Sequence[ITOAwareMetrics]
) -> float:
    """Return directed Pareto set coverage C(left, right), without weights."""

    if not right:
        raise ValueError("right Pareto set must be non-empty")
    covered = sum(any(dominates(candidate, target) for candidate in left) for target in right)
    return covered / len(right)


def _initial_population(seed: int) -> tuple[tuple[int, ...], ...]:
    rng = random.Random(seed)
    population: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
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


def _arm_payload(
    metrics: Sequence[ITOAwareMetrics],
    *,
    constraints: HardConstraints,
    classical_evaluations: int,
    actual_ito_evaluations: int,
    selection_ito_calls: int,
) -> dict[str, Any]:
    if not metrics:
        raise RuntimeError("terminal Pareto set unexpectedly empty")

    best = max(
        metrics,
        key=lambda item: feasibility_rank(_to_classical(item), constraints),
    )
    hard_count = sum(is_admissible(_to_classical(item), constraints) for item in metrics)
    structural_count = sum(
        structural_gate_count(_to_classical(item), constraints) == 4 for item in metrics
    )

    return {
        "terminal_set_size": len(metrics),
        "min_ito": min(item.improved_transparency_order for item in metrics),
        "hard_admissible_count": hard_count,
        "structural_target_count": structural_count,
        "best_feasibility_metrics": _metrics_dict(best),
        "terminal_metrics": [_metrics_dict(item) for item in metrics],
        "classical_evaluations": classical_evaluations,
        "actual_ito_evaluations": actual_ito_evaluations,
        "selection_ito_calls": selection_ito_calls,
    }


def run_seed(seed: int) -> dict[str, Any]:
    """Execute the three frozen Phase-1L arms for one fresh development seed."""

    validate_seed_registry()
    if seed not in PHASE1L_DEV_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase 1L development seed")

    constraints = HardConstraints()
    initial = _initial_population(seed)
    digest = _population_digest(initial)

    pareto_config = StagedParetoConfig(seed=seed, **PARETO_CONFIG_KWARGS)

    arm_a_result = evolve_staged_pareto(
        pareto_config,
        constraints=constraints,
        initial_population=initial,
    )
    arm_a_metrics = tuple(arm_a_result.pareto_metrics)

    arm_b_result = evolve_staged_pareto(
        pareto_config,
        constraints=constraints,
        initial_population=initial,
        ito_evaluator=lambda _candidate: NEUTRAL_ITO,
    )
    arm_b_metrics = tuple(
        _with_actual_ito(metrics, sbox)
        for sbox, metrics in zip(
            arm_b_result.pareto_sboxes,
            arm_b_result.pareto_metrics,
            strict=True,
        )
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
    arm_c_classical = ga_cache[arm_c_result.best_sbox]
    arm_c_metrics = _from_classical_with_actual_ito(
        arm_c_classical,
        arm_c_result.best_sbox,
    )

    if arm_a_result.classical_evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Arm A classical budget drift: {arm_a_result.classical_evaluations}"
        )
    if arm_b_result.classical_evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Arm B classical budget drift: {arm_b_result.classical_evaluations}"
        )
    if arm_c_result.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(f"Arm C classical budget drift: {arm_c_result.evaluations}")

    coverage_a_b = pareto_set_coverage(arm_a_metrics, arm_b_metrics)
    coverage_b_a = pareto_set_coverage(arm_b_metrics, arm_a_metrics)

    return {
        "phase": "1L",
        "seed": seed,
        "initial_population_digest_sha256": digest,
        "coverage_a_b": coverage_a_b,
        "coverage_b_a": coverage_b_a,
        "coverage_outcome": (
            "a_win"
            if coverage_a_b > coverage_b_a
            else "a_loss"
            if coverage_b_a > coverage_a_b
            else "tie"
        ),
        "arm_a": _arm_payload(
            arm_a_metrics,
            constraints=constraints,
            classical_evaluations=arm_a_result.classical_evaluations,
            actual_ito_evaluations=arm_a_result.ito_evaluations,
            selection_ito_calls=arm_a_result.ito_evaluations,
        ),
        "arm_b": _arm_payload(
            arm_b_metrics,
            constraints=constraints,
            classical_evaluations=arm_b_result.classical_evaluations,
            actual_ito_evaluations=len(arm_b_metrics),
            selection_ito_calls=arm_b_result.ito_evaluations,
        ),
        "arm_c": {
            "best_feasibility_metrics": _metrics_dict(arm_c_metrics),
            "hard_admissible_count": int(
                is_admissible(arm_c_classical, constraints)
            ),
            "structural_target_count": int(
                structural_gate_count(arm_c_classical, constraints) == 4
            ),
            "classical_evaluations": arm_c_result.evaluations,
            "actual_ito_evaluations": 1,
        },
        "neural_oracle_executed": False,
    }


def aggregate_development(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the frozen five-seed development experiment and apply its gate."""

    if len(results) != 5:
        raise ValueError("Phase 1L development requires exactly five seed results")

    wins = sum(item["coverage_a_b"] > item["coverage_b_a"] for item in results)
    losses = sum(item["coverage_a_b"] < item["coverage_b_a"] for item in results)
    ties = len(results) - wins - losses

    median_a_b = median(item["coverage_a_b"] for item in results)
    median_b_a = median(item["coverage_b_a"] for item in results)
    median_min_ito_a = median(item["arm_a"]["min_ito"] for item in results)
    median_min_ito_b = median(item["arm_b"]["min_ito"] for item in results)

    hard_a = sum(item["arm_a"]["hard_admissible_count"] for item in results)
    hard_b = sum(item["arm_b"]["hard_admissible_count"] for item in results)
    structural_a = sum(
        item["arm_a"]["structural_target_count"] for item in results
    )
    structural_b = sum(
        item["arm_b"]["structural_target_count"] for item in results
    )

    budgets_exact = all(
        item[arm]["classical_evaluations"] == CLASSICAL_BUDGET
        for item in results
        for arm in ("arm_a", "arm_b", "arm_c")
    )
    declared_seeds = tuple(
        item["seed"] for item in results if "seed" in item
    )
    seed_registry_exact = (
        True
        if not declared_seeds
        else tuple(sorted(declared_seeds)) == tuple(sorted(PHASE1L_DEV_SEEDS))
    )
    neural_blocked = all(not item.get("neural_oracle_executed", False) for item in results)

    checks = {
        "coverage_wins_gt_losses": wins > losses,
        "median_coverage_a_gt_b": median_a_b > median_b_a,
        "median_min_ito_a_lt_b": median_min_ito_a < median_min_ito_b,
        "hard_admissible_a_ge_b": hard_a >= hard_b,
        "structural_target_a_ge_b": structural_a >= structural_b,
        "exact_classical_budgets": budgets_exact,
        "fresh_seed_registry_exact": seed_registry_exact,
        "neural_oracle_blocked": neural_blocked,
    }
    passed = all(checks.values())

    return {
        "summary": {
            "coverage_wins": wins,
            "coverage_losses": losses,
            "coverage_ties": ties,
            "median_coverage_a_b": median_a_b,
            "median_coverage_b_a": median_b_a,
            "median_min_ito_a": median_min_ito_a,
            "median_min_ito_b": median_min_ito_b,
            "hard_admissible_a": hard_a,
            "hard_admissible_b": hard_b,
            "structural_target_a": structural_a,
            "structural_target_b": structural_b,
        },
        "development_checks": checks,
        "verdict": "phase1l_dev_pass" if passed else "phase1l_dev_fail",
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
        payload = runs[0] if len(runs) == 1 else {"per_seed": runs, **aggregate_development(runs)}

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
