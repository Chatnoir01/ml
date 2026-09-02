"""Frozen Phase-1I fresh-population confirmation runner and aggregator.

The code is committed before the development winner is known.  A confirmation
pair can run only for the configuration named by a valid frozen-selection receipt.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from math import comb
from pathlib import Path
import statistics
from typing import Any

from .evolution import HardConstraints
from .experiment_seeds import PHASE1I_CONFIRM_RESERVED_SEEDS
from .independent_verify import verify_independently
from .phase1i import CONFIGURATIONS, TOTAL_BUDGET, _outcome, _run_continued_ga, _run_directed


def exact_one_sided_sign_p(directed_wins: int, comparator_wins: int) -> float:
    if directed_wins < 0 or comparator_wins < 0:
        raise ValueError("win counts must be non-negative")
    trials = directed_wins + comparator_wins
    if trials == 0:
        return 1.0
    return sum(comb(trials, k) for k in range(directed_wins, trials + 1)) / (2**trials)


def selected_configuration(selection: dict[str, Any]) -> str:
    if selection.get("experiment") != "phase1i_frozen_development_selection":
        raise ValueError("invalid Phase-1I selection receipt")
    if selection.get("development_gate") != "pass" or not selection.get("confirmation_allowed"):
        raise ValueError("Phase-1I development receipt does not allow confirmation")
    name = selection.get("selected_configuration")
    if name not in CONFIGURATIONS:
        raise ValueError("selection receipt names an unknown Phase-1I configuration")
    return str(name)


def _independent_matches(search_side: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    independent = verify_independently(tuple(search_side["best_sbox"]))
    expected = search_side["best_metrics"]
    checks = {
        "nonlinearity": independent.nonlinearity == int(expected["nonlinearity"]),
        "differential_uniformity": independent.differential_uniformity
        == int(expected["differential_uniformity"]),
        "max_linear_correlation": independent.max_linear_correlation
        == int(expected["max_linear_correlation"]),
        "algebraic_degree": independent.algebraic_degree == int(expected["algebraic_degree"]),
        "sac_score": abs(independent.sac_score - float(expected["sac_score"])) <= 1e-15,
    }
    return all(checks.values()), {
        "metrics": asdict(independent),
        "checks": checks,
        "matches": all(checks.values()),
    }


def run_pair(*, selection: dict[str, Any], seed: int) -> dict[str, Any]:
    if seed not in PHASE1I_CONFIRM_RESERVED_SEEDS:
        raise ValueError(f"seed {seed} is not a reserved Phase-1I confirmation seed")
    name = selected_configuration(selection)
    cycle_lengths, proposal_pool = CONFIGURATIONS[name]
    constraints = HardConstraints()

    directed = _run_directed(
        seed,
        cycle_lengths=cycle_lengths,
        proposal_pool=proposal_pool,
        constraints=constraints,
    )
    comparator = _run_continued_ga(seed, constraints=constraints)
    if directed["unique_evaluations"] != TOTAL_BUDGET:
        raise RuntimeError("directed confirmation arm budget mismatch")
    if comparator["unique_evaluations"] != TOTAL_BUDGET:
        raise RuntimeError("comparator confirmation arm budget mismatch")

    directed_match, directed_independent = _independent_matches(directed)
    comparator_match, comparator_independent = _independent_matches(comparator)
    outcome = _outcome(directed, comparator)

    return {
        "schema_version": 1,
        "experiment": "phase1i_fresh_confirmation_pair",
        "scientific_status": "fresh_population_confirmation_pair",
        "selected_configuration": name,
        "seed": seed,
        "configuration": {
            "cycle_lengths": list(cycle_lengths),
            "proposal_pool": proposal_pool,
            "total_evaluations_each_arm": TOTAL_BUDGET,
        },
        "outcome": outcome,
        "directed": directed,
        "comparator": comparator,
        "independent_verification": {
            "directed": directed_independent,
            "comparator": comparator_independent,
            "pair_matches": directed_match and comparator_match,
        },
    }


def aggregate_pairs(*, selection: dict[str, Any], pairs: list[dict[str, Any]]) -> dict[str, Any]:
    name = selected_configuration(selection)
    expected_seeds = set(PHASE1I_CONFIRM_RESERVED_SEEDS)
    if len(pairs) != len(expected_seeds):
        raise ValueError("Phase-1I confirmation aggregation requires exactly nine pairs")
    observed_seeds = {int(pair["seed"]) for pair in pairs}
    if observed_seeds != expected_seeds:
        raise ValueError("Phase-1I confirmation seed set mismatch")
    if any(pair.get("selected_configuration") != name for pair in pairs):
        raise ValueError("confirmation pair configuration does not match frozen selection")
    if any(pair.get("experiment") != "phase1i_fresh_confirmation_pair" for pair in pairs):
        raise ValueError("unexpected document in Phase-1I confirmation aggregation")

    directed_admissible = sum(pair["directed"]["found_admissible"] for pair in pairs)
    comparator_admissible = sum(pair["comparator"]["found_admissible"] for pair in pairs)
    directed_target = sum(pair["directed"]["found_structural_target"] for pair in pairs)
    comparator_target = sum(pair["comparator"]["found_structural_target"] for pair in pairs)
    directed_wins = sum(pair["outcome"] == "directed" for pair in pairs)
    comparator_wins = sum(pair["outcome"] == "comparator" for pair in pairs)
    ties = sum(pair["outcome"] == "tie" for pair in pairs)
    p_value = exact_one_sided_sign_p(directed_wins, comparator_wins)

    median_nl = float(statistics.median(pair["directed"]["best_metrics"]["nonlinearity"] for pair in pairs))
    median_du = float(statistics.median(pair["directed"]["best_metrics"]["differential_uniformity"] for pair in pairs))
    median_corr = float(statistics.median(pair["directed"]["best_metrics"]["max_linear_correlation"] for pair in pairs))

    exact_budgets = all(
        pair["directed"]["unique_evaluations"] == TOTAL_BUDGET
        and pair["comparator"]["unique_evaluations"] == TOTAL_BUDGET
        for pair in pairs
    )
    independent_matches = all(
        pair["independent_verification"]["pair_matches"] for pair in pairs
    )

    checks = {
        "directed_admissible_at_least_5_of_9": directed_admissible >= 5,
        "directed_target_at_least_5_of_9": directed_target >= 5,
        "directed_admissible_strictly_beats_comparator": directed_admissible > comparator_admissible,
        "directed_target_strictly_beats_comparator": directed_target > comparator_target,
        "directed_wins_strictly_exceed_comparator": directed_wins > comparator_wins,
        "one_sided_sign_p_below_0_05": p_value < 0.05,
        "median_directed_nonlinearity_at_least_100": median_nl >= 100,
        "median_directed_du_at_most_8": median_du <= 8,
        "median_directed_max_corr_at_most_64": median_corr <= 64,
        "exact_980_evaluation_budgets": exact_budgets,
        "exact_reserved_seed_set": observed_seeds == expected_seeds,
        "independent_verification_all_18_best_candidates": independent_matches,
    }
    passed = all(checks.values())

    return {
        "schema_version": 1,
        "experiment": "phase1i_fresh_population_confirmation",
        "selected_configuration": name,
        "summary": {
            "directed_admissible_runs": directed_admissible,
            "comparator_admissible_runs": comparator_admissible,
            "directed_target_runs": directed_target,
            "comparator_target_runs": comparator_target,
            "directed_wins": directed_wins,
            "comparator_wins": comparator_wins,
            "ties": ties,
            "non_tied_pairs": directed_wins + comparator_wins,
            "exact_one_sided_sign_p": p_value,
            "median_nonlinearity_directed": median_nl,
            "median_du_directed": median_du,
            "median_max_corr_directed": median_corr,
            "checks": checks,
            "verdict": "pass" if passed else "fail",
            "global_gate1": "green" if passed else "red",
            "neural_oracle": "unblocked" if passed else "blocked",
        },
        "pairs": sorted(pairs, key=lambda pair: pair["seed"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    pair_parser = subparsers.add_parser("pair")
    pair_parser.add_argument("--selection", type=Path, required=True)
    pair_parser.add_argument("--seed", type=int, required=True)
    pair_parser.add_argument("--output", type=Path, required=True)

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--selection", type=Path, required=True)
    aggregate_parser.add_argument("inputs", type=Path, nargs="+")
    aggregate_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if args.command == "pair":
        result = run_pair(selection=selection, seed=args.seed)
    else:
        pairs = [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs]
        result = aggregate_pairs(selection=selection, pairs=pairs)

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.command == "pair":
        print(json.dumps({
            "seed": result["seed"],
            "outcome": result["outcome"],
            "directed_admissible": result["directed"]["found_admissible"],
            "comparator_admissible": result["comparator"]["found_admissible"],
            "independent_match": result["independent_verification"]["pair_matches"],
        }, sort_keys=True))
    else:
        print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
