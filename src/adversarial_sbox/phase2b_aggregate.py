"""Frozen Phase-2B held-out aggregation and support statistics."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Any

from .phase2b import (
    ARCHITECTURE,
    CLASSICAL_BUDGET_PER_ARM_SEED,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
    VALIDATION_DATASET_SEEDS,
    VALIDATION_MODEL_SEEDS,
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


def _sha_matches(payload: dict[str, Any], field: str) -> bool:
    stored = str(payload.get(field, ""))
    if len(stored) != 64:
        return False
    clean = {key: value for key, value in payload.items() if key != field}
    blob = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest() == stored


def score_payload_integrity(
    payload: dict[str, Any],
    *,
    purpose: str,
    dataset_seeds: Sequence[int],
    model_seeds: Sequence[int],
) -> bool:
    """Verify one complete 16-training Oracle score ledger and its receipt."""

    try:
        if str(payload.get("purpose", "")) != purpose:
            return False
        if str(payload.get("architecture", "")) != ARCHITECTURE:
            return False
        if int(payload.get("depth", -1)) != DEPTH:
            return False
        if tuple(int(value) for value in payload.get("differences", ())) != DIFFERENCES:
            return False
        if int(payload.get("pair_count", -1)) != PAIR_COUNT:
            return False
        if tuple(int(value) for value in payload.get("split_sizes", ())) != SPLIT_SIZES:
            return False
        if int(payload.get("training_count", -1)) != ORACLE_TRAININGS_PER_SCORE:
            return False
        if not str(payload.get("fingerprint", "")):
            return False
        if not _sha_matches(payload, "scientific_payload_sha256"):
            return False

        frozen_dataset = tuple(int(value) for value in dataset_seeds)
        frozen_model = tuple(int(value) for value in model_seeds)
        if len(frozen_dataset) != 8 or len(frozen_model) != 8:
            return False
        runs = list(payload.get("runs", []))
        if len(runs) != ORACLE_TRAININGS_PER_SCORE:
            return False

        expected_keys = {
            (int(difference), replicate)
            for difference in DIFFERENCES
            for replicate in range(8)
        }
        seen: set[tuple[int, int]] = set()
        neural_values: list[float] = []
        null_values: list[float] = []
        for run in runs:
            difference = int(run.get("difference", -1))
            replicate = int(run.get("replicate", -1))
            key = (difference, replicate)
            if key not in expected_keys or key in seen:
                return False
            seen.add(key)
            if int(run.get("dataset_seed", -1)) != frozen_dataset[replicate]:
                return False
            if int(run.get("model_seed", -1)) != frozen_model[replicate]:
                return False
            sizes = (
                int(run.get("train_size", -1)),
                int(run.get("validation_size", -1)),
                int(run.get("test_size", -1)),
            )
            if sizes != SPLIT_SIZES:
                return False
            neural = float(run.get("neural_advantage", float("nan")))
            null = float(run.get("null_advantage", float("nan")))
            if not math.isfinite(neural) or not math.isfinite(null):
                return False
            neural_values.append(neural)
            null_values.append(null)

        if seen != expected_keys:
            return False
        expected_neural = float(sum(neural_values) / len(neural_values))
        expected_null = float(sum(null_values) / len(null_values))
        if not math.isclose(
            float(payload.get("neural_advantage", float("nan"))),
            expected_neural,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            return False
        if not math.isclose(
            float(payload.get("null_advantage", float("nan"))),
            expected_null,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            return False
        return True
    except (TypeError, ValueError, KeyError, IndexError):
        return False


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
            receipt_integrity &= _sha_matches(run, "scientific_payload_sha256")
            receipt_integrity &= len(set(fingerprints)) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
            for receipt in receipts:
                score_payload = receipt.get("score_payload", {})
                score_ok = isinstance(score_payload, dict) and score_payload_integrity(
                    score_payload,
                    purpose="fitness",
                    dataset_seeds=FITNESS_DATASET_SEEDS,
                    model_seeds=FITNESS_MODEL_SEEDS,
                )
                if score_ok:
                    score_ok &= str(receipt.get("fingerprint", "")) == str(
                        score_payload.get("fingerprint", "")
                    )
                    score_ok &= str(receipt.get("payload_sha256", "")) == str(
                        score_payload.get("scientific_payload_sha256", "")
                    )
                    score_ok &= int(receipt.get("training_count", -1)) == ORACLE_TRAININGS_PER_SCORE
                    score_ok &= str(receipt.get("role", "")) in {"selection", "padding"}
                    score_ok &= math.isclose(
                        float(receipt.get("neural_advantage", float("nan"))),
                        float(score_payload.get("neural_advantage", float("nan"))),
                        rel_tol=0.0,
                        abs_tol=0.0,
                    )
                receipt_integrity &= bool(score_ok)

            validation = validations[(int(seed), arm)]
            score = validation.get("score", {})
            terminal_fp = str(run.get("terminal_fingerprint", ""))
            validation_score_integrity = isinstance(score, dict) and score_payload_integrity(
                score,
                purpose="validation",
                dataset_seeds=VALIDATION_DATASET_SEEDS,
                model_seeds=VALIDATION_MODEL_SEEDS,
            )
            receipt_integrity &= bool(validation_score_integrity)
            terminal_validation_identity &= (
                str(validation.get("terminal_fingerprint", "")) == terminal_fp
                and str(score.get("fingerprint", "")) == terminal_fp
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
