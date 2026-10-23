"""Held-out candidate-matched TPM test contracts; never security assurance."""
from __future__ import annotations

import json

import pytest

from tpm_lab import TPMProtocol
from tpm_lab.heldout import (
    COMPARISONS,
    HoldoutPlan,
    _holms_two,
    replicated_geometric_trial,
    run_holdout,
)
from tpm_lab.sync import trial


def _smoke() -> HoldoutPlan:
    # Engineering-only short run; production scientific defaults are fixed.
    return HoldoutPlan(trials=2, max_steps=1000)


def test_confirmatory_plan_has_new_reserved_seed_and_frozen_contrasts():
    plan = HoldoutPlan()
    assert plan.master_seed == 971023
    assert plan.trials == 64
    assert plan.ensemble_candidates == 9
    assert plan.genetic_candidates == 16
    assert COMPARISONS == (("ensemble9", "geometric9"), ("genetic16", "geometric16"))
    assert len(plan.sha256()) == 64


def test_holdout_reproducible_and_matching_legitimate_streams():
    report = run_holdout(_smoke())
    assert report == run_holdout(_smoke())
    assert report["no_cryptographic_security_proven"] is True
    assert report["no_private_weights_or_key_exported"] is True
    assert report["attack_population_sizes_matched_within_contrast"] is True
    assert report["runtime_and_optimizer_operations_not_equated"] is True
    assert report["synchronized_trials"] + report["censored_trials"] == 2
    assert len(report["registered_contrasts"]) == 2
    assert set(report["arms"]) == {"ensemble9", "geometric9", "genetic16", "geometric16"}
    assert all(row["steps_to_sync"] == trial(_smoke().validated_protocol(), trial_index=i)["steps_to_sync"]
               for i, row in enumerate(report["trial_records"]))


def test_no_secret_weights_in_exported_trial_records():
    report = run_holdout(_smoke())
    expected = {
        "trial_index", "synchronized", "steps_to_sync",
        "ensemble9", "geometric9", "genetic16", "geometric16",
    }
    assert all(set(row) == expected for row in report["trial_records"])
    assert all(not isinstance(x, (list, tuple, dict)) for row in report["trial_records"]
               for x in row.values())
    assert '"private_key"' not in json.dumps(report)


def test_geometric_attack_uses_same_synchronized_baseline_only_for_scoring():
    plan = _smoke()
    p = plan.validated_protocol()
    x = replicated_geometric_trial(p, trial_index=0, candidates=9)
    baseline = trial(p, trial_index=0)
    assert x["steps_to_sync"] == baseline["steps_to_sync"]
    assert x["synchronized"] == baseline["synchronized"]
    assert x["research_only_no_key_export"] is True
    assert x["any_match_at_sync"] is not None


def test_censoring_does_not_count_as_attacker_failure():
    out = run_holdout(HoldoutPlan(trials=2, max_steps=1))
    assert out["censored_trials"] == 2
    assert out["synchronized_trials"] == 0
    for metrics in out["arms"].values():
        assert metrics["denominator"] == 0
        assert metrics["conditional_rate"] is None
    for contrast in out["paired_contrasts"].values():
        assert contrast["paired_difference"] is None
        assert contrast["exact_mcnemar_two_sided_p"] is None
        assert contrast["holm_two_contrasts_adjusted_p"] is None


def test_holm_two_comparisons_corrects_order_and_monotonicity():
    p = {"ensemble9_vs_geometric9": 0.03, "genetic16_vs_geometric16": 0.01}
    got = _holms_two(p)
    assert got["genetic16_vs_geometric16"] == pytest.approx(0.02)
    assert got["ensemble9_vs_geometric9"] == pytest.approx(0.03)


@pytest.mark.parametrize("updates", [
    {"trials": 0}, {"trials": 101}, {"trials": True},
    {"master_seed": -1}, {"max_steps": 0}, {"ensemble_candidates": 8},
    {"genetic_candidates": 15}, {"inputs_per_unit": 9}, {"hidden_units": 4},
    {"synaptic_depth": 3},
])
def test_bad_plan_fails_closed(updates):
    with pytest.raises(ValueError):
        run_holdout(HoldoutPlan(**updates))


@pytest.mark.parametrize("candidate_size", [0, 129, True])
def test_bad_geometric_budget_rejected(candidate_size):
    with pytest.raises(ValueError):
        replicated_geometric_trial(TPMProtocol(trials=1), trial_index=0, candidates=candidate_size)
