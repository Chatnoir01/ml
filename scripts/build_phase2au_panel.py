"""Build the preregistered Phase-2A-U fresh classical panel without neural execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.phase2au import (
    CLASSICAL_BUDGET,
    CLASSICAL_SOURCE_SEEDS,
    PANEL_SIZE,
    CandidateRecord,
    is_phase2au_eligible,
    panel_digest,
    replay_phase1o_arm_a,
    select_phase2au_panel,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_seed_payload(seed: int) -> dict[str, object]:
    """Replay one frozen Phase-2A-U source seed twice and emit full terminal records."""

    seed = int(seed)
    if seed not in CLASSICAL_SOURCE_SEEDS:
        raise ValueError(f"seed {seed} is not frozen for Phase 2A-U reconstruction")

    first = replay_phase1o_arm_a(seed)
    second = replay_phase1o_arm_a(seed)
    first_payload = [record.canonical_payload() for record in first]
    second_payload = [record.canonical_payload() for record in second]
    if _canonical(first_payload) != _canonical(second_payload):
        raise RuntimeError(f"Phase 2A-U seed {seed} replay is not deterministic")

    return {
        "phase": "2A-U-panel-seed",
        "seed": seed,
        "classical_evaluations_per_replay": CLASSICAL_BUDGET,
        "replays": 2,
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


def _eligible_per_seed(records: list[CandidateRecord]) -> dict[int, CandidateRecord]:
    per_seed: dict[int, CandidateRecord] = {}
    for record in sorted(records, key=lambda item: (item.source_seed, item.fingerprint)):
        if record.source_seed not in CLASSICAL_SOURCE_SEEDS:
            continue
        if not is_phase2au_eligible(record):
            continue
        current = per_seed.get(record.source_seed)
        if current is None or record.fingerprint < current.fingerprint:
            per_seed[record.source_seed] = record
    return per_seed


def _revalidate(record: CandidateRecord) -> None:
    metrics = evaluate_classical(record.sbox)
    if fingerprint_sbox(record.sbox) != record.fingerprint:
        raise RuntimeError("Phase 2A-U committed fingerprint mismatch")
    if (
        metrics.differential_uniformity != record.differential_uniformity
        or metrics.nonlinearity != record.nonlinearity
        or metrics.max_linear_correlation != record.max_linear_correlation
        or metrics.algebraic_degree != record.algebraic_degree
        or metrics.sac_score != record.sac_score
    ):
        raise RuntimeError("Phase 2A-U independent classical revalidation mismatch")
    if not is_phase2au_eligible(record):
        raise RuntimeError("Phase 2A-U selected record no longer satisfies eligibility")


def build_panel_from_seed_payloads(seed_payloads: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate exactly the twelve preregistered source-seed replay receipts."""

    actual_seeds = tuple(sorted(int(item["seed"]) for item in seed_payloads))
    expected_seeds = tuple(sorted(CLASSICAL_SOURCE_SEEDS))
    if actual_seeds != expected_seeds:
        raise ValueError("Phase 2A-U aggregation requires exactly the twelve frozen source seeds")
    if not all(bool(item.get("deterministic_replay")) for item in seed_payloads):
        raise RuntimeError("Phase 2A-U seed replay determinism receipt failed")
    if any(bool(item.get("neural_training_executed")) for item in seed_payloads):
        raise RuntimeError("neural training is forbidden during Phase 2A-U panel reconstruction")
    if not all(int(item.get("classical_evaluations_per_replay", -1)) == CLASSICAL_BUDGET for item in seed_payloads):
        raise RuntimeError("Phase 2A-U classical budget receipt drift")
    if not all(int(item.get("replays", -1)) == 2 for item in seed_payloads):
        raise RuntimeError("Phase 2A-U requires exactly two deterministic replays per source seed")

    records: list[CandidateRecord] = []
    for item in seed_payloads:
        seed = int(item["seed"])
        for raw in item["terminal_records"]:
            record = _record_from_payload(raw)
            if record.source_seed != seed:
                raise RuntimeError("Phase 2A-U seed/source provenance mismatch")
            records.append(record)

    per_seed = _eligible_per_seed(records)
    eligible_receipts = [
        {
            "source_seed": seed,
            "fingerprint": record.fingerprint,
            "sac_score": record.sac_score,
        }
        for seed, record in sorted(per_seed.items())
    ]

    common = {
        "phase": "2A-U-panel",
        "source_seeds": list(CLASSICAL_SOURCE_SEEDS),
        "source_seed_count": len(CLASSICAL_SOURCE_SEEDS),
        "classical_evaluations_per_replay": CLASSICAL_BUDGET,
        "replays_per_seed": 2,
        "deterministic_replay": True,
        "neural_training_executed": False,
        "eligible_source_seed_count": len(per_seed),
        "eligible_source_representatives": eligible_receipts,
    }

    if len(per_seed) < PANEL_SIZE:
        return {
            **common,
            "panel_ready": False,
            "panel_size": 0,
            "panel_digest_sha256": None,
            "classical_revalidation": False,
            "classification": "phase2au_inconclusive_prerequisites",
            "candidates": [],
        }

    panel = select_phase2au_panel(records)
    if len(panel) != PANEL_SIZE:
        raise RuntimeError("Phase 2A-U panel size drift")

    committed: list[dict[str, object]] = []
    for record in panel:
        _revalidate(record)
        committed.append(record.canonical_payload())

    return {
        **common,
        "panel_ready": True,
        "panel_size": PANEL_SIZE,
        "panel_digest_sha256": panel_digest(panel),
        "classical_revalidation": True,
        "classification": "phase2au_panel_ready",
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
            raise RuntimeError("Phase 2A-U panel aggregation is not deterministic")
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
