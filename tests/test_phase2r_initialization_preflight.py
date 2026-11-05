"""Synthetic-only tests for prospective Phase 2R zero-training preflight."""
from __future__ import annotations

import copy
import hashlib
import json
from unittest.mock import patch

import pytest

np = pytest.importorskip("numpy", reason="scientific preflight uses explicit NumPy")
from adversarial_sbox.datasets import PairSample
from adversarial_sbox.phase2g import TRAINING_MODEL_BASE_SEEDS, TRAINING_DATASET_BASE_SEEDS
from adversarial_sbox.phase2r_initialization_preflight import (
    _canonical, STATUS, THREAD_VARS, DIFFERENCES, REPLICATES, SPLIT_NAMES,
    checkpoint_zero_seeded_initialization, one_pretraining_cell,
    compare_pretraining_receipts,
)
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256, FIXTURE_ID
from adversarial_sbox.phase2r_observation import observe_checkpoint_zero


def _sha(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()


def _fake_receipt(arm: str) -> dict:
    cells = []
    for d in DIFFERENCES:
        for r in REPLICATES:
            cells.append({
                "difference": d, "replicate": r,
                "dataset_seed": TRAINING_DATASET_BASE_SEEDS[r],
                "model_seed": TRAINING_MODEL_BASE_SEEDS[r],
                "dataset_sha256": {name: _sha(f"{d}-{r}-{name}") for name in SPLIT_NAMES},
                "initialization_sha256": _sha(f"seeded-{r}"),
                "rng_state_sha256": _sha(f"rng-{r}"),
            })
    report = {
        "schema_version": 1, "status": STATUS,
        "arm_label_metadata_only": arm, "fixture_id": FIXTURE_ID,
        "curriculum_sha256": CURRICULUM_SHA256,
        "python_version": "3.12.14", "numpy_version": "2.5.3",
        "machine": "x86_64", "runner_commit": "a"*40,
        "thread_limits": {var: "1" for var in THREAD_VARS},
        "numpy_runtime_report_sha256": _sha("synthetic-runtime"),
        "cells": cells, "model_cell_count": 16,
        "neural_training_performed": False,
        "historical_phase2g_artifacts_used": False,
        "historical_phase2g_anomaly_explained": False,
        "scientific_result": False,
    }
    report["receipt_sha256"] = hashlib.sha256(_canonical(report)).hexdigest()
    return report


def _reseal(receipt: dict) -> None:
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()


def test_original_seed_recipe_is_reproducible_without_training():
    seed = TRAINING_MODEL_BASE_SEEDS[0]
    weights_1, rng_1 = checkpoint_zero_seeded_initialization(seed)
    weights_2, rng_2 = checkpoint_zero_seeded_initialization(seed)
    one = observe_checkpoint_zero(tensors=weights_1, rng=rng_1)
    two = observe_checkpoint_zero(tensors=weights_2, rng=rng_2)
    assert one["initialization_sha256"] == two["initialization_sha256"]
    assert one["rng_state_sha256"] == two["rng_state_sha256"]
    np.testing.assert_array_equal(rng_1.permutation(12), rng_2.permutation(12))
    assert one["neural_training_performed"] is False


def test_distinct_registered_model_seed_changes_initialized_state():
    w1, rng1 = checkpoint_zero_seeded_initialization(TRAINING_MODEL_BASE_SEEDS[0])
    w2, rng2 = checkpoint_zero_seeded_initialization(TRAINING_MODEL_BASE_SEEDS[1])
    assert observe_checkpoint_zero(tensors=w1, rng=rng1)["initialization_sha256"] != (
        observe_checkpoint_zero(tensors=w2, rng=rng2)["initialization_sha256"]
    )


def test_unregistered_model_seed_does_not_initialize():
    for value in (True, 0, 999999, 1.5, "786009"):
        with pytest.raises(ValueError, match="unregistered"):
            checkpoint_zero_seeded_initialization(value)


def test_one_cell_hashes_three_splits_without_training():
    sample = PairSample(11, 22, 0)
    expected = ((sample,) * 5600, (sample,) * 1200, (sample,) * 1200)
    with patch("adversarial_sbox.phase2r_initialization_preflight.build_shared_training_splits",
               return_value=expected) as build:
        result = one_pretraining_cell((), difference=1, replicate=0)
    build.assert_called_once_with((), difference=1,
                                 dataset_seed=TRAINING_DATASET_BASE_SEEDS[0])
    assert len(result["dataset_sha256"]) == 3
    assert len(set(result["dataset_sha256"].values())) == 3
    assert result["initialization_sha256"] != result["rng_state_sha256"]


def test_two_independent_synthetic_receipts_compare_by_all_16_cells():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    r = compare_pretraining_receipts(a, f)
    assert r["status"] == "PASS_PRETRAINING_TWO_RUNNER_BYTE_INVARIANCE"
    assert r["data_matches"] == 16
    assert r["initialization_matches"] == 16
    assert r["rng_matches"] == 16
    assert r["neural_training_performed"] is False


def test_one_different_model_init_is_reported_not_ignored():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["cells"][4]["initialization_sha256"] = _sha("different")
    _reseal(f)
    result = compare_pretraining_receipts(a, f)
    assert result["initialization_matches"] == 15
    assert result["status"] == "FAIL_PRETRAINING_BYTES_DIVERGE"


def test_dataset_difference_cannot_pass_as_identical():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["cells"][5]["dataset_sha256"]["test"] = _sha("bad-test")
    _reseal(f)
    result = compare_pretraining_receipts(a, f)
    assert result["data_matches"] == 15
    assert result["status"] == "FAIL_PRETRAINING_BYTES_DIVERGE"


def test_modified_receipt_or_missing_cell_fails_closed():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["cells"][0]["model_seed"] += 1
    with pytest.raises(ValueError, match="integrity"):
        compare_pretraining_receipts(a, f)
    _reseal(f)
    with pytest.raises(ValueError, match="seed identity"):
        compare_pretraining_receipts(a, f)
    f = _fake_receipt("F")
    f["cells"][0] = copy.deepcopy(f["cells"][1])
    _reseal(f)
    with pytest.raises(ValueError, match="duplicate"):
        compare_pretraining_receipts(a, f)


def test_runtime_version_and_thread_limits_must_be_pinned():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["numpy_version"] = "2.5.2"
    _reseal(f)
    with pytest.raises(ValueError, match="numerical environment"):
        compare_pretraining_receipts(a, f)
    f = _fake_receipt("F")
    f["thread_limits"]["OPENBLAS_NUM_THREADS"] = "8"
    _reseal(f)
    with pytest.raises(ValueError, match="thread controls"):
        compare_pretraining_receipts(a, f)


def test_refuses_duplicate_arm_labels_even_with_matching_hashes():
    a = _fake_receipt("A")
    another_a = _fake_receipt("A")
    with pytest.raises(ValueError, match="A/F-labelled"):
        compare_pretraining_receipts(a, another_a)


def test_different_numpy_runtime_diagnostic_is_not_full_comparability():
    """Actual 2026-11-05 A/F jobs had identical bytes but different runtime hashes."""
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["numpy_runtime_report_sha256"] = _sha("different CPU or BLAS report")
    _reseal(f)
    result = compare_pretraining_receipts(a, f)
    assert result["data_matches"] == 16
    assert result["initialization_matches"] == 16
    assert result["rng_matches"] == 16
    assert result["exact_pretraining_byte_invariance_observed"] is True
    assert result["numpy_runtime_report_hashes_match"] is False
    assert result["runtime_comparability_established"] is False
    assert result["status"] == "INCOMPARABLE_NUMPY_RUNTIME_REPORT_MISMATCH"


def test_different_source_commits_rejected_even_if_all_16_byte_hashes_match():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["runner_commit"] = "b" * 40
    _reseal(f)
    with pytest.raises(ValueError, match="source commit mismatch"):
        compare_pretraining_receipts(a, f)


def test_missing_numpy_runtime_report_digest_rejected():
    a, f = _fake_receipt("A"), _fake_receipt("F")
    f["numpy_runtime_report_sha256"] = "invalid"
    _reseal(f)
    with pytest.raises(ValueError, match="NumPy runtime"):
        compare_pretraining_receipts(a, f)
