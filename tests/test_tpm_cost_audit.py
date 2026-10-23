"""Retrospective TPM algorithmic workload checks, NOT a security benchmark."""
from __future__ import annotations

import json

import pytest

from tpm_lab.cost_audit import cost_trial, run_cost_audit
from tpm_lab.heldout import HoldoutPlan, run_holdout


def smoke_plan() -> HoldoutPlan:
    return HoldoutPlan(trials=2, max_steps=1000)


def test_instrumentation_reproduces_uninstrumented_attack_outcomes():
    plan = smoke_plan()
    raw = run_holdout(plan)
    instrumented = run_cost_audit(plan, first_trials=2)
    for baseline, cost in zip(raw["trial_records"], instrumented["trial_records"]):
        assert baseline["steps_to_sync"] == cost["steps_to_sync"]
        for name in ("ensemble9", "geometric9", "genetic16", "geometric16"):
            assert baseline[name] == cost["arms"][name]["at_least_one_exact_state_match"]


def test_same_run_yields_identical_counts_not_timing_noise():
    plan = smoke_plan()
    assert run_cost_audit(plan, first_trials=2) == run_cost_audit(plan, first_trials=2)


def test_attacker_calls_separate_from_legitimate_party_calls():
    row = cost_trial(smoke_plan(), trial_index=0)
    assert row["synchronized"]
    for label, data in row["arms"].items():
        counts = data["work"]
        assert counts["honest_constructions"] == 2
        assert counts["honest_evaluations"] == 2 * row["steps_to_sync"]
        assert counts["honest_updates"] % 2 == 0
        assert counts["attacker_constructions"] >= 1
        assert counts["attacker_evaluations"] > 0
        assert counts["attacker_updates"] >= 0
        assert counts["attacker_attempted_weight_writes"] >= 0
    assert row["arms"]["geometric9"]["work"]["attacker_constructions"] == 9
    assert row["arms"]["geometric16"]["work"]["attacker_constructions"] == 16
    assert row["arms"]["ensemble9"]["work"]["attacker_constructions"] == 9
    assert row["arms"]["genetic16"]["work"]["attacker_constructions"] >= 16


def test_no_secret_weights_output_or_fake_cpu_equation():
    report = run_cost_audit(smoke_plan(), first_trials=1)
    assert report["operations_are_invocation_counts_not_CPU_equivalence"] is True
    assert report["cohort_already_used_for_holdout"] is True
    assert report["global_class_patching_single_thread_only"] is True
    assert report["no_private_weights_or_keys_exported"] is True
    assert report["not_crypto_security_assurance"] is True
    dumped = json.dumps(report)
    assert '"weights":' not in dumped
    assert '"private_key":' not in dumped
    expected = {"trial_index", "synchronized", "steps_to_sync", "arms"}
    assert set(report["trial_records"][0]) == expected


@pytest.mark.parametrize("bad", [0, 3, True, 1.5, -1])
def test_invalid_retrospective_cohort_rejected(bad):
    with pytest.raises(ValueError):
        run_cost_audit(smoke_plan(), first_trials=bad)


@pytest.mark.parametrize("bad", [2, True, -1])
def test_bad_trial_index_rejected(bad):
    with pytest.raises(ValueError):
        cost_trial(smoke_plan(), trial_index=bad)
