"""Blind confirmatory experiment for Phase 1.

The configuration, seeds, and pass criteria in this module are frozen before the
confirmatory workflow is created or run. Development/tuning code must not use
these seeds. A failed confirmation is retained as evidence; it is never converted
into a tuning run.
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark

# Fresh confirmatory seeds: deliberately disjoint from all development and short
# baseline seeds used before this protocol was written.
CONFIRMATION_SEEDS = (
    131,
    137,
    149,
    157,
    163,
    173,
    181,
    191,
    197,
    211,
    223,
    227,
)

# Frozen winner of the development sweep. Do not change after confirmation data
# exist; a later configuration must use a new experiment/version and fresh seeds.
FROZEN_CONFIGURATION: dict[str, Any] = {
    "population_size": 10,
    "generations": 12,
    "elite_count": 2,
    "tournament_size": 3,
    "mutation_swaps": 3,
    "crossover_rate": 0.0,
    "immigrant_fraction": 0.25,
}

# Pre-registered Phase-1 criteria.
ALPHA = 0.05
MIN_REPEATED_ADMISSIBLE_RUNS = 3


def exact_one_sided_sign_test(*, wins: int, losses: int) -> float:
    """Exact P[X >= wins] for X~Binomial(wins+losses, 0.5), ties excluded."""

    if wins < 0 or losses < 0:
        raise ValueError("wins and losses must be non-negative")
    n = wins + losses
    if n == 0:
        return 1.0
    numerator = sum(comb(n, k) for k in range(wins, n + 1))
    return numerator / (2**n)


def evaluate_preregistered_gates(evidence: dict[str, Any]) -> dict[str, Any]:
    """Apply criteria that were fixed before observing confirmation results."""

    summary = evidence["summary"]
    runs = evidence["runs"]
    ga_wins = int(summary["ga_wins"])
    random_wins = int(summary["random_wins"])
    p_value = exact_one_sided_sign_test(wins=ga_wins, losses=random_wins)

    ga_admissible = sum(float(row["ga"]["rank"][0]) == 1.0 for row in runs)
    random_admissible = sum(float(row["random"]["rank"][0]) == 1.0 for row in runs)

    # Gate 1A asks whether the frozen search strategy is superior to equal-budget
    # random search, not merely whether it wins a SAC tie-break.
    gate1a_search_superiority = bool(
        p_value < ALPHA
        and summary["median_constraint_violation_ga"]
        < summary["median_constraint_violation_random"]
        and summary["median_nonlinearity_ga"]
        >= summary["median_nonlinearity_random"]
        and summary["median_differential_uniformity_ga"]
        <= summary["median_differential_uniformity_random"]
    )

    # Gate 1B encodes the original requirement that hard-threshold candidates are
    # found repeatedly, not as one lucky run. Three of twelve is fixed here before
    # execution and GA must also beat random on admissible-run count.
    gate1b_repeated_admissibility = bool(
        ga_admissible >= MIN_REPEATED_ADMISSIBLE_RUNS
        and ga_admissible > random_admissible
    )

    return {
        "alpha": ALPHA,
        "sign_test_one_sided_p": p_value,
        "non_tied_comparisons": ga_wins + random_wins,
        "ga_admissible_runs": ga_admissible,
        "random_admissible_runs": random_admissible,
        "candidate_found": ga_admissible > 0,
        "gate1a_search_superiority": gate1a_search_superiority,
        "gate1b_repeated_admissibility": gate1b_repeated_admissibility,
        "gate1_full_pass": gate1a_search_superiority
        and gate1b_repeated_admissibility,
    }


def run_confirmation() -> dict[str, Any]:
    evidence = run_benchmark(
        seeds=CONFIRMATION_SEEDS,
        **FROZEN_CONFIGURATION,
    )
    gates = evaluate_preregistered_gates(evidence)
    return {
        "schema_version": 1,
        "experiment": "phase1_blind_confirmation",
        "scientific_status": "confirmatory_frozen_no_retuning",
        "preregistered_before_execution": {
            "seeds": list(CONFIRMATION_SEEDS),
            "configuration": FROZEN_CONFIGURATION,
            "criteria": {
                "gate1a": [
                    "one-sided exact sign-test p < 0.05",
                    "median constraint violation GA < random",
                    "median nonlinearity GA >= random",
                    "median differential uniformity GA <= random",
                ],
                "gate1b": [
                    "GA admissible in at least 3 of 12 runs",
                    "GA admissible-run count > random admissible-run count",
                ],
                "full_gate1": "gate1a AND gate1b",
            },
        },
        "gates": gates,
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
    print(json.dumps(result["gates"], sort_keys=True))
    print(json.dumps(result["evidence"]["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
