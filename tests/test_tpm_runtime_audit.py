"""TPM wall-time instrumentation correctness, not speed/security proof."""
from __future__ import annotations

import json

import pytest

from tpm_lab.heldout import HoldoutPlan, run_holdout
from tpm_lab.runtime_audit import ARMS, CONTRASTS, TimingProtocol, run_runtime_audit


def smoke() -> tuple[HoldoutPlan, TimingProtocol]:
    return HoldoutPlan(trials=2, max_steps=1000), TimingProtocol(
        first_trials=2, repeats=1
    )


def test_runtime_benchmark_preserves_every_attack_outcome():
    plan, settings = smoke()
    source = run_holdout(plan)
    audit = run_runtime_audit(plan, settings)
    assert audit["cohort_already_observed_not_new_confirmation"]
    assert audit["no_claim_of_equalized_cpu_gpu_or_security"]
    assert audit["holdout_plan_sha256"] == source["plan_sha256"]
    for old, measured in zip(source["trial_records"], audit["measurements"]):
        assert old["trial_index"] == measured["trial_index"]
        assert old["steps_to_sync"] == measured["steps_to_sync"]
        for arm in ARMS:
            assert old[arm] == measured["arms"][arm]["success"]
            assert len(measured["arms"][arm]["elapsed_ns"]) == 1
            assert measured["arms"][arm]["elapsed_ns"][0] > 0


def test_two_repeats_stable_result_without_fixing_timing_values():
    plan = HoldoutPlan(trials=1, max_steps=1000)
    result = run_runtime_audit(plan, TimingProtocol(first_trials=1, repeats=2))
    assert set(result["summary"]) == set(ARMS)
    assert result["single_process_sequential_workloads"]
    assert result["garbage_collection_preceded_each_measurement"]
    for arm in ARMS:
        assert len(result["measurements"][0]["arms"][arm]["elapsed_ns"]) == 2
    assert len(result["paired_runtime_ratios"]) == len(CONTRASTS)
    assert all(v["median_of_paired_wall_time_ratios"] > 0
               for v in result["paired_runtime_ratios"].values())


def test_no_secret_weights_and_timing_nonportable_explicit():
    plan = HoldoutPlan(trials=1, max_steps=1000)
    output = run_runtime_audit(plan, TimingProtocol(first_trials=1, repeats=1))
    serialized = json.dumps(output)
    assert '"weights":' not in serialized
    assert '"private_key":' not in serialized
    assert output["no_secret_key_or_private_weights_exported"]
    assert output["no_claim_of_equalized_cpu_gpu_or_security"]


@pytest.mark.parametrize("changes", [
    {"first_trials": 0}, {"first_trials": 3},
    {"first_trials": True}, {"repeats": 0}, {"repeats": 4},
    {"repeats": True}, {"order_seed": -1}, {"order_seed": True},
])
def test_invalid_timing_protocol_fails_closed(changes):
    plan = HoldoutPlan(trials=2, max_steps=1000)
    with pytest.raises(ValueError):
        run_runtime_audit(plan, TimingProtocol(**changes))
