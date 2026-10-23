"""Run a retrospective TPM attacker-work audit of already-observed seeds.

--smoke audits first two trials. --full audits 64. NO NEW held-out claim,
no secret keys, and no 'equal CPU' claim.
"""
from __future__ import annotations

import argparse
import json

from tpm_lab.cost_audit import run_cost_audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--smoke", action="store_true")
    choices.add_argument("--full", action="store_true")
    args = parser.parse_args()
    report = run_cost_audit(first_trials=64 if args.full else 2)
    report["mode"] = "retrospective_64_trial_cost" if args.full else "engineering_smoke"
    report["security_verdict"] = "NOT_ESTABLISHED"
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
