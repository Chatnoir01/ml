#!/usr/bin/env python3
"""Build Secure Core's identity-bound Secretkeeper SkSession in a locked AOSP tree.

This command requires:
- the reviewed Android 17 Secretkeeper/hardware-interface revisions;
- a contract lock created by secure_core_aosp_secretkeeper_preflight.py;
- the Secure Core android_native directory already integrated inside AOSP.

The receipt records only hashes and the Soong return code. A successful build is
source-integration evidence, not proof of pVM execution or hostile-host resistance.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from secure_core_mobile.aosp_verified_session_build import (
    run_verified_session_soong_build,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aosp-root", type=Path, required=True)
    parser.add_argument("--secure-core-native-dir", type=Path, required=True)
    parser.add_argument("--contract-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    receipt = run_verified_session_soong_build(
        aosp_root=args.aosp_root,
        secure_core_android_native_dir=args.secure_core_native_dir,
        contract_lock_path=args.contract_lock,
        timeout=args.timeout,
    )
    payload = asdict(receipt)
    payload["receipt_sha256"] = receipt.receipt_sha256
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    raise SystemExit(0 if receipt.build_succeeded else 2)


if __name__ == "__main__":
    main()
