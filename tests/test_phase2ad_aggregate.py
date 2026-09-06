"""Synthetic aggregate tests for Phase 2A-D; no neural training is executed."""

import hashlib
import json

from adversarial_sbox.phase2ad import ARCHITECTURE, DATASET_SEEDS, MODEL_SEEDS
from adversarial_sbox.phase2ad_runner import aggregate_cells, load_frozen_panel


def _cell(depth: int, difference: int, candidate_values: list[float]) -> dict:
    panel = load_frozen_panel()
    runs = []
    for candidate_index, candidate in enumerate(panel):
        for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "source_seed": candidate["source_seed"],
                    "fingerprint": candidate["fingerprint"],
                    "replicate": replicate,
                    "dataset_seed": dataset_seed,
                    "model_seed": model_seed,
                    "neural_advantage": candidate_values[candidate_index],
                    "null_advantage": 0.02,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2ad_depth_attenuation_cell",
        "depth": depth,
        "architecture": ARCHITECTURE,
        "input_difference": difference,
        "pair_count": 1,
        "panel_digest_sha256": "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30",
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["scientific_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def test_phase2ad_synthetic_strong_depth_collapse_is_supported():
    values = {
        3: [0.39, 0.26, 0.34, 0.30, 0.37, 0.41],
        4: [0.42, 0.24, 0.35, 0.29, 0.39, 0.44],
        5: [0.332, 0.326, 0.331, 0.329, 0.333, 0.330],
    }
    results = [
        _cell(depth, difference, values[depth])
        for depth in (3, 4, 5)
        for difference in (0x00000001, 0x00000100)
    ]

    aggregate = aggregate_cells(results)

    assert aggregate["total_trainings"] == 360
    assert aggregate["training_count_exact"] is True
    assert aggregate["panel_revalidated"] is True
    assert aggregate["deterministic_receipts"] is True
    assert aggregate["seed_registry_exact"] is True
    assert aggregate["neural_evolutionary_pressure"] is False
    assert aggregate["primary_requirements_pass"] is True
    assert aggregate["primary_4_to_5"]["delta"] > 0.0
    assert aggregate["primary_4_to_5"]["permutation_p"] < 0.05
    assert aggregate["primary_4_to_5"]["variance_ratio_V5_over_V4"] <= 0.75
    assert aggregate["verdict"] == "phase2ad_depth_attenuation_supported"
