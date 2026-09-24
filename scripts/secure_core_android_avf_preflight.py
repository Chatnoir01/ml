#!/usr/bin/env python3
"""Run Secure Core's local Android/AVF guest preflight and emit JSON.

The report contains no Secretkeeper public-key bytes, only profile/digest
metadata. It is diagnostic and does not itself establish platform authority.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.android_avf_preflight import run_avf_guest_preflight


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt = run_avf_guest_preflight()
    payload = asdict(receipt)
    payload["state"] = str(receipt.state)
    payload["receipt_sha256"] = receipt.receipt_sha256
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
