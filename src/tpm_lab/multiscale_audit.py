"""Independent, output-only audit of the frozen 96-session TPM report.

No attacker code is called; never consumes raw private weight vectors.
This verifier was created separately from the registered protocol to
identify malformed/inconsistent receipts without tuning attack outcomes.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from typing import Any

EXPECTED_SCALES = (
    ("small_N8_L2", 8, 2, 25102311),
    ("medium_N16_L3", 16, 3, 25102319),
    ("large_N32_L4", 32, 4, 25102331),
)
FROZEN_PLAN_SHA256 = "6d282d9130f03e41204607af690c50501afec816d5820639c2eeba2178d69569"
EXPECTED_ROW_KEYS = {
    "trial_index", "synchronized", "steps_to_sync",
    "cooperative_success", "geometric_success",
    "cooperative_attacker_forward_evaluations",
    "geometric_attacker_forward_evaluations",
    "cooperative_attacker_updates", "geometric_attacker_updates",
    "cooperative_attempted_weight_writes",
    "geometric_attempted_weight_writes",
}
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version", "kind", "plan", "plan_sha256",
    "prespecified_scales", "registered_family", "scales",
    "new_seed_cohorts_disjoint_from_pilot_and_holdout",
    "attacker_candidate_counts_matched",
    "attacker_forward_evaluations_matched_per_trial",
    "CPU_runtime_memory_not_equalized",
    "posthoc_scales_or_trial_exclusions_not_permitted",
    "all_attackers_observe_public_transcript_only",
    "not_a_secure_key_exchange_or_cryptographic_proof",
    "no_private_keys_or_weights_exported",
    "execution_level", "security_verdict",
}
EXPECTED_AGGREGATE_KEYS = {
    "n", "l", "master_seed", "protocol_sha256", "synchronized_trials",
    "censored_trials", "median_steps_conditional", "cooperative9_exact_matches",
    "geometric9_exact_matches", "cooperative9_wilson_95pct",
    "geometric9_wilson_95pct", "first_only", "second_only", "both",
    "neither", "exact_two_sided_mcnemar_p", "adjusted_holm_p",
    "cooperative_minus_geometric_success_rate",
    "forward_evaluations_balanced_per_trial", "trials",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _close(actual: Any, expected: float | None, label: str) -> None:
    if expected is None:
        _require(actual is None, f"{label}: expected null")
    else:
        _require(type(actual) in (int, float), f"{label}: expected a number")
        _require(
            math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12),
            f"{label}: numeric mismatch",
        )


def _wilson(successes: int, observed: int) -> list[float] | None:
    if observed == 0:
        return None
    z = 1.96
    rate = successes / observed
    d = 1 + z * z / observed
    m = (rate + z * z / (2 * observed)) / d
    spread = z * math.sqrt(rate * (1 - rate) / observed + z * z / (4 * observed**2)) / d
    return [max(0.0, m - spread), min(1.0, m + spread)]


def _mcnemar(first_only: int, second_only: int) -> float:
    discordant = first_only + second_only
    if discordant == 0:
        return 1.0
    numerator = sum(math.comb(discordant, j) for j in range(min(first_only, second_only) + 1))
    return min(1.0, 2.0 * numerator / (1 << discordant))


def _plan_receipt() -> str:
    plan = {"candidates": 9, "max_steps": 12000, "trials_per_scale": 32}
    d = {
        "plan": plan,
        "scales": [
            {"name": name, "n": n, "l": l, "seed": seed}
            for name, n, l, seed in EXPECTED_SCALES
        ],
        "candidates": 9,
        "contrast": "cooperative9_vs_geometric9",
        "endpoint": "exact_match_at_first_legitimate_sync",
        "p_correction": "Holm_across_three_scales",
    }
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit_multiscale_receipt(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute every published binary, denominator and statistical result.

    Rejects extra trial/aggregate fields to prevent raw model weight output.
    Accepts ONLY the registered full 96-session plan, not smoke data.
    """
    _require(isinstance(report, dict), "report must be an object")
    _require(set(report) == EXPECTED_TOP_LEVEL_KEYS, "unexpected top-level fields (possible secret export)")
    _require(report.get("schema_version") == 1, "schema mismatch")
    _require(report.get("kind") == "prospective_multiscale_neural_tpm_attack_comparison", "report kind mismatch")
    _require(report.get("plan") == {"candidates": 9, "max_steps": 12000, "trials_per_scale": 32}, "plan changed")
    _require(report.get("plan_sha256") == FROZEN_PLAN_SHA256, "registered SHA-256 changed")
    _require(_plan_receipt() == FROZEN_PLAN_SHA256, "independent plan digest mismatch")
    expected_scale_dicts = [
        {"name": name, "n": n, "l": l, "seed": seed}
        for name, n, l, seed in EXPECTED_SCALES
    ]
    _require(report.get("prespecified_scales") == expected_scale_dicts, "scale set changed")
    _require(report.get("registered_family") == "three paired cooperative9_vs_geometric9 contrasts", "statistical family changed")
    for flag in (
        "new_seed_cohorts_disjoint_from_pilot_and_holdout",
        "attacker_candidate_counts_matched",
        "attacker_forward_evaluations_matched_per_trial",
        "CPU_runtime_memory_not_equalized",
        "posthoc_scales_or_trial_exclusions_not_permitted",
        "all_attackers_observe_public_transcript_only",
        "not_a_secure_key_exchange_or_cryptographic_proof",
        "no_private_keys_or_weights_exported",
    ):
        _require(report.get(flag) is True, f"missing research-only receipt {flag}")
    _require(report.get("execution_level") == "predeclared_96_trial_confirmation", "not the full confirmation")
    _require(report.get("security_verdict") == "NOT_ESTABLISHED", "unsupported security verdict")
    scales = report.get("scales")
    _require(isinstance(scales, dict) and set(scales) == {s[0] for s in EXPECTED_SCALES}, "incorrect scale keys")
    p_values = {}
    reconciled = {}
    total_trials = 0
    for name, n, l, seed in EXPECTED_SCALES:
        item = scales[name]
        _require(isinstance(item, dict) and set(item) == EXPECTED_AGGREGATE_KEYS, f"{name}: unexpected metric fields")
        _require((item["n"], item["l"], item["master_seed"]) == (n, l, seed), f"{name}: scale parameters changed")
        protocol_spec = {
            "hidden_units": 3, "inputs_per_unit": n, "synaptic_depth": l,
            "max_steps": 12000, "trials": 32, "master_seed": seed,
            "learning_rule": "hebbian",
        }
        expected_protocol_sha = hashlib.sha256(
            json.dumps(protocol_spec, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        _require(item["protocol_sha256"] == expected_protocol_sha, f"{name}: protocol SHA mismatch")
        _require(item["forward_evaluations_balanced_per_trial"] is True, f"{name}: forward count assertion missing")
        rows = item["trials"]
        _require(isinstance(rows, list) and len(rows) == 32, f"{name}: missing trials")
        synchronized = []
        for index, row in enumerate(rows):
            _require(isinstance(row, dict) and set(row) == EXPECTED_ROW_KEYS, f"{name}: unexpected trial fields (potential secret export)")
            _require(type(row["trial_index"]) is int and row["trial_index"] == index, f"{name}: trial order/index mismatch")
            _require(type(row["synchronized"]) is bool, f"{name}: synchronized must be boolean")
            e1 = row["cooperative_attacker_forward_evaluations"]
            e2 = row["geometric_attacker_forward_evaluations"]
            _require(type(e1) is int and e1 >= 0 and type(e2) is int and e2 == e1, f"{name}: forward evaluations not matched")
            for key in ("cooperative_attacker_updates", "geometric_attacker_updates",
                        "cooperative_attempted_weight_writes", "geometric_attempted_weight_writes"):
                _require(type(row[key]) is int and row[key] >= 0, f"{name}: invalid work counter")
            if row["synchronized"]:
                _require(
                    type(row["steps_to_sync"]) is int and 1 <= row["steps_to_sync"] <= 12000,
                    f"{name}: invalid synchronization step",
                )
                _require(
                    type(row["cooperative_success"]) is bool and type(row["geometric_success"]) is bool,
                    f"{name}: synchronized attack outcome must be boolean",
                )
                synchronized.append(row)
            else:
                _require(
                    row["steps_to_sync"] is None and row["cooperative_success"] is None and row["geometric_success"] is None,
                    f"{name}: censored trials must have null outcomes",
                )
        count = len(synchronized)
        _require(item["synchronized_trials"] == count and item["censored_trials"] == 32-count, f"{name}: incorrect censoring")
        med = statistics.median(r["steps_to_sync"] for r in synchronized) if count else None
        _close(item["median_steps_conditional"], med, f"{name}: median sync step")
        first = sum(r["cooperative_success"] for r in synchronized)
        second = sum(r["geometric_success"] for r in synchronized)
        both = sum(r["cooperative_success"] and r["geometric_success"] for r in synchronized)
        first_only = first-both
        second_only = second-both
        neither = count-first_only-second_only-both
        for key, expected in (
            ("cooperative9_exact_matches", first),
            ("geometric9_exact_matches", second),
            ("first_only", first_only),
            ("second_only", second_only),
            ("both", both),
            ("neither", neither),
        ):
            _require(type(item[key]) is int and item[key] == expected, f"{name}: {key} disagrees with raw trials")
        _close(item["cooperative_minus_geometric_success_rate"], (first-second)/count if count else None, f"{name}: paired effect")
        for metric, successes in (
            ("cooperative9_wilson_95pct", first),
            ("geometric9_wilson_95pct", second),
        ):
            expected_interval = _wilson(successes, count)
            if expected_interval is None:
                _require(item[metric] is None, f"{name}: censored Wilson interval must be null")
            else:
                got = item[metric]
                _require(isinstance(got, list) and len(got) == 2, f"{name}: malformed Wilson interval")
                for index, expected in enumerate(expected_interval):
                    _close(got[index], expected, f"{name}: Wilson {metric}[{index}]")
        p = _mcnemar(first_only, second_only) if count else None
        _close(item["exact_two_sided_mcnemar_p"], p, f"{name}: exact paired p")
        p_values[name] = p if p is not None else 1.0
        reconciled[name] = {
            "synchronized": count,
            "censored": 32-count,
            "cooperative_success": first,
            "geometric_success": second,
            "both": both,
            "cooperative_only": first_only,
            "geometric_only": second_only,
            "neither": neither,
            "recomputed_exact_mcnemar_p": p,
        }
        total_trials += len(rows)
    order = sorted(p_values, key=lambda x: (p_values[x], x))
    high = 0.0
    for index, name in enumerate(order):
        high = max(high, min(1.0, (3-index)*p_values[name]))
        expected = high if reconciled[name]["synchronized"] else None
        _close(scales[name]["adjusted_holm_p"], expected, f"{name}: Holm adjustment")
        reconciled[name]["recomputed_holm_p"] = expected
    _require(total_trials == 96, "invalid overall sample size")

    return {
        "schema_version": 1,
        "kind": "independent_output_only_tpm_96_receipt_audit",
        "plan_sha256": FROZEN_PLAN_SHA256,
        "audited_new_trial_count": total_trials,
        "scales": reconciled,
        "all_three_predeclared_contrasts_checked": True,
        "only_public_aggregate_statistics_exported": True,
        "no_raw_private_model_weights_or_keys_exported": True,
        "no_cryptographic_security_guarantee": True,
    }
