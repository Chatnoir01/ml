"""Synthetic-only test of checkpoint-zero numerical forward probe. NO training."""
from __future__ import annotations

import copy
import hashlib
from unittest.mock import patch

import pytest

np = pytest.importorskip("numpy")
from adversarial_sbox.datasets import PairSample
from adversarial_sbox.neural100 import BATCH_SIZE
from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_forward_only_probe import (
    _STAGES, _array_receipt, _canonical, compare_forward_probes,
    forward_only_probe,
)


def _hash(x):
    return hashlib.sha256(str(x).encode("utf-8")).hexdigest()


def _receipt():
    stage = _array_receipt(np.zeros((3, 12), dtype=np.float32))
    profile = {
        "schema_version": 1, "python_version": "3.12.14",
        "numpy_version": "2.5.3", "simd_available": ["AVX2"],
        "blas_libraries": [{"architecture": "Haswell", "num_threads": 1}],
    }
    fields = {
        "schema_version": 1,
        "purpose": "phase2r_first_forward_batch_without_training",
        "source_commit": "a" * 40,
        "fixture_sha256": "09e94da031992240d857a139768445c042cb712abf866f15084300a4a267e8a2",
        "difference": 1, "replicate": 0,
        "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
        "batch_size": BATCH_SIZE,
        "initialization_sha256": _hash("init"),
        "rng_state_sha256": _hash("rng"),
        "runtime_profile": profile,
        "runtime_profile_sha256": hashlib.sha256(_canonical(profile)).hexdigest(),
        "stages": {name: copy.deepcopy(stage) for name in _STAGES},
        "neural_training_performed": False,
        "gradient_computed": False,
        "optimizer_update_performed": False,
        "historical_phase2g_anomaly_explained": False,
    }
    fields["receipt_sha256"] = hashlib.sha256(_canonical(fields)).hexdigest()
    return fields


def _reseal(x):
    x.pop("receipt_sha256", None)
    x["receipt_sha256"] = hashlib.sha256(_canonical(x)).hexdigest()


def test_f32_stage_hash_binds_value_shape_order_and_dtype():
    left = np.arange(24, dtype=np.float32).reshape(2, 12)
    assert _array_receipt(left)["sha256"] == _array_receipt(left.copy())["sha256"]
    assert _array_receipt(left)["sha256"] != _array_receipt(left[::-1])["sha256"]
    assert _array_receipt(left)["sha256"] != _array_receipt(left.reshape(3, 8))["sha256"]
    with pytest.raises(ValueError, match="float32"):
        _array_receipt(left.astype(np.float64))


def test_identical_synthetic_forward_stage_receipts_are_non_scientific():
    x, y = _receipt(), _receipt()
    r = compare_forward_probes(x, y)
    assert r["all_stage_bytes_equal"] is True
    assert r["earliest_different_stage"] is None
    assert r["normalized_runtime_profiles_identical"] is True
    assert r["scientific_verdict"] == "EXPLORATORY_NUMERICAL_PROBE_ONLY"
    assert r["neural_training_performed"] is False


def test_first_float_difference_is_localized_without_training():
    a, f = _receipt(), _receipt()
    f["stages"]["second_linear"]["sha256"] = _hash("changed")
    _reseal(f)
    r = compare_forward_probes(a, f)
    assert r["earliest_different_stage"] == "second_linear"
    assert r["all_stage_bytes_equal"] is False
    assert r["status"] == "DIFFERENT_FORWARD_BYTES_SAMPLED"


def test_different_cpu_runtime_is_not_silent_equivalence():
    a, f = _receipt(), _receipt()
    f["runtime_profile"]["blas_libraries"][0]["architecture"] = "SkylakeX"
    f["runtime_profile_sha256"] = hashlib.sha256(_canonical(f["runtime_profile"])).hexdigest()
    _reseal(f)
    r = compare_forward_probes(a, f)
    assert r["normalized_runtime_profiles_identical"] is False
    assert r["all_stage_bytes_equal"] is True
    assert r["status"] == "IDENTICAL_FORWARD_BYTES_UNDER_INCOMPARABLE_RUNNERS"


def test_tampered_source_or_stage_fails_closed():
    a, f = _receipt(), _receipt()
    f["stages"]["logits"]["sha256"] = _hash("unsealed")
    with pytest.raises(ValueError, match="integrity"):
        compare_forward_probes(a, f)
    f = _receipt()
    f["initialization_sha256"] = _hash("different")
    _reseal(f)
    with pytest.raises(ValueError, match="prerequisite differs"):
        compare_forward_probes(a, f)


def test_one_fixed_synthetic_batch_executes_only_forward_arrays(tmp_path):
    sample = PairSample(0x12345678, 0xBADCAFE0, 1)
    fixture = tuple()
    with patch("adversarial_sbox.phase2r_forward_only_probe.load_phase2r_fixture", return_value=fixture), \
         patch("adversarial_sbox.phase2r_forward_only_probe.build_shared_training_splits",
               return_value=((sample,)*5600, (sample,)*1200, (sample,)*1200)), \
         patch("adversarial_sbox.phase2r_forward_only_probe.stable_numpy_runtime_profile",
               return_value={"schema_version": 1, "blas_libraries": [{"architecture": "synthetic"}]}), \
         patch.dict("os.environ", {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                                  "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
                                  "VECLIB_MAXIMUM_THREADS": "1", "GITHUB_SHA": "a"*40}):
        dump = tmp_path / "frozen-synthetic-forward-arrays.npz"
        result = forward_only_probe(tensor_output=dump)
    with np.load(dump, allow_pickle=False) as tensors:
        assert set(tensors.files) == set(_STAGES)
        assert {k: _array_receipt(tensors[k]) for k in _STAGES} == result["stages"]
    assert set(result["stages"]) == set(_STAGES)
    assert result["stages"]["input_features"]["shape"] == [BATCH_SIZE, 12]
    assert result["neural_training_performed"] is False
    assert result["gradient_computed"] is False
    assert result["optimizer_update_performed"] is False
    assert result["historical_phase2g_anomaly_explained"] is False


def test_invalid_registered_seed_or_unpinned_runtime_fails_closed():
    a, f = _receipt(), _receipt()
    f["model_seed"] += 1
    _reseal(f)
    with pytest.raises(ValueError, match="registered source and seed"):
        compare_forward_probes(a, f)
    f = _receipt()
    f["runtime_profile"]["blas_libraries"][0]["num_threads"] = 2
    f["runtime_profile_sha256"] = hashlib.sha256(
        _canonical(f["runtime_profile"])
    ).hexdigest()
    _reseal(f)
    with pytest.raises(ValueError, match="fully observed"):
        compare_forward_probes(a, f)
