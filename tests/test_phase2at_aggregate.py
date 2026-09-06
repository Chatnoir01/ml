import hashlib

from adversarial_sbox.phase2at import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DIFFERENCES,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
)
from adversarial_sbox.phase2at_runner import (
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
        "experiment": "phase2at_depth_profile_cell",
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


def test_phase2at_synthetic_aggregate_replicates_depth4_peak():
    scores = {
        3: [0.910, 0.908, 0.906, 0.904, 0.902, 0.900],
        4: [0.35, 0.33, 0.31, 0.29, 0.27, 0.25],
        5: [0.060, 0.056, 0.052, 0.048, 0.044, 0.040],
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
    assert result["profile_criteria"]["H4_gt_H3"] is True
    assert result["profile_criteria"]["H4_gt_H5"] is True
    assert result["profile_criteria"]["R4_gt_R3"] is True
    assert result["profile_criteria"]["R4_gt_R5"] is True
    assert result["profile_criteria"]["M3_gt_M4_gt_M5"] is True
    assert result["profile_criteria"]["depth4_p_lt_0_05"] is True
    assert result["verdict"] == "phase2at_depth4_peak_replicated"
    assert result["neural_evolutionary_pressure"] is False
