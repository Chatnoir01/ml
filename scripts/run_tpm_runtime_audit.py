"""Time the *already observed* TPM attackers on one machine.

--smoke measures first 2 trials, one repetition. --full measures all
previously observed 64 trials, two repetitions. Results are affected by
runner load and Python runtime and are NOT security guarantees.
"""
from __future__ import annotations

import argparse
import json

from tpm_lab.runtime_audit import TimingProtocol, run_runtime_audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--full", action="store_true")
    args = parser.parse_args()
    config = (
        TimingProtocol(first_trials=2, repeats=1)
        if args.smoke else TimingProtocol(first_trials=64, repeats=2)
    )
    output = run_runtime_audit(timing=config)
    output["execution_level"] = "engineering_smoke" if args.smoke else "retrospective_wall_time_audit"
    output["security_verdict"] = "NOT_ESTABLISHED"
    print(json.dumps(output, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
