"""Run an isolated TPM simulation; no private weights or keys are exported."""

from __future__ import annotations

import argparse
import json

from tpm_lab import TPMProtocol, run_study


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="three trials for quick checks")
    parser.add_argument("--seed", type=int, default=782023)
    args = parser.parse_args()
    p = TPMProtocol(master_seed=args.seed, trials=3 if args.smoke else 8)
    result = run_study(p)
    result["evaluation_level"] = "engineering_smoke" if args.smoke else "exploratory_pilot"
    result["security_verdict"] = "NO_CRYPTOGRAPHIC_SECURITY_ESTABLISHED"
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
