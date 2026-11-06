"""Synthetic-only numerical difference receipt tests. No model training."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

np = pytest.importorskip("numpy", reason="Optional scientific NumPy dependency is required for synthetic tests")

from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_forward_only_probe import _STAGES, _array_receipt, _canonical
from adversarial_sbox.phase2r_dispatch_numeric_audit import (
    _EXPECTED_SHAPES, EXPERIMENT, audit_controlled_dispatch,
)


def _hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _arrays():
    return {
        name: (np.arange(np.prod(_EXPECTED_SHAPES[name]), dtype=np.float32)
               .reshape(_EXPECTED_SHAPES[name]) / np.float32(1024.0))
        for name in _STAGES
    }


def _receipt(arch: str, arrays) -> dict:
    profile = {
        "schema_version": 1,
        "python_version": "3.12.14",
        "numpy_version": "2.5.3",
        "os": "Linux",
        "architecture": "x86_64",
        "simd_available": ["AVX2", "FMA3"],
        "simd_baseline": ["SSE2"],
        "simd_dispatch": ["AVX2"],
        "blas_libraries": [{
            "user_api": "blas", "internal_api": "openblas",
            "version": "0.3.34.106.0", "threading_layer": "pthreads",
            "architecture": arch, "num_threads": 1
        }],
    }
    r = {
        "schema_version": 1,
        "purpose": "phase2r_first_forward_batch_without_training",
        "source_commit": "a" * 40,
        "fixture_sha256": "09e94da031992240d857a139768445c042cb712abf866f15084300a4a267e8a2",
        "difference": 1, "replicate": 0, "batch_size": 256,
        "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
        "initialization_sha256": _hash("same-init"),
        "rng_state_sha256": _hash("same-rng"),
        "runtime_profile": profile,
        "runtime_profile_sha256": _hash_profile(profile),
        "stages": {k: _array_receipt(v) for k, v in arrays.items()},
        "neural_training_performed": False,
        "gradient_computed": False,
        "optimizer_update_performed": False,
        "historical_phase2g_anomaly_explained": False,
    }
    r["receipt_sha256"] = hashlib.sha256(_canonical(r)).hexdigest()
    return r


def _hash_profile(v):
    return hashlib.sha256(_canonical(v)).hexdigest()


def _reseal(r):
    r["runtime_profile_sha256"] = _hash_profile(r["runtime_profile"])
    r.pop("receipt_sha256", None)
    r["receipt_sha256"] = _hash_profile(r)


def _synthetic_pair(tmp_path, *, mutated_stage=None):
    h_arrays = _arrays()
    n_arrays = copy.deepcopy(h_arrays)
    if mutated_stage:
        n_arrays[mutated_stage][0, 0] += np.float32(0.125)
    hp, npz = tmp_path / "haswell.npz", tmp_path / "nehalem.npz"
    np.savez(hp, **h_arrays)
    np.savez(npz, **n_arrays)
    return _receipt("Haswell", h_arrays), _receipt("Nehalem", n_arrays), hp, npz


def test_same_host_pinned_core_change_without_any_float_difference(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    r = audit_controlled_dispatch(h, n, hp, npz)
    assert r["experiment"] == EXPERIMENT
    assert r["outcome"] == "NO_BITWISE_DIFFERENCE_IN_SAMPLED_FORWARD_PASS"
    assert r["distinct_stage_count"] == 0
    assert r["first_bitwise_different_stage"] is None
    assert r["neural_training_performed"] is False
    assert r["original_phase2g_64_of_144_explained"] is False
    assert all(x["bitwise_differing_float32_values"] == 0 for x in r["stages"])


def test_first_differing_stage_and_max_numeric_difference(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path, mutated_stage="first_linear")
    r = audit_controlled_dispatch(h, n, hp, npz)
    assert r["outcome"] == "BITWISE_DIFFERENCE_OBSERVED_WITH_CONTROLLED_DISPATCH"
    assert r["first_bitwise_different_stage"] == "first_linear"
    assert r["distinct_stage_count"] == 1
    first = next(x for x in r["stages"] if x["stage"] == "first_linear")
    assert first["bitwise_differing_float32_values"] == 1
    assert first["maximum_absolute_difference"] == pytest.approx(0.125)
    assert r["stages"][0]["bitwise_differing_float32_values"] == 0


def test_wrong_actual_blas_core_fails_closed(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    n["runtime_profile"]["blas_libraries"][0]["architecture"] = "Haswell"
    _reseal(n)
    with pytest.raises(ValueError, match="did not select"):
        audit_controlled_dispatch(h, n, hp, npz)


def test_cpu_simd_drift_outside_dispatch_is_rejected(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    n["runtime_profile"]["simd_available"] += ["AVX512F"]
    _reseal(n)
    with pytest.raises(ValueError, match="not one comparable numerical host"):
        audit_controlled_dispatch(h, n, hp, npz)


def test_changed_npz_bytes_without_updated_sealed_receipt_rejected(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    data = _arrays()
    data["first_tanh"][0, 0] += np.float32(3.0)
    np.savez(npz, **data)
    with pytest.raises(ValueError, match="NPZ stage bytes"):
        audit_controlled_dispatch(h, n, hp, npz)


def test_wrong_shape_with_self_consistent_receipts_rejected(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    arr = _arrays()
    arr["first_linear"] = arr["first_linear"].reshape(512, 24)
    np.savez(npz, **arr)
    n["stages"]["first_linear"] = _array_receipt(arr["first_linear"])
    _reseal(n)
    with pytest.raises(ValueError, match="stage shape"):
        audit_controlled_dispatch(h, n, hp, npz)


def test_wrong_source_receipt_seed_must_fail(tmp_path):
    h, n, hp, npz = _synthetic_pair(tmp_path)
    n["model_seed"] += 1
    _reseal(n)
    with pytest.raises(ValueError, match="seed identity|prerequisite"):
        audit_controlled_dispatch(h, n, hp, npz)
