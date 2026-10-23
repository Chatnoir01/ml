"""Run paired TPM benchmark; no keys are generated or released."""
from __future__ import annotations
import argparse
import json
from tpm_lab.comparison import ComparisonPlan,compare


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke",action="store_true",help="2 short trials, engineering only")
    parser.add_argument("--trials",type=int,default=32)
    parser.add_argument("--seed",type=int,default=782023)
    args=parser.parse_args()
    plan=ComparisonPlan(trials=2 if args.smoke else args.trials,master_seed=args.seed,max_steps=1000 if args.smoke else 8000,ensemble_size=3 if args.smoke else 9,genetic_population=3 if args.smoke else 16)
    result=compare(plan)
    result["security_verdict"]="NOT_ESTABLISHED"
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
