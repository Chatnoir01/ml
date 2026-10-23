"""Run independently reserved TPM held-out trial set; research only.

CLI requires explicit --smoke (2 trials) or --confirm (frozen 64 trials).
No arbitrary seed overrides and no direct CryptoWall integration.
"""
from __future__ import annotations

import argparse
import json

from tpm_lab.heldout import HoldoutPlan, run_holdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    plan = HoldoutPlan() if args.confirm else HoldoutPlan(trials=2, max_steps=1000)
    result = run_holdout(plan)
    result["execution_mode"] = "reserved_64_trial_confirmation" if args.confirm else "engineering_smoke"
    result["security_verdict"] = "NOT_ESTABLISHED"
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
