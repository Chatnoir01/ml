"""Frozen Phase 2F terminal-freeze, held-out aggregation and support statistics."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Any

from .evolution import ClassicalMetrics, HardConstraints, is_admissible
from .phase2f import (
    ARCHITECTURE,
    ARMS,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
    SUPPORT_CHECKS,
    phase2f_verdict,
)
from .phase2f_terminal_freeze import freeze_terminals
from .phase2f_validation import validation_seed_gate
from .phase2f_validation_seeds import VALIDATION_DATASET_SEEDS, VALIDATION_MODEL_SEEDS


def exact_one_sided_sign_p(wins: int, losses: int) -> float:
    wins = int(wins)
    losses = int(losses)
    if wins < 0 or losses < 0:
        raise ValueError("sign-test counts must be non-negative")
    n = wins + losses
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(wins, n + 1)) / (2**n))


def _classical_metrics(payload: dict[str, Any]) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=int(payload["nonlinearity"]),
        differential_uniformity=int(payload["differential_uniformity"]),
        max_linear_correlation=int(payload["max_linear_correlation"]),
        sac_score=float(payload.get("sac_score", 0.5)),
        algebraic_degree=int(payload["algebraic_degree"]),
        fingerprint=str(payload.get("fingerprint", "")),
    )


def componentwise_classical_non_degradation(
    b1_payload: dict[str, Any], c_payload: dict[str, Any]
) -> bool:
    b1 = _classical_metrics(b1_payload)
    c = _classical_metrics(c_payload)
    constraints = HardConstraints()
    return bool(
        int(is_admissible(b1, constraints)) >= int(is_admissible(c, constraints))
        and b1.nonlinearity >= c.nonlinearity
        and b1.differential_uniformity <= c.differential_uniformity
        and b1.max_linear_correlation <= c.max_linear_correlation
        and b1.algebraic_degree >= c.algebraic_degree
    )


def mechanism_activity(run: dict[str, Any]) -> dict[str, Any]:
    events = [
        event
        for event in run.get("selection_events", [])
        if bool(event.get("membership_changed"))
        and bool(event.get("cross_protected_key_membership_change"))
        and bool(event.get("scored"))
    ]
    return {
        "cross_key_membership_changes": int(len(events)),
        "active": bool(events),
        "event_indices": [
            int(index)
            for index, event in enumerate(run.get("selection_events", []))
            if bool(event.get("membership_changed"))
            and bool(event.get("cross_protected_key_membership_change"))
            and bool(event.get("scored"))
        ],
    }


def summarize_support(
    *,
    o0: Sequence[float],
    b1: Sequence[float],
    sb1: Sequence[float],
    mechanism_active: Sequence[bool],
    classical_non_degradation: bool,
) -> dict[str, Any]:
    if not (
        len(o0) == len(b1) == len(sb1) == len(mechanism_active) == len(EVOLUTION_SEEDS)
    ):
        raise ValueError("Phase 2F support summary requires exactly nine paired seeds")
    o0v = [float(value) for value in o0]
    b1v = [float(value) for value in b1]
    sb1v = [float(value) for value in sb1]
    if not all(math.isfinite(value) for value in [*o0v, *b1v, *sb1v]):
        raise ValueError("Phase 2F support values must be finite")

    mechanism_wins = sum(bool(value) for value in mechanism_active)
    reductions = [left - right for left, right in zip(o0v, b1v)]
    wins = sum(delta > 0.0 for delta in reductions)
    losses = sum(delta < 0.0 for delta in reductions)
    ties = len(reductions) - wins - losses
    sign_p = exact_one_sided_sign_p(wins, losses)
    mean_reduction = float(statistics.fmean(reductions))
    specificity = [left - right for left, right in zip(sb1v, b1v)]
    specificity_wins = sum(delta > 0.0 for delta in specificity)

    checks = {
        "mechanism_activity_6_of_9": bool(mechanism_wins >= 6),
        "b1_wins_o0_8_of_9": bool(wins >= 8),
        "paired_sign_p_lt_005": bool(sign_p < 0.05),
        "mean_reduction_ge_002": bool(mean_reduction >= 0.02),
        "classical_non_degradation": bool(classical_non_degradation),
        "b1_wins_sb1_6_of_9": bool(specificity_wins >= 6),
        "b1_mean_lt_sb1_mean": bool(statistics.fmean(b1v) < statistics.fmean(sb1v)),
    }
    return {
        "checks": checks,
        "mechanism_activity": {
            "active_seeds": int(mechanism_wins),
            "per_seed": [bool(value) for value in mechanism_active],
        },
        "paired_b1_vs_o0": {
            "wins": int(wins),
            "losses": int(losses),
            "ties": int(ties),
            "exact_one_sided_sign_p": float(sign_p),
            "mean_reduction_o0_minus_b1": mean_reduction,
            "per_seed_reductions": reductions,
        },
        "specificity_b1_vs_sb1": {
            "wins": int(specificity_wins),
            "per_seed_sb1_minus_b1": specificity,
            "mean_b1": float(statistics.fmean(b1v)),
            "mean_sb1": float(statistics.fmean(sb1v)),
        },
        "verdict": phase2f_verdict(True, checks),
    }


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
        if not _sha_matches(payload, "scientific_payload_sha256"):
            return False
        ds = tuple(int(value) for value in dataset_seeds)
        ms = tuple(int(value) for value in model_seeds)
        runs = list(payload.get("runs", []))
        if len(ds) != 8 or len(ms) != 8 or len(runs) != ORACLE_TRAININGS_PER_SCORE:
            return False
        expected = {(int(diff), replicate) for diff in DIFFERENCES for replicate in range(8)}
        seen: set[tuple[int, int]] = set()
        neural: list[float] = []
        null: list[float] = []
        for run in runs:
            key = (int(run.get("difference", -1)), int(run.get("replicate", -1)))
            if key not in expected or key in seen:
                return False
            seen.add(key)
            replicate = key[1]
            if int(run.get("dataset_seed", -1)) != ds[replicate]:
                return False
            if int(run.get("model_seed", -1)) != ms[replicate]:
                return False
            sizes = (
                int(run.get("train_size", -1)),
                int(run.get("validation_size", -1)),
                int(run.get("test_size", -1)),
            )
            if sizes != SPLIT_SIZES:
                return False
            advantage = float(run.get("neural_advantage", float("nan")))
            null_advantage = float(run.get("null_advantage", float("nan")))
            if not math.isfinite(advantage) or not math.isfinite(null_advantage):
                return False
            neural.append(advantage)
            null.append(null_advantage)
        if seen != expected:
            return False
        return bool(
            math.isclose(float(payload.get("neural_advantage")), sum(neural) / len(neural), rel_tol=0.0, abs_tol=1e-15)
            and math.isclose(float(payload.get("null_advantage")), sum(null) / len(null), rel_tol=0.0, abs_tol=1e-15)
        )
    except (TypeError, ValueError, KeyError, IndexError):
        return False


def _expected_cells() -> set[tuple[int, str]]:
    return {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _index_records(records: Sequence[dict[str, Any]], *, phase: str) -> dict[tuple[int, str], dict[str, Any]]:
    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for item in records:
        if str(item.get("phase", "")) != phase:
            raise ValueError(f"Phase 2F expected {phase!r} record")
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in indexed:
            raise ValueError(f"invalid or duplicate Phase 2F record {key!r}")
        indexed[key] = item
    if set(indexed) != expected:
        raise ValueError("Phase 2F requires exact 9-seed × 4-arm records")
    return indexed


def aggregate_phase2f(
    arm_results: Sequence[dict[str, Any]],
    validation_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    arms = _index_records(arm_results, phase="2F")
    validations = _index_records(validation_results, phase="2F-validation")
    terminal_freeze = freeze_terminals(arm_results)
    terminal_freeze_sha256 = str(terminal_freeze["terminal_freeze_sha256"])

    heldout: dict[str, list[float]] = {arm: [] for arm in ARMS}
    validation_integrity = True
    validation_freeze_identity = True
    terminal_validation_identity = True
    classical_non_degradation = True
    mechanism_by_seed: list[bool] = []
    mechanism_details: list[dict[str, Any]] = []

    for seed in EVOLUTION_SEEDS:
        c = arms[(int(seed), "C")]
        b1 = arms[(int(seed), "B1")]
        classical_non_degradation &= componentwise_classical_non_degradation(
            dict(b1["terminal_classical"]), dict(c["terminal_classical"])
        )
        activity = mechanism_activity(b1)
        mechanism_by_seed.append(bool(activity["active"]))
        mechanism_details.append({"seed": int(seed), **activity})

        for arm in ARMS:
            run = arms[(int(seed), arm)]
            validation = validations[(int(seed), arm)]
            validation_freeze_identity &= bool(
                str(validation.get("terminal_freeze_sha256", "")) == terminal_freeze_sha256
            )
            score = validation.get("score", {})
            ok = isinstance(score, dict) and score_payload_integrity(
                score,
                purpose="validation",
                dataset_seeds=VALIDATION_DATASET_SEEDS,
                model_seeds=VALIDATION_MODEL_SEEDS,
            )
            validation_integrity &= bool(ok)
            terminal_fp = str(run.get("terminal_fingerprint", ""))
            terminal_validation_identity &= bool(
                str(validation.get("terminal_fingerprint", "")) == terminal_fp
                and str(score.get("fingerprint", "")) == terminal_fp
            )
            try:
                advantage = float(score.get("neural_advantage", float("nan")))
            except (TypeError, ValueError):
                advantage = float("nan")
            heldout[arm].append(advantage)

    finite = all(math.isfinite(value) for values in heldout.values() for value in values)
    prerequisites = {
        "terminal_freeze": bool(terminal_freeze["prerequisites"]["pass"]),
        "validation_seed_gate": bool(validation_seed_gate()),
        "validation_receipt_integrity": bool(validation_integrity),
        "validation_terminal_freeze_identity": bool(validation_freeze_identity),
        "terminal_validation_identity": bool(terminal_validation_identity),
        "heldout_scores_finite": bool(finite),
    }
    prerequisites["pass"] = all(prerequisites.values())

    if prerequisites["pass"]:
        support = summarize_support(
            o0=heldout["O0"],
            b1=heldout["B1"],
            sb1=heldout["SB1"],
            mechanism_active=mechanism_by_seed,
            classical_non_degradation=classical_non_degradation,
        )
    else:
        support = {
            "checks": {name: False for name in SUPPORT_CHECKS},
            "mechanism_activity": {
                "active_seeds": int(sum(mechanism_by_seed)),
                "per_seed": mechanism_by_seed,
                "not_interpreted": True,
            },
            "paired_b1_vs_o0": {"not_interpreted": True},
            "specificity_b1_vs_sb1": {"not_interpreted": True},
            "verdict": "phase2f_inconclusive_prerequisites",
        }

    verdict = phase2f_verdict(bool(prerequisites["pass"]), support["checks"])
    heldout_payload = {
        arm: [value if math.isfinite(value) else None for value in values]
        for arm, values in heldout.items()
    }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2F",
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "terminal_freeze_sha256": terminal_freeze_sha256,
        "prerequisites": prerequisites,
        "mechanism_activity": mechanism_details,
        "classical_non_degradation": bool(classical_non_degradation),
        "heldout": heldout_payload,
        "support": {**support, "verdict": verdict},
        "verdict": verdict,
    }
    payload["aggregate_payload_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload
