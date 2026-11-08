"""Deterministic engineering tests for idealized BB84 statistics."""

from __future__ import annotations

import json

import pytest

from quantum_lab import BB84Config, simulate_bb84


def test_clean_channel_without_eve_has_zero_qber():
    x = simulate_bb84(BB84Config(seed=101))
    assert x["intercepted_signals"] == 0
    assert x["public_sample_qber"] == 0.0
    assert x["all_sifted_qber_research_only"] == 0.0
    assert x["demo_qber_alarm"] is False
    assert x["no_secure_key_derived"] is True
    assert x["no_physical_quantum_claim"] is True


def test_complete_intercept_resend_has_statistical_disturbance():
    x = simulate_bb84(BB84Config(eve_intercept_probability=1.0, seed=102))
    assert x["intercepted_signals"] == x["signals"]
    # Approximate expected 0.25, not 100% certain detection each trial.
    assert 0.19 <= x["public_sample_qber"] <= 0.31
    assert 0.20 <= x["all_sifted_qber_research_only"] <= 0.30
    assert x["demo_qber_alarm"] is True


def test_partial_interception_not_claimed_immediately_detectable():
    x = simulate_bb84(BB84Config(eve_intercept_probability=0.02, seed=103))
    assert 0 < x["intercepted_signals"] < x["signals"]
    assert x["no_secure_key_derived"] is True
    assert x["authenticated_classical_channel"] is False


def test_independent_channel_noise_causes_nonzero_qber():
    x = simulate_bb84(BB84Config(channel_flip_probability=0.1, seed=104))
    assert 0.07 <= x["all_sifted_qber_research_only"] <= 0.13
    assert x["no_physical_quantum_claim"] is True


def test_public_sampling_does_not_release_private_bits():
    x = simulate_bb84(BB84Config(seed=105))
    assert x["publicly_compared_signals"] + x["unrevealed_sifted_signals"] == x["sifted_signals"]
    assert 0 < x["publicly_compared_signals"] < x["sifted_signals"]
    dumped = json.dumps(x)
    for sensitive in ("raw_key", "secret_key", "unrevealed_bits", "shared_key_bytes"):
        assert sensitive not in dumped
    assert x["error_correction_implemented"] is False
    assert x["privacy_amplification_implemented"] is False


def test_reproducible_for_fixed_simulation_seed():
    first = simulate_bb84(BB84Config(seed=106, eve_intercept_probability=0.5))
    second = simulate_bb84(BB84Config(seed=106, eve_intercept_probability=0.5))
    assert first == second


@pytest.mark.parametrize("invalid", [
    {"signals": 0}, {"signals": True}, {"signals": 9},
    {"eve_intercept_probability": -0.1}, {"eve_intercept_probability": 1.1},
    {"channel_flip_probability": -1}, {"channel_flip_probability": 2},
    {"public_test_fraction": 0.0}, {"public_test_fraction": 1.0},
    {"seed": -1}, {"seed": True}, {"demo_qber_alarm_threshold": -1},
])
def test_invalid_protocol_configuration_fails_closed(invalid):
    with pytest.raises(ValueError):
        simulate_bb84(BB84Config(**invalid))
