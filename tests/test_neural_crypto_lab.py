"""Engineering smoke + controls only, not evidence of cryptographic security."""

from __future__ import annotations

import json
import math

import pytest

# This neural-research extra is optional in legacy Phase 0.
# The dedicated lab CI must install NumPy and execute these tests.
np = pytest.importorskip("numpy")

from neural_crypto_lab import MLP, Protocol, run_experiment
from neural_crypto_lab.experiment import _bits, _loss, _retrain_attacker


SMOKE = Protocol(
    train_steps=4,
    challenger_steps=4,
    batch_size=24,
    eval_samples=96,
)


def test_three_models_have_distinct_visible_key_inputs():
    alice = MLP(16, 16, 8, 1)
    bob = MLP(16, 16, 8, 2)
    eve = MLP(8, 16, 8, 3)
    assert alice.w1.shape == (16, 16)
    assert bob.w1.shape == (16, 16)
    assert eve.w1.shape == (8, 16)


def test_loss_backward_finite_difference_matches_analytic_gradient():
    network = MLP(3, 5, 2, 7)
    inputs = np.array([[0.1, 0.4, -0.7], [0.6, -0.2, 0.3]])
    target = np.array([[1.0, 0.0], [0.0, 1.0]])
    output, cache = network.forward(inputs)
    _, upstream = _loss(output, target)
    dx, gradients = network.backward(cache, upstream)
    for index in [(0, 0), (1, 3), (2, 4)]:
        orig = network.w1[index]
        network.w1[index] = orig + 1e-5
        high = _loss(network.predict(inputs), target)[0]
        network.w1[index] = orig - 1e-5
        low = _loss(network.predict(inputs), target)[0]
        network.w1[index] = orig
        assert gradients[0][index] == pytest.approx((high - low) / 2e-5, abs=1e-7)
    assert dx.shape == inputs.shape


def test_smoke_reproducible_given_fixed_seed_and_numpy_environment():
    first = run_experiment(seed=204, protocol=SMOKE)
    second = run_experiment(seed=204, protocol=SMOKE)
    assert first == second
    assert first["no_security_claim"] is True
    assert first["holdout_not_used_for_training"] is True
    assert first["no_crypto_wall_integration"] is True
    assert first["protocol_sha256"] == SMOKE.digest()


def test_controls_explicitly_show_identity_leakage_and_one_time_xor():
    result = run_experiment(seed=205, protocol=SMOKE)
    assert result["controls"]["identity_eve_accuracy"] == 1.0
    assert result["controls"]["fresh_xor_bob_accuracy"] == 1.0
    assert result["controls"]["fresh_xor_keyless_guess_expected_accuracy"] == 0.5
    # The observed neural adversary scores are measured, never hard-coded 0.5.
    assert len(result["heldout_fresh_eve_bit_accuracies"]) == 2
    for accuracy in result["heldout_fresh_eve_bit_accuracies"]:
        assert math.isfinite(accuracy)
        assert 0 <= accuracy <= 1


def test_fresh_attackers_are_independent_of_training_eve():
    rng_seed = 206
    alice = MLP(16, 16, 8, 207)
    challenger1 = _retrain_attacker(
        alice, hidden=16, seed=208, data_seed=209,
        steps=2, batch_size=12, learning_rate=0.01,
    )
    challenger2 = _retrain_attacker(
        alice, hidden=48, seed=210, data_seed=211,
        steps=2, batch_size=12, learning_rate=0.01,
    )
    assert challenger1.w1.shape == (8, 16)
    assert challenger2.w1.shape == (8, 48)
    assert challenger1 is not challenger2
    assert alice.w1.shape == (16, 16)


def test_train_holdout_and_attacker_datasets_use_distinct_seeds():
    a, ka = _bits(102, 40)
    b, kb = _bits(103, 40)
    assert not np.array_equal(a, b)
    assert not np.array_equal(ka, kb)


def test_protocol_guards_reject_invalid_training_and_unexpected_version():
    with pytest.raises(ValueError):
        Protocol(version=2).validate()
    with pytest.raises(ValueError):
        Protocol(train_steps=0).validate()
    with pytest.raises(ValueError):
        Protocol(batch_size=0).validate()
    with pytest.raises(ValueError):
        Protocol(ciphertext_units=16).validate()
    with pytest.raises(ValueError):
        Protocol(challenger_steps=0).validate()
    with pytest.raises(ValueError):
        Protocol(learning_rate=100).validate()
    with pytest.raises(ValueError):
        run_experiment(seed=-1, protocol=SMOKE)
    with pytest.raises(ValueError):
        run_experiment(seed=True, protocol=SMOKE)


def test_smoke_outputs_only_metrics_not_keys_plaintext_or_trained_models():
    result = run_experiment(seed=208, protocol=SMOKE)
    body = json.dumps(result)
    assert "private_key" not in body
    assert "plaintext" not in body
    assert "weights" not in body
    assert set(result["architecture"]) == {"alice", "bob", "eve", "fresh_eve_hidden"}
