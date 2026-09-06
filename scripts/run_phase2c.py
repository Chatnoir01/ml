#!/usr/bin/env python3
"""Run frozen Phase 2C-A diagnostics from existing Phase 2B arm JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2c_diagnostics import analyze_phase2c_artifacts, dump_phase2c_diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm-files", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payloads = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.arm_files]
    result = analyze_phase2c_artifacts(payloads)
    Path(args.output).write_text(dump_phase2c_diagnostics(result), encoding="utf-8")


if __name__ == "__main__":
    main()
