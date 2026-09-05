"""Build the frozen Phase-2A fresh classical panel without neural execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.phase2a import (
    PANEL_SIZE,
    panel_digest,
    reconstruct_fresh_panel,
)
from adversarial_sbox.provenance import fingerprint_sbox


def build_panel_payload() -> dict[str, object]:
    first = reconstruct_fresh_panel()
    second = reconstruct_fresh_panel()

    first_payload = [record.canonical_payload() for record in first]
    second_payload = [record.canonical_payload() for record in second]
    if first_payload != second_payload:
        raise RuntimeError("Phase 2A panel replay is not deterministic")
    if len(first) != PANEL_SIZE:
        raise RuntimeError("Phase 2A panel size drift")

    records: list[dict[str, object]] = []
    for record in first:
        metrics = evaluate_classical(record.sbox)
        if fingerprint_sbox(record.sbox) != record.fingerprint:
            raise RuntimeError("Phase 2A committed fingerprint mismatch")
        if (
            metrics.differential_uniformity != record.differential_uniformity
            or metrics.nonlinearity != record.nonlinearity
            or metrics.max_linear_correlation != record.max_linear_correlation
            or metrics.algebraic_degree != record.algebraic_degree
            or metrics.sac_score != record.sac_score
        ):
            raise RuntimeError("Phase 2A independent classical revalidation mismatch")
        records.append(record.canonical_payload())

    return {
        "phase": "2A-panel",
        "panel_size": PANEL_SIZE,
        "panel_digest_sha256": panel_digest(first),
        "deterministic_replay": True,
        "classical_revalidation": True,
        "neural_training_executed": False,
        "candidates": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_panel_payload()
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
