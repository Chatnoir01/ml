"""Synthetic-only controls for one first historical gradient/Adam microstep.

No full neural model training or actual Phase2G/2U scientific execution.
"""
from __future__ import annotations

import copy
import hashlib

import pytest

np = pytest.importorskip("numpy", reason="Optional scientific NumPy dependency is required for synthetic tests")

from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2r_forward_only_probe import _array_receipt
from adversarial_sbox.phase2r_initialization_preflight import _canonical
from adversarial_sbox.phase2r_first_adam_microstep import (
    GRADIENTS, UPDATED, PARAMETERS, PROTOCOL, SHAPES, STAGES,
    compare_original_microstep_receipts, original_first_step_tensors,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _recalc(data: dict):
    data.pop("receipt_sha256", None)
    data["receipt_sha256"] = hashlib.sha256(_canonical(data)).hexdigest()


def _source(arch: str, values: dict) -> dict:
    profile = {
        "schema_version": 1,
        "python_version": "3.12.14", "numpy_version": "2.5.3",
        "os": "Linux", "architecture": "x86_64",
        "simd_available": ["AVX2", "FMA3"],
        "simd_baseline": ["SSE2"],
        "simd_dispatch": ["AVX2"],
        "blas_libraries": [{
            "user_api": "blas", "internal_api": "openblas",
            "version": "0.3.34.106.0",
            "threading_layer": "pthreads", "architecture": arch,
            "num_threads": 1,
        }],
    }
    doc = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "source_commit": "a" * 40,
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
        "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
        "original_training_rows": 5600,
        "first_minibatch_size": 256,
        "original_rng_permutation_used": True,
        "first_batch_index_sha256": _sha("idx"),
        "initialization_sha256": _sha("init"),
        "rng_pre_permutation_sha256": _sha("rngpre"),
        "rng_post_permutation_sha256": _sha("rngpost"),
        "stages": {name: _array_receipt(values[name]) for name in STAGES},
        "runtime_profile": profile,
        "runtime_profile_sha256": hashlib.sha256(_canonical(profile)).hexdigest(),
        "one_adam_step_executed": True,
        "adam_step_index": 1,
        "parameter_updates_executed": 6,
        "full_neural_training_performed": False,
        "phase2u_neural_trainings_performed": 0,
        "historical_phase2g_anomaly_explained": False,
        "scientific_status": "EXPLORATORY_SYNTHETIC_SINGLE_ADAM_STEP_ONLY",
    }
    _recalc(doc)
    return doc


def _pair(tmp_path, mutation: str | None = None):
    base = {
        name: np.zeros(SHAPES[name], dtype=np.float32) for name in STAGES
    }
    alt = copy.deepcopy(base)
    if mutation:
        alt[mutation].flat[0] = np.float32(0.125)
    a_path = tmp_path / "haswell.npz"
    b_path = tmp_path / "nehalem.npz"
    np.savez(a_path, **base)
    np.savez(b_path, **alt)
    return _source("Haswell", base), _source("Nehalem", alt), a_path, b_path


def test_same_math_microstep_is_deterministic_and_six_parameters_change():
    rng = np.random.default_rng(751)
    xb = rng.standard_normal((256, 12)).astype(np.float32)
    labels = (np.arange(256) % 2).astype(np.float32)
    params = {
        "w1": rng.normal(0, 0.2, (12, 48)).astype(np.float32),
        "b1": np.zeros(48, np.float32),
        "w2": rng.normal(0, 0.2, (48, 24)).astype(np.float32),
        "b2": np.zeros(24, np.float32),
        "w3": rng.normal(0, 0.2, 24).astype(np.float32),
        "b3": np.float32(0),
    }
    first = original_first_step_tensors(xb, labels, params)
    again = original_first_step_tensors(xb, labels, params)
    assert set(first) == set(STAGES)
    assert {name: _array_receipt(v) for name, v in first.items()} == {
        name: _array_receipt(v) for name, v in again.items()
    }
    assert all(first["updated_"+name].shape == SHAPES["updated_"+name]
               for name in PARAMETERS)
    assert all(np.any(first["updated_"+name] != params[name])
               for name in PARAMETERS)
    assert np.isfinite(first["grad_w1"]).all()


