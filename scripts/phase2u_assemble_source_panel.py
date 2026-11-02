"""Phase 2U: assemble 19 original GitHub-source receipts into exact frozen panel.

Only the original source JSON bytes are inputs. This script never generates
replacement S-Boxes or neural labels. The existing Phase 2U source gate
recalculates all classical metrics and rejects old family/obvious clones.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from adversarial_sbox.phase2u_generate import PUBLIC_SEEDS, TARGET_CANDIDATES, digest
from adversarial_sbox.phase2u_panel import AdmissionRejected, aggregate

EXPECTED_PREFIX = PUBLIC_SEEDS[:19]
assert len(EXPECTED_PREFIX) == 19


def collect(source_root: Path) -> list[dict]:
    paths = list(source_root.glob("**/seed-*.json"))
    if len(paths) != len(EXPECTED_PREFIX):
        raise AdmissionRejected(
            f"expected exactly 19 original source JSONs, got {len(paths)}"
        )
    inputs: dict[int, dict] = {}
    for path in paths:
        if path.stat().st_size > 128 * 1024:
            raise AdmissionRejected("oversized original source")
        raw = path.read_bytes()
        entry = json.loads(raw)
        seed = entry.get("seed")
        if type(seed) is not int or seed not in EXPECTED_PREFIX:
            raise AdmissionRejected("seed outside frozen 19-source prefix")
        if path.name != f"seed-{seed}.json" or seed in inputs:
            raise AdmissionRejected("wrong filename or duplicate source seed")
        entry["_original_source_bytes_sha256_internal"] = hashlib.sha256(raw).hexdigest()
        # The original JSON bytes digest is derived independently for archive
        # verification, but must not be passed to admission or change its seal.
        inputs[seed] = entry
    originals = []
    for seed in EXPECTED_PREFIX:
        item = dict(inputs[seed])
        item.pop("_original_source_bytes_sha256_internal")
        originals.append(item)
    return originals


def create_source_panel(source_root: Path) -> dict:
    receipts = collect(source_root)
    panel = aggregate(receipts)
    if (panel["status"] != "PANEL_COMPLETE_NO_NEURAL_OUTCOMES"
            or panel["selected_count"] != TARGET_CANDIDATES
            or panel["examined_seed_count"] != len(EXPECTED_PREFIX)
            or panel["registered_seed_prefix"] != list(EXPECTED_PREFIX)):
        raise AdmissionRejected(
            "final prospective source panel not independently admitted"
        )
    if panel["new_neural_trainings"] != 0:
        raise AdmissionRejected("source is contaminated with neural outcomes")
    actual = dict(panel)
    claimed = actual.pop("panel_receipt_sha256")
    if digest(actual) != claimed:
        raise AdmissionRejected("panel receipt integrity mismatch")
    return panel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    panel = create_source_panel(args.input_root)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(panel, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
    print("FINAL_PHASE2U_SOURCE_PANEL_SHA256=" + panel["panel_receipt_sha256"])
    print("SOURCE_SEEDS=" + str(panel["examined_seed_count"]))
    print("SOURCE_CANDIDATES=" + str(panel["selected_count"]))
    print("NEW_NEURAL_TRAININGS=0")


if __name__ == "__main__":
    main()
