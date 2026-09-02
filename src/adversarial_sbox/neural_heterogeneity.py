"""Preregistered multi-regime neural heterogeneity challenger for the educational ToySPN.

This module is exploratory only. It does not change Global Gate 1 and it does not
apply neural pressure to evolution. See research/NEURAL_HETEROGENEITY_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Iterable, Sequence

from .datasets import PairSample, generate_balanced_pairs, split_dataset
from .neural100 import (
    ADAM_BETA1,
    ADAM_BETA2,
    ADAM_EPSILON,
    BATCH_SIZE,
    PAIR_COUNT,
    WEIGHT_DECAY,
    _advantage,
    _auc_from_scores,
    _numpy,
    _train_one as _train_bit_relu_mlp,
    _verify_candidate,
)
from .neural100_candidates import CANDIDATES
from .spn import ToySPN

ROUND_KEYS = (
    0x243F6A88,
    0x85A308D3,
    0x13198A2E,
    0x03707344,
    0xA4093822,
    0x299F31D0,
)
ROUND_COUNTS = (3, 4, 5)
INPUT_DIFFERENCES = (0x00000001, 0x00000100, 0x00010001, 0x01010101)
ARCHITECTURES = ("bit_relu_mlp", "byte_tanh_mlp")
REPLICATES = 5

DATASET_BASE_SEEDS = (510001, 510013, 510031, 510047, 510059)
MODEL_BASE_SEEDS = (610001, 610019, 610031, 610043, 610051)

BYTE_HIDDEN_1 = 48
BYTE_HIDDEN_2 = 24
BYTE_EPOCHS = 32
BYTE_LEARNING_RATE = 0.003

GLOBAL_PERMUTATIONS = 10000
GLOBAL_PERMUTATION_SEED = 920001
ARCH_PERMUTATIONS = 5000
ARCH_PERMUTATION_SEEDS = {
    "bit_relu_mlp": 920101,
    "byte_tanh_mlp": 920201,
}

REGIMES = tuple(
    (rounds, input_difference)
    for rounds in ROUND_COUNTS
    for input_difference in INPUT_DIFFERENCES
)


def regime_index(rounds: int, input_difference: int) -> int:
    target = (int(rounds), int(input_difference))
    try:
        return REGIMES.index(target)
    except ValueError as exc:
        raise ValueError(f"undeclared regime {target!r}") from exc


def frozen_seeds(
    rounds: int,
    input_difference: int,
    architecture: str,
    replicate: int,
) -> tuple[int, int]:
    if architecture not in ARCHITECTURES:
        raise ValueError(f"unknown architecture {architecture!r}")
    if not 0 <= int(replicate) < REPLICATES:
        raise ValueError(f"replicate must be in [0, {REPLICATES - 1}]")
    g = regime_index(rounds, input_difference)
    r = int(replicate)
    dataset_seed = int(DATASET_BASE_SEEDS[r] + 1000 * g)
    architecture_offset = 0 if architecture == "bit_relu_mlp" else 100000
    model_seed = int(MODEL_BASE_SEEDS[r] + 1000 * g + architecture_offset)
    return dataset_seed, model_seed


def _samples_to_byte_arrays(samples: Sequence[PairSample]):
    np = _numpy()
    features = np.empty((len(samples), 12), dtype=np.float32)
    labels = np.empty(len(samples), dtype=np.float32)
    for row, sample in enumerate(samples):
        values = (int(sample.left), int(sample.right), int(sample.left) ^ int(sample.right))
        column = 0
        for value in values:
            for shift in (24, 16, 8, 0):
                byte = (value >> shift) & 0xFF
                features[row, column] = np.float32(byte / 127.5 - 1.0)
                column += 1
        labels[row] = np.float32(sample.label)
    return features, labels


def _sigmoid(logits):
    np = _numpy()
    clipped = np.clip(logits, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _adam_update(param, moment, variance, gradient, step: int, learning_rate: float):
    np = _numpy()
    moment = ADAM_BETA1 * moment + (1.0 - ADAM_BETA1) * gradient
    variance = ADAM_BETA2 * variance + (1.0 - ADAM_BETA2) * (gradient * gradient)
    correction1 = 1.0 - ADAM_BETA1**step
    correction2 = 1.0 - ADAM_BETA2**step
    param = param - learning_rate * (moment / correction1) / (
        np.sqrt(variance / correction2) + ADAM_EPSILON
    )
    return param, moment, variance


def _train_byte_tanh_mlp(
    *,
    train_samples: Sequence[PairSample],
    validation_samples: Sequence[PairSample],
    test_samples: Sequence[PairSample],
    model_seed: int,
) -> dict[str, float]:
    np = _numpy()
    x_train, y_train = _samples_to_byte_arrays(train_samples)
    x_validation, y_validation = _samples_to_byte_arrays(validation_samples)
    x_test, y_test = _samples_to_byte_arrays(test_samples)

    rng = np.random.default_rng(int(model_seed))
    w1 = rng.normal(0.0, math.sqrt(1.0 / 12.0), size=(12, BYTE_HIDDEN_1)).astype(np.float32)
    b1 = np.zeros(BYTE_HIDDEN_1, dtype=np.float32)
    w2 = rng.normal(
        0.0, math.sqrt(1.0 / BYTE_HIDDEN_1), size=(BYTE_HIDDEN_1, BYTE_HIDDEN_2)
    ).astype(np.float32)
    b2 = np.zeros(BYTE_HIDDEN_2, dtype=np.float32)
    w3 = rng.normal(0.0, math.sqrt(1.0 / BYTE_HIDDEN_2), size=(BYTE_HIDDEN_2,)).astype(
        np.float32
    )
    b3 = np.float32(0.0)

    m_w1 = np.zeros_like(w1)
    v_w1 = np.zeros_like(w1)
    m_b1 = np.zeros_like(b1)
    v_b1 = np.zeros_like(b1)
    m_w2 = np.zeros_like(w2)
    v_w2 = np.zeros_like(w2)
    m_b2 = np.zeros_like(b2)
    v_b2 = np.zeros_like(b2)
    m_w3 = np.zeros_like(w3)
    v_w3 = np.zeros_like(w3)
    m_b3 = np.float32(0.0)
    v_b3 = np.float32(0.0)
    step = 0

    for _epoch in range(BYTE_EPOCHS):
        order = rng.permutation(len(x_train))
        for start in range(0, len(order), BATCH_SIZE):
            batch_index = order[start : start + BATCH_SIZE]
            xb = x_train[batch_index]
            yb = y_train[batch_index]

            h1 = np.tanh(xb @ w1 + b1)
            h2 = np.tanh(h1 @ w2 + b2)
            logits = h2 @ w3 + b3
            probabilities = _sigmoid(logits)

            batch_size = float(len(batch_index))
            dlogits = (probabilities - yb) / batch_size
            grad_w3 = h2.T @ dlogits + WEIGHT_DECAY * w3
            grad_b3 = np.sum(dlogits, dtype=np.float32)
            dh2 = dlogits[:, None] * w3[None, :]
            dh2_pre = dh2 * (1.0 - h2 * h2)
            grad_w2 = h1.T @ dh2_pre + WEIGHT_DECAY * w2
            grad_b2 = np.sum(dh2_pre, axis=0, dtype=np.float32)
            dh1 = dh2_pre @ w2.T
            dh1_pre = dh1 * (1.0 - h1 * h1)
            grad_w1 = xb.T @ dh1_pre + WEIGHT_DECAY * w1
            grad_b1 = np.sum(dh1_pre, axis=0, dtype=np.float32)

            step += 1
            w1, m_w1, v_w1 = _adam_update(
                w1, m_w1, v_w1, grad_w1, step, BYTE_LEARNING_RATE
            )
            b1, m_b1, v_b1 = _adam_update(
                b1, m_b1, v_b1, grad_b1, step, BYTE_LEARNING_RATE
            )
            w2, m_w2, v_w2 = _adam_update(
                w2, m_w2, v_w2, grad_w2, step, BYTE_LEARNING_RATE
            )
            b2, m_b2, v_b2 = _adam_update(
                b2, m_b2, v_b2, grad_b2, step, BYTE_LEARNING_RATE
            )
            w3, m_w3, v_w3 = _adam_update(
                w3, m_w3, v_w3, grad_w3, step, BYTE_LEARNING_RATE
            )
            b3, m_b3, v_b3 = _adam_update(
                b3, m_b3, v_b3, grad_b3, step, BYTE_LEARNING_RATE
            )

    validation_scores = _sigmoid(
        np.tanh(np.tanh(x_validation @ w1 + b1) @ w2 + b2) @ w3 + b3
    )
    test_scores = _sigmoid(np.tanh(np.tanh(x_test @ w1 + b1) @ w2 + b2) @ w3 + b3)

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
    null_rng = random.Random(int(model_seed) ^ 0x6B6B6B6B)
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


def run_cell(rounds: int, input_difference: int, architecture: str) -> dict[str, Any]:
    rounds = int(rounds)
    input_difference = int(input_difference)
    if architecture not in ARCHITECTURES:
        raise ValueError(f"unknown architecture {architecture!r}")
    g = regime_index(rounds, input_difference)
    keys = ROUND_KEYS[: rounds + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index, candidate in enumerate(CANDIDATES):
        sbox, metrics = _verify_candidate(candidate_index)
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != rounds:
            raise RuntimeError(f"expected {rounds} rounds, got {cipher.rounds}")

        for replicate in range(REPLICATES):
            dataset_seed, model_seed = frozen_seeds(
                rounds, input_difference, architecture, replicate
            )
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=input_difference,
                seed=dataset_seed,
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            if architecture == "bit_relu_mlp":
                endpoint = _train_bit_relu_mlp(
                    train_samples=train_samples,
                    validation_samples=validation_samples,
                    test_samples=test_samples,
                    model_seed=model_seed,
                )
            else:
                endpoint = _train_byte_tanh_mlp(
                    train_samples=train_samples,
                    validation_samples=validation_samples,
                    test_samples=test_samples,
                    model_seed=model_seed,
                )
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "fingerprint": str(candidate["fingerprint"]),
                    "classical_metrics": metrics,
                    "replicate": replicate,
                    "dataset_seed": dataset_seed,
                    "model_seed": model_seed,
                    "train_size": len(train_samples),
                    "validation_size": len(validation_samples),
                    "test_size": len(test_samples),
                    **endpoint,
                }
            )

    return {
        "schema_version": 1,
        "experiment": "neural_sbox_heterogeneity_cell",
        "scientific_status": "exploratory_diagnostic_not_gate1_not_phase2",
        "regime_index": g,
        "rounds": rounds,
        "input_difference": input_difference,
        "architecture": architecture,
        "pair_count": PAIR_COUNT,
        "runs": runs,
    }


def _mean(values: Iterable[float]) -> float:
    frozen = [float(value) for value in values]
    if not frozen:
        raise ValueError("cannot compute mean of an empty sequence")
    return float(sum(frozen) / len(frozen))


def _variance_of_candidate_means(blocks: Sequence[Sequence[float]]) -> float:
    if not blocks or any(len(block) != len(CANDIDATES) for block in blocks):
        raise ValueError("each block must contain exactly the ten candidates")
    candidate_sums = [0.0] * len(CANDIDATES)
    for block in blocks:
        for candidate_index, value in enumerate(block):
            candidate_sums[candidate_index] += float(value)
    means = [total / len(blocks) for total in candidate_sums]
    return float(statistics.pvariance(means))


def blocked_heterogeneity_p(
    blocks: Sequence[Sequence[float]],
    *,
    repetitions: int,
    seed: int,
) -> tuple[float, float]:
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    frozen = [[float(value) for value in block] for block in blocks]
    observed = _variance_of_candidate_means(frozen)
    rng = random.Random(int(seed))
    exceedances = 0

    for _ in range(int(repetitions)):
        candidate_sums = [0.0] * len(CANDIDATES)
        for block in frozen:
            shuffled = list(block)
            rng.shuffle(shuffled)
            for candidate_index, value in enumerate(shuffled):
                candidate_sums[candidate_index] += value
        means = [total / len(frozen) for total in candidate_sums]
        statistic = statistics.pvariance(means)
        if statistic >= observed - 1e-18:
            exceedances += 1

    p_value = (1 + exceedances) / (1 + int(repetitions))
    return float(observed), float(p_value)


def _average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: float(values[index]))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        value = float(values[order[cursor]])
        while end < len(order) and float(values[order[end]]) == value:
            end += 1
        average_rank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = average_rank
        cursor = end
    return ranks


def spearman_correlation(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman correlation requires equal sequences of length >= 2")
    x = _average_ranks(left)
    y = _average_ranks(right)
    mean_x = _mean(x)
    mean_y = _mean(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denom_x = math.sqrt(sum((a - mean_x) ** 2 for a in x))
    denom_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
    if denom_x == 0.0 or denom_y == 0.0:
        return 0.0
    return float(numerator / (denom_x * denom_y))


def _expected_cell_keys() -> set[tuple[int, int, str]]:
    return {
        (rounds, input_difference, architecture)
        for rounds, input_difference in REGIMES
        for architecture in ARCHITECTURES
    }


def aggregate_cell_results(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(results) != len(REGIMES) * len(ARCHITECTURES):
        raise ValueError("aggregation requires exactly 24 cell result objects")

    cells: dict[tuple[int, int, str], dict[str, Any]] = {}
    for item in results:
        key = (
            int(item["rounds"]),
            int(item["input_difference"]),
            str(item["architecture"]),
        )
        if key in cells:
            raise ValueError(f"duplicate cell {key!r}")
        cells[key] = item

    if set(cells) != _expected_cell_keys():
        raise ValueError("cell set does not match the frozen factorial design")

    block_map: dict[tuple[int, int, str, int], list[float | None]] = {}
    null_map: dict[tuple[int, int, str, int], list[float | None]] = {}
    total_trainings = 0

    for (rounds, input_difference, architecture), item in cells.items():
        if int(item["regime_index"]) != regime_index(rounds, input_difference):
            raise ValueError("regime index mismatch")
        runs = item["runs"]
        if len(runs) != len(CANDIDATES) * REPLICATES:
            raise ValueError("every cell must contain exactly 50 trainings")

        seen_pairs: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < len(CANDIDATES):
                raise ValueError("candidate index out of range")
            if not 0 <= replicate < REPLICATES:
                raise ValueError("replicate out of range")
            pair = (candidate_index, replicate)
            if pair in seen_pairs:
                raise ValueError("duplicate candidate/replicate training")
            seen_pairs.add(pair)

            expected_candidate = CANDIDATES[candidate_index]
            if str(run["fingerprint"]) != str(expected_candidate["fingerprint"]):
                raise ValueError("candidate fingerprint mismatch")
            expected_dataset_seed, expected_model_seed = frozen_seeds(
                rounds, input_difference, architecture, replicate
            )
            if int(run["dataset_seed"]) != expected_dataset_seed:
                raise ValueError("dataset seed mismatch")
            if int(run["model_seed"]) != expected_model_seed:
                raise ValueError("model seed mismatch")

            block_key = (rounds, input_difference, architecture, replicate)
            block = block_map.setdefault(block_key, [None] * len(CANDIDATES))
            null_block = null_map.setdefault(block_key, [None] * len(CANDIDATES))
            if block[candidate_index] is not None:
                raise ValueError("duplicate candidate entry inside block")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1

    if total_trainings != 1200:
        raise ValueError(f"expected exactly 1200 trainings, got {total_trainings}")
    if len(block_map) != 120:
        raise ValueError(f"expected exactly 120 complete blocks, got {len(block_map)}")
    if any(any(value is None for value in block) for block in block_map.values()):
        raise ValueError("incomplete neural block")
    if any(any(value is None for value in block) for block in null_map.values()):
        raise ValueError("incomplete null block")

    ordered_block_keys = sorted(
        block_map,
        key=lambda key: (
            regime_index(key[0], key[1]),
            ARCHITECTURES.index(key[2]),
            key[3],
        ),
    )
    global_blocks = [
        [float(value) for value in block_map[key]] for key in ordered_block_keys
    ]
    global_variance, global_p = blocked_heterogeneity_p(
        global_blocks,
        repetitions=GLOBAL_PERMUTATIONS,
        seed=GLOBAL_PERMUTATION_SEED,
    )

    candidate_summaries: list[dict[str, Any]] = []
    architecture_candidate_means: dict[str, list[float]] = {
        architecture: [] for architecture in ARCHITECTURES
    }

    for candidate_index, candidate in enumerate(CANDIDATES):
        advantages = [
            float(block_map[key][candidate_index]) for key in ordered_block_keys
        ]
        null_advantages = [
            float(null_map[key][candidate_index]) for key in ordered_block_keys
        ]
        architecture_means: dict[str, float] = {}
        for architecture in ARCHITECTURES:
            values = [
                float(block_map[key][candidate_index])
                for key in ordered_block_keys
                if key[2] == architecture
            ]
            architecture_means[architecture] = _mean(values)
            architecture_candidate_means[architecture].append(_mean(values))
        candidate_summaries.append(
            {
                "candidate_index": candidate_index,
                "fingerprint": str(candidate["fingerprint"]),
                "mean_advantage": _mean(advantages),
                "median_advantage": float(statistics.median(advantages)),
                "std_advantage": float(statistics.pstdev(advantages)),
                "mean_null_advantage": _mean(null_advantages),
                "architecture_mean_advantages": architecture_means,
            }
        )

    architecture_tests: dict[str, dict[str, float]] = {}
    for architecture in ARCHITECTURES:
        keys = [key for key in ordered_block_keys if key[2] == architecture]
        blocks = [[float(value) for value in block_map[key]] for key in keys]
        variance, p_value = blocked_heterogeneity_p(
            blocks,
            repetitions=ARCH_PERMUTATIONS,
            seed=ARCH_PERMUTATION_SEEDS[architecture],
        )
        architecture_tests[architecture] = {
            "heterogeneity_variance": variance,
            "heterogeneity_permutation_p": p_value,
        }

    spearman = spearman_correlation(
        architecture_candidate_means["bit_relu_mlp"],
        architecture_candidate_means["byte_tanh_mlp"],
    )

    overall_means = [float(item["mean_advantage"]) for item in candidate_summaries]
    overall_range = max(overall_means) - min(overall_means)
    best = max(candidate_summaries, key=lambda item: float(item["mean_advantage"]))
    signal_condition = any(
        float(item["mean_advantage"]) >= 0.04
        and float(item["mean_advantage"]) - float(item["mean_null_advantage"]) >= 0.02
        for item in candidate_summaries
    )
    global_condition = global_p < 0.01 and overall_range >= 0.015
    replication_condition = (
        architecture_tests["bit_relu_mlp"]["heterogeneity_permutation_p"] < 0.05
        and architecture_tests["byte_tanh_mlp"]["heterogeneity_permutation_p"] < 0.05
        and spearman >= 0.40
    )

    if signal_condition and global_condition and replication_condition:
        diagnostic = "replicated_sbox_heterogeneity"
    elif signal_condition and global_condition:
        diagnostic = "global_heterogeneity_not_replicated"
    elif signal_condition:
        diagnostic = "residual_signal_no_sbox_heterogeneity"
    else:
        diagnostic = "no_exploitable_residual_at_frozen_budget"

    regime_summaries: list[dict[str, Any]] = []
    for rounds, input_difference in REGIMES:
        candidate_means = []
        for candidate_index in range(len(CANDIDATES)):
            values = [
                float(block_map[key][candidate_index])
                for key in ordered_block_keys
                if key[0] == rounds and key[1] == input_difference
            ]
            candidate_means.append(_mean(values))
        regime_summaries.append(
            {
                "rounds": rounds,
                "input_difference": input_difference,
                "candidate_mean_advantage_range": max(candidate_means) - min(candidate_means),
                "max_candidate_index": max(
                    range(len(candidate_means)), key=lambda index: candidate_means[index]
                ),
                "max_candidate_mean_advantage": max(candidate_means),
            }
        )

    return {
        "schema_version": 1,
        "experiment": "neural_sbox_heterogeneity_aggregate",
        "scientific_status": "exploratory_diagnostic_not_gate1_not_phase2",
        "summary": {
            "total_trainings": total_trainings,
            "candidate_count": len(CANDIDATES),
            "regime_count": len(REGIMES),
            "architecture_count": len(ARCHITECTURES),
            "replicates": REPLICATES,
            "global_heterogeneity_variance": global_variance,
            "global_heterogeneity_permutation_p": global_p,
            "candidate_mean_advantage_range": overall_range,
            "architecture_spearman": spearman,
            "max_candidate_index": int(best["candidate_index"]),
            "max_candidate_fingerprint": str(best["fingerprint"]),
            "max_candidate_mean_advantage": float(best["mean_advantage"]),
            "max_candidate_mean_null_advantage": float(best["mean_null_advantage"]),
            "diagnostic": diagnostic,
            "global_gate1": "red",
            "neural_oracle": "blocked",
        },
        "architecture_tests": architecture_tests,
        "candidates": candidate_summaries,
        "regimes": regime_summaries,
    }


def aggregate_directory(input_dir: Path) -> dict[str, Any]:
    paths = sorted(input_dir.rglob("neural-heterogeneity-cell-*.json"))
    if len(paths) != 24:
        raise ValueError(f"expected 24 cell JSON files in {input_dir}, found {len(paths)}")
    return aggregate_cell_results(
        [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train-cell")
    train_parser.add_argument("--rounds", type=int, required=True)
    train_parser.add_argument("--input-difference", type=lambda value: int(value, 0), required=True)
    train_parser.add_argument("--architecture", choices=ARCHITECTURES, required=True)
    train_parser.add_argument("--output", type=Path, required=True)

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--input-dir", type=Path, required=True)
    aggregate_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "train-cell":
        result = run_cell(args.rounds, args.input_difference, args.architecture)
        _write_json(args.output, result)
        print(
            json.dumps(
                {
                    "rounds": result["rounds"],
                    "input_difference": result["input_difference"],
                    "architecture": result["architecture"],
                    "trainings": len(result["runs"]),
                    "mean_advantage": _mean(
                        run["neural_advantage"] for run in result["runs"]
                    ),
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
