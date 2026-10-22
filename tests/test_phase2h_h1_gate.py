"""H1 model/probe proof availability; SHA receipts are not frozen model weights."""

from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2h_h1_gate import assess_h1_receipt_feasibility


def _arm_with_receipts() -> dict:
    checkpoints = []
    for generation in (0, 5, 10, 15):
        checkpoints.append({
            "generation": generation,
            "training_receipt_sha256": "a" * 64,
            "model_receipts": [
                {
                    "difference": difference,
                    "replicate": replicate,
                    "dataset_seed": 776003 + replicate,
                    "model_seed": 786009 + replicate,
                    "state_sha256": f"{generation * 100 + difference + replicate:064x}",
                }
                for difference in (1, 256)
                for replicate in range(8)
            ],
            "score_receipts": [{"fingerprint": "candidate", "neural_advantage": 0.2}],
        })
    return {"checkpoints": checkpoints}


def test_complete_model_hash_receipts_never_impersonate_saved_model_weights() -> None:
    result = assess_h1_receipt_feasibility(_arm_with_receipts())
    assert result["checkpoint_count"] == 4
    assert result["hash_receipt_grid_complete"] is True
    assert result["serialized_checkpoint_states_present"] is False
    assert result["checkpoint_probe_fields_present"] is False
    assert result["forgetting_matrix_go"] is False
    assert result["status"].startswith("NO_GO")
    assert all(cp["model_hash_receipts"] == 16 for cp in result["checkpoint_evidence"])


def test_model_hashes_and_checkpoint_scores_are_not_immutable_h1_probes() -> None:
    raw = _arm_with_receipts()
    raw["checkpoints"][0]["score_receipts"].append(
        {"fingerprint": "other", "neural_advantage": 0.1}
    )
    result = assess_h1_receipt_feasibility(raw)
    assert result["checkpoint_probe_fields_present"] is False
    assert result["forgetting_matrix_go"] is False


def test_fake_injected_model_states_do_not_auto_authorize_forgetting_matrix() -> None:
    raw = _arm_with_receipts()
    for checkpoint in raw["checkpoints"]:
        for receipt in checkpoint["model_receipts"]:
            receipt["state_bytes_b64"] = "FAKE_TEST_FIXTURE"
        checkpoint["immutable_probe_results"] = [1.0]
    result = assess_h1_receipt_feasibility(raw)
    assert result["serialized_checkpoint_states_present"] is True
    assert result["checkpoint_probe_fields_present"] is True
    assert result["forgetting_matrix_go"] is False
    assert all(not item["model_snapshot_independently_verified"] for item in result["checkpoint_evidence"])


def test_missing_or_duplicate_model_receipt_cannot_be_a_complete_grid() -> None:
    raw = _arm_with_receipts()
    raw["checkpoints"][0]["model_receipts"].pop()
    assert assess_h1_receipt_feasibility(raw)["hash_receipt_grid_complete"] is False
    raw = _arm_with_receipts()
    raw["checkpoints"][0]["model_receipts"][1] = copy.deepcopy(
        raw["checkpoints"][0]["model_receipts"][0]
    )
    assert assess_h1_receipt_feasibility(raw)["hash_receipt_grid_complete"] is False


def test_corrupt_model_hash_rejected_as_complete_grid() -> None:
    raw = _arm_with_receipts()
    raw["checkpoints"][0]["model_receipts"][0]["state_sha256"] = "not-a-hash"
    assert assess_h1_receipt_feasibility(raw)["hash_receipt_grid_complete"] is False


def test_duplicate_or_missing_checkpoint_is_rejected() -> None:
    raw = _arm_with_receipts()
    raw["checkpoints"].append(dict(raw["checkpoints"][0]))
    with pytest.raises(ValueError, match="duplicate or unexpected"):
        assess_h1_receipt_feasibility(raw)
    raw = _arm_with_receipts()
    raw["checkpoints"].pop()
    with pytest.raises(ValueError, match="incomplete"):
        assess_h1_receipt_feasibility(raw)


def test_missing_all_model_receipts_is_unknown_not_a_go() -> None:
    raw = _arm_with_receipts()
    for checkpoint in raw["checkpoints"]:
        checkpoint.pop("model_receipts")
    result = assess_h1_receipt_feasibility(raw)
    assert result["hash_receipt_grid_complete"] is False
    assert result["forgetting_matrix_go"] is False
    assert all(row["model_hash_receipts"] == 0 for row in result["checkpoint_evidence"])
