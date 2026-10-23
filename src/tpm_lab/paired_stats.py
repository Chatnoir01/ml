"""Audit preregistered TPM paired trials; descriptive, not crypto security.

Pairwise contrasts in this module were selected after viewing the 32-trial
pilot, so exploratory p-values MUST NOT be treated as confirmatory evidence.
"""
from __future__ import annotations

import math
from typing import Any

ATTACKS = ("naive", "geometric", "random_flip", "ensemble", "genetic")
CONTRASTS = (("ensemble", "geometric"), ("geometric", "naive"), ("genetic", "geometric"))


def exact_mcnemar_two_sided(first_only: int, second_only: int) -> float:
    """Exact symmetric-binomial test on discordant paired observations."""
    if (type(first_only) is not int or type(second_only) is not int
            or first_only < 0 or second_only < 0):
        raise ValueError("discordant counts must be nonnegative integers")
    n = first_only + second_only
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(first_only, second_only) + 1))
    return min(1.0, 2.0 * tail / (1 << n))


def audit_paired_report(report: dict[str, Any]) -> dict[str, Any]:
    """Cross-check exported trial rows vs aggregates and paired contrasts.

    This function rejects nested raw keys/private weights in per-trial records.
    All report results must be binary attack outcomes, never secret materials.
    """
    from .comparison import ComparisonPlan

    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    if report.get("schema_version") != 1 or report.get("kind") != "descriptive_tpm_paired_attacker_comparison":
        raise ValueError("unsupported report schema")
    if report.get("not_proof_of_security") is not True or report.get("no_private_weights_or_keys_exported") is not True:
        raise ValueError("missing research-only or nonexport receipt")
    p = report.get("plan")
    if not isinstance(p, dict) or set(p) != {"trials", "master_seed", "max_steps", "ensemble_size", "genetic_population"}:
        raise ValueError("unrecognized plan")
    plan = ComparisonPlan(**p)
    if report.get("plan_sha256") != plan.sha256() or report.get("protocol_sha256") != plan.protocol().sha256():
        raise ValueError("plan/protocol digest mismatch")

    rows = report.get("trial_records")
    if not isinstance(rows, list) or len(rows) != plan.trials:
        raise ValueError("trial count mismatch")
    expected_row_fields = {"trial_index", "synchronized", "steps_to_sync", *ATTACKS}
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != expected_row_fields or row["trial_index"] != i:
            raise ValueError("unexpected trial shape/index; possible data leak")
        if type(row["synchronized"]) is not bool:
            raise ValueError("synchronization must be boolean")
        if row["synchronized"]:
            if type(row["steps_to_sync"]) is not int or not (1 <= row["steps_to_sync"] <= plan.max_steps):
                raise ValueError("invalid synchronization step")
            if any(type(row[name]) is not bool for name in ATTACKS):
                raise ValueError("observed attack outcomes must be boolean")
        elif row["steps_to_sync"] is not None or any(row[name] is not None for name in ATTACKS):
            raise ValueError("censored trials must have null attack outcomes")

    observed = [r for r in rows if r["synchronized"]]
    if report.get("synchronized_trials") != len(observed) or report.get("censored_trials") != plan.trials - len(observed):
        raise ValueError("censoring denominator mismatch")
    attacks = report.get("attack_results")
    if not isinstance(attacks, dict) or set(attacks) != set(ATTACKS):
        raise ValueError("unexpected attack metrics")
    for name in ATTACKS:
        source = attacks[name]
        successes = sum(r[name] for r in observed)
        if source["exact_match_trials"] != successes or source["denominator_synchronized"] != len(observed):
            raise ValueError("aggregate/row successes disagree")
        expected = successes / len(observed) if observed else None
        if source["rate_conditional_on_sync"] != expected:
            raise ValueError("published rate disagrees with raw trial outcomes")

    comparisons = {}
    for first, second in CONTRASTS:
        first_only = sum(r[first] and not r[second] for r in observed)
        second_only = sum(r[second] and not r[first] for r in observed)
        both = sum(r[first] and r[second] for r in observed)
        neither = len(observed) - first_only - second_only - both
        comparisons[f"{first}_vs_{second}"] = {
            "first_only": first_only,
            "second_only": second_only,
            "both": both,
            "neither": neither,
            "discordant": first_only + second_only,
            "exact_mcnemar_two_sided_p_exploratory": exact_mcnemar_two_sided(first_only, second_only),
        }
    return {
        "schema_version": 1,
        "report_plan_sha256": report["plan_sha256"],
        "synchronized_trials": len(observed),
        "censored_trials": plan.trials - len(observed),
        "comparisons": comparisons,
        "posthoc_contrasts_not_preregistered": True,
        "p_values_not_multiplicity_adjusted": True,
        "attacker_compute_budgets_not_equal": True,
        "not_cryptographic_security_evidence": True,
        "no_private_weights_or_keys_exported": True,
    }
