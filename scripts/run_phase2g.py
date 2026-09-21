#!/usr/bin/env python3
"""CLI for the frozen Phase 2G cell, terminal-freeze, H-validation and aggregate stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2g import ARMS


ALLOWED_VERDICTS = {
    "phase2g_adaptive_coevolution_supported",
    "phase2g_adaptive_coevolution_not_supported",
    "phase2g_inconclusive_prerequisites",
}


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_many(paths: list[Path] | None) -> list[dict]:
    if not paths:
        return []
    return [_read(path) for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--output", type=Path, required=True)

    parser.add_argument("--freeze-arm-files", type=Path, nargs="+")
    parser.add_argument("--validate-terminal-freeze", type=Path)
    parser.add_argument("--aggregate-arm-files", type=Path, nargs="+")
    parser.add_argument("--terminal-freeze", type=Path)
    parser.add_argument("--heldout-validation", type=Path)
    args = parser.parse_args()

    if args.freeze_arm_files:
        if any(
            value is not None
            for value in (
                args.seed,
                args.arm,
                args.validate_terminal_freeze,
                args.aggregate_arm_files,
                args.terminal_freeze,
                args.heldout_validation,
            )
        ):
            raise SystemExit("Phase 2G terminal freeze cannot be mixed with another mode")

        from adversarial_sbox.phase2g_terminal_freeze import (
            freeze_phase2g_terminals,
            heldout_h_authorized,
        )

        payload = freeze_phase2g_terminals(_read_many(args.freeze_arm_files))
        if not heldout_h_authorized(payload):
            raise SystemExit("Phase 2G terminal freeze failed closed")
        _write(args.output, payload)
        return

    if args.validate_terminal_freeze is not None:
        if any(
            value is not None
            for value in (
                args.seed,
                args.arm,
                args.aggregate_arm_files,
                args.terminal_freeze,
                args.heldout_validation,
            )
        ):
            raise SystemExit("Phase 2G held-out validation cannot be mixed with another mode")

        freeze = _read(args.validate_terminal_freeze)

        # Fail closed before even importing the post-freeze validation module.
        from adversarial_sbox.phase2g_terminal_freeze import heldout_h_authorized

        if not heldout_h_authorized(freeze):
            raise SystemExit("Phase 2G held-out H is not authorized by terminal freeze")

        from adversarial_sbox.phase2g_validation import validate_frozen_terminals

        payload = validate_frozen_terminals(freeze)
        if int(payload.get("cell_count", -1)) != 36:
            raise SystemExit("Phase 2G held-out validation cell-count drift")
        if int(payload.get("heldout_training_count", -1)) != 576:
            raise SystemExit("Phase 2G held-out validation training-count drift")
        if not bool(payload.get("heldout_accessed", False)):
            raise SystemExit("Phase 2G held-out validation access receipt is missing")
        _write(args.output, payload)
        return

    if args.aggregate_arm_files:
        if args.terminal_freeze is None or args.heldout_validation is None:
            raise SystemExit(
                "Phase 2G aggregate requires --terminal-freeze and --heldout-validation"
            )
        if any(value is not None for value in (args.seed, args.arm)):
            raise SystemExit("Phase 2G aggregate cannot be mixed with cell execution")

        from adversarial_sbox.phase2g_aggregate import aggregate_phase2g_results

        payload = aggregate_phase2g_results(
            arm_results=_read_many(args.aggregate_arm_files),
            terminal_freeze=_read(args.terminal_freeze),
            heldout_validation=_read(args.heldout_validation),
        )
        if int(payload.get("total_training_count", -1)) != 2880:
            raise SystemExit("Phase 2G aggregate total-training budget drift")
        if str(payload.get("verdict", "")) not in ALLOWED_VERDICTS:
            raise SystemExit("Phase 2G aggregate emitted an unauthorized verdict")
        _write(args.output, payload)
        return

    if args.terminal_freeze is not None or args.heldout_validation is not None:
        raise SystemExit("Phase 2G freeze/validation arguments require their matching mode")
    if args.seed is None or args.arm is None:
        raise SystemExit("--seed and --arm are required for Phase 2G cell execution")

    from adversarial_sbox.phase2g_experiment import run_phase2g_scientific_cell

    payload = run_phase2g_scientific_cell(seed=int(args.seed), arm=str(args.arm))
    if int(payload.get("classical_evaluations", -1)) != 340:
        raise SystemExit("Phase 2G cell classical budget drift")
    if int(payload.get("checkpoint_trainings", -1)) != 64:
        raise SystemExit("Phase 2G cell checkpoint-training budget drift")
    if bool(payload.get("heldout_accessed", True)):
        raise SystemExit("Phase 2G cell illegally accessed held-out H")
    _write(args.output, payload)


if __name__ == "__main__":
    main()
