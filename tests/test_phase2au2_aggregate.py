"""Synthetic U2 aggregation tests; no neural training is executed."""

import hashlib
import json

import pytest

from adversarial_sbox.neural100 import PAIR_COUNT
from adversarial_sbox.phase2au2 import (
    ARCHITECTURE,
    BLOCK_A_DATASET_SEEDS,
    BLOCK_A_MODEL_SEEDS,
    BLOCK_B_DATASET_SEEDS,
    BLOCK_B_MODEL_SEEDS,
    DEPTH,
    DIFFERENCES,
    PANEL_DIGEST_SHA256,
)
from adversarial_sbox.phase2au2_runner import (
    EXPECTED_TEST_SIZE,
    EXPECTED_TRAIN_SIZE,
    EXPECTED_VALIDATION_SIZE,
    aggregate_cells,
    load_frozen_panel,
)


def _receipt(payload: dict) -> str:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    blob = json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
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
                    "train_size": EXPECTED_TRAIN_SIZE,
                    "validation_size": EXPECTED_VALIDATION_SIZE,
                    "test_size": EXPECTED_TEST_SIZE,
                    "neural_advantage": float(scores[candidate_index]),
                    "null_advantage": 0.0,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2au2_oracle_cell",
        "block": block,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "input_difference": int(difference),
        "pair_count": PAIR_COUNT,
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    payload["scientific_payload_sha256"] = _receipt(payload)
    return payload


def _qualified_cells() -> list[dict]:
    scores_a = [0.42, 0.36, 0.30, 0.24, 0.18, 0.12]
    scores_b = [0.41, 0.35, 0.29, 0.23, 0.17, 0.11]
    return [
        _cell("A", DIFFERENCES[0], scores_a),
        _cell("A", DIFFERENCES[1], scores_a),
        _cell("B", DIFFERENCES[0], scores_b),
        _cell("B", DIFFERENCES[1], scores_b),
    ]


def test_phase2au2_synthetic_qualified_path_is_deterministic():
    cells = _qualified_cells()
    first = aggregate_cells(cells)
    second = aggregate_cells(cells)
    assert first == second
    assert first["pair_count"] == PAIR_COUNT
    assert first["expected_split_sizes"] == {
        "train": EXPECTED_TRAIN_SIZE,
        "validation": EXPECTED_VALIDATION_SIZE,
        "test": EXPECTED_TEST_SIZE,
    }
    assert first["total_trainings"] == 192
    assert first["fresh_seed_registry_exact_and_disjoint"] is True
    assert first["prerequisites_pass"] is True
    assert all(first["qualification_checks"].values())
    assert first["verdict"] == "phase2au2_oracle_qualified"
    assert first["neural_evolutionary_pressure"] is False


def test_phase2au2_rejects_pair_count_drift():
    cells = _qualified_cells()
    cells[0]["pair_count"] = 1
    cells[0]["scientific_payload_sha256"] = _receipt(cells[0])
    with pytest.raises(ValueError, match="pair-count provenance mismatch"):
        aggregate_cells(cells)


def test_phase2au2_rejects_split_size_drift():
    cells = _qualified_cells()
    cells[0]["runs"][0]["train_size"] = 1
    cells[0]["scientific_payload_sha256"] = _receipt(cells[0])
    with pytest.raises(ValueError, match="train-size provenance mismatch"):
        aggregate_cells(cells)
