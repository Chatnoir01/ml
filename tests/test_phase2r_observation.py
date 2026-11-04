"""Synthetic observation-only tests; NO Phase 2R neural training."""
from __future__ import annotations

import copy
import json

import pytest

np = pytest.importorskip("numpy", reason="Phase 2R observation requires optional NumPy")
from adversarial_sbox.phase2r_observation import observe_checkpoint_zero


def _setup():
    rng = np.random.default_rng(41003)
    tensors = {
        "w1": rng.normal(size=(12, 4)).astype(np.float32),
        "b1": np.zeros(4, dtype=np.float32),
        "w2": rng.normal(size=(4, 3)).astype(np.float32),
        "b2": np.zeros(3, dtype=np.float32),
        "w3": rng.normal(size=(3,)).astype(np.float32),
        "b3": np.float32(0.0),
    }
    return rng, tensors


def _state(rng):
    return copy.deepcopy(rng.bit_generator.state)


def test_observation_does_not_consume_randomness_or_modify_weights():
    rng, tensors = _setup()
    before_rng = _state(rng)
    before_weights = {k: np.array(v, copy=True) for k, v in tensors.items()}
    first = observe_checkpoint_zero(tensors=tensors, rng=rng)
    second = observe_checkpoint_zero(tensors=tensors, rng=rng)
    assert first == second
    assert json.dumps(_state(rng), sort_keys=True) == json.dumps(before_rng, sort_keys=True)
    for name in tensors:
        np.testing.assert_array_equal(tensors[name], before_weights[name])
    assert first["neural_training_performed"] is False
    assert first["historical_phase2g_anomaly_explained"] is False


def test_single_weight_change_detected_without_training():
    rng, tensors = _setup()
    baseline = observe_checkpoint_zero(tensors=tensors, rng=rng)
    tensors["w1"][0, 0] = np.nextafter(tensors["w1"][0, 0], np.float32("inf"))
    changed = observe_checkpoint_zero(tensors=tensors, rng=rng)
    assert changed["initialization_sha256"] != baseline["initialization_sha256"]
    assert changed["rng_state_sha256"] == baseline["rng_state_sha256"]


def test_rng_advance_detected_separately_from_weights():
    rng, tensors = _setup()
    before = observe_checkpoint_zero(tensors=tensors, rng=rng)
    rng.random()
    after = observe_checkpoint_zero(tensors=tensors, rng=rng)
    assert before["initialization_sha256"] == after["initialization_sha256"]
    assert before["rng_state_sha256"] != after["rng_state_sha256"]


def test_reject_missing_tensor_and_silent_dtype_coercion():
    rng, tensors = _setup()
    incomplete = dict(tensors)
    del incomplete["b3"]
    with pytest.raises(ValueError, match="six"):
        observe_checkpoint_zero(tensors=incomplete, rng=rng)
    tensors["w1"] = tensors["w1"].astype(np.float64)
    with pytest.raises(ValueError, match="float32"):
        observe_checkpoint_zero(tensors=tensors, rng=rng)


def test_reject_nan_without_leaking_weights():
    rng, tensors = _setup()
    tensors["b1"][0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        observe_checkpoint_zero(tensors=tensors, rng=rng)
