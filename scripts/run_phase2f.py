#!/usr/bin/env python3
"""CLI for preregistered Phase 2F arm, terminal-freeze, validation and aggregate stages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from adversarial_sbox.phase2f import ARMS


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_many(paths):
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def _sha_matches(payload: dict, field: str) -> bool:
    stored = str(payload.get(field, ""))
    if len(stored) != 64:
        return False
    clean = {key: value for key, value in payload.items() if key != field}
    blob = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest() == stored


def _require_terminal_freeze(run: dict, freeze: dict) -> None:
    if not _sha_matches(run, "scientific_payload_sha256"):
        raise SystemExit("Phase 2F arm payload checksum failed before held-out validation")
    if not _sha_matches(freeze, "terminal_freeze_sha256"):
        raise SystemExit("Phase 2F terminal-freeze checksum failed before held-out validation")
    if str(freeze.get("phase")) != "2F-terminal-freeze":
        raise SystemExit("invalid Phase 2F terminal-freeze manifest")
    if not bool(freeze.get("prerequisites", {}).get("pass")):
        raise SystemExit("Phase 2F terminal-freeze prerequisites did not pass")
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
        from adversarial_sbox.phase2f_terminal_freeze import freeze_terminals

        payload = freeze_terminals(_read_many(args.freeze_arm_files))
        _write(args.output, payload)
        if not bool(payload.get("prerequisites", {}).get("pass")):
            raise SystemExit("Phase 2F terminal-freeze prerequisites failed closed")
        return

    if args.aggregate_arm_files or args.aggregate_validation_files:
        if not args.aggregate_arm_files or not args.aggregate_validation_files:
            raise SystemExit("both aggregate file groups are required")
        from adversarial_sbox.phase2f_aggregate import aggregate_phase2f

        payload = aggregate_phase2f(
            _read_many(args.aggregate_arm_files),
            _read_many(args.aggregate_validation_files),
        )
        _write(args.output, payload)
        if not bool(payload.get("prerequisites", {}).get("pass")):
            raise SystemExit("Phase 2F aggregate prerequisites failed closed")
        if str(payload.get("verdict", "")) == "phase2f_inconclusive_prerequisites":
            raise SystemExit("Phase 2F inconclusive prerequisite verdict cannot pass workflow")
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
        from adversarial_sbox.phase2f_aggregate import score_payload_integrity
        from adversarial_sbox.phase2f_validation import score_terminal_candidate
        from adversarial_sbox.phase2f_validation_seeds import (
            VALIDATION_DATASET_SEEDS,
            VALIDATION_MODEL_SEEDS,
        )

        score = score_terminal_candidate(run["terminal_sbox"])
        if not score_payload_integrity(
            score,
            purpose="validation",
            dataset_seeds=VALIDATION_DATASET_SEEDS,
            model_seeds=VALIDATION_MODEL_SEEDS,
        ):
            raise SystemExit("Phase 2F held-out validation receipt failed integrity gate")
        _write(
            args.output,
            {
                "schema_version": 1,
                "phase": "2F-validation",
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
    from adversarial_sbox.phase2f_runner import run_arm

    _write(args.output, run_arm(seed=int(args.seed), arm=str(args.arm)))


if __name__ == "__main__":
    main()
