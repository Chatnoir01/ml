"""Verify paired attribution and reject forged aggregate reports."""
from __future__ import annotations
import copy
import pytest
from tpm_lab.comparison import ComparisonPlan, compare
from tpm_lab.paired_stats import audit_paired_report, exact_mcnemar_two_sided


def test_exact_mcnemar_known_tables():
    assert exact_mcnemar_two_sided(0, 0) == 1.0
    assert exact_mcnemar_two_sided(8, 5) == pytest.approx(0.5810546875)
    assert exact_mcnemar_two_sided(14, 1) == pytest.approx(0.0009765625)
    assert exact_mcnemar_two_sided(1, 7) == pytest.approx(0.0703125)
    for a, b in ((-1, 0), (0, -1), (True, 1), (1.1, 2)):
        with pytest.raises(ValueError):
            exact_mcnemar_two_sided(a, b)


def test_audit_recomputes_paired_discordance_and_reproducibility():
    report = compare(ComparisonPlan(trials=2, max_steps=1000, ensemble_size=3, genetic_population=3))
    audit = audit_paired_report(report)
    assert audit["synchronized_trials"] + audit["censored_trials"] == 2
    assert audit["posthoc_contrasts_not_preregistered"] is True
    assert audit["p_values_not_multiplicity_adjusted"] is True
    assert audit["not_cryptographic_security_evidence"] is True
    assert audit == audit_paired_report(report)


def test_detects_manipulated_aggregate_and_hidden_nested_content():
    report = compare(ComparisonPlan(trials=2, max_steps=1000, ensemble_size=3, genetic_population=3))
    bad = copy.deepcopy(report)
    bad["attack_results"]["naive"]["exact_match_trials"] += 1
    with pytest.raises(ValueError, match="successes disagree"):
        audit_paired_report(bad)
    bad = copy.deepcopy(report)
    bad["trial_records"][0]["raw_secret_weights"] = [1, 2, 3]
    with pytest.raises(ValueError, match="unexpected trial shape"):
        audit_paired_report(bad)
    bad = copy.deepcopy(report)
    bad["protocol_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        audit_paired_report(bad)
    bad = copy.deepcopy(report)
    bad["median_sync_steps_conditional"] = -10
    with pytest.raises(ValueError, match="median synchronization"):
        audit_paired_report(bad)
    bad = copy.deepcopy(report)
    bad["attack_results"]["naive"]["wilson_95pct_descriptive"] = (0.0, 1.0)
    with pytest.raises(ValueError, match="interval disagrees"):
        audit_paired_report(bad)


def test_censored_records_never_enter_attack_denominator():
    report = compare(ComparisonPlan(trials=2, max_steps=1, ensemble_size=3, genetic_population=3))
    audit = audit_paired_report(report)
    assert audit["synchronized_trials"] == 0
    assert audit["censored_trials"] == 2
    for x in audit["comparisons"].values():
        assert x["discordant"] == 0
        assert x["exact_mcnemar_two_sided_p_exploratory"] == 1.0
