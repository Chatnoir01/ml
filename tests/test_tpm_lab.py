"""TPM toy protocol tests verify code, not key secrecy."""
from __future__ import annotations
import json
import random
import pytest
from tpm_lab.sync import TPM, TPMProtocol, _signal, run_study, trial


def test_output_has_parity_of_hidden_signs():
    net = TPM(k=3, n=2, l=2, rng=random.Random(3))
    net.weights = [[1, 1], [-1, 2], [-1, 1]]
    tau, hidden, fields = net.evaluate(((1, 1), (1, -1), (-1, 1)))
    assert fields == (2, -3, 2)
    assert hidden == (1, -1, 1)
    assert tau == -1


def test_zero_local_field_uses_fixed_positive_tie_rule():
    net = TPM(k=3, n=2, l=1, rng=random.Random(3))
    net.weights = [[0, 0], [0, 0], [0, 0]]
    assert net.evaluate(((1, -1), (1, -1), (-1, 1)))[0] == 1


def test_only_matching_hidden_neurons_update_and_clip():
    net = TPM(k=3, n=2, l=1, rng=random.Random(9))
    net.weights = [[1, 0], [-1, 0], [1, 1]]
    inp = ((1, 1), (1, -1), (-1, 1))
    net.update(inp, public_tau=1, hidden=(1, -1, 1))
    assert net.weights == [[1, 1], [-1, 0], [0, 1]]


def test_bad_teacher_inputs_rejected():
    net = TPM(k=3, n=2, l=1, rng=random.Random(7))
    with pytest.raises(ValueError):
        net.update(((1, 1),) * 3, 0, (1, 1, 1))
    with pytest.raises(ValueError):
        net.evaluate(((1, 1), (2, 1), (1, -1)))


def test_fixed_seed_gives_identical_complete_records():
    p = TPMProtocol(max_steps=1000, trials=3, inputs_per_unit=8)
    first = run_study(p)
    second = run_study(p)
    assert first == second
    assert len(first["trials"]) == 3
    assert first["protocol_sha256"] == p.sha256()


def test_known_tiny_seed_sync_but_attacker_sometimes_also_succeeds():
    p = TPMProtocol(max_steps=2000, trials=8)
    result = run_study(p)
    assert result["synchronized_trials"] == 8
    assert result["attacker_exact_matches_at_sync"]["geometric"] > 0
    assert result["attacker_comparison_denominator"] == 8
    assert result["no_production_crypto_integration"] is True


def test_no_sync_does_not_treat_attackers_as_failed_or_secure():
    p = TPMProtocol(max_steps=1, trials=3)
    result = run_study(p)
    assert result["unsynchronized_trials"] == 3
    assert result["median_steps_conditional_on_sync"] is None
    assert result["attacker_comparison_denominator"] == 0
    assert all(r["attacker_exact_match_at_sync"] is None for r in result["trials"])


def test_result_does_not_export_private_weights_or_secret_key():
    r = run_study(TPMProtocol(trials=2, max_steps=200))
    dumped = json.dumps(r)
    assert '"weights":' not in dumped
    assert '"shared_key":' not in dumped
    assert '"private_key":' not in dumped
    assert r["authentication_not_implemented"]
    assert r["does_not_generate_a_secure_key"]


def test_different_trials_are_distinct_public_experiments():
    p = TPMProtocol(trials=2)
    assert trial(p, trial_index=0) != trial(p, trial_index=1)
    assert _signal(random.Random(1), 3, 8) != _signal(random.Random(2), 3, 8)


@pytest.mark.parametrize("kwargs", [
    {"hidden_units": 2}, {"hidden_units": 4}, {"hidden_units": True},
    {"inputs_per_unit": 0}, {"inputs_per_unit": True}, {"synaptic_depth": 0},
    {"max_steps": 0}, {"max_steps": False}, {"max_steps": 100001},
    {"trials": 0}, {"trials": 101}, {"master_seed": -1},
    {"learning_rule": "antihebbian"},
])
def test_bad_protocol_fails_closed(kwargs):
    with pytest.raises(ValueError):
        run_study(TPMProtocol(**kwargs))


def test_bad_trial_index_fails_closed():
    with pytest.raises(ValueError):
        trial(TPMProtocol(trials=1), trial_index=1)
    with pytest.raises(ValueError):
        trial(TPMProtocol(trials=1), trial_index=True)
