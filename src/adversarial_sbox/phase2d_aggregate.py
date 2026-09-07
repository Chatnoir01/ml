"""Frozen Phase 2D terminal-freeze, held-out aggregation and support statistics."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Any

from .evolution import ClassicalMetrics, HardConstraints, primary_security_key
from .phase2_evolution_seed_registry import phase2d_evolution_seeds_are_fresh
from .phase2d import (
    ARCHITECTURE,
    ARMS,
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
    SUPPORT_CHECKS,
    VALIDATION_DATASET_SEEDS,
    VALIDATION_MODEL_SEEDS,
    phase2d_verdict,
)
from .phase2d_validation import validation_seed_gate


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


def protected_classical_key(payload: dict[str, Any]) -> tuple[float, ...]:
    return primary_security_key(_classical_metrics(payload), HardConstraints())


def transmission_plus2_rate(run: dict[str, Any]) -> dict[str, Any]:
    """Unique-fingerprint +2 descendant rate frozen in issue #109 clarification."""

    states: dict[str, bool | None] = {}
    for event in run.get("lineage_diagnostics", []):
        for item in event.get("entered", []):
            fingerprint = str(item.get("fingerprint", ""))
            if not fingerprint:
                continue
            value = item.get("descendant_plus_2")
            normalized = None if value is None else bool(value)
            prior = states.get(fingerprint)
            if prior is True or normalized is True:
                states[fingerprint] = True
            elif prior is False or normalized is False:
                states[fingerprint] = False
            else:
                states[fingerprint] = None
    defined = [value for value in states.values() if value is not None]
    persistent = sum(value is True for value in defined)
    return {
        "defined_unique": int(len(defined)),
        "persistent_unique": int(persistent),
        "rate": float(persistent / len(defined)) if defined else 0.0,
    }


def summarize_support(
    *,
    o0: Sequence[float],
    op1: Sequence[float],
    sp1: Sequence[float],
    transmission_o0: Sequence[float],
    transmission_op1: Sequence[float],
    classical_non_degradation: bool,
) -> dict[str, Any]:
    if not (
        len(o0)
        == len(op1)
        == len(sp1)
        == len(transmission_o0)
        == len(transmission_op1)
        == len(EVOLUTION_SEEDS)
    ):
        raise ValueError("Phase 2D support summary requires exactly nine paired seeds")
    o0v = [float(value) for value in o0]
    op1v = [float(value) for value in op1]
    sp1v = [float(value) for value in sp1]
    t0 = [float(value) for value in transmission_o0]
    t1 = [float(value) for value in transmission_op1]
    if not all(math.isfinite(value) for value in [*o0v, *op1v, *sp1v, *t0, *t1]):
        raise ValueError("Phase 2D support values must be finite")

    transmission_wins = sum(left > right for left, right in zip(t1, t0))
    diff_o0_op1 = [left - right for left, right in zip(o0v, op1v)]
    wins = sum(delta > 0.0 for delta in diff_o0_op1)
    losses = sum(delta < 0.0 for delta in diff_o0_op1)
    ties = len(diff_o0_op1) - wins - losses
    sign_p = exact_one_sided_sign_p(wins, losses)
    mean_reduction = float(statistics.fmean(diff_o0_op1))
    specificity = [left - right for left, right in zip(sp1v, op1v)]
    specificity_wins = sum(delta > 0.0 for delta in specificity)
    checks = {
        "mechanism_transmission_6_of_9": bool(transmission_wins >= 6),
        "op1_wins_o0_8_of_9": bool(wins >= 8),
        "paired_sign_p_lt_005": bool(sign_p < 0.05),
        "mean_reduction_ge_002": bool(mean_reduction >= 0.02),
        "classical_non_degradation": bool(classical_non_degradation),
        "op1_wins_sp1_6_of_9": bool(specificity_wins >= 6),
        "op1_mean_lt_sp1_mean": bool(statistics.fmean(op1v) < statistics.fmean(sp1v)),
    }
    return {
        "checks": checks,
        "mechanism_transmission": {
            "wins_op1_gt_o0": int(transmission_wins),
            "o0_rates": t0,
            "op1_rates": t1,
        },
        "paired_op1_vs_o0": {
            "wins": int(wins),
            "losses": int(losses),
            "ties": int(ties),
            "exact_one_sided_sign_p": float(sign_p),
            "mean_reduction_o0_minus_op1": mean_reduction,
            "per_seed_reductions": diff_o0_op1,
        },
        "specificity_op1_vs_sp1": {
            "wins": int(specificity_wins),
            "per_seed_sp1_minus_op1": specificity,
            "mean_op1": float(statistics.fmean(op1v)),
            "mean_sp1": float(statistics.fmean(sp1v)),
        },
        "verdict": phase2d_verdict(True, checks),
    }


