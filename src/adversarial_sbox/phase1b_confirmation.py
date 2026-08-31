"""Preregistered Phase-1B V2 confirmation.

The configuration, seeds and pass criteria are frozen in
``research/PHASE1B_CONFIRMATION_PROTOCOL.md`` before any confirmation workflow is
created. Confirmation output is evidence, including when Gate 1 remains red.
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark
from .experiment_seeds import CONFIRM_V2_RESERVED_SEEDS

FROZEN_CONFIGURATION: dict[str, Any] = {
    "population_size": 12,
    "generations": 8,
    "elite_count": 2,
    "tournament_size": 3,
    "mutation_swaps": 3,
    "crossover_rate": 0.0,
    "immigrant_fraction": 0.0,
    "offspring_multiplier": 3,
    "ranking_mode": "feasibility_first",
    "comparison_mode": "primary",
}

ALPHA = 0.05
MIN_REPEATED_ADMISSIBLE_RUNS = 2


def exact_one_sided_sign_test(*, wins: int, losses: int) -> float:
    """Return P[X >= wins] for X~Binomial(wins+losses, 0.5), ties excluded."""

    if wins < 0 or losses < 0:
        raise ValueError("wins and losses must be non-negative")
    n = wins + losses
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(wins, n + 1)) / (2**n)


def evaluate_preregistered_gates(evidence: dict[str, Any]) -> dict[str, Any]:
    """Apply the Phase-1B criteria frozen before confirmation execution."""

    summary = evidence["summary"]
    wins = int(summary["primary_ga_wins"])
    losses = int(summary["primary_random_wins"])
    ties = int(summary["primary_ties"])
    p_value = exact_one_sided_sign_test(wins=wins, losses=losses)

    nl_ga = float(summary["median_nonlinearity_ga"])
    nl_random = float(summary["median_nonlinearity_random"])
    du_ga = float(summary["median_differential_uniformity_ga"])
    du_random = float(summary["median_differential_uniformity_random"])
    lat_ga = float(summary["median_max_linear_correlation_ga"])
    lat_random = float(summary["median_max_linear_correlation_random"])
    violation_ga = float(summary["median_constraint_violation_ga"])
    violation_random = float(summary["median_constraint_violation_random"])

    structural_nonworse = (
        nl_ga >= nl_random and du_ga <= du_random and lat_ga <= lat_random
    )
    strict_structural_improvement = (
        nl_ga > nl_random or du_ga < du_random or lat_ga < lat_random
    )

    gate1a = bool(
        p_value < ALPHA
        and violation_ga < violation_random
        and structural_nonworse
        and strict_structural_improvement
    )

    ga_admissible = int(summary["admissible_ga"])
    random_admissible = int(summary["admissible_random"])
    gate1b = bool(
        ga_admissible >= MIN_REPEATED_ADMISSIBLE_RUNS
        and ga_admissible > random_admissible
    )

    return {
        "alpha": ALPHA,
        "primary_ga_wins": wins,
        "primary_random_wins": losses,
        "primary_ties": ties,
        "non_tied_primary_comparisons": wins + losses,
        "exact_one_sided_sign_test_p": p_value,
        "structural_nonworse": structural_nonworse,
        "strict_structural_median_improvement": strict_structural_improvement,
        "median_constraint_violation_improved": violation_ga < violation_random,
        "ga_admissible_runs": ga_admissible,
        "random_admissible_runs": random_admissible,
        "minimum_repeated_admissible_runs": MIN_REPEATED_ADMISSIBLE_RUNS,
        "gate1a_primary_search_superiority": gate1a,
        "gate1b_repeated_admissibility": gate1b,
        "gate1_full_pass": gate1a and gate1b,
    }


def run_confirmation() -> dict[str, Any]:
    evidence = run_benchmark(
        seeds=tuple(CONFIRM_V2_RESERVED_SEEDS),
        **FROZEN_CONFIGURATION,
    )
    gates = evaluate_preregistered_gates(evidence)
    return {
        "schema_version": 1,
        "experiment": "phase1b_v2_preregistered_confirmation",
        "scientific_status": "confirmatory_frozen_no_retuning",
        "preregistered_before_execution": {
            "seeds": list(CONFIRM_V2_RESERVED_SEEDS),
            "configuration": FROZEN_CONFIGURATION,
            "criteria": {
                "gate1a": [
                    "one-sided exact sign-test on non-tied primary outcomes p < 0.05",
                    "median constraint violation GA < random",
                    "median NL GA >= random",
                    "median differential uniformity GA <= random",
                    "median max linear correlation GA <= random",
                    "at least one strict structural median improvement",
                ],
                "gate1b": [
                    "GA admissible in at least 2 of 9 runs",
                    "GA admissible-run count > random admissible-run count",
                ],
                "full_gate1": "gate1a AND gate1b",
            },
        },
        "gates": gates,
        "evidence": evidence,
        "verdict": "gate1_green" if gates["gate1_full_pass"] else "gate1_red",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("phase1b-confirmation.json")
    )
    args = parser.parse_args()
    result = run_confirmation()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["gates"], sort_keys=True))
    print(json.dumps(result["evidence"]["summary"], sort_keys=True))
    print(result["verdict"])


if __name__ == "__main__":
    main()
