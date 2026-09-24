#!/usr/bin/env python3
"""Inspect a local AOSP checkout for the Secretkeeper/AuthGraph API required by Secure Core."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.aosp_secretkeeper_contract import (
    inspect_aosp_secretkeeper_contract,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aosp-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt = inspect_aosp_secretkeeper_contract(args.aosp_root)
    payload = asdict(receipt)
    payload["receipt_sha256"] = receipt.receipt_sha256
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    raise SystemExit(
        0 if receipt.eligible_for_secure_core_native_authgraph else 2
    )


if __name__ == "__main__":
    main()
