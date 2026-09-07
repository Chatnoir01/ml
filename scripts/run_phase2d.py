#!/usr/bin/env python3
"""CLI for preregistered Phase 2D arm, terminal-freeze, validation and aggregate stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2d import ARMS
from adversarial_sbox.phase2d_runner import run_arm


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_many(paths):
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def _require_terminal_freeze(run: dict, freeze: dict) -> None:
    if str(freeze.get("phase")) != "2D-terminal-freeze":
        raise SystemExit("invalid Phase 2D terminal-freeze manifest")
    if not bool(freeze.get("prerequisites", {}).get("pass")):
        raise SystemExit("Phase 2D terminal-freeze prerequisites did not pass")
    seed = int(run["seed"])
    arm = str(run["arm"])
    matches = [
        item
        for item in freeze.get("terminals", [])
        if int(item.get("seed", -1)) == seed and str(item.get("arm", "")) == arm
    ]
    if len(matches) != 1:
        raise SystemExit("terminal cell missing or duplicated in freeze manifest")
    terminal = matches[0]
    if str(terminal.get("terminal_fingerprint", "")) != str(run["terminal_fingerprint"]):
        raise SystemExit("terminal fingerprint differs from frozen manifest")
    if list(terminal.get("terminal_sbox", [])) != list(run["terminal_sbox"]):
        raise SystemExit("terminal S-Box differs from frozen manifest")
    if str(terminal.get("arm_payload_sha256", "")) != str(run["scientific_payload_sha256"]):
        raise SystemExit("arm payload receipt differs from frozen manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze-arm-files", type=Path, nargs="+")
    parser.add_argument("--validate-arm-result", type=Path)
    parser.add_argument("--terminal-freeze", type=Path)
    parser.add_argument("--aggregate-arm-files", type=Path, nargs="+")
    parser.add_argument("--aggregate-validation-files", type=Path, nargs="+")
    args = parser.parse_args()

    if args.freeze_arm_files:
        if any(
            value is not None
            for value in (
                args.validate_arm_result,
                args.aggregate_arm_files,
                args.aggregate_validation_files,
            )
        ):
            raise SystemExit("terminal freeze cannot be mixed with other modes")
        from adversarial_sbox.phase2d_terminal_freeze import freeze_terminals

        _write(args.output, freeze_terminals(_read_many(args.freeze_arm_files)))
        return

    if args.aggregate_arm_files or args.aggregate_validation_files:
        if not args.aggregate_arm_files or not args.aggregate_validation_files:
            raise SystemExit("both aggregate file groups are required")
        from adversarial_sbox.phase2d_aggregate import aggregate_phase2d

        _write(
            args.output,
            aggregate_phase2d(
                _read_many(args.aggregate_arm_files),
                _read_many(args.aggregate_validation_files),
            ),
        )
        return

    if args.validate_arm_result:
        if args.terminal_freeze is None:
            raise SystemExit("held-out validation requires --terminal-freeze")
        run = json.loads(args.validate_arm_result.read_text(encoding="utf-8"))
        freeze = json.loads(args.terminal_freeze.read_text(encoding="utf-8"))
        _require_terminal_freeze(run, freeze)
        seed = int(run["seed"])
        arm = str(run["arm"])
        if args.seed is not None and int(args.seed) != seed:
            raise SystemExit("validation seed does not match arm result")
        if args.arm is not None and str(args.arm) != arm:
            raise SystemExit("validation arm does not match arm result")
        from adversarial_sbox.phase2d_validation import score_terminal_candidate

        score = score_terminal_candidate(run["terminal_sbox"])
        _write(
            args.output,
            {
                "schema_version": 1,
                "phase": "2D-validation",
                "seed": seed,
                "arm": arm,
                "terminal_fingerprint": str(run["terminal_fingerprint"]),
                "terminal_freeze_sha256": str(freeze["terminal_freeze_sha256"]),
                "score": score,
            },
        )
        return

    if args.seed is None or args.arm is None:
        raise SystemExit("--seed and --arm are required for arm execution")
    _write(args.output, run_arm(seed=int(args.seed), arm=str(args.arm)))


if __name__ == "__main__":
    main()
