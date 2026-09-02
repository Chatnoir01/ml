"""Frozen Phase 1H plateau-directed warm-start confirmation.

No scientific tuning knobs are exposed.  The selected Phase-1H development
configuration (ties panel, proposal pool 96, cycle-4, beam 8, 600 full fitness
evaluations) is evaluated on exactly the nine preregistered reserved seeds against
the existing equal-budget strict combined-hotspot comparator.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from math import comb
from pathlib import Path
import statistics
from typing import Any

from .evolution import HardConstraints, is_admissible
from .experiment_seeds import PHASE1H_CONFIRM_RESERVED_SEEDS
from .phase1d import (
    EXPECTED_PHASE1B_FINGERPRINT,
    continuation_rank,
    reproduce_phase1b_frontier_candidate,
)
from .phase1e import guided_adaptive_search
from .phase1h import plateau_directed_search, structural_target

CONFIRM_PANEL_MODE = "ties"
CONFIRM_PROPOSAL_POOL = 96
CONFIRM_CYCLE_LENGTH = 4
CONFIRM_BEAM_WIDTH = 8
CONFIRM_EVALUATIONS = 600
COMPARATOR_SEED_XOR = 0x1A1A1A1A
CONFIRM_SEEDS = tuple(PHASE1H_CONFIRM_RESERVED_SEEDS)


def exact_one_sided_sign_p(directed_wins: int, comparator_wins: int) -> float:
    """Exact one-sided sign-test tail for a directed superiority alternative."""

    if directed_wins < 0 or comparator_wins < 0:
        raise ValueError("win counts must be non-negative")
    trials = directed_wins + comparator_wins
    if trials == 0 or directed_wins <= comparator_wins:
        return 1.0
    numerator = sum(comb(trials, k) for k in range(directed_wins, trials + 1))
    return numerator / (2**trials)


def validate_confirmation_seed(seed: int) -> None:
    if seed not in CONFIRM_SEEDS:
        raise ValueError(
            f"seed {seed} is not in the frozen Phase-1H confirmation registry"
        )


def _metrics_dict_target(metrics_dict: dict[str, Any], constraints: HardConstraints) -> bool:
    return (
        int(metrics_dict["nonlinearity"]) >= constraints.min_nonlinearity
        and int(metrics_dict["differential_uniformity"])
        <= constraints.max_differential_uniformity
        and int(metrics_dict["max_linear_correlation"])
        <= constraints.max_linear_correlation
        and int(metrics_dict["algebraic_degree"]) >= constraints.min_algebraic_degree
    )


def run_one(seed: int) -> dict[str, Any]:
    """Run one frozen directed/comparator confirmation pair."""

    validate_confirmation_seed(seed)
    start, start_metrics = reproduce_phase1b_frontier_candidate()
    if (
        start_metrics.fingerprint != EXPECTED_PHASE1B_FINGERPRINT
        or start_metrics.nonlinearity != 98
        or start_metrics.differential_uniformity != 8
        or start_metrics.max_linear_correlation != 60
        or start_metrics.algebraic_degree != 7
        or start_metrics.sac_score != 0.501708984375
    ):
        raise RuntimeError("Phase-1H confirmation warm-start provenance mismatch")

    constraints = HardConstraints()
    directed = plateau_directed_search(
        start,
        seed=seed,
        evaluations=CONFIRM_EVALUATIONS,
        proposal_pool=CONFIRM_PROPOSAL_POOL,
        panel_mode=CONFIRM_PANEL_MODE,
        beam_width=CONFIRM_BEAM_WIDTH,
        constraints=constraints,
    )
    comparator = guided_adaptive_search(
        start,
        seed=seed ^ COMPARATOR_SEED_XOR,
        evaluations=CONFIRM_EVALUATIONS,
        beam_width=CONFIRM_BEAM_WIDTH,
        cycle_length=CONFIRM_CYCLE_LENGTH,
        guidance="combined",
        constraints=constraints,
    )

    if directed["evaluations"] != CONFIRM_EVALUATIONS:
        raise RuntimeError("directed confirmation budget mismatch")
    if comparator["evaluations"] != CONFIRM_EVALUATIONS:
        raise RuntimeError("comparator confirmation budget mismatch")

    directed_metrics = directed["best_metrics"]
    comparator_metrics = comparator["best_metrics"]
    directed_target = _metrics_dict_target(directed_metrics, constraints)
    comparator_target = _metrics_dict_target(comparator_metrics, constraints)

    directed_rank = tuple(directed["best_rank"])
    comparator_rank = tuple(comparator["best_rank"])
    outcome = (
        "directed"
        if directed_rank > comparator_rank
        else "comparator"
        if directed_rank < comparator_rank
        else "tie"
    )

    return {
        "schema_version": 1,
        "experiment": "phase1h_plateau_directed_confirmation_pair",
        "scientific_status": "warm_start_operator_confirmation_not_global_gate1",
        "seed": seed,
        "configuration": {
            "panel_mode": CONFIRM_PANEL_MODE,
            "proposal_pool": CONFIRM_PROPOSAL_POOL,
            "cycle_length": CONFIRM_CYCLE_LENGTH,
            "beam_width": CONFIRM_BEAM_WIDTH,
            "evaluations_each": CONFIRM_EVALUATIONS,
            "comparator": "phase1e_combined_cycle4_strict",
        },
        "historical_start_metrics": asdict(start_metrics),
        "directed": directed,
        "comparator": comparator,
        "directed_target": directed_target,
        "comparator_target": comparator_target,
        "directed_admissible": bool(directed["found_admissible"]),
        "comparator_admissible": bool(comparator["found_admissible"]),
        "outcome": outcome,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if tuple(row["seed"] for row in rows) != CONFIRM_SEEDS:
        raise ValueError("confirmation rows must use the exact frozen seed order")

    directed_admissible = sum(row["directed_admissible"] for row in rows)
    comparator_admissible = sum(row["comparator_admissible"] for row in rows)
    directed_target = sum(row["directed_target"] for row in rows)
    comparator_target = sum(row["comparator_target"] for row in rows)
    directed_wins = sum(row["outcome"] == "directed" for row in rows)
    comparator_wins = sum(row["outcome"] == "comparator" for row in rows)
    ties = sum(row["outcome"] == "tie" for row in rows)
    sign_p = exact_one_sided_sign_p(directed_wins, comparator_wins)

    def median(metric: str) -> float:
        return float(
            statistics.median(row["directed"]["best_metrics"][metric] for row in rows)
        )

    median_nl = median("nonlinearity")
    median_du = median("differential_uniformity")
    median_corr = median("max_linear_correlation")
    exact_budgets = all(
        row["directed"]["evaluations"] == CONFIRM_EVALUATIONS
        and row["comparator"]["evaluations"] == CONFIRM_EVALUATIONS
        and row["historical_start_metrics"]["fingerprint"]
        == EXPECTED_PHASE1B_FINGERPRINT
        for row in rows
    )

    checks = {
        "directed_admissible_at_least_5_of_9": directed_admissible >= 5,
        "directed_target_at_least_5_of_9": directed_target >= 5,
        "directed_admissible_strictly_beats_comparator": directed_admissible
        > comparator_admissible,
        "directed_target_strictly_beats_comparator": directed_target > comparator_target,
        "directed_wins_strictly_exceed_comparator": directed_wins > comparator_wins,
        "one_sided_sign_p_below_0_05": sign_p < 0.05,
        "median_directed_nonlinearity_at_least_100": median_nl >= 100,
        "median_directed_du_at_most_8": median_du <= 8,
        "median_directed_max_corr_at_most_56": median_corr <= 56,
        "exact_budgets_and_provenance": exact_budgets,
    }
    passed = all(checks.values())

    return {
        "directed_admissible_runs": directed_admissible,
        "comparator_admissible_runs": comparator_admissible,
        "directed_target_runs": directed_target,
        "comparator_target_runs": comparator_target,
        "directed_wins": directed_wins,
        "comparator_wins": comparator_wins,
        "ties": ties,
        "non_tied_pairs": directed_wins + comparator_wins,
        "exact_one_sided_sign_p": sign_p,
        "median_nonlinearity_directed": median_nl,
        "median_du_directed": median_du,
        "median_max_corr_directed": median_corr,
        "checks": checks,
        "verdict": "warm_start_confirm_pass" if passed else "warm_start_confirm_fail",
        "global_gate1": "red",
        "neural_oracle": "blocked",
    }


def run_confirmation() -> dict[str, Any]:
    rows = [run_one(seed) for seed in CONFIRM_SEEDS]
    summary = aggregate(rows)
    return {
        "schema_version": 1,
        "experiment": "phase1h_plateau_directed_confirmation",
        "scientific_status": "warm_start_operator_confirmation_not_global_gate1",
        "configuration": {
            "panel_mode": CONFIRM_PANEL_MODE,
            "proposal_pool": CONFIRM_PROPOSAL_POOL,
            "cycle_length": CONFIRM_CYCLE_LENGTH,
            "beam_width": CONFIRM_BEAM_WIDTH,
            "evaluations_each": CONFIRM_EVALUATIONS,
            "seeds": list(CONFIRM_SEEDS),
            "comparator_seed_xor": COMPARATOR_SEED_XOR,
        },
        "summary": summary,
        "runs": rows,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_confirmation()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
