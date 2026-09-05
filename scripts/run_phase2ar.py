#!/usr/bin/env python3
"""CLI for the frozen Phase 2A-R diagnostic; does not alter evolution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2ar_runner import aggregate_cells, run_cell


def _write(payload: dict, output: str) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    Path(output).write_text(text, encoding="utf-8")
    print(text, end="")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--regime", choices=("A", "B", "C", "D"))
    mode.add_argument("--aggregate-files", nargs="+")
    parser.add_argument("--difference", type=lambda value: int(value, 0))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.regime is not None:
        if args.difference is None:
            parser.error("--difference is required with --regime")
        payload = run_cell(args.regime, args.difference)
    else:
        if args.difference is not None:
            parser.error("--difference is invalid with --aggregate-files")
        payload = aggregate_cells(
            [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.aggregate_files]
        )
    _write(payload, args.output)


if __name__ == "__main__":
    main()
