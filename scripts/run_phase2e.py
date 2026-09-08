#!/usr/bin/env python3
"""Run Phase 2E diagnostics from already-frozen Phase 2D JSON artifacts only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adversarial_sbox.phase2e import (
    INCONCLUSIVE_STATUS,
    VALID_STATUS,
    analyze_phase2e,
)


def _json_files(root: Path, filename: str) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    return sorted(path for path in root.rglob(filename) if path.is_file())


def _load_one(root: Path, filename: str) -> dict[str, Any]:
    matches = _json_files(root, filename)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename!r} under {root}, found {len(matches)}"
        )
    return json.loads(matches[0].read_text(encoding="utf-8"))


def _canonical_text(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-root", type=Path, required=True)
    parser.add_argument("--terminal-freeze-root", type=Path, required=True)
    parser.add_argument("--aggregate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--reverse-input",
        action="store_true",
        help="Reverse the 36 arm files before analysis to prove traversal-order invariance.",
    )
    args = parser.parse_args()

    arm_paths = _json_files(args.arm_root, "arm.json")
    if args.reverse_input:
        arm_paths = list(reversed(arm_paths))
    arm_results = [json.loads(path.read_text(encoding="utf-8")) for path in arm_paths]

    terminal_freeze = _load_one(
        args.terminal_freeze_root, "phase2d-terminal-freeze.json"
    )
    aggregate = _load_one(args.aggregate_root, "phase2d-result.json")

    result = analyze_phase2e(arm_results, terminal_freeze, aggregate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_canonical_text(result), encoding="utf-8")

    print("PHASE2E_STATUS:", result["status"])
    print("SOURCE_CELL_COUNT:", result.get("source_cell_count"))
    print("PHASE2E_SHA256:", result["scientific_payload_sha256"])
    if result["status"] == INCONCLUSIVE_STATUS:
        print("PROVENANCE_FAILURES:", json.dumps(result.get("provenance_failures", [])))
        return 2
    if result["status"] != VALID_STATUS:
        raise RuntimeError(f"unexpected Phase 2E status {result['status']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
