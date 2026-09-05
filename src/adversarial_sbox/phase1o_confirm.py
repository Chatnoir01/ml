"""Blinded Phase 1O confirmation wrapper.

This module reuses the frozen Phase-1O search mechanism unchanged. It only
restricts execution to the preregistered reserved confirmation seeds and applies
the separately preregistered nine-seed confirmation gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from .experiment_seeds import PHASE1O_CONFIRM_RESERVED_SEEDS, validate_seed_registry
from .phase1m import CLASSICAL_BUDGET, ITO_NONINFERIORITY_TOLERANCE
from .phase1o import _canonical_payload, _run_seed_once

CONFIRMATION_REQUIRED_JOINT_SEEDS = 5


def _run_confirmation_once(seed: int) -> dict[str, Any]:
    payload = _run_seed_once(seed)
    return {**payload, "phase": "1O-confirm"}


def run_confirmation_seed(seed: int) -> dict[str, Any]:
    """Run one reserved Phase-1O confirmation seed twice for determinism."""

    validate_seed_registry()
    if seed not in PHASE1O_CONFIRM_RESERVED_SEEDS:
        raise ValueError(f"seed {seed} is not a Phase 1O confirmation seed")

    first = _run_confirmation_once(seed)
    second = _run_confirmation_once(seed)
    first_bytes = _canonical_payload(first)
    if first_bytes != _canonical_payload(second):
        raise RuntimeError(
            "Phase 1O confirmation fixed-seed scientific payload is not deterministic"
        )
    return {
        **first,
        "scientific_payload_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "deterministic_payload_match": True,
    }


def aggregate_confirmation(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Apply the frozen eleven-check confirmation gate to exactly nine results."""

    if len(results) != len(PHASE1O_CONFIRM_RESERVED_SEEDS):
        raise ValueError("Phase 1O confirmation requires exactly nine seed results")

    joint_a = sum(item["arm_a"]["joint_target_count"] for item in results)
    joint_b = sum(item["arm_b"]["joint_target_count"] for item in results)
    joint_seed_successes_a = sum(
        item["arm_a"]["joint_target_count"] > 0 for item in results
    )
    du8_seed_successes_a = sum(item["arm_a"]["du8_count"] > 0 for item in results)
    du8_seed_successes_b = sum(item["arm_b"]["du8_count"] > 0 for item in results)

    best_du_a = [item["arm_a"]["best_du"] for item in results]
    best_du_b = [item["arm_b"]["best_du"] for item in results]
    best_du_wins = sum(a < b for a, b in zip(best_du_a, best_du_b))
    best_du_losses = sum(a > b for a, b in zip(best_du_a, best_du_b))
    best_du_ties = len(results) - best_du_wins - best_du_losses

    median_best_du_a = median(best_du_a)
    median_best_du_b = median(best_du_b)
    protected_a = sum(
        item["arm_a"]["protected_classical_count"] for item in results
    )
    protected_b = sum(
        item["arm_b"]["protected_classical_count"] for item in results
    )
    median_min_ito_a = median(item["arm_a"]["min_ito"] for item in results)
    median_min_ito_b = median(item["arm_b"]["min_ito"] for item in results)

    checks = {
        "joint_aggregate_advantage": joint_a > joint_b,
        "joint_seed_successes_ge_5": (
            joint_seed_successes_a >= CONFIRMATION_REQUIRED_JOINT_SEEDS
        ),
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
        "reserved_seed_registry_exact": (
            tuple(sorted(item["seed"] for item in results))
            == tuple(sorted(PHASE1O_CONFIRM_RESERVED_SEEDS))
        ),
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
        "confirmation_checks": checks,
        "verdict": (
            "phase1o_confirm_pass"
            if all(checks.values())
            else "phase1o_confirm_fail"
        ),
    }


def aggregate_files(paths: Sequence[Path]) -> dict[str, Any]:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    return {"per_seed": results, **aggregate_confirmation(results)}


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
        runs = [run_confirmation_seed(seed) for seed in args.seeds]
        payload = (
            runs[0]
            if len(runs) == 1
            else {"per_seed": runs, **aggregate_confirmation(runs)}
        )
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
