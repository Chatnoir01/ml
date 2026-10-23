"""Tests for bounded genetic-style TPM branching; not a security proof."""
import pytest
from tpm_lab import TPMProtocol
from tpm_lab.genetic import genetic_trial, genetic_study


def test_repeatability():
    p=TPMProtocol(trials=2,max_steps=1000)
    assert genetic_study(p,population=8)==genetic_study(p,population=8)


def test_private_state_not_exported():
    r=genetic_study(TPMProtocol(trials=2,max_steps=1000),population=8)
    assert r["not_secure_key_exchange"]
    assert r["attacker_denominator"]==r["legitimate_sync_count"]
    assert all("weights" not in str(t) for t in r["trials"])


def test_censored_trials_do_not_count_as_failed_attacks():
    r=genetic_study(TPMProtocol(trials=2,max_steps=1),population=8)
    assert r["legitimate_sync_count"]==0
    assert r["attacker_denominator"]==0
    assert all(t["at_least_one_exact_match"] is None for t in r["trials"])


@pytest.mark.parametrize("population",[0,1,129,True,2.5])
def test_invalid_population(population):
    with pytest.raises(ValueError):
        genetic_trial(TPMProtocol(),trial_index=0,population=population)


def test_invalid_trial_index():
    with pytest.raises(ValueError):
        genetic_trial(TPMProtocol(trials=1),trial_index=1)
