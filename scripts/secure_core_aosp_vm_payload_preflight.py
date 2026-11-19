#!/usr/bin/env python3
"""Inspect a local Android 17 VM Payload API contract for Secure Core."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.aosp_vm_payload_contract import (
    KNOWN_VM_PAYLOAD_TARGETS,
    inspect_vm_payload_contract,
    verify_vm_payload_source_target,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aosp-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--target",
        choices=sorted(KNOWN_VM_PAYLOAD_TARGETS),
        help="Require an exact reviewed Virtualization repository revision.",
    )
    args = parser.parse_args()

    target = None
    if args.target is not None:
        target = KNOWN_VM_PAYLOAD_TARGETS[args.target]
        verify_vm_payload_source_target(args.aosp_root, target)

    receipt = inspect_vm_payload_contract(args.aosp_root)
    payload = asdict(receipt)
    payload["receipt_sha256"] = receipt.receipt_sha256
    if target is not None:
        payload["source_target"] = asdict(target)

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    raise SystemExit(
        0 if receipt.eligible_for_secure_core_payload else 2
    )


if __name__ == "__main__":
    main()