def _inconclusive_support(
    *,
    transmission_o0: Sequence[float],
    transmission_op1: Sequence[float],
) -> dict[str, Any]:
    """Return a deterministic non-interpretive support receipt for failed prerequisites."""

    t0 = [float(value) for value in transmission_o0]
    t1 = [float(value) for value in transmission_op1]
    transmission_wins = sum(left > right for left, right in zip(t1, t0))
    return {
        "checks": {name: False for name in SUPPORT_CHECKS},
        "mechanism_transmission": {
            "wins_op1_gt_o0": int(transmission_wins),
            "o0_rates": t0,
            "op1_rates": t1,
            "not_interpreted": True,
        },
        "paired_op1_vs_o0": {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "exact_one_sided_sign_p": 1.0,
            "mean_reduction_o0_minus_op1": None,
            "per_seed_reductions": [],
            "not_interpreted": True,
        },
        "specificity_op1_vs_sp1": {
            "wins": 0,
            "per_seed_sp1_minus_op1": [],
            "mean_op1": None,
            "mean_sp1": None,
            "not_interpreted": True,
        },
        "verdict": "phase2d_inconclusive_prerequisites",
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
        if len(ds) != 8 or len(ms) != 8:
            return False
        runs = list(payload.get("runs", []))
        if len(runs) != ORACLE_TRAININGS_PER_SCORE:
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
            a = float(run.get("neural_advantage", float("nan")))
            n = float(run.get("null_advantage", float("nan")))
            if not math.isfinite(a) or not math.isfinite(n):
                return False
            neural.append(a)
            null.append(n)
        if seen != expected:
            return False
        return bool(
            math.isclose(
                float(payload.get("neural_advantage")),
                sum(neural) / len(neural),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            and math.isclose(
                float(payload.get("null_advantage")),
                sum(null) / len(null),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
        )
    except (TypeError, ValueError, KeyError, IndexError):
        return False


def validation_matches_terminal_freeze(
    validation: dict[str, Any],
    terminal_freeze_sha256: str,
) -> bool:
    """Bind every held-out receipt to the exact pre-validation terminal freeze."""

    expected = str(terminal_freeze_sha256)
    return bool(
        len(expected) == 64
        and str(validation.get("phase", "")) == "2D-validation"
        and str(validation.get("terminal_freeze_sha256", "")) == expected
    )


def _expected_cells() -> set[tuple[int, str]]:
    return {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _index_arm_results(
    arm_results: Sequence[dict[str, Any]],
) -> dict[tuple[int, str], dict[str, Any]]:
    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for item in arm_results:
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in indexed:
            raise ValueError(f"invalid or duplicate Phase 2D arm record {key!r}")
        indexed[key] = item
    if set(indexed) != expected:
        raise ValueError("Phase 2D requires exact 9-seed × 4-arm records")
    return indexed


def freeze_terminals(arm_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    arms = _index_arm_results(arm_results)
    exact_budgets = True
    receipt_integrity = True
    same_initial_population = True
    terminals: list[dict[str, Any]] = []
    for seed in EVOLUTION_SEEDS:
        per_seed = [arms[(int(seed), arm)] for arm in ARMS]
        digests = {
            str(item.get("initial_population_digest_sha256", "")) for item in per_seed
        }
        same_initial_population &= len(digests) == 1 and "" not in digests
        for arm in ARMS:
            run = arms[(int(seed), arm)]
            receipts = list(run.get("oracle_receipts", []))
            exact_budgets &= bool(
                str(run.get("phase")) == "2D"
                and int(run.get("classical_evaluations", -1))
                == CLASSICAL_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_candidate_scores", -1))
                == ORACLE_SCORE_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_fitness_trainings", -1))
                == FITNESS_TRAININGS_PER_ARM_SEED
                and len(receipts) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
            )
            receipt_integrity &= _sha_matches(run, "scientific_payload_sha256")
            seen_fp: set[str] = set()
            for receipt in receipts:
                fp = str(receipt.get("fingerprint", ""))
                score = receipt.get("score_payload", {})
                ok = isinstance(score, dict) and score_payload_integrity(
                    score,
                    purpose="fitness",
                    dataset_seeds=FITNESS_DATASET_SEEDS,
                    model_seeds=FITNESS_MODEL_SEEDS,
                )
                ok &= fp != "" and fp not in seen_fp
                seen_fp.add(fp)
                ok &= str(score.get("fingerprint", "")) == fp
                ok &= str(receipt.get("payload_sha256", "")) == str(
                    score.get("scientific_payload_sha256", "")
                )
                ok &= int(receipt.get("training_count", -1)) == ORACLE_TRAININGS_PER_SCORE
                ok &= str(receipt.get("role", "")) in {"selection", "padding"}
                receipt_integrity &= bool(ok)
            terminals.append(
                {
                    "seed": int(seed),
                    "arm": arm,
                    "terminal_fingerprint": str(run.get("terminal_fingerprint", "")),
                    "terminal_sbox": list(run.get("terminal_sbox", [])),
                    "terminal_classical": dict(run.get("terminal_classical", {})),
                    "arm_payload_sha256": str(run.get("scientific_payload_sha256", "")),
                }
            )
    prerequisites = {
        "fresh_evolution_seeds": bool(phase2d_evolution_seeds_are_fresh(EVOLUTION_SEEDS)),
        "exact_budgets": bool(exact_budgets),
        "receipt_integrity": bool(receipt_integrity),
        "same_initial_population": bool(same_initial_population),
    }
    prerequisites["pass"] = all(prerequisites.values())
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2D-terminal-freeze",
        "cell_count": 36,
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "prerequisites": prerequisites,
        "terminals": sorted(terminals, key=lambda item: (item["seed"], item["arm"])),
    }
    payload["terminal_freeze_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def aggregate_phase2d(
    arm_results: Sequence[dict[str, Any]],
    validation_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    arms = _index_arm_results(arm_results)
    terminal_freeze = freeze_terminals(arm_results)
    terminal_freeze_sha256 = str(terminal_freeze["terminal_freeze_sha256"])
    expected = _expected_cells()
    validations: dict[tuple[int, str], dict[str, Any]] = {}
    for item in validation_results:
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in validations:
            raise ValueError(f"invalid or duplicate Phase 2D validation record {key!r}")
        validations[key] = item
    if set(validations) != expected:
        raise ValueError("Phase 2D aggregate requires exact 36 held-out validation records")

    validation_integrity = True
    terminal_validation_identity = True
    validation_terminal_freeze_identity = True
    heldout: dict[str, list[float]] = {arm: [] for arm in ARMS}
    transmission_o0: list[float] = []
    transmission_op1: list[float] = []
    classical_non_degradation = True

    for seed in EVOLUTION_SEEDS:
        c = arms[(int(seed), "C")]
        o0 = arms[(int(seed), "O0")]
        op1 = arms[(int(seed), "OP1")]
        op1_key = protected_classical_key(dict(op1["terminal_classical"]))
        classical_non_degradation &= bool(
            op1_key >= protected_classical_key(dict(c["terminal_classical"]))
            and op1_key >= protected_classical_key(dict(o0["terminal_classical"]))
        )
        transmission_o0.append(float(transmission_plus2_rate(o0)["rate"]))
        transmission_op1.append(float(transmission_plus2_rate(op1)["rate"]))
        for arm in ARMS:
            run = arms[(int(seed), arm)]
            validation = validations[(int(seed), arm)]
            validation_terminal_freeze_identity &= validation_matches_terminal_freeze(
                validation,
                terminal_freeze_sha256,
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
        "validation_terminal_freeze_identity": bool(validation_terminal_freeze_identity),
        "terminal_validation_identity": bool(terminal_validation_identity),
        "heldout_scores_finite": bool(finite),
    }
    prerequisites["pass"] = all(prerequisites.values())

    if prerequisites["pass"]:
        support = summarize_support(
            o0=heldout["O0"],
            op1=heldout["OP1"],
            sp1=heldout["SP1"],
            transmission_o0=transmission_o0,
            transmission_op1=transmission_op1,
            classical_non_degradation=classical_non_degradation,
        )
    else:
        support = _inconclusive_support(
            transmission_o0=transmission_o0,
            transmission_op1=transmission_op1,
        )
    verdict = phase2d_verdict(bool(prerequisites["pass"]), support["checks"])
    heldout_payload = {
        arm: [value if math.isfinite(value) else None for value in values]
        for arm, values in heldout.items()
    }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2D",
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "terminal_freeze_sha256": terminal_freeze_sha256,
        "prerequisites": prerequisites,
        "classical_non_degradation": bool(classical_non_degradation),
        "heldout": heldout_payload,
        "support": {**support, "verdict": verdict},
        "verdict": verdict,
    }
    payload["aggregate_payload_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload
