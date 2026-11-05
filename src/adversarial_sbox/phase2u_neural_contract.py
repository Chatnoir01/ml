"""Read-only Phase 2U outcome receipt contract and preregistered statistics.

No new neural training, no access to sealed Phase 2U outcomes, no source
regeneration, no reranking, and no Phase 2R scientific execution authorization.
Statistical calculations on supplied receipt rows do NOT authenticate those rows.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Mapping
from typing import Any

from .phase2u_predict import verify_prediction_receipt
from .phase2t_evaluate import (
    spearman, one_sided_permutation_p, bootstrap_spearman_ci,
    PERMUTATIONS, PERMUTATION_SEED, BOOTSTRAP_REPS, BOOTSTRAP_SEED,
    SPEARMAN_MINIMUM, PERMUTATION_P_THRESHOLD,
    MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL,
)

# Frozen original Phase 2U pre-neural prediction. Never substitute a rerun.
PREDICTION_SHA256 = "cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4"
SOURCE_PANEL_CANONICAL_SHA256 = "512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef"
DIFFERENCES = (1, 256)
DATASET_SEEDS = (930101, 930113, 930127, 930139)
MODEL_SEEDS = (940101, 940113, 940127, 940139)
NULL_SHUFFLE_XOR_MASK = 0x6B6B6B6B
NULL_LABEL_STRATEGY = "test_label_shuffle_after_training_fixed_score_vector"
CANDIDATES = 12
NEURAL_ROWS = CANDIDATES * len(DIFFERENCES) * len(DATASET_SEEDS)

# Inherited from the publicly recorded but source-blocked Phase 2T-v1
# hypothesis, NOT a retroactive optimization based on Phase 2U neural scores.
_PREDECLARED_STATS = (19999, 950101, 2000, 950113, 0.60, 0.05, 0.02)
PROTOCOL = {
    "schema_version": 1,
    "experiment": "phase2u_neural_prospective_v1",
    "frozen_prediction_sha256": PREDICTION_SHA256,
    "source_panel_canonical_sha256": SOURCE_PANEL_CANONICAL_SHA256,
    "cipher": "32-bit four-round historical ToySPN fixed public keys",
    "neural_architecture": "byte_tanh_mlp",
    "candidate_count": CANDIDATES,
    "differences": list(DIFFERENCES),
    "dataset_seeds": list(DATASET_SEEDS),
    "model_seeds": list(MODEL_SEEDS),
    "neural_training_count": NEURAL_ROWS,
    "cross_run_runtime_lock_and_commit_identical": True,
    "same_seed_initial_weights_identical_across_candidates_and_differences": True,
    "within_cell_train_validation_test_hashes_distinct": True,
    "cross_candidate_same_regime_split_hashes_distinct": True,
    "null_label_strategy": NULL_LABEL_STRATEGY,
    "null_shuffle_seed_rule": "model_seed_xor_0x6B6B6B6B",
    "candidate_neural_score": "mean_over_8_of_2_times_abs(test_auc_minus_0.5)",
    "null_score": "mean_over_8_of_2_times_abs(shuffled_null_auc_minus_0.5)",
    "primary": "positive_spearman_correlation_across_12_independent_candidate_scores",
    "permutation_iterations": _PREDECLARED_STATS[0],
    "permutation_seed": _PREDECLARED_STATS[1],
    "bootstrap_iterations": _PREDECLARED_STATS[2],
    "bootstrap_seed": _PREDECLARED_STATS[3],
    "spearman_minimum": _PREDECLARED_STATS[4],
    "one_sided_p_below": _PREDECLARED_STATS[5],
    "mean_neural_minus_null_minimum": _PREDECLARED_STATS[6],
    "scientific_training_permitted_by_this_contract": False,
}
PROTOCOL_SHA256 = hashlib.sha256(
    json.dumps(PROTOCOL, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()


class Phase2UOutcomeRejected(ValueError):
    pass


def _hex64(value: Any, name: str) -> str:
    if (type(value) is not str or len(value) != 64 or
            any(ch not in "0123456789abcdef" for ch in value)):
        raise Phase2UOutcomeRejected(f"missing or invalid {name}")
    return value


def _auc(value: Any, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise Phase2UOutcomeRejected(f"invalid {name}")
    return float(value)


def validate_phase2u_neural_receipts(
    prediction: dict[str, Any], outcome: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate structure/provenance claims, not the authenticity of experiments."""
    if not isinstance(prediction, dict):
        raise Phase2UOutcomeRejected("prediction must be a JSON object")
    verify_prediction_receipt(prediction)
    if _hex64(prediction.get("prediction_receipt_sha256"), "frozen prediction") != PREDICTION_SHA256:
        raise Phase2UOutcomeRejected("not the originally frozen Phase 2U prediction")
    if (type(outcome) is not dict or outcome.get("schema_version") != 1
            or outcome.get("experiment") != PROTOCOL["experiment"]
            or outcome.get("protocol_sha256") != PROTOCOL_SHA256
            or outcome.get("prediction_receipt_sha256") != PREDICTION_SHA256
            or outcome.get("source_panel_canonical_sha256") != SOURCE_PANEL_CANONICAL_SHA256):
        raise Phase2UOutcomeRejected("outcome is not bound to exact Phase 2U protocol and original sources")
    if (PERMUTATIONS, PERMUTATION_SEED, BOOTSTRAP_REPS, BOOTSTRAP_SEED,
        SPEARMAN_MINIMUM, PERMUTATION_P_THRESHOLD,
        MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL) != _PREDECLARED_STATS:
        raise Phase2UOutcomeRejected("inherited frozen statistical implementation changed")
    if not isinstance(prediction.get("predictions"), list) or len(prediction["predictions"]) != CANDIDATES:
        raise Phase2UOutcomeRejected("missing exact 12 frozen candidate rows")
    candidates = {r["fingerprint"]: r["classical_feature_score"] for r in prediction["predictions"]}
    if len(candidates) != CANDIDATES:
        raise Phase2UOutcomeRejected("duplicate frozen candidate identity")
    runs = outcome.get("runs")
    if not isinstance(runs, list) or len(runs) != NEURAL_ROWS:
        raise Phase2UOutcomeRejected("exactly 96 neural rows are required")
    collected: dict[str, list[tuple[float, float]]] = {f: [] for f in candidates}
    seen: set[tuple[str, int, int]] = set()
    expected_environment: tuple[str, str, str] | None = None
    expected_initialization_by_replicate: dict[int, str] = {}
    dataset_used: dict[tuple[int, int, str], set[str]] = {}
    for row in runs:
        if type(row) is not dict:
            raise Phase2UOutcomeRejected("invalid neural row")
        fingerprint = row.get("fingerprint")
        difference, replicate = row.get("difference"), row.get("replicate")
        if (fingerprint not in candidates or type(difference) is not int
                or difference not in DIFFERENCES or type(replicate) is not int
                or replicate not in range(len(DATASET_SEEDS))):
            raise Phase2UOutcomeRejected("unregistered candidate, difference or replicate")
        key = (fingerprint, difference, replicate)
        if key in seen:
            raise Phase2UOutcomeRejected("duplicate candidate/difference/replicate")
        seen.add(key)
        if (type(row.get("dataset_seed")) is not int or
                row["dataset_seed"] != DATASET_SEEDS[replicate] or
                type(row.get("model_seed")) is not int or
                row["model_seed"] != MODEL_SEEDS[replicate]):
            raise Phase2UOutcomeRejected("unregistered dataset/model seed")
        dataset = row.get("dataset_sha256")
        if not isinstance(dataset, dict) or set(dataset) != {"train", "validation", "test"}:
            raise Phase2UOutcomeRejected("missing three dataset split hashes")
        for label in ("train", "validation", "test"):
            _hex64(dataset[label], f"{label} dataset SHA-256")
        if len(set(dataset.values())) != 3:
            raise Phase2UOutcomeRejected("train, validation and test dataset hashes must be distinct")
        for label in ("train", "validation", "test"):
            group = dataset_used.setdefault((difference, replicate, label), set())
            if dataset[label] in group:
                raise Phase2UOutcomeRejected("different candidates reused identical dataset split bytes")
            group.add(dataset[label])
        for label in ("initialization_sha256", "final_state_sha256",
                      "rng_state_sha256", "runtime_manifest_sha256",
                      "dependency_lock_sha256"):
            _hex64(row.get(label), label)
        source_commit = row.get("runner_commit_sha")
        if (type(source_commit) is not str or len(source_commit) != 40 or
                any(c not in "0123456789abcdef" for c in source_commit)):
            raise Phase2UOutcomeRejected("missing source commit SHA")
        environment = (row["runtime_manifest_sha256"],
                       row["dependency_lock_sha256"], source_commit)
        if expected_environment is None:
            expected_environment = environment
        elif environment != expected_environment:
            raise Phase2UOutcomeRejected("mixed runtime, dependency lock or runner commit")
        initial = row["initialization_sha256"]
        first_initial = expected_initialization_by_replicate.setdefault(replicate, initial)
        if initial != first_initial:
            raise Phase2UOutcomeRejected("same model seed produced different initial tensors")
        if (row.get("null_label_strategy") != NULL_LABEL_STRATEGY or
                type(row.get("null_shuffle_seed")) is not int or
                row["null_shuffle_seed"] != (MODEL_SEEDS[replicate] ^ NULL_SHUFFLE_XOR_MASK)):
            raise Phase2UOutcomeRejected("null-label evaluation strategy or shuffle seed changed")
        measured = _auc(row.get("test_auc"), "test AUC")
        shuffled = _auc(row.get("null_auc"), "null AUC")
        collected[fingerprint].append((measured, shuffled))
    if len(seen) != NEURAL_ROWS or any(len(v) != 8 for v in collected.values()):
        raise Phase2UOutcomeRejected("incomplete matched 96-row outcome grid")
    return [{
        "fingerprint": fp,
        "classical_score": score,
        "neural_advantage": statistics.fmean(2 * abs(a - 0.5) for a, _ in collected[fp]),
        "null_advantage": statistics.fmean(2 * abs(n - 0.5) for _, n in collected[fp]),
        "replicate_count": len(collected[fp]),
    } for fp, score in sorted(candidates.items())]


