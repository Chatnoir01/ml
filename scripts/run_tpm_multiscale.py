"""Execute fixed TPM 3-scale fresh-seed study (research only).

--smoke runs one short engineering trial per scale, no security results.
--confirm runs all preregistered 32 trials per scale (96 total).
"""
from __future__ import annotations

import argparse
import json

from tpm_lab.multiscale import ScalePlan,run_multiscale


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke",action="store_true")
    mode.add_argument("--confirm",action="store_true")
    args=parser.parse_args()
    plan=ScalePlan() if args.confirm else ScalePlan(trials_per_scale=1,max_steps=300)
    report=run_multiscale(plan)
    report["execution_level"]="predeclared_96_trial_confirmation" if args.confirm else "engineering_smoke"
    report["security_verdict"]="NOT_ESTABLISHED"
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
