"""Run *toy* Alice/Bob/Eve experiments, never production encryption.

Default mode is a short engineering smoke. --full opts in to the fixed v1
research budget; no automatic CI workflow executes a full experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from neural_crypto_lab import DEFAULT_SEED, Protocol, run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true", help="short test, no science claim")
    mode.add_argument("--full", action="store_true", help="run fixed v1 research budget")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.full:
        protocol = Protocol()
    else:
        protocol = Protocol(train_steps=4, challenger_steps=4, batch_size=24, eval_samples=96)

    result = run_experiment(seed=args.seed, protocol=protocol)
    result["mode"] = "full_exploratory" if args.full else "smoke_only"
    # These are engineering observations; never infer provable secrecy from Eve error.
    result["security_verdict"] = "NOT_EVALUATED_CRYPTOGRAPHICALLY"
    raw = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
