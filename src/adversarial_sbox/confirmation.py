"""Preregistered Phase-1 confirmatory experiment.

The configuration, seeds, statistical test, and verdict criteria mirror
research/PHASE1_CONFIRMATION_PROTOCOL.md. This module must not be modified in
response to its own confirmatory output and still be called the same experiment.
"""

from __future__ import annotations

import argparse
from math import comb
import json
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark

CONFIRMATION_SEEDS = (211, 223, 227, 229, 233, 239, 241, 251, 257)

FROZEN_CONFIGURATION = {
    "population_size": 10,
    "generations": 6,
    "elite_count": 2,
    "tournament_size": 3,
    "mutation_swaps": 3,
    "crossover_rate": 0.0,
    "offspring_multiplier": 3,
}


def one_sided_sign_test_p(*, wins: int, losses: int) -> float:
    """Exact P[X >= wins] for X~Binomial(wins+losses, 0.5), ignoring ties."""

    if wins < 0 or losses < 0:
        raise ValueError("wins and losses must be non-negative")
    n = wins + losses
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(wins, n + 1)) / (2**n)


def run_confirmation() -> dict[str, Any]:
    evidence = run_benchmark(seeds=CONFIRMATION_SEEDS, **FROZEN_CONFIGURATION)
    summary = evidence["summary"]

    wins = int(summary["ga_wins"])
    losses = int(summary["random_wins"])
    p_value = one_sided_sign_test_p(wins=wins, losses=losses)

    non_regression = {
        "nl": summary["median_nonlinearity_ga"]
        >= summary["median_nonlinearity_random"],
        "du": summary["median_differential_uniformity_ga"]
        <= summary["median_differential_uniformity_random"],
        "linear": summary["median_max_linear_correlation_ga"]
        <= summary["median_max_linear_correlation_random"],
        "admissible_count": summary["admissible_ga"]
        >= summary["admissible_random"],
    }

    relative_advantage_confirmed = bool(
        p_value <= 0.05
        and wins > losses
        and all(non_regression.values())
    )
    repeated_admissibility = bool(
        summary["admissible_ga"] >= 3
        and summary["admissible_ga"] > summary["admissible_random"]
    )
    gate1_passed = relative_advantage_confirmed and repeated_admissibility

    if gate1_passed:
        verdict = "gate1_passed"
    elif relative_advantage_confirmed:
        verdict = "relative_advantage_confirmed_gate1_open"
    else:
        verdict = "gate1_red"

    return {
        "schema_version": 1,
        "experiment": "phase1_preregistered_confirmation",
        "protocol": "research/PHASE1_CONFIRMATION_PROTOCOL.md",
        "frozen_configuration_name": "local_3swap_x3",
        "frozen_configuration": FROZEN_CONFIGURATION,
        "confirmatory_seeds": list(CONFIRMATION_SEEDS),
        "statistical_test": {
            "name": "one_sided_exact_sign_test_non_ties",
            "ga_wins": wins,
            "random_wins": losses,
            "ties": int(summary["ties"]),
            "p_value": p_value,
            "alpha": 0.05,
        },
        "non_regression": non_regression,
        "relative_advantage_confirmed": relative_advantage_confirmed,
        "repeated_admissibility": repeated_admissibility,
        "gate1_passed": gate1_passed,
        "verdict": verdict,
        "evidence": evidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("phase1-confirmation.json")
    )
    args = parser.parse_args()
    result = run_confirmation()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    concise = {
        "verdict": result["verdict"],
        "gate1_passed": result["gate1_passed"],
        "relative_advantage_confirmed": result["relative_advantage_confirmed"],
        "repeated_admissibility": result["repeated_admissibility"],
        "statistical_test": result["statistical_test"],
        "summary": result["evidence"]["summary"],
    }
    print(json.dumps(concise, sort_keys=True))


if __name__ == "__main__":
    main()
