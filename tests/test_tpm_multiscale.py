"""Prospective TPM 3-scale experimental guards; no security theorem."""
from __future__ import annotations

import json
import pytest

from tpm_lab.multiscale import (
    SCALES, ATTACKER_CANDIDATES, ScalePlan, _holm_adjust, _pair_trial,
    run_multiscale,
)


def _smoke() -> ScalePlan:
    return ScalePlan(trials_per_scale=1, max_steps=300)


def test_preregistered_three_scales_and_independent_seed_cohorts():
    assert [(s.name,s.n,s.l,s.seed) for s in SCALES] == [
        ("small_N8_L2",8,2,25_102_311),
        ("medium_N16_L3",16,3,25_102_319),
        ("large_N32_L4",32,4,25_102_331),
    ]
    assert ATTACKER_CANDIDATES == 9
    assert ScalePlan().trials_per_scale == 32
    assert ScalePlan().max_steps == 12_000
    assert len(ScalePlan().sha256()) == 64


def test_smoke_determinism_without_seed_or_method_selection():
    p=_smoke()
    first=run_multiscale(p)
    second=run_multiscale(p)
    assert first==second
    assert first["new_seed_cohorts_disjoint_from_pilot_and_holdout"]
    assert first["attacker_candidate_counts_matched"]
    assert first["attacker_forward_evaluations_matched_per_trial"]
    assert first["CPU_runtime_memory_not_equalized"]
    assert first["no_private_keys_or_weights_exported"]
    assert set(first["scales"])=={s.name for s in SCALES}


def test_every_trial_matches_actual_forward_count_and_honest_sync():
    p=_smoke()
    for scale in SCALES:
        row=_pair_trial(p,scale,trial_index=0)
        assert row["cooperative_attacker_forward_evaluations"] == row["geometric_attacker_forward_evaluations"]
        assert row["cooperative_attacker_updates"] >= 0
        assert row["geometric_attacker_updates"] >= 0
        assert isinstance(row["synchronized"],bool)
        if not row["synchronized"]:
            assert row["cooperative_success"] is None
            assert row["geometric_success"] is None


def test_no_nested_weights_or_private_state_in_export():
    r=run_multiscale(_smoke())
    for scale in r["scales"].values():
        assert scale["synchronized_trials"] + scale["censored_trials"] == 1
        assert len(scale["trials"]) == 1
        for row in scale["trials"]:
            assert set(row) == {
                "trial_index","synchronized","steps_to_sync",
                "cooperative_success","geometric_success",
                "cooperative_attacker_forward_evaluations",
                "geometric_attacker_forward_evaluations",
                "cooperative_attacker_updates","geometric_attacker_updates",
                "cooperative_attempted_weight_writes","geometric_attempted_weight_writes",
            }
            assert not any(isinstance(x,(dict,list,tuple)) for x in row.values())
    output=json.dumps(r)
    assert '"private_key":' not in output
    assert '"weights":' not in output
    assert r["not_a_secure_key_exchange_or_cryptographic_proof"]


def test_multiple_comparison_correction_with_three_predeclared_scales():
    names=[s.name for s in SCALES]
    corrected=_holm_adjust({names[0]:0.03,names[1]:0.01,names[2]:0.025})
    assert corrected[names[1]]==pytest.approx(0.03)
    assert corrected[names[2]]==pytest.approx(0.05)
    assert corrected[names[0]]==pytest.approx(0.05)


@pytest.mark.parametrize("kwargs",[
    {"trials_per_scale":0},{"trials_per_scale":33},{"trials_per_scale":True},
    {"max_steps":0},{"max_steps":12001},{"max_steps":True},
    {"candidates":8},{"candidates":10},{"candidates":True},
])
def test_reject_nonregistered_or_invalid_resource_plan(kwargs):
    with pytest.raises(ValueError):
        run_multiscale(ScalePlan(**kwargs))


def test_outside_trial_index_fails():
    with pytest.raises(ValueError):
        _pair_trial(_smoke(),SCALES[0],trial_index=1)
