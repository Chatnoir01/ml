#!/usr/bin/env python3
"""Prepare a candidate Android AVF authoritative trust-profile pin offline.

This tool never activates trust. It only emits a deterministic receipt and the
profile SHA-256 that must later be provisioned through a separate protected
deployment channel.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from secure_core_mobile.avf_trust_provisioning import prepare_authoritative_profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchors-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile-version", type=int, default=1)
    args = parser.parse_args()

    _, receipt = prepare_authoritative_profile(
        args.anchors_dir,
        profile_version=args.profile_version,
    )
    payload = {
        "schema_version": receipt.schema_version,
        "profile_version": receipt.profile_version,
        "anchor_count": receipt.anchor_count,
        "anchor_sha256": list(receipt.anchor_sha256),
        "profile_sha256": receipt.profile_sha256,
        "authorization_status": receipt.authorization_status,
        "receipt_sha256": receipt.receipt_sha256,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
