import hashlib

from adversarial_sbox.phase2as import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DIFFERENCES,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
)
from adversarial_sbox.phase2as_runner import (
    _canonical_without_receipt,
    aggregate_cells,
    load_frozen_panel,
)


def _cell(depth: int, difference: int, scores: list[float]) -> dict:
    panel = load_frozen_panel()
    runs = []
    for candidate_index, candidate in enumerate(panel):
        for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "source_seed": int(candidate["source_seed"]),
                    "fingerprint": str(candidate["fingerprint"]),
                    "replicate": replicate,
                    "dataset_seed": dataset_seed,
                    "model_seed": model_seed,
                    "neural_advantage": scores[candidate_index],
                    "null_advantage": 0.01,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2as_depth_attenuation_cell",
        "architecture": ARCHITECTURE,
        "depth": depth,
        "input_difference": difference,
        "pair_count": 1,
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload


def test_phase2as_synthetic_aggregate_supports_strong_monotonic_attenuation():
    scores = {
        3: [0.10, 0.08, 0.06, 0.04, 0.02, 0.00],
        4: [0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
        5: [0.055, 0.052, 0.049, 0.046, 0.043, 0.040],
    }
    cells = [
        _cell(depth, difference, scores[depth])
        for depth in (3, 4, 5)
        for difference in DIFFERENCES
    ]
    result = aggregate_cells(cells)
    assert result["total_trainings"] == 288
    assert result["training_count_exact"] is True
    assert result["panel_revalidated"] is True
    assert result["deterministic_receipts"] is True
    assert result["signal_all_depths"] is True
    assert result["prerequisites_pass"] is True
    assert result["attenuation_criteria"] == {
        "H3_gt_H4_gt_H5": True,
        "H5_over_H4_le_0_50": True,
        "R3_ge_R4_gt_R5": True,
        "R5_over_R4_le_0_75": True,
    }
    assert result["verdict"] == "phase2as_depth_attenuation_supported"
    assert result["neural_evolutionary_pressure"] is False
