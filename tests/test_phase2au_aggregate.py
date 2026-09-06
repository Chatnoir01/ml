"""Synthetic aggregation contract for historical Phase 2A-U; no neural training."""

import hashlib
import json

from adversarial_sbox.phase2au import (
    ARCHITECTURE,
    BLOCK_A_DATASET_SEEDS,
    BLOCK_A_MODEL_SEEDS,
    BLOCK_B_DATASET_SEEDS,
    BLOCK_B_MODEL_SEEDS,
    DEPTH,
    DIFFERENCES,
    PANEL_DIGEST_SHA256,
)
from adversarial_sbox.phase2au_runner import aggregate_cells, load_frozen_panel


def _receipt(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _cell(block: str, difference: int, scores: list[float]) -> dict:
    panel = load_frozen_panel()
    dataset_seeds = BLOCK_A_DATASET_SEEDS if block == "A" else BLOCK_B_DATASET_SEEDS
    model_seeds = BLOCK_A_MODEL_SEEDS if block == "A" else BLOCK_B_MODEL_SEEDS
    runs = []
    for candidate_index, candidate in enumerate(panel):
        for replicate, (dataset_seed, model_seed) in enumerate(zip(dataset_seeds, model_seeds)):
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "source_seed": int(candidate["source_seed"]),
                    "fingerprint": str(candidate["fingerprint"]),
                    "replicate": replicate,
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": 1,
                    "validation_size": 1,
                    "test_size": 1,
                    "neural_advantage": float(scores[candidate_index]),
                    "null_advantage": 0.0,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2au_oracle_cell",
        "block": block,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "input_difference": int(difference),
        "pair_count": 1,
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    payload["scientific_payload_sha256"] = _receipt(payload)
    return payload


def test_phase2au_historical_stats_remain_deterministic_but_provenance_is_inconclusive():
    scores_a = [0.42, 0.36, 0.30, 0.24, 0.18, 0.12]
    scores_b = [0.41, 0.35, 0.29, 0.23, 0.17, 0.11]
    cells = [
        _cell("A", DIFFERENCES[0], scores_a),
        _cell("A", DIFFERENCES[1], scores_a),
        _cell("B", DIFFERENCES[0], scores_b),
        _cell("B", DIFFERENCES[1], scores_b),
    ]
    first = aggregate_cells(cells)
    second = aggregate_cells(cells)
    assert first == second
    assert first["total_trainings"] == 192
    assert first["fresh_seed_registry_exact_and_disjoint"] is False
    assert first["prerequisites_pass"] is False
    assert all(first["qualification_checks"].values())
    assert first["verdict"] == "phase2au_inconclusive_prerequisites"
    assert first["neural_evolutionary_pressure"] is False
