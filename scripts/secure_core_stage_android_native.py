#!/usr/bin/env python3
"""Stage Secure Core Android-native sources into an AOSP checkout safely."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.aosp_native_staging import stage_android_native_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aosp-root", type=Path, required=True)
    parser.add_argument("--source-native-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Explicitly replace different allowlisted destination files.",
    )
    args = parser.parse_args()

    receipt = stage_android_native_sources(
        aosp_root=args.aosp_root,
        source_native_dir=args.source_native_dir,
        replace_existing=args.replace_existing,
    )
    payload = asdict(receipt)
    payload["receipt_sha256"] = receipt.receipt_sha256
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
