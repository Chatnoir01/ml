"""Run or aggregate the frozen Phase-2A Neural Oracle qualification experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2a_runner import aggregate_cells, run_cell


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--side", choices=("oracle", "challenger"))
    parser.add_argument("--input-difference", type=lambda value: int(value, 0))
    parser.add_argument("--aggregate-files", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.aggregate_files:
        if args.side is not None or args.input_difference is not None:
            raise SystemExit("cell arguments cannot be combined with --aggregate-files")
        results = [
            json.loads(path.read_text(encoding="utf-8")) for path in args.aggregate_files
        ]
        first = aggregate_cells(results)
        second = aggregate_cells(results)
        if _canonical(first) != _canonical(second):
            raise RuntimeError("Phase 2A aggregate analysis is not deterministic")
        payload = first
    else:
        if args.side is None or args.input_difference is None:
            raise SystemExit("--side and --input-difference are required for a cell run")
        payload = run_cell(args.side, args.input_difference)

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
