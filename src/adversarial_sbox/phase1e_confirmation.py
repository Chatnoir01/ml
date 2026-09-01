"""Frozen Phase 1E confirmation runner.

No tuning knobs are exposed: the configuration and seeds were preregistered before
any confirmation run. This evaluates the selected combined-cycle-4 hotspot-guided
operator against the equal-budget unguided adaptive comparator.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from math import comb
from pathlib import Path
from typing import Any

from .evolution import HardConstraints
from .experiment_seeds import PHASE1E_CONFIRM_RESERVED_SEEDS
from .phase1d import EXPECTED_PHASE1B_FINGERPRINT, continuation_rank, reproduce_phase1b_frontier_candidate
from .phase1e import guided_adaptive_search, unguided_adaptive_search

CONFIRM_GUIDANCE = "combined"
CONFIRM_CYCLE_LENGTH = 4
CONFIRM_BEAM_WIDTH = 8
CONFIRM_EVALUATIONS = 600
UNGUIDED_SEED_XOR = 0x1E1E1E1E


def exact_one_sided_sign_p(guided_wins: int, unguided_wins: int) -> float:
    """Exact P[X>=guided_wins] for non-tied outcomes under p=0.5."""

    if guided_wins < 0 or unguided_wins < 0:
        raise ValueError("win counts must be non-negative")
    trials = guided_wins + unguided_wins
    if trials == 0:
        return 1.0
    numerator = sum(comb(trials, k) for k in range(guided_wins, trials + 1))
    return numerator / (2**trials)


def validate_confirmation_seed(seed: int) -> None:
    if seed not in PHASE1E_CONFIRM_RESERVED_SEEDS:
        raise ValueError(
            f"seed {seed} is not in the frozen Phase-1E confirmation registry"
        )


def run_one(seed: int) -> dict[str, Any]:
    """Run one preregistered confirmation pair at the frozen configuration."""

    validate_confirmation_seed(seed)
    start, start_metrics = reproduce_phase1b_frontier_candidate()
    if start_metrics.fingerprint != EXPECTED_PHASE1B_FINGERPRINT:
        raise RuntimeError("Phase-1E confirmation warm-start fingerprint mismatch")

    constraints = HardConstraints()
    guided = guided_adaptive_search(
        start,
        seed=seed,
        evaluations=CONFIRM_EVALUATIONS,
        beam_width=CONFIRM_BEAM_WIDTH,
        cycle_length=CONFIRM_CYCLE_LENGTH,
        guidance=CONFIRM_GUIDANCE,
        constraints=constraints,
    )
    unguided = unguided_adaptive_search(
        start,
        seed=seed ^ UNGUIDED_SEED_XOR,
        evaluations=CONFIRM_EVALUATIONS,
        beam_width=CONFIRM_BEAM_WIDTH,
        cycle_length=CONFIRM_CYCLE_LENGTH,
        constraints=constraints,
    )

    guided_rank = tuple(guided["best_rank"])
    unguided_rank = tuple(unguided["best_rank"])
    outcome = (
        "guided"
        if guided_rank > unguided_rank
        else "unguided"
        if guided_rank < unguided_rank
        else "tie"
    )

    return {
        "schema_version": 1,
        "experiment": "phase1e_hotspot_guided_confirmation_pair",
        "scientific_status": "warm_start_operator_confirmation_not_global_gate1",
        "seed": seed,
        "configuration": {
            "guidance": CONFIRM_GUIDANCE,
            "cycle_length": CONFIRM_CYCLE_LENGTH,
            "beam_width": CONFIRM_BEAM_WIDTH,
            "evaluations_each": CONFIRM_EVALUATIONS,
        },
        "historical_start_metrics": asdict(start_metrics),
        "outcome": outcome,
        "guided": guided,
        "unguided": unguided,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_one(args.seed)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "seed": result["seed"],
                "outcome": result["outcome"],
                "guided_target": result["guided"]["found_target"],
                "unguided_target": result["unguided"]["found_target"],
                "guided_admissible": result["guided"]["found_admissible"],
                "unguided_admissible": result["unguided"]["found_admissible"],
                "guided_metrics": result["guided"]["best_metrics"],
                "unguided_metrics": result["unguided"]["best_metrics"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
