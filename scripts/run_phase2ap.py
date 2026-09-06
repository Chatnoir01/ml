#!/usr/bin/env python3
"""CLI for the frozen Phase 2A-P R4 peak confirmation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2ap_runner import aggregate_cells, run_cell


def _write(payload: dict, output: str) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    Path(output).write_text(text, encoding="utf-8")
    print(text, end="")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--depth", type=int, choices=(3, 4, 5))
    mode.add_argument("--aggregate-files", nargs="+")
    parser.add_argument("--difference", type=lambda value: int(value, 0))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.depth is not None:
        if args.difference is None:
            parser.error("--difference is required with --depth")
        payload = run_cell(args.depth, args.difference)
    else:
        if args.difference is not None:
            parser.error("--difference is invalid with --aggregate-files")
        payload = aggregate_cells(
            [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.aggregate_files]
        )
    _write(payload, args.output)


if __name__ == "__main__":
    main()
