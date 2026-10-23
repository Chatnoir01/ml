"""Engineering checks for independent TPM ensemble attack, not secrecy."""
import pytest
from tpm_lab import TPMProtocol
from tpm_lab.ensemble import ensemble_study, ensemble_trial, _parity


def test_parity():
    assert _parity((1,-1,1)) == -1
    assert _parity((-1,-1,1)) == 1


def test_deterministic_ensemble():
    p=TPMProtocol(trials=3,max_steps=2000)
    assert ensemble_study(p,attackers=5)==ensemble_study(p,attackers=5)


def test_attackers_do_not_export_secret_weights():
    p=TPMProtocol(trials=2,max_steps=2000)
    r=ensemble_study(p,attackers=5)
    assert r["no_secure_key_generated"]
    assert r["research_only"]
    assert r["attacker_denominator"]==r["synchronized_trials"]
    assert all("weights" not in str(t) for t in r["trials"])


def test_censored_trials_are_not_counted_as_attack_failures():
    p=TPMProtocol(trials=3,max_steps=1)
    r=ensemble_study(p,attackers=5)
    assert r["synchronized_trials"]==0
    assert r["attacker_denominator"]==0
    assert all(t["at_least_one_attacker_matches"] is None for t in r["trials"])


@pytest.mark.parametrize("size",[0,1,2,4,102,True])
def test_reject_invalid_ensemble_size(size):
    with pytest.raises(ValueError):
        ensemble_trial(TPMProtocol(),trial_index=0,attackers=size)


def test_reject_invalid_trial_index():
    with pytest.raises(ValueError):
        ensemble_trial(TPMProtocol(trials=1),trial_index=1)
