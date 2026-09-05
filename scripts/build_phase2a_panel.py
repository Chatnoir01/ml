"""Build the frozen Phase-2A fresh classical panel without neural execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.experiment_seeds import PHASE1O_CONFIRM_RESERVED_SEEDS
from adversarial_sbox.phase2a import (
    PANEL_SIZE,
    CandidateRecord,
    _replay_phase1o_arm_a,
    panel_digest,
    select_fresh_panel,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_seed_payload(seed: int) -> dict[str, object]:
    """Replay one frozen confirmation seed twice and emit full terminal records."""

    seed = int(seed)
    if seed not in PHASE1O_CONFIRM_RESERVED_SEEDS:
        raise ValueError(f"seed {seed} is not reserved for Phase 2A reconstruction")
    first = _replay_phase1o_arm_a(seed)
    second = _replay_phase1o_arm_a(seed)
    first_payload = [record.canonical_payload() for record in first]
    second_payload = [record.canonical_payload() for record in second]
    if _canonical(first_payload) != _canonical(second_payload):
        raise RuntimeError(f"Phase 2A seed {seed} replay is not deterministic")
    return {
        "phase": "2A-panel-seed",
        "seed": seed,
        "deterministic_replay": True,
        "neural_training_executed": False,
        "terminal_records": first_payload,
    }


def _record_from_payload(payload: dict[str, object]) -> CandidateRecord:
    return CandidateRecord(
        source_seed=int(payload["source_seed"]),
        fingerprint=str(payload["fingerprint"]),
        sbox=tuple(int(value) for value in payload["sbox"]),
        differential_uniformity=int(payload["differential_uniformity"]),
        nonlinearity=int(payload["nonlinearity"]),
        max_linear_correlation=int(payload["max_linear_correlation"]),
        algebraic_degree=int(payload["algebraic_degree"]),
        sac_score=float(payload["sac_score"]),
    )


def build_panel_from_seed_payloads(seed_payloads: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate the nine independently replayed seed receipts into the panel."""

    if tuple(sorted(int(item["seed"]) for item in seed_payloads)) != tuple(
        sorted(PHASE1O_CONFIRM_RESERVED_SEEDS)
    ):
        raise ValueError("Phase 2A panel aggregation requires exactly the nine reserved seeds")
    if not all(bool(item.get("deterministic_replay")) for item in seed_payloads):
        raise RuntimeError("Phase 2A seed replay determinism receipt failed")
    if any(bool(item.get("neural_training_executed")) for item in seed_payloads):
        raise RuntimeError("neural training is forbidden during Phase 2A panel reconstruction")

    records: list[CandidateRecord] = []
    for item in seed_payloads:
        seed = int(item["seed"])
        for raw in item["terminal_records"]:
            record = _record_from_payload(raw)
            if record.source_seed != seed:
                raise RuntimeError("Phase 2A seed/source provenance mismatch")
            records.append(record)

    panel = select_fresh_panel(records)
    if len(panel) != PANEL_SIZE:
        raise RuntimeError("Phase 2A panel size drift")

    committed: list[dict[str, object]] = []
    for record in panel:
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
        committed.append(record.canonical_payload())

    return {
        "phase": "2A-panel",
        "panel_size": PANEL_SIZE,
        "panel_digest_sha256": panel_digest(panel),
        "deterministic_replay": True,
        "classical_revalidation": True,
        "neural_training_executed": False,
        "source_seeds": list(PHASE1O_CONFIRM_RESERVED_SEEDS),
        "candidates": committed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--aggregate-files", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.aggregate_files:
        if args.seed is not None:
            raise SystemExit("--seed cannot be combined with --aggregate-files")
        seed_payloads = [
            json.loads(path.read_text(encoding="utf-8")) for path in args.aggregate_files
        ]
        first = build_panel_from_seed_payloads(seed_payloads)
        second = build_panel_from_seed_payloads(seed_payloads)
        if _canonical(first) != _canonical(second):
            raise RuntimeError("Phase 2A panel aggregation is not deterministic")
        payload = first
    else:
        if args.seed is None:
            raise SystemExit("--seed is required unless --aggregate-files is used")
        payload = build_seed_payload(args.seed)

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
