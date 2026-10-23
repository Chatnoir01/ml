"""Blind validation of frozen 96-session report, before any new results.

Fixtures are SYNTHETIC and are NOT observations from the registered seeds.
"""
from __future__ import annotations

import copy
import pytest

from tpm_lab.multiscale import SCALES, ScalePlan
from tpm_lab.multiscale_audit import audit_multiscale_receipt, _wilson
from tpm_lab.sync import TPMProtocol


def synthetic_96_trial_report() -> dict:
    """Synthetic 32×3 records, with deliberately simple paired outcomes."""
    values = {}
    for scale in SCALES:
        rows = []
        for i in range(32):
            # These fake records are only for testing algebra and schemas.
            coop = i < 5
            geo = i < 7
            rows.append({
                "trial_index": i,
                "synchronized": True,
                "steps_to_sync": 15,
                "cooperative_success": coop,
                "geometric_success": geo,
                "cooperative_attacker_forward_evaluations": 63,
                "geometric_attacker_forward_evaluations": 63,
                "cooperative_attacker_updates": 63,
                "geometric_attacker_updates": 63,
                "cooperative_attempted_weight_writes": 64,
                "geometric_attempted_weight_writes": 64,
            })
        proto = TPMProtocol(
            inputs_per_unit=scale.n,
            synaptic_depth=scale.l,
            master_seed=scale.seed,
            trials=32,
            max_steps=12000,
        )
        values[scale.name] = {
            "n": scale.n,
            "l": scale.l,
            "master_seed": scale.seed,
            "protocol_sha256": proto.sha256(),
            "synchronized_trials": 32,
            "censored_trials": 0,
            "median_steps_conditional": 15,
            "cooperative9_exact_matches": 5,
            "geometric9_exact_matches": 7,
            "cooperative9_wilson_95pct": _wilson(5, 32),
            "geometric9_wilson_95pct": _wilson(7, 32),
            "first_only": 0,
            "second_only": 2,
            "both": 5,
            "neither": 25,
            "exact_two_sided_mcnemar_p": 0.5,
            "adjusted_holm_p": 1.0,
            "cooperative_minus_geometric_success_rate": -2/32,
            "forward_evaluations_balanced_per_trial": True,
            "trials": rows,
        }
    return {
        "schema_version": 1,
        "kind": "prospective_multiscale_neural_tpm_attack_comparison",
        "plan": {"trials_per_scale": 32, "max_steps": 12000, "candidates": 9},
        "plan_sha256": ScalePlan().sha256(),
        "prespecified_scales": [
            {"name": x.name, "n": x.n, "l": x.l, "seed": x.seed}
            for x in SCALES
        ],
        "registered_family": "three paired cooperative9_vs_geometric9 contrasts",
        "scales": values,
        "new_seed_cohorts_disjoint_from_pilot_and_holdout": True,
        "attacker_candidate_counts_matched": True,
        "attacker_forward_evaluations_matched_per_trial": True,
        "CPU_runtime_memory_not_equalized": True,
        "posthoc_scales_or_trial_exclusions_not_permitted": True,
        "all_attackers_observe_public_transcript_only": True,
        "not_a_secure_key_exchange_or_cryptographic_proof": True,
        "no_private_keys_or_weights_exported": True,
        "execution_level": "predeclared_96_trial_confirmation",
        "security_verdict": "NOT_ESTABLISHED",
    }


def test_synthetic_96_trial_fixture_passes_full_algebra_audit():
    result = audit_multiscale_receipt(synthetic_96_trial_report())
    assert result["audited_new_trial_count"] == 96
    assert result["all_three_predeclared_contrasts_checked"]
    assert result["no_cryptographic_security_guarantee"]
    for data in result["scales"].values():
        assert data["cooperative_success"] == 5
        assert data["geometric_success"] == 7
        assert data["recomputed_holm_p"] == 1.0


@pytest.mark.parametrize("mutator, message", [
    (lambda r: r.update(private_key=[1,2,3]), "top-level"),
    (lambda r: r["scales"]["small_N8_L2"]["trials"][0].update(weights=[1,2]), "trial fields"),
    (lambda r: r["scales"]["medium_N16_L3"].update(cooperative9_exact_matches=6), "exact_matches"),
    (lambda r: r["scales"]["large_N32_L4"]["trials"][1].update(geometric_success=False), "exact_matches"),
    (lambda r: r["scales"]["medium_N16_L3"].update(first_only=1), "first_only"),
    (lambda r: r["scales"]["small_N8_L2"].update(adjusted_holm_p=0.03), "Holm adjustment"),
    (lambda r: r["scales"]["large_N32_L4"].update(exact_two_sided_mcnemar_p=0.1), "exact paired p"),
    (lambda r: r["scales"]["medium_N16_L3"].update(geometric9_wilson_95pct=[0.0,1.0]), "Wilson"),
    (lambda r: r["scales"]["small_N8_L2"].update(median_steps_conditional=20), "median sync"),
    (lambda r: r["scales"]["small_N8_L2"].update(protocol_sha256="0"*64), "protocol SHA"),
    (lambda r: r["scales"]["medium_N16_L3"]["trials"][0].update(geometric_attacker_forward_evaluations=7), "forward evaluations"),
    (lambda r: r["scales"]["small_N8_L2"]["trials"][0].update(synchronized=False), "censored"),
])
def test_rejects_tampered_or_inconsistent_report(mutator, message):
    data = copy.deepcopy(synthetic_96_trial_report())
    mutator(data)
    with pytest.raises(ValueError, match=message):
        audit_multiscale_receipt(data)


def test_cannot_label_smoke_as_frozen_96_trial_confirmation():
    result = synthetic_96_trial_report()
    result["execution_level"] = "engineering_smoke"
    with pytest.raises(ValueError, match="full confirmation"):
        audit_multiscale_receipt(result)
