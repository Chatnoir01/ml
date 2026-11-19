#!/usr/bin/env python3
"""Run the Secure Core Android native-bridge preflight.

The output is secret-free diagnostic evidence. It never claims that merely
loading the bridge or observing an attestation chain proves trusted pVM
execution.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.android_native_preflight import (
    run_android_native_preflight,
)


def _challenge(value: str) -> bytes:
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("challenge must be hex") from exc
    if not decoded or len(decoded) > 64:
        raise argparse.ArgumentTypeError(
            "challenge must encode 1..64 bytes"
        )
    return decoded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--challenge-hex", type=_challenge)
    args = parser.parse_args()

    receipt = run_android_native_preflight(
        bridge_path=args.bridge,
        challenge=args.challenge_hex,
    )
    payload = asdict(receipt)
    payload["state"] = str(receipt.state)
    payload["receipt_sha256"] = receipt.receipt_sha256

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
