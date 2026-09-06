#!/usr/bin/env python3
"""Frozen CLI for Phase 2B arm execution, terminal validation, and aggregation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2b_aggregate import aggregate_phase2b
from adversarial_sbox.phase2b_runner import run_arm
from adversarial_sbox.phase2b_validation import score_terminal_candidate


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=("control", "oracle", "shuffled"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-arm-result", type=Path)
    parser.add_argument("--aggregate-arm-files", type=Path, nargs="+")
    parser.add_argument("--aggregate-validation-files", type=Path, nargs="+")
    args = parser.parse_args()

    if args.aggregate_arm_files or args.aggregate_validation_files:
        if not args.aggregate_arm_files or not args.aggregate_validation_files:
            raise SystemExit("both aggregate file groups are required")
        arm_results = [json.loads(path.read_text(encoding="utf-8")) for path in args.aggregate_arm_files]
        validation_results = [
            json.loads(path.read_text(encoding="utf-8")) for path in args.aggregate_validation_files
        ]
        _write(args.output, aggregate_phase2b(arm_results, validation_results))
        return

    if args.validate_arm_result:
        run = json.loads(args.validate_arm_result.read_text(encoding="utf-8"))
        seed = int(run["seed"])
        arm = str(run["arm"])
        if args.seed is not None and int(args.seed) != seed:
            raise SystemExit("validation seed does not match arm result")
        if args.arm is not None and str(args.arm) != arm:
            raise SystemExit("validation arm does not match arm result")
        score = score_terminal_candidate(run["terminal_sbox"])
        payload = {
            "schema_version": 1,
            "phase": "2B",
            "seed": seed,
            "arm": arm,
            "terminal_fingerprint": str(run["terminal_fingerprint"]),
            "score": score,
        }
        _write(args.output, payload)
        return

    if args.seed is None or args.arm is None:
        raise SystemExit("--seed and --arm are required for arm execution")
    _write(args.output, run_arm(seed=int(args.seed), mode=str(args.arm)))


if __name__ == "__main__":
    main()