def test_first_step_gradient_w3_matches_independent_classic_expression():
    rng = np.random.default_rng(514)
    xb = rng.normal(size=(256, 12)).astype(np.float32)
    yb = np.asarray([0., 1.] * 128, dtype=np.float32)
    params = {
        "w1": rng.normal(0, 0.1, (12, 48)).astype(np.float32),
        "b1": np.zeros(48, np.float32),
        "w2": rng.normal(0, 0.1, (48, 24)).astype(np.float32),
        "b2": np.zeros(24, np.float32),
        "w3": rng.normal(0, 0.1, 24).astype(np.float32),
        "b3": np.float32(0.0),
    }
    output = original_first_step_tensors(xb, yb, params)
    from adversarial_sbox.neural100 import WEIGHT_DECAY
    expected = output["second_tanh"].T @ ((output["probabilities"]-yb)/256.0)
    expected += WEIGHT_DECAY * params["w3"]
    np.testing.assert_array_equal(output["grad_w3"], expected)


def test_zero_mismatch_receipts_are_not_historical_scientific_verdict(tmp_path):
    a, b, pa, pb = _pair(tmp_path)
    result = compare_original_microstep_receipts(a, b, pa, pb)
    assert result["total_stages"] == len(STAGES)
    assert result["gradient_stage_changes"] == 0
    assert result["updated_parameter_changes"] == 0
    assert result["full_neural_training_performed"] is False
    assert result["phase2u_neural_trainings_performed"] == 0
    assert result["historical_phase2g_cause_identified"] is False


def test_gradient_drift_is_counted_and_localized(tmp_path):
    a, b, pa, pb = _pair(tmp_path, mutation="grad_w2")
    result = compare_original_microstep_receipts(a, b, pa, pb)
    assert result["first_different_gradient"] == "grad_w2"
    assert result["first_different_updated_parameter"] is None
    assert result["gradient_stage_changes"] == 1
    assert result["observed_outcome"] == "GRADIENT_OR_PARAMETER_BIT_DIFFERENCE_OBSERVED"


def test_parameter_drift_is_counted_and_localized(tmp_path):
    a, b, pa, pb = _pair(tmp_path, mutation="updated_w1")
    result = compare_original_microstep_receipts(a, b, pa, pb)
    assert result["first_different_updated_parameter"] == "updated_w1"
    assert result["updated_parameter_changes"] == 1


def test_tampered_original_npz_or_hash_is_rejected(tmp_path):
    a, b, pa, pb = _pair(tmp_path)
    with np.load(pb) as data:
        values = {key: data[key] for key in data.files}
    values["grad_w1"].flat[0] = np.float32(0.75)
    np.savez(pb, **values)
    with pytest.raises(ValueError, match="NPZ stage"):
        compare_original_microstep_receipts(a, b, pa, pb)
    a, b, pa, pb = _pair(tmp_path)
    b["model_seed"] += 1
    with pytest.raises(ValueError, match="integrity"):
        compare_original_microstep_receipts(a, b, pa, pb)


def test_false_kernel_or_runtime_drift_rejected(tmp_path):
    a, b, pa, pb = _pair(tmp_path)
    b["runtime_profile"]["blas_libraries"][0]["architecture"] = "Haswell"
    b["runtime_profile_sha256"] = hashlib.sha256(_canonical(b["runtime_profile"])).hexdigest()
    _recalc(b)
    with pytest.raises(ValueError, match="wrong selected"):
        compare_original_microstep_receipts(a, b, pa, pb)
    a, b, pa, pb = _pair(tmp_path)
    b["runtime_profile"]["simd_available"].append("AVX512F")
    b["runtime_profile_sha256"] = hashlib.sha256(_canonical(b["runtime_profile"])).hexdigest()
    _recalc(b)
    with pytest.raises(ValueError, match="same-host"):
        compare_original_microstep_receipts(a, b, pa, pb)


def test_permutation_or_input_drift_fails_closed(tmp_path):
    a, b, pa, pb = _pair(tmp_path)
    b["first_batch_index_sha256"] = _sha("changed")
    _recalc(b)
    with pytest.raises(ValueError, match="permutation or initialized"):
        compare_original_microstep_receipts(a, b, pa, pb)
    a, b, pa, pb = _pair(tmp_path, mutation="batch_features")
    with pytest.raises(ValueError, match="input features or labels"):
        compare_original_microstep_receipts(a, b, pa, pb)
