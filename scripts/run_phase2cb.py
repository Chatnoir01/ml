#!/usr/bin/env python3
"""Run the preregistered Phase 2C-B frozen-score instrumented replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.phase2cb_runner import (
    aggregate_replay_cells,
    dump_phase2cb_result,
    run_replay_cell,
)

AUTHORIZATION_TOKEN = "AUTHORIZED_PHASE2CB_FROZEN_SCORE_REPLAY"


def _require_execution_marker() -> None:
    marker = Path("research/PHASE2CB_EXECUTE.md")
    if not marker.exists() or marker.read_text().strip() != AUTHORIZATION_TOKEN:
        raise SystemExit("Phase 2C-B real replay is not authorized")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm-files", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    _require_execution_marker()
    originals = [json.loads(Path(path).read_text()) for path in args.arm_files]
    cells = [run_replay_cell(payload) for payload in originals]
    aggregate = aggregate_replay_cells(cells)
    Path(args.output).write_text(dump_phase2cb_result(aggregate))


if __name__ == "__main__":
    main()
