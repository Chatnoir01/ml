"""Shared synthetic full-provenance Phase 2G cell fixtures for CI only.

No neural training, real evolution, or held-out H access occurs here.  The helper
only constructs deterministic receipts matching the frozen scientific-cell schema
so downstream freeze/validation/aggregate tests exercise the strict pre-H gate.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from adversarial_sbox.phase2g import (
    CHECKPOINT_GENERATIONS,
    SCORING_DATASET_BASE_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from adversarial_sbox.provenance import fingerprint_sbox


def canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def attach_sha(payload: dict, field: str = "scientific_payload_sha256") -> dict:
    clean = {key: value for key, value in payload.items() if key != field}
    payload[field] = hashlib.sha256(canonical(clean)).hexdigest()
    return payload


def sbox(offset: int) -> list[int]:
    offset = int(offset) % 256
    return list(range(offset, 256)) + list(range(offset))


def _population_digest(fingerprints: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(fingerprints).encode("ascii")).hexdigest()


def make_full_cell(
    *,
    seed: int,
    arm: str,
    arm_index: int,
    terminal_offset: int | None = None,
    terminal_classical: Mapping[str, object] | None = None,
    selection_events: Sequence[Mapping[str, object]] = (),
    initial_salt: str = "matched",
) -> dict[str, object]:
    if terminal_offset is None:
        terminal_offset = (int(seed) + int(arm_index)) % 256
    terminal_sbox = sbox(terminal_offset)
    terminal_fingerprint = fingerprint_sbox(terminal_sbox)
    classical = dict(
        terminal_classical
        or {
            "admissible": True,
            "nonlinearity": 100 + int(arm_index),
            "differential_uniformity": 8,
            "max_abs_lat": 32,
            "algebraic_degree": 7,
        }
    )

    initial = [
        sha_text(f"{seed}:{initial_salt}:initial:{index}") for index in range(20)
    ]
    current = list(initial)
    generation_trace: list[dict[str, object]] = []
    classical_ledger: list[dict[str, object]] = []
    parent_map: dict[str, str] = {}
    checkpoint_populations: dict[int, list[str]] = {}
    checkpoint_after: dict[int, list[str]] = {}

    def ledger_row(fingerprint: str, *, terminal: bool = False) -> dict[str, object]:
        return {
            "fingerprint": fingerprint,
            "nonlinearity": int(classical["nonlinearity"]) if terminal else 100,
            "differential_uniformity": int(classical["differential_uniformity"]) if terminal else 8,
            "max_abs_lat": int(classical["max_abs_lat"]) if terminal else 32,
            "sac_score": 0.5,
            "algebraic_degree": int(classical["algebraic_degree"]) if terminal else 7,
        }

    classical_ledger.extend(ledger_row(fingerprint) for fingerprint in initial)

    for generation in range(20):
        population_before = list(current)
        if generation in CHECKPOINT_GENERATIONS:
            checkpoint_populations[generation] = list(population_before)
        shortlist = list(population_before[:8])
        parents = list(shortlist[:4])
        proposals = [
            sha_text(f"{seed}:{arm}:proposal:{generation}:{index}")
            for index in range(16)
        ]
        if generation == 19:
            proposals[0] = terminal_fingerprint
        for index, proposal in enumerate(proposals):
            parent_map[proposal] = parents[index % len(parents)]
            classical_ledger.append(
                ledger_row(proposal, terminal=proposal == terminal_fingerprint)
            )
        next_population = [*population_before[:4], *proposals]
        generation_trace.append(
            {
                "generation": generation,
                "population_before": population_before,
                "shortlist": shortlist,
                "parents": parents,
                "proposals": proposals,
                "next_population": next_population,
            }
        )
        current = next_population
        if generation in (4, 9, 14, 19):
            checkpoint_after[generation - 4] = list(current)

    checkpoints: list[dict[str, object]] = []
    for checkpoint_index, generation in enumerate(CHECKPOINT_GENERATIONS):
        t_seeds = list(
            expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        m_seeds = list(
            expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, checkpoint_index)
        )
        q_seeds = list(
            expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        curriculum = (
            list(initial) if arm == "F" else list(checkpoint_populations[generation])
        )
        model_receipts = [
            {
                "difference": difference,
                "replicate": replicate,
                "dataset_seed": t_seeds[replicate],
                "model_seed": m_seeds[replicate],
                "state_sha256": sha_text(
                    f"{seed}:{arm}:{generation}:{difference}:{replicate}:state"
                ),
            }
            for difference in (1, 256)
            for replicate in range(8)
        ]
        checkpoints.append(
            {
                "generation": generation,
                "checkpoint_generation": generation,
                "block_start_generation": generation,
                "block_end_generation": generation + 5,
                "selection_enabled": arm != "C",
                "training_count": 16,
                "training_receipt_sha256": sha_text(
                    f"{seed}:{arm}:{generation}:training"
                ),
                "curriculum_fingerprints": curriculum,
                "curriculum_digest_sha256": _population_digest(curriculum),
                "population_before_fingerprints": list(checkpoint_populations[generation]),
                "population_after_fingerprints": list(checkpoint_after[generation]),
                "classical_evaluations": 80,
                "shuffle_rng_seed": (
                    int(sha_text(f"shuffle:{seed}:{generation}")[:16], 16)
                    if arm == "S"
                    else None
                ),
                "training_dataset_seeds": t_seeds,
                "training_model_seeds": m_seeds,
                "scoring_dataset_seeds": q_seeds,
                "model_receipts": model_receipts,
                "score_cache_hits": 0,
                "score_cache_misses": 0,
                "score_receipts": [],
            }
        )

    assert len(classical_ledger) == 340
    assert len({row["fingerprint"] for row in classical_ledger}) == 340
    assert terminal_fingerprint in current

    payload: dict[str, object] = {
        "schema_version": 1,
        "phase": "2G",
        "arm": arm,
        "seed": int(seed),
        "generation_count": 20,
        "classical_evaluations": 340,
        "checkpoint_training_count": 64,
        "checkpoint_trainings": 64,
        "initial_population_digest_sha256": _population_digest(initial),
        "terminal_population_digest_sha256": _population_digest(current),
        "terminal_sbox": terminal_sbox,
        "terminal_fingerprint": terminal_fingerprint,
        "terminal_classical": classical,
        "terminal_selection_rule": "historical_classical_only",
        "checkpoints": checkpoints,
        "selection_events": [dict(event) for event in selection_events],
        "generation_trace": generation_trace,
        "classical_evaluation_ledger": classical_ledger,
        "parent_map": parent_map,
        "lineage_diagnostics": [],
        "heldout_accessed": False,
    }
    return attach_sha(payload)
