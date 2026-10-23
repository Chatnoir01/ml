"""Only synthetic receipts: testing Phase-2R validation never trains models."""

from __future__ import annotations

import copy
import hashlib

import pytest

from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2r_repro import (
    MODEL_GRID, PROTOCOL_SHA256, audit_prospective_receipts,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _runtime() -> dict:
    return {
        "python_version": "3.12.0",
        "numpy_version": "2.1.0",
        "platform": "Linux synthetic-test",
        "blas_provider": "synthetic-test-blas",
        "blas_version": "0-test",
        "machine": "synthetic-test-cpu",
        "source_sha256": _hash("source fixture"),
        "dependency_lock_sha256": _hash("lock fixture"),
        "thread_limits": {
            "OPENBLAS_NUM_THREADS": 1,
            "OMP_NUM_THREADS": 1,
            "MKL_NUM_THREADS": 1,
            "NUMEXPR_NUM_THREADS": 1,
            "VECLIB_MAXIMUM_THREADS": 1,
        },
    }


def _fixture() -> dict:
    curriculum_hash = CURRICULUM_SHA256
    runs = []
    for arm, repeat in (("A", 1), ("A", 2), ("F", 1), ("F", 2)):
        models = []
        for difference, replicate in MODEL_GRID:
            cell = f"{difference}:{replicate}"
            models.append({
                "difference": difference,
                "replicate": replicate,
                "dataset_seed": TRAINING_DATASET_BASE_SEEDS[replicate],
                "model_seed": TRAINING_MODEL_BASE_SEEDS[replicate],
                "curriculum_sha256": curriculum_hash,
                "dataset_sha256": {
                    name: _hash(f"{cell}:{name}") for name in ("train", "validation", "test")
                },
                "initialization_sha256": _hash(f"{cell}:init"),
                "state_sha256": _hash(f"{cell}:state"),
            })
        runs.append({
            "arm": arm,
            "repeat": repeat,
            "runtime": _runtime(),
            "curriculum_sha256": curriculum_hash,
            "models": models,
        })
    return {"protocol_sha256": PROTOCOL_SHA256, "runs": runs}


def test_matching_synthetic_byte_receipts_pass_but_do_not_establish_cause() -> None:
    result = audit_prospective_receipts(_fixture())
    assert result["status"] == "PASS_CONTROL_BYTE_REPRODUCIBILITY"
    assert result["run_count"] == 4
    assert len(result["paired_comparisons"]) == 4
    assert result["authorizes_phase_2i"] is False
    assert result["causal_explanation_established"] is False
    assert result["does_not_modify_phase_2g"] is True
    assert len(result["audit_sha256"]) == 64


def test_a_repeat_model_state_hash_mismatch_is_reported_without_causal_claim() -> None:
    bundle = _fixture()
    bundle["runs"][1]["models"][0]["state_sha256"] = _hash("different trained state")
    result = audit_prospective_receipts(bundle)
    assert result["status"] == "NOT_REPRODUCIBLE_OR_INCOMPARABLE"
    assert result["paired_comparisons"][0]["status"] == "FAIL_SERIALIZED_MODEL_BYTES_DIFFER"
    assert result["paired_comparisons"][0]["model_state_hash_different_cell_count"] == 1
    assert result["paired_comparisons"][1]["status"] == "PASS_REPRODUCIBLE_BYTES_IN_CONTROL"
    assert result["causal_explanation_established"] is False


def test_dataset_difference_precedes_model_explanation() -> None:
    bundle = _fixture()
    bundle["runs"][0]["models"][0]["dataset_sha256"]["train"] = _hash("different dataset")
    result = audit_prospective_receipts(bundle)
    assert result["paired_comparisons"][0]["status"] == "FAIL_DATA_BYTES_DIFFER"
    assert result["paired_comparisons"][2]["status"] == "FAIL_DATA_BYTES_DIFFER"


def test_initialization_difference_precedes_model_explanation() -> None:
    bundle = _fixture()
    bundle["runs"][0]["models"][0]["initialization_sha256"] = _hash("different init")
    result = audit_prospective_receipts(bundle)
    assert result["paired_comparisons"][0]["status"] == "FAIL_INITIALIZATION_BYTES_DIFFER"


def test_runtime_or_curriculum_mismatch_is_incomparable() -> None:
    bundle = _fixture()
    bundle["runs"][0]["runtime"]["numpy_version"] = "2.2.1"
    result = audit_prospective_receipts(bundle)
    assert result["paired_comparisons"][0]["status"] == "INCOMPARABLE_DIFFERENT_RUNTIME_OR_CURRICULUM"
    bundle = _fixture()
    bundle["runs"][0]["curriculum_sha256"] = _hash("alternate candidate pool")
    for model in bundle["runs"][0]["models"]:
        model["curriculum_sha256"] = bundle["runs"][0]["curriculum_sha256"]
    with pytest.raises(ValueError, match="differs from pinned"):
        audit_prospective_receipts(bundle)


def test_run_reordering_does_not_change_result_bytes() -> None:
    bundle = _fixture()
    first = audit_prospective_receipts(bundle)
    reversed_bundle = copy.deepcopy(bundle)
    reversed_bundle["runs"].reverse()
    for run in reversed_bundle["runs"]:
        run["models"].reverse()
    second = audit_prospective_receipts(reversed_bundle)
    assert first == second
    assert first["audit_sha256"] == second["audit_sha256"]


def test_missing_or_duplicate_run_fails_closed() -> None:
    bundle = _fixture()
    bundle["runs"].pop()
    with pytest.raises(ValueError, match="incomplete"):
        audit_prospective_receipts(bundle)
    bundle = _fixture()
    bundle["runs"][0] = copy.deepcopy(bundle["runs"][1])
    with pytest.raises(ValueError, match="duplicate"):
        audit_prospective_receipts(bundle)


def test_missing_or_duplicate_model_receipt_fails_closed() -> None:
    bundle = _fixture()
    bundle["runs"][0]["models"].pop()
    with pytest.raises(ValueError, match="incomplete"):
        audit_prospective_receipts(bundle)
    bundle = _fixture()
    bundle["runs"][0]["models"][1] = copy.deepcopy(bundle["runs"][0]["models"][0])
    with pytest.raises(ValueError, match="duplicate"):
        audit_prospective_receipts(bundle)


def test_wrong_dataset_or_training_seed_is_not_a_comparable_experiment() -> None:
    bundle = _fixture()
    bundle["runs"][2]["models"][0]["dataset_seed"] += 1
    with pytest.raises(ValueError, match="frozen checkpoint-0 registry"):
        audit_prospective_receipts(bundle)


def test_missing_evidence_does_not_look_like_equal_bytes() -> None:
    bundle = _fixture()
    bundle["runs"][0]["models"][0]["dataset_sha256"].pop("test")
    with pytest.raises(ValueError, match="incomplete train/validation/test"):
        audit_prospective_receipts(bundle)
    bundle = _fixture()
    bundle["runs"][0]["models"][0]["initialization_sha256"] = ""
    with pytest.raises(ValueError, match="initialization SHA-256"):
        audit_prospective_receipts(bundle)


def test_runtime_thread_metadata_cannot_be_omitted_or_invented() -> None:
    bundle = _fixture()
    bundle["runs"][0]["runtime"]["thread_limits"].pop("MKL_NUM_THREADS")
    with pytest.raises(ValueError, match="incomplete thread-limit"):
        audit_prospective_receipts(bundle)
    bundle = _fixture()
    bundle["runs"][0]["runtime"]["thread_limits"]["OMP_NUM_THREADS"] = 0
    with pytest.raises(ValueError, match="invalid thread-limit"):
        audit_prospective_receipts(bundle)


def test_protocol_hash_is_pinned_before_prospective_receipt_validation() -> None:
    bundle = _fixture()
    bundle["protocol_sha256"] = _hash("another protocol")
    with pytest.raises(ValueError, match="protocol hash"):
        audit_prospective_receipts(bundle)
