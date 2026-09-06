"""RED-first aggregate statistics for Phase 2B; synthetic inputs only."""

import copy
import hashlib
import json

from adversarial_sbox.phase2b import (
    ARCHITECTURE,
    DEPTH,
    DIFFERENCES,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    PAIR_COUNT,
    SPLIT_SIZES,
)
from adversarial_sbox.phase2b_aggregate import (
    exact_one_sided_sign_p,
    score_payload_integrity,
    summarize_support,
)


def _synthetic_score_payload() -> dict:
    runs = []
    for difference in DIFFERENCES:
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(FITNESS_DATASET_SEEDS, FITNESS_MODEL_SEEDS)
        ):
            runs.append(
                {
                    "difference": int(difference),
                    "replicate": replicate,
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": SPLIT_SIZES[0],
                    "validation_size": SPLIT_SIZES[1],
                    "test_size": SPLIT_SIZES[2],
                    "neural_advantage": 0.4,
                    "null_advantage": 0.02,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2b_candidate_oracle_score",
        "purpose": "fitness",
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "split_sizes": list(SPLIT_SIZES),
        "fingerprint": "synthetic-fingerprint",
        "training_count": 16,
        "neural_advantage": 0.4,
        "null_advantage": 0.02,
        "runs": runs,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["scientific_payload_sha256"] = hashlib.sha256(blob).hexdigest()
    return payload


def test_exact_sign_test_for_eight_of_nine_wins_is_preregistered_significant():
    assert abs(exact_one_sided_sign_p(8, 1) - (10 / 512)) < 1e-15
    assert exact_one_sided_sign_p(9, 0) == 1 / 512


def test_zero_differences_are_excluded_from_sign_test_not_counted_as_wins():
    assert exact_one_sided_sign_p(8, 0) == 1 / 256


def test_full_score_payload_integrity_rejects_seed_or_receipt_tampering():
    payload = _synthetic_score_payload()
    assert score_payload_integrity(
        payload,
        purpose="fitness",
        dataset_seeds=FITNESS_DATASET_SEEDS,
        model_seeds=FITNESS_MODEL_SEEDS,
    ) is True

    tampered_seed = copy.deepcopy(payload)
    tampered_seed["runs"][0]["dataset_seed"] += 1
    assert score_payload_integrity(
        tampered_seed,
        purpose="fitness",
        dataset_seeds=FITNESS_DATASET_SEEDS,
        model_seeds=FITNESS_MODEL_SEEDS,
    ) is False

    tampered_hash = copy.deepcopy(payload)
    tampered_hash["scientific_payload_sha256"] = "0" * 64
    assert score_payload_integrity(
        tampered_hash,
        purpose="fitness",
        dataset_seeds=FITNESS_DATASET_SEEDS,
        model_seeds=FITNESS_MODEL_SEEDS,
    ) is False


def test_synthetic_supported_summary_requires_all_six_gates():
    c = [0.40] * 9
    o = [0.35] * 9
    s = [0.39] * 9
    result = summarize_support(
        control=c,
        oracle=o,
        shuffled=s,
        classical_non_degradation=True,
    )
    assert result["checks"]["o_wins_c_8_of_9"] is True
    assert result["checks"]["paired_sign_p_lt_005"] is True
    assert result["checks"]["mean_reduction_ge_002"] is True
    assert result["checks"]["o_wins_s_6_of_9"] is True
    assert result["checks"]["o_reduction_gt_s_reduction"] is True
    assert result["verdict"] == "phase2b_oracle_pressure_supported"


def test_classical_degradation_is_valid_but_not_supported():
    result = summarize_support(
        control=[0.40] * 9,
        oracle=[0.30] * 9,
        shuffled=[0.39] * 9,
        classical_non_degradation=False,
    )
    assert result["verdict"] == "phase2b_oracle_pressure_not_supported"
