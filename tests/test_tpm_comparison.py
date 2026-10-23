"""Paired TPM benchmarking invariants; no cryptographic proof."""
import pytest
from tpm_lab.comparison import ComparisonPlan,compare,wilson_interval


def test_wilson_bounds():
    assert wilson_interval(0,0) is None
    assert wilson_interval(0,10)[0] == 0
    assert wilson_interval(10,10)[1] == 1
    assert wilson_interval(5,10)[0] < 0.5 < wilson_interval(5,10)[1]


def test_paired_benchmark_reproducible():
    plan=ComparisonPlan(trials=2,max_steps=1000,ensemble_size=3,genetic_population=3)
    first=compare(plan)
    assert first==compare(plan)
    assert first["synchronized_trials"]+first["censored_trials"]==2
    assert first["resource_budgets_differ_across_arms"]
    assert first["no_private_weights_or_keys_exported"]
    assert set(first["attack_results"])=={"naive","geometric","random_flip","ensemble","genetic"}


def test_all_censored_means_no_attack_denominator():
    r=compare(ComparisonPlan(trials=2,max_steps=1,ensemble_size=3,genetic_population=3))
    assert r["synchronized_trials"]==0
    assert all(v["rate_conditional_on_sync"] is None for v in r["attack_results"].values())
    assert all(v["wilson_95pct_descriptive"] is None for v in r["attack_results"].values())


@pytest.mark.parametrize("kwargs",[{"trials":0},{"ensemble_size":4},{"ensemble_size":1},{"genetic_population":1},{"genetic_population":129}])
def test_invalid_plan(kwargs):
    with pytest.raises(ValueError):
        compare(ComparisonPlan(**kwargs))
