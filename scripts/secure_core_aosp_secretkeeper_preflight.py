#!/usr/bin/env python3
"""Inspect and optionally lock a local AOSP Secretkeeper/AuthGraph source contract."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.aosp_secretkeeper_contract import (
    KNOWN_AOSP_SECRETKEEPER_TARGETS,
    inspect_aosp_secretkeeper_contract,
    load_aosp_secretkeeper_contract_lock,
    lock_aosp_secretkeeper_contract,
    verify_aosp_secretkeeper_contract_lock,
    verify_aosp_secretkeeper_source_target,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aosp-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--target",
        choices=sorted(KNOWN_AOSP_SECRETKEEPER_TARGETS),
        help="Require exact component revisions for a reviewed AOSP target.",
    )
    parser.add_argument(
        "--lock-output",
        type=Path,
        help="Write an exact reviewed source-contract lock when eligible.",
    )
    parser.add_argument(
        "--require-lock",
        type=Path,
        help="Require the inspected snapshot to match this existing lock.",
    )
    args = parser.parse_args()

    target = None
    if args.target is not None:
        target = KNOWN_AOSP_SECRETKEEPER_TARGETS[args.target]
        verify_aosp_secretkeeper_source_target(args.aosp_root, target)

    receipt = inspect_aosp_secretkeeper_contract(args.aosp_root)
    payload = asdict(receipt)
    payload["receipt_sha256"] = receipt.receipt_sha256
    if target is not None:
        payload["source_target"] = asdict(target)
    _write_json(args.output, payload)

    if args.require_lock is not None:
        lock = load_aosp_secretkeeper_contract_lock(args.require_lock)
        verify_aosp_secretkeeper_contract_lock(receipt, lock)

    if args.lock_output is not None:
        lock = lock_aosp_secretkeeper_contract(receipt)
        lock_payload = asdict(lock)
        lock_payload["lock_sha256"] = lock.lock_sha256
        # lock_sha256 is a receipt for display/review, not part of the lock body.
        _write_json(args.lock_output, lock_payload)

    raise SystemExit(
        0 if receipt.eligible_for_secure_core_native_authgraph else 2
    )


if __name__ == "__main__":
    main()
