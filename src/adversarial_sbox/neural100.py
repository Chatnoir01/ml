"""Frozen 100-training neural residual diagnostic for the educational ToySPN.

This module is intentionally exploratory. It does not change Gate 1 and it does
not apply neural pressure to evolution. See research/NEURAL100_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Iterable, Sequence

from .datasets import PairSample, generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100_candidates import CANDIDATES, DATASET_SEEDS, MATCHED_METRICS, MODEL_SEEDS
from .spn import ToySPN

ROUND_KEYS = (
    0x243F6A88,
    0x85A308D3,
    0x13198A2E,
    0x03707344,
    0xA4093822,
    0x299F31D0,
)
ROUNDS = 5
INPUT_DIFFERENCE = 0x00000001
PAIR_COUNT = 8192
HIDDEN_UNITS = 64
EPOCHS = 24
BATCH_SIZE = 256
LEARNING_RATE = 0.002
WEIGHT_DECAY = 1e-4
ADAM_BETA1 = 0.9
ADAM_BETA2 = 0.999
ADAM_EPSILON = 1e-8
PERMUTATION_REPETITIONS = 5000
PERMUTATION_SEED = 910001


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised by workflow install gate
        raise RuntimeError(
            "Neural100 requires NumPy; install the package with the 'neural' extra"
        ) from exc
    return np


def _auc_from_scores(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Tie-aware ROC AUC using average ranks, implemented without dependencies."""

    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must be non-empty and have equal length")
    positives = sum(int(value) for value in labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("AUC requires both classes")

    order = sorted(range(len(scores)), key=lambda index: float(scores[index]))
    ranks = [0.0] * len(scores)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        value = float(scores[order[cursor]])
        while end < len(order) and float(scores[order[end]]) == value:
            end += 1
        # Ranks are one-based. Average the inclusive rank interval.
        average_rank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = average_rank
        cursor = end

    positive_rank_sum = sum(
        ranks[index] for index, label in enumerate(labels) if int(label) == 1
    )
    return float(
        (positive_rank_sum - positives * (positives + 1) / 2.0)
        / (positives * negatives)
    )


def _advantage(auc: float) -> float:
    return float(2.0 * abs(float(auc) - 0.5))


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    if not 0 <= candidate_index < len(CANDIDATES):
        raise ValueError(f"candidate index must be in [0, {len(CANDIDATES) - 1}]")
    candidate = CANDIDATES[candidate_index]
    sbox = tuple(int(value) for value in candidate["sbox"])
    metrics = evaluate_classical(sbox)
    expected = {
        "nonlinearity": int(MATCHED_METRICS["nonlinearity"]),
        "differential_uniformity": int(MATCHED_METRICS["differential_uniformity"]),
        "max_linear_correlation": int(MATCHED_METRICS["max_linear_correlation"]),
        "algebraic_degree": int(MATCHED_METRICS["algebraic_degree"]),
        "sac_score": float(MATCHED_METRICS["sac_score"]),
        "fingerprint": str(candidate["fingerprint"]),
    }
    actual = asdict(metrics)
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            raise RuntimeError(
                f"candidate {candidate_index} provenance mismatch for {key}: "
                f"expected {expected_value!r}, got {actual[key]!r}"
            )
    return sbox, actual


def _samples_to_arrays(samples: Sequence[PairSample]):
    np = _numpy()
    features = np.empty((len(samples), 96), dtype=np.float32)
    labels = np.empty(len(samples), dtype=np.float32)
    for row, sample in enumerate(samples):
        values = (int(sample.left), int(sample.right), int(sample.left) ^ int(sample.right))
        column = 0
        for value in values:
            for bit in range(31, -1, -1):
                features[row, column] = float((value >> bit) & 1)
                column += 1
        labels[row] = float(sample.label)
    return features, labels


def _sigmoid(logits):
    np = _numpy()
    clipped = np.clip(logits, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _train_one(
    *,
    train_samples: Sequence[PairSample],
    validation_samples: Sequence[PairSample],
    test_samples: Sequence[PairSample],
    model_seed: int,
) -> dict[str, float]:
    np = _numpy()
    x_train, y_train = _samples_to_arrays(train_samples)
    x_validation, y_validation = _samples_to_arrays(validation_samples)
    x_test, y_test = _samples_to_arrays(test_samples)

    rng = np.random.default_rng(int(model_seed))
    # He-style initialization is frozen by the experimental SHA.
    w1 = rng.normal(0.0, math.sqrt(2.0 / 96.0), size=(96, HIDDEN_UNITS)).astype(np.float32)
    b1 = np.zeros(HIDDEN_UNITS, dtype=np.float32)
    w2 = rng.normal(0.0, math.sqrt(2.0 / HIDDEN_UNITS), size=(HIDDEN_UNITS,)).astype(np.float32)
    b2 = np.float32(0.0)

    mw1 = np.zeros_like(w1)
    vw1 = np.zeros_like(w1)
    mb1 = np.zeros_like(b1)
    vb1 = np.zeros_like(b1)
    mw2 = np.zeros_like(w2)
    vw2 = np.zeros_like(w2)
    mb2 = np.float32(0.0)
    vb2 = np.float32(0.0)
    step = 0

    for _epoch in range(EPOCHS):
        order = rng.permutation(len(x_train))
        for start in range(0, len(order), BATCH_SIZE):
            batch_index = order[start : start + BATCH_SIZE]
            xb = x_train[batch_index]
            yb = y_train[batch_index]

            hidden_pre = xb @ w1 + b1
            hidden = np.maximum(hidden_pre, 0.0)
            logits = hidden @ w2 + b2
            probabilities = _sigmoid(logits)

            batch_size = float(len(batch_index))
            dlogits = (probabilities - yb) / batch_size
            grad_w2 = hidden.T @ dlogits + WEIGHT_DECAY * w2
            grad_b2 = np.sum(dlogits, dtype=np.float32)
            dhidden = dlogits[:, None] * w2[None, :]
            dhidden[hidden_pre <= 0.0] = 0.0
            grad_w1 = xb.T @ dhidden + WEIGHT_DECAY * w1
            grad_b1 = np.sum(dhidden, axis=0, dtype=np.float32)

            step += 1
            correction1 = 1.0 - ADAM_BETA1**step
            correction2 = 1.0 - ADAM_BETA2**step

            mw1 = ADAM_BETA1 * mw1 + (1.0 - ADAM_BETA1) * grad_w1
            vw1 = ADAM_BETA2 * vw1 + (1.0 - ADAM_BETA2) * (grad_w1 * grad_w1)
            mb1 = ADAM_BETA1 * mb1 + (1.0 - ADAM_BETA1) * grad_b1
            vb1 = ADAM_BETA2 * vb1 + (1.0 - ADAM_BETA2) * (grad_b1 * grad_b1)
            mw2 = ADAM_BETA1 * mw2 + (1.0 - ADAM_BETA1) * grad_w2
            vw2 = ADAM_BETA2 * vw2 + (1.0 - ADAM_BETA2) * (grad_w2 * grad_w2)
            mb2 = np.float32(ADAM_BETA1 * mb2 + (1.0 - ADAM_BETA1) * grad_b2)
            vb2 = np.float32(ADAM_BETA2 * vb2 + (1.0 - ADAM_BETA2) * grad_b2 * grad_b2)

            w1 -= LEARNING_RATE * (mw1 / correction1) / (np.sqrt(vw1 / correction2) + ADAM_EPSILON)
            b1 -= LEARNING_RATE * (mb1 / correction1) / (np.sqrt(vb1 / correction2) + ADAM_EPSILON)
            w2 -= LEARNING_RATE * (mw2 / correction1) / (np.sqrt(vw2 / correction2) + ADAM_EPSILON)
            b2 -= np.float32(
                LEARNING_RATE
                * (mb2 / correction1)
                / (math.sqrt(float(vb2 / correction2)) + ADAM_EPSILON)
            )

    validation_scores = _sigmoid(np.maximum(x_validation @ w1 + b1, 0.0) @ w2 + b2)
    test_scores = _sigmoid(np.maximum(x_test @ w1 + b1, 0.0) @ w2 + b2)
    validation_labels = [int(value) for value in y_validation.tolist()]
    test_labels = [int(value) for value in y_test.tolist()]
    validation_score_list = [float(value) for value in validation_scores.tolist()]
    test_score_list = [float(value) for value in test_scores.tolist()]

    validation_auc = _auc_from_scores(validation_labels, validation_score_list)
    test_auc = _auc_from_scores(test_labels, test_score_list)
    predictions = [1 if score >= 0.5 else 0 for score in test_score_list]
    test_accuracy = sum(
        int(prediction == label) for prediction, label in zip(predictions, test_labels)
    ) / len(test_labels)

    null_labels = list(test_labels)
    null_rng = random.Random(int(model_seed) ^ 0x5A5A5A5A)
    null_rng.shuffle(null_labels)
    null_auc = _auc_from_scores(null_labels, test_score_list)

    return {
        "validation_auc": float(validation_auc),
        "test_auc": float(test_auc),
        "test_accuracy": float(test_accuracy),
        "neural_advantage": _advantage(test_auc),
        "null_auc": float(null_auc),
        "null_advantage": _advantage(null_auc),
    }


def run_candidate(candidate_index: int) -> dict[str, Any]:
    sbox, metrics = _verify_candidate(candidate_index)
    candidate = CANDIDATES[candidate_index]
    runs: list[dict[str, Any]] = []

    for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
        cipher = ToySPN(sbox, ROUND_KEYS)
        if cipher.rounds != ROUNDS:
            raise RuntimeError(f"expected {ROUNDS} ToySPN rounds, got {cipher.rounds}")
        samples = generate_balanced_pairs(
            cipher,
            pair_count=PAIR_COUNT,
            input_difference=INPUT_DIFFERENCE,
            seed=int(dataset_seed),
        )
        train_samples, validation_samples, test_samples = split_dataset(samples)
        endpoint = _train_one(
            train_samples=train_samples,
            validation_samples=validation_samples,
            test_samples=test_samples,
            model_seed=int(model_seed),
        )
        runs.append(
            {
                "replicate": replicate,
                "dataset_seed": int(dataset_seed),
                "model_seed": int(model_seed),
                "train_size": len(train_samples),
                "validation_size": len(validation_samples),
                "test_size": len(test_samples),
                **endpoint,
            }
        )

    return {
        "schema_version": 1,
        "experiment": "neural100_residual_screen_candidate",
        "scientific_status": "exploratory_diagnostic_not_gate1_not_phase2",
        "candidate_index": int(candidate_index),
        "fingerprint": str(candidate["fingerprint"]),
        "classical_metrics": metrics,
        "configuration": {
            "rounds": ROUNDS,
            "round_keys": [int(value) for value in ROUND_KEYS],
            "input_difference": INPUT_DIFFERENCE,
            "pair_count": PAIR_COUNT,
            "hidden_units": HIDDEN_UNITS,
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "adam_beta1": ADAM_BETA1,
            "adam_beta2": ADAM_BETA2,
            "adam_epsilon": ADAM_EPSILON,
        },
        "runs": runs,
    }


def _mean(values: Iterable[float]) -> float:
    frozen = [float(value) for value in values]
    if not frozen:
        raise ValueError("cannot compute mean of an empty sequence")
    return float(sum(frozen) / len(frozen))


def _paired_heterogeneity_p(matrix: list[list[float]]) -> tuple[float, float]:
    """Permutation p-value for variance of per-candidate mean advantages."""

    if len(matrix) != 10 or any(len(row) != 10 for row in matrix):
        raise ValueError("paired heterogeneity matrix must be 10 candidates x 10 replicates")
    observed_means = [_mean(row) for row in matrix]
    observed = statistics.pvariance(observed_means)

    rng = random.Random(PERMUTATION_SEED)
    exceedances = 0
    for _ in range(PERMUTATION_REPETITIONS):
        permuted = [[0.0] * 10 for _ in range(10)]
        for replicate in range(10):
            values = [matrix[candidate][replicate] for candidate in range(10)]
            rng.shuffle(values)
            for candidate, value in enumerate(values):
                permuted[candidate][replicate] = value
        statistic = statistics.pvariance([_mean(row) for row in permuted])
        if statistic >= observed - 1e-18:
            exceedances += 1
    p_value = (1 + exceedances) / (PERMUTATION_REPETITIONS + 1)
    return float(observed), float(p_value)


def aggregate_candidate_results(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(results) != 10:
        raise ValueError("aggregation requires exactly ten candidate result objects")
    ordered = sorted(results, key=lambda item: int(item["candidate_index"]))
    if [int(item["candidate_index"]) for item in ordered] != list(range(10)):
        raise ValueError("candidate result indices must be exactly 0..9")

    candidate_summaries: list[dict[str, Any]] = []
    advantage_matrix: list[list[float]] = []
    all_runs = 0

    for candidate_index, item in enumerate(ordered):
        expected = CANDIDATES[candidate_index]
        if item["fingerprint"] != expected["fingerprint"]:
            raise ValueError(f"fingerprint mismatch for candidate {candidate_index}")
        runs = sorted(item["runs"], key=lambda run: int(run["replicate"]))
        if len(runs) != 10 or [int(run["replicate"]) for run in runs] != list(range(10)):
            raise ValueError(f"candidate {candidate_index} must contain replicates 0..9")
        for replicate, run in enumerate(runs):
            if int(run["dataset_seed"]) != int(DATASET_SEEDS[replicate]):
                raise ValueError("dataset seed mismatch during aggregation")
            if int(run["model_seed"]) != int(MODEL_SEEDS[replicate]):
                raise ValueError("model seed mismatch during aggregation")

        aucs = [float(run["test_auc"]) for run in runs]
        advantages = [float(run["neural_advantage"]) for run in runs]
        null_advantages = [float(run["null_advantage"]) for run in runs]
        advantage_matrix.append(advantages)
        candidate_summaries.append(
            {
                "candidate_index": candidate_index,
                "fingerprint": item["fingerprint"],
                "mean_test_auc": _mean(aucs),
                "median_test_auc": float(statistics.median(aucs)),
                "mean_advantage": _mean(advantages),
                "median_advantage": float(statistics.median(advantages)),
                "std_advantage": float(statistics.pstdev(advantages)),
                "mean_null_advantage": _mean(null_advantages),
            }
        )
        all_runs += len(runs)

    observed_variance, heterogeneity_p = _paired_heterogeneity_p(advantage_matrix)
    best = max(candidate_summaries, key=lambda item: float(item["mean_advantage"]))
    mean_advantages = [float(item["mean_advantage"]) for item in candidate_summaries]
    advantage_range = max(mean_advantages) - min(mean_advantages)
    signal_condition = (
        float(best["mean_advantage"]) >= 0.04
        and float(best["mean_advantage"]) - float(best["mean_null_advantage"]) >= 0.02
    )
    heterogeneity_condition = advantage_range >= 0.02 and heterogeneity_p < 0.01
    if signal_condition and heterogeneity_condition:
        diagnostic = "residual_signal_and_heterogeneity"
    elif signal_condition:
        diagnostic = "residual_signal_no_heterogeneity"
    else:
        diagnostic = "no_exploitable_residual_at_frozen_budget"

    return {
        "schema_version": 1,
        "experiment": "neural100_residual_screen_aggregate",
        "scientific_status": "exploratory_diagnostic_not_gate1_not_phase2",
        "summary": {
            "total_trainings": all_runs,
            "candidate_count": len(candidate_summaries),
            "replicates_per_candidate": 10,
            "max_candidate_mean_advantage": float(best["mean_advantage"]),
            "max_candidate_mean_null_advantage": float(best["mean_null_advantage"]),
            "max_candidate_index": int(best["candidate_index"]),
            "max_candidate_fingerprint": str(best["fingerprint"]),
            "candidate_mean_advantage_range": float(advantage_range),
            "heterogeneity_variance": float(observed_variance),
            "heterogeneity_permutation_p": float(heterogeneity_p),
            "permutation_repetitions": PERMUTATION_REPETITIONS,
            "diagnostic": diagnostic,
            "global_gate1": "red",
            "neural_oracle": "blocked",
        },
        "candidates": candidate_summaries,
    }


def aggregate_directory(input_dir: Path) -> dict[str, Any]:
    paths = sorted(input_dir.glob("neural100-candidate-*.json"))
    if len(paths) != 10:
        raise ValueError(f"expected 10 candidate JSON files in {input_dir}, found {len(paths)}")
    return aggregate_candidate_results(
        [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="run ten frozen trainings for one S-box")
    train_parser.add_argument("--candidate-index", type=int, required=True)
    train_parser.add_argument("--output", type=Path, required=True)

    aggregate_parser = subparsers.add_parser("aggregate", help="aggregate all ten candidate jobs")
    aggregate_parser.add_argument("--input-dir", type=Path, required=True)
    aggregate_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "train":
        result = run_candidate(args.candidate_index)
        _write_json(args.output, result)
        print(
            json.dumps(
                {
                    "candidate_index": result["candidate_index"],
                    "fingerprint": result["fingerprint"],
                    "trainings": len(result["runs"]),
                    "mean_test_auc": _mean(run["test_auc"] for run in result["runs"]),
                    "mean_advantage": _mean(run["neural_advantage"] for run in result["runs"]),
                },
                sort_keys=True,
            )
        )
    else:
        aggregate = aggregate_directory(args.input_dir)
        _write_json(args.output, aggregate)
        print(json.dumps(aggregate["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
