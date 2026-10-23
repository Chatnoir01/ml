"""Audit a TPM trial-report JSON and print exploratory paired comparisons."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tpm_lab.paired_stats import audit_paired_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = audit_paired_report(json.loads(args.report.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
