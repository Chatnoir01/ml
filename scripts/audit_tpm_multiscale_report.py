"""Blind audit frozen 96 TPM source report without recomputing attacker runs.

Example:
    python scripts/audit_tpm_multiscale_report.py tpm_multiscale_96_report.json

The checker rejects altered aggregates, p-values, Wilson intervals,
synchronization/censor counts, secret-export fields or modified protocols.
It never turns experiment success into cryptographic security assurance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tpm_lab.multiscale_audit import audit_multiscale_receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_report", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.source_report.read_text(encoding="utf-8"))
    audited = audit_multiscale_receipt(raw)
    print(json.dumps(audited, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
