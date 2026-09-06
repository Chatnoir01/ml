"""Frozen Phase-2B held-out aggregation and support statistics."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Any

from .phase2b import (
    CLASSICAL_BUDGET_PER_ARM_SEED,
    EVOLUTION_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    phase2b_verdict,
)
from .phase2b_validation import validation_seed_gate

ARMS = ("control", "oracle", "shuffled")


def exact_one_sided_sign_p(wins: int, losses: int) -> float:
    """Exact one-sided sign-test p-value; exact ties are excluded by caller."""

    wins = int(wins)
    losses = int(losses)
    if wins < 0 or losses < 0:
        raise ValueError("sign-test counts must be non-negative")
    n = wins + losses
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(wins, n + 1)) / (2**n))


def summarize_support(
    *,
    control: Sequence[float],
    oracle: Sequence[float],
    shuffled: Sequence[float],
    classical_non_degradation: bool,
) -> dict[str, Any]:
    """Apply the exact preregistered six-gate support rule to nine paired seeds."""

    if not (len(control) == len(oracle) == len(shuffled) == len(EVOLUTION_SEEDS)):
        raise ValueError("Phase 2B support summary requires exactly nine paired seeds")
    c = [float(value) for value in control]
    o = [float(value) for value in oracle]
    s = [float(value) for value in shuffled]
    if not all(math.isfinite(value) for value in [*c, *o, *s]):
        raise ValueError("Phase 2B held-out scores must be finite")

    diff_oc = [left - right for left, right in zip(c, o)]
    wins_oc = sum(delta > 0.0 for delta in diff_oc)
    losses_oc = sum(delta < 0.0 for delta in diff_oc)
    ties_oc = len(diff_oc) - wins_oc - losses_oc
    sign_p = exact_one_sided_sign_p(wins_oc, losses_oc)
    mean_reduction_oc = float(statistics.fmean(diff_oc))

    diff_os = [left - right for left, right in zip(s, o)]
    wins_os = sum(delta > 0.0 for delta in diff_os)
    ties_os = sum(delta == 0.0 for delta in diff_os)
    mean_reduction_sc = float(statistics.fmean(left - right for left, right in zip(c, s)))

    checks = {
        "o_wins_c_8_of_9": bool(wins_oc >= 8),
        "paired_sign_p_lt_005": bool(sign_p < 0.05),
        "mean_reduction_ge_002": bool(mean_reduction_oc >= 0.02),
        "classical_non_degradation": bool(classical_non_degradation),
        "o_wins_s_6_of_9": bool(wins_os >= 6),
        "o_reduction_gt_s_reduction": bool(mean_reduction_oc > mean_reduction_sc),
    }
    return {
        "checks": checks,
        "paired_o_vs_c": {
            "wins": int(wins_oc),
            "losses": int(losses_oc),
            "ties": int(ties_oc),
            "exact_one_sided_sign_p": float(sign_p),
            "mean_reduction_c_minus_o": mean_reduction_oc,
            "per_seed_reductions": diff_oc,
        },
        "specificity_o_vs_s": {
            "wins": int(wins_os),
            "ties": int(ties_os),
            "mean_reduction_c_minus_s": mean_reduction_sc,
            "per_seed_s_minus_o": diff_os,
        },
        "verdict": phase2b_verdict(True, checks),
    }


def _joint(metrics: dict[str, Any]) -> bool:
    return bool(
        int(metrics["differential_uniformity"]) <= 8
        and int(metrics["nonlinearity"]) >= 100
        and int(metrics["max_linear_correlation"]) <= 64
        and int(metrics["algebraic_degree"]) >= 6
    )


def _classically_non_degraded(control: dict[str, Any], oracle: dict[str, Any]) -> bool:
    c = control["terminal_classical"]
    o = oracle["terminal_classical"]
    return bool(
        (not _joint(c) or _joint(o))
        and int(o["differential_uniformity"]) <= int(c["differential_uniformity"])
        and int(o["nonlinearity"]) >= int(c["nonlinearity"])
        and int(o["max_linear_correlation"]) <= int(c["max_linear_correlation"])
        and int(o["algebraic_degree"]) >= int(c["algebraic_degree"])
    )


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    clean = {key: value for key, value in payload.items() if key != "aggregate_payload_sha256"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")


def aggregate_phase2b(
    arm_results: Sequence[dict[str, Any]],
    validation_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Validate all 27 arm/validation records and apply the frozen Phase-2B rule."""

    expected = {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}
    arms: dict[tuple[int, str], dict[str, Any]] = {}
    for item in arm_results:
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in arms:
            raise ValueError(f"invalid or duplicate Phase 2B arm record {key!r}")
        arms[key] = item
    validations: dict[tuple[int, str], dict[str, Any]] = {}
    for item in validation_results:
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in validations:
            raise ValueError(f"invalid or duplicate Phase 2B validation record {key!r}")
        validations[key] = item
    if set(arms) != expected or set(validations) != expected:
        raise ValueError("Phase 2B aggregate requires exact 9-seed × 3-arm records")

    exact_budgets = True
    receipt_integrity = True
    terminal_validation_identity = True
    same_initial_population = True
    held_out_scores: dict[str, list[float]] = {arm: [] for arm in ARMS}
    classical_non_degradation = True

    for seed in EVOLUTION_SEEDS:
        per_seed_arms = [arms[(int(seed), arm)] for arm in ARMS]
        digests = {str(item.get("initial_population_digest_sha256", "")) for item in per_seed_arms}
        same_initial_population &= len(digests) == 1 and "" not in digests

        classical_non_degradation &= _classically_non_degraded(
            arms[(int(seed), "control")],
            arms[(int(seed), "oracle")],
        )

        for arm in ARMS:
            run = arms[(int(seed), arm)]
            receipts = list(run.get("oracle_receipts", []))
            exact_budgets &= (
                int(run.get("classical_evaluations", -1)) == CLASSICAL_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_candidate_scores", -1)) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_fitness_trainings", -1)) == FITNESS_TRAININGS_PER_ARM_SEED
                and len(receipts) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
            )
            fingerprints = [str(receipt.get("fingerprint", "")) for receipt in receipts]
            receipt_integrity &= (
                len(set(fingerprints)) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
                and all(
                    str(receipt.get("payload_sha256", ""))
                    and int(receipt.get("training_count", -1)) == ORACLE_TRAININGS_PER_SCORE
                    and str(receipt.get("role", "")) in {"selection", "padding"}
                    for receipt in receipts
                )
            )

            validation = validations[(int(seed), arm)]
            score = validation.get("score", {})
            terminal_fp = str(run.get("terminal_fingerprint", ""))
            terminal_validation_identity &= (
                str(validation.get("terminal_fingerprint", "")) == terminal_fp
                and str(score.get("fingerprint", "")) == terminal_fp
                and str(score.get("purpose", "")) == "validation"
                and int(score.get("training_count", -1)) == ORACLE_TRAININGS_PER_SCORE
                and bool(score.get("scientific_payload_sha256", ""))
            )
            held_out_scores[arm].append(float(score.get("neural_advantage", float("nan"))))

    provenance_prerequisites = bool(
        validation_seed_gate()
        and exact_budgets
        and receipt_integrity
        and terminal_validation_identity
        and same_initial_population
        and all(math.isfinite(value) for values in held_out_scores.values() for value in values)
    )

    summary = summarize_support(
        control=held_out_scores["control"],
        oracle=held_out_scores["oracle"],
        shuffled=held_out_scores["shuffled"],
        classical_non_degradation=classical_non_degradation,
    )
    verdict = phase2b_verdict(provenance_prerequisites, summary["checks"])
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2B",
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "prerequisites": {
            "validation_seed_gate": bool(validation_seed_gate()),
            "exact_budgets": bool(exact_budgets),
            "receipt_integrity": bool(receipt_integrity),
            "terminal_validation_identity": bool(terminal_validation_identity),
            "same_initial_population": bool(same_initial_population),
            "pass": provenance_prerequisites,
        },
        "classical_non_degradation": bool(classical_non_degradation),
        "held_out_block_v": held_out_scores,
        "support": {**summary, "verdict": verdict},
        "verdict": verdict,
    }
    payload["aggregate_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload
