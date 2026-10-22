"""Checkpoint-0 provenance audit must not conflate state-hash drift with causal drift."""

from __future__ import annotations

import copy
import hashlib

import pytest

from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2h_baseline import audit_checkpoint0_baseline


def _arm(arm: str, *, mismatch: bool = False) -> dict:
    curriculum = [f"candidate-{i:02d}" for i in range(20)]
    digest = hashlib.sha256("\n".join(sorted(curriculum)).encode("ascii")).hexdigest()
    models = []
    for difference in (1, 256):
        for replicate in range(8):
            fingerprint = f"{difference * 100 + replicate:064x}"
            if mismatch and difference == 256 and replicate in (0, 1, 7):
                fingerprint = f"{difference * 1000 + replicate:064x}"
            models.append({
                "difference": difference,
                "replicate": replicate,
                "dataset_seed": TRAINING_DATASET_BASE_SEEDS[replicate],
                "model_seed": TRAINING_MODEL_BASE_SEEDS[replicate],
                "state_sha256": fingerprint,
            })
    return {
        "arm": arm,
        "checkpoints": [{
            "generation": 0,
            "curriculum_fingerprints": curriculum,
            "curriculum_digest_sha256": digest,
            "model_receipts": models,
            "training_dataset_seeds": list(TRAINING_DATASET_BASE_SEEDS),
            "training_model_seeds": list(TRAINING_MODEL_BASE_SEEDS),
            "training_receipt_sha256": (arm.lower() * 64),
        }],
    }


def test_identical_declared_inputs_and_model_hashes_pass_comparability() -> None:
    result = audit_checkpoint0_baseline(_arm("A"), _arm("F"))
    assert result["status"] == "MATCHED_DECLARED_INPUTS_MATCHED_MODEL_HASHES"
    assert result["same_declared_training_inputs"] is True
    assert result["model_state_sha256_mismatches"] == 0
    assert result["causal_explanation_established"] is False


def test_same_declared_inputs_but_model_hashes_differ_reports_pattern() -> None:
    result = audit_checkpoint0_baseline(_arm("A", mismatch=True), _arm("F"))
    assert result["status"] == "MATCHED_DECLARED_INPUTS_DIFFERENT_MODEL_HASHES"
    assert result["model_state_sha256_mismatches"] == 3
    assert result["mismatches_by_difference"]["1"]["different_model_state_sha256_count"] == 0
    assert result["mismatches_by_difference"]["256"]["different_replicates"] == [0, 1, 7]
    assert result["causal_explanation_established"] is False


def test_arm_bound_training_receipts_do_not_count_as_state_mismatch() -> None:
    adaptive, fixed = _arm("A"), _arm("F")
    assert adaptive["checkpoints"][0]["training_receipt_sha256"] != fixed["checkpoints"][0]["training_receipt_sha256"]
    result = audit_checkpoint0_baseline(adaptive, fixed)
    assert result["model_state_sha256_mismatches"] == 0


def test_seed_mismatch_blocks_same_inputs_claim_even_if_state_hashes_match() -> None:
    fixed = _arm("F")
    fixed["checkpoints"][0]["model_receipts"][0]["model_seed"] += 1
    result = audit_checkpoint0_baseline(_arm("A"), fixed)
    assert result["status"] == "DECLARED_INPUT_MISMATCH"
    assert result["declared_model_seeds_equal"] is False
    assert result["same_declared_training_inputs"] is False


def test_missing_metadata_is_unknown_not_proven_equivalent() -> None:
    fixed = _arm("F")
    del fixed["checkpoints"][0]["training_dataset_seeds"]
    result = audit_checkpoint0_baseline(_arm("A"), fixed)
    assert result["status"] == "INSUFFICIENT_DECLARED_INPUT_EVIDENCE"
    assert result["checkpoint_seed_arrays_match_frozen"] is None


def test_missing_model_hash_grid_does_not_authorize_comparison() -> None:
    fixed = _arm("F")
    del fixed["checkpoints"][0]["model_receipts"]
    result = audit_checkpoint0_baseline(_arm("A"), fixed)
    assert result["status"] == "INSUFFICIENT_DECLARED_INPUT_EVIDENCE"
    assert result["model_state_sha256_mismatches"] is None


def test_duplicate_model_or_checkpoint_refused() -> None:
    fixed = _arm("F")
    fixed["checkpoints"][0]["model_receipts"][1] = copy.deepcopy(
        fixed["checkpoints"][0]["model_receipts"][0]
    )
    with pytest.raises(ValueError, match="duplicate or unexpected"):
        audit_checkpoint0_baseline(_arm("A"), fixed)
    fixed = _arm("F")
    fixed["checkpoints"].append(copy.deepcopy(fixed["checkpoints"][0]))
    with pytest.raises(ValueError, match="exactly one"):
        audit_checkpoint0_baseline(_arm("A"), fixed)


def test_curriculum_digest_corruption_refused() -> None:
    fixed = _arm("F")
    fixed["checkpoints"][0]["curriculum_digest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="curriculum digest mismatch"):
        audit_checkpoint0_baseline(_arm("A"), fixed)


def test_curriculum_order_is_not_material_if_digest_is_canonical() -> None:
    fixed = _arm("F")
    fixed["checkpoints"][0]["curriculum_fingerprints"].reverse()
    result = audit_checkpoint0_baseline(_arm("A"), fixed)
    assert result["same_declared_training_inputs"] is True


def test_miniature_fixture_is_unknown_not_automatically_invalid() -> None:
    fixed = _arm("F")
    fixed["checkpoints"][0]["curriculum_fingerprints"] = ["synthetic-only"]
    result = audit_checkpoint0_baseline(_arm("A"), fixed)
    assert result["curriculum_equal_and_hash_verified"] is None
    assert result["status"] == "INSUFFICIENT_DECLARED_INPUT_EVIDENCE"
    assert result["same_declared_training_inputs"] is False