def analyze_supplied_phase2u_receipts(prediction: dict[str, Any],
                                     outcome: dict[str, Any]) -> dict[str, Any]:
    """Read-only arithmetic; no claim that any supplied outcome is real."""
    rows = validate_phase2u_neural_receipts(prediction, outcome)
    x = [r["classical_score"] for r in rows]
    y = [r["neural_advantage"] for r in rows]
    rho = spearman(x, y)
    p = None if rho is None else one_sided_permutation_p(x, y, rho)
    margin = statistics.fmean(r["neural_advantage"]-r["null_advantage"] for r in rows)
    criteria = (
        rho is not None and rho >= SPEARMAN_MINIMUM
        and p is not None and p < PERMUTATION_P_THRESHOLD
        and margin >= MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL
    )
    return {
        "schema_version": 1,
        "experiment": "phase2u_provisional_read_only_analysis",
        "protocol_sha256": PROTOCOL_SHA256,
        "frozen_prediction_sha256": PREDICTION_SHA256,
        "candidate_count": len(rows),
        "supplied_outcome_row_count": NEURAL_ROWS,
        "spearman_rho": rho,
        "one_sided_permutation_p": p,
        "mean_neural_minus_null": margin,
        "bootstrap_ci_exploratory": bootstrap_spearman_ci(x, y),
        "mathematical_thresholds_met_on_supplied_data": bool(criteria),
        "scientific_validation_status": "UNAUTHENTICATED_SUPPLIED_RECEIPTS_NOT_SCIENTIFIC_VERDICT",
        "phase2r_provenance_gate_established": False,
        "authorizes_neural_training": False,
        "individual_candidate_rows": rows,
    }
