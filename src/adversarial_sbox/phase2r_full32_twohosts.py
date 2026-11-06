"""Complete 32-epoch SYNTHETIC control for last two Phase2R-unused seeds.

Prospective fixed N=2 NEW-to-Phase2R seeds (replicates 6,7) numerical intervention. Exactly 704 original Adam updates
per seed and kernel. No Phase 2G historical replay or Phase 2U neural training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from .neural100 import BATCH_SIZE, WEIGHT_DECAY, _auc_from_scores, _advantage
from .neural_heterogeneity import (
    BYTE_LEARNING_RATE, _adam_update, _samples_to_byte_arrays, _sigmoid,
)
from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from .phase2g_shared_model import build_shared_training_splits
from .phase2r_fixture import CURRICULUM_SHA256, load_phase2r_fixture
from .phase2r_first_adam_microstep import PARAMETERS, PARAM_SHAPES
from .phase2r_first_epoch import epoch_step as frozen_first_epoch_step
from .phase2r_four_fresh_seeds import bounded_historical_update as frozen_two_epoch_step
from .phase2r_first_adam_microstep import _normalized as comparable_runtime
from .phase2r_eight_adam_steps import _index_hash
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero
from .phase2r_serialization import hash_pair_split

PROTOCOL = "phase2r_full32_last_two_seeds_two_hosts_v1"
REPLICATES = (6, 7)
EPOCHS = 32
EVALUATION_EPOCHS = (1, 2, 4, 8, 16, 32)
BATCHES_PER_EPOCH = 22
STEPS = EPOCHS * BATCHES_PER_EPOCH
TOTAL_PARAMETERS = sum(math.prod(s) for s in PARAM_SHAPES.values())
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_EPOCH_END = tuple(
    [f"moment_{x}" for x in PARAMETERS] +
    [f"variance_{x}" for x in PARAMETERS] +
    ["test_probabilities", "test_labels"]
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sigmoid_model(weights: dict[str, Any], features: Any) -> Any:
    import numpy as np
    w1, b1, w2, b2, w3, b3 = [weights[k] for k in PARAMETERS]
    return _sigmoid(np.tanh(np.tanh(features @ w1 + b1) @ w2 + b2) @ w3 + b3)


def bounded_historical_update(
    xb: Any, yb: Any, weights: dict[str, Any],
    moments: dict[str, Any], variances: dict[str, Any],
    global_step: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Transcribe original Phase 2G gradient + Adam in exact operation order.

    Unlike the frozen single-epoch study, Adam step increments 23..44 in epoch 2.
    All 22 epoch-1 calculations are checked against the independent frozen
    epoch_step() before any result can be emitted.
    """
    import numpy as np
    if type(global_step) is not int or not 1 <= global_step <= STEPS:
        raise ValueError("outside two registered epochs of 44 steps")
    expected_rows = 224 if global_step % BATCHES_PER_EPOCH == 0 else BATCH_SIZE
    if (xb.shape != (expected_rows, 12) or yb.shape != (expected_rows,) or
            xb.dtype != np.float32 or yb.dtype != np.float32):
        raise ValueError("incorrect historical minibatch shape or dtype")
    if any(tuple(z) != PARAMETERS for z in (weights, moments, variances)):
        raise ValueError("must preserve exact original six model parameter keys")
    w1, b1, w2, b2, w3, b3 = [weights[k] for k in PARAMETERS]
    h1 = np.tanh(xb @ w1 + b1)
    h2 = np.tanh(h1 @ w2 + b2)
    logits = h2 @ w3 + b3
    probs = _sigmoid(logits)
    dlogits = (probs - yb) / float(len(xb))
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
    grads = {
        "w1": grad_w1, "b1": grad_b1,
        "w2": grad_w2, "b2": grad_b2,
        "w3": grad_w3, "b3": grad_b3,
    }
    new_weights, new_moments, new_variances = {}, {}, {}
    for k in PARAMETERS:
        updated, m, v = _adam_update(
            weights[k], moments[k], variances[k],
            grads[k], global_step, BYTE_LEARNING_RATE,
        )
        new_weights[k] = updated
        new_moments[k] = m
        new_variances[k] = v
        if (np.asarray(updated).dtype != np.float32 or
                np.asarray(updated).shape != PARAM_SHAPES[k] or
                not np.isfinite(updated).all()):
            raise RuntimeError("out-of-scope numerical model state")
    stages = {
        "batch_features": xb, "batch_labels": yb,
        "first_linear": xb @ w1 + b1, "first_tanh": h1,
        "second_linear": h1 @ w2 + b2, "second_tanh": h2,
        "logits": logits, "probabilities": probs,
    }
    for k in PARAMETERS:
        stages["grad_" + k] = grads[k]
        stages["updated_" + k] = new_weights[k]
        stages["moment_" + k] = new_moments[k]
        stages["variance_" + k] = new_variances[k]
    return stages, new_weights, new_moments, new_variances


def emit_full32_synthetic(tensors_path: Path) -> dict[str, Any]:
    import numpy as np
    if any(os.environ.get(var) != "1" for var in THREAD_VARS):
        raise ValueError("five numeric thread environment variables must equal one")
    fixture = load_phase2r_fixture()
    source: dict[str, Any] = {}
    arrays: dict[str, Any] = {}
    replicas: list[dict[str, Any]] = []
    for r in REPLICATES:
        dataset_seed = TRAINING_DATASET_BASE_SEEDS[r]
        model_seed = TRAINING_MODEL_BASE_SEEDS[r]
        splits = build_shared_training_splits(fixture, difference=1,
                                              dataset_seed=dataset_seed)
        if tuple(len(s) for s in splits) != (5600, 1200, 1200):
            raise ValueError("historical synthetic split geometry drift")
        split_hashes = {
            name: hash_pair_split(part, split=name)
            for name, part in zip(("train", "validation", "test"), splits)
        }
        x_train, y_train = _samples_to_byte_arrays(splits[0])
        _samples_to_byte_arrays(splits[1])
        x_test, y_test = _samples_to_byte_arrays(splits[2])
        weights, rng = checkpoint_zero_seeded_initialization(model_seed)
        initial = observe_checkpoint_zero(tensors=weights, rng=rng)
        moments = {k: np.zeros_like(p) if k != "b3" else np.float32(0.0)
                   for k, p in weights.items()}
        variances = {k: np.zeros_like(p) if k != "b3" else np.float32(0.0)
                     for k, p in weights.items()}
        record: dict[str, Any] = {
            "replicate": r, "dataset_seed": dataset_seed, "model_seed": model_seed,
            "dataset_sha256": split_hashes,
            "initialization_sha256": initial["initialization_sha256"],
            "rng_before_epoch1_sha256": initial["rng_state_sha256"],
            "epochs": [],
        }
        for epoch in range(1, EPOCHS + 1):
            order = rng.permutation(5600)
            if sorted(order.tolist()) != list(range(5600)):
                raise ValueError("unregistered epoch permutation not bijective")
            epoch_receipt: dict[str, Any] = {
                "epoch": epoch,
                "permutation_sha256": _index_hash(order, scope="entire-permutation"),
                "permutation_indices": [int(i) for i in order.tolist()],
                "rng_after_permutation_sha256": _sha(_canonical(rng.bit_generator.state)),
                "batches": [],
                "epoch_end_receipts": {},
            }
            for j in range(BATCHES_PER_EPOCH):
                step = (epoch - 1) * BATCHES_PER_EPOCH + j + 1
                chosen = order[j * BATCH_SIZE:(j + 1) * BATCH_SIZE]
                target = BATCH_SIZE if j < BATCHES_PER_EPOCH-1 else 224
                if len(chosen) != target:
                    raise ValueError("the final registered minibatch must contain 224")
                xb, yb = x_train[chosen], y_train[chosen]
                old_weights, old_m, old_v = weights, moments, variances
                stage, weights, moments, variances = bounded_historical_update(
                    xb, yb, weights, moments, variances, step,
                )
                if epoch == 1:
                    expected, ew, em, ev = frozen_first_epoch_step(
                        xb, yb, old_weights, old_m, old_v, step,
                    )
                    for name in expected:
                        if _array_receipt(expected[name]) != _array_receipt(stage[name]):
                            raise RuntimeError(f"independent frozen first-epoch math differs at {r}/{step}/{name}")
                    for actual, baseline in ((weights, ew), (moments, em), (variances, ev)):
                        if any(_array_receipt(actual[k]) != _array_receipt(baseline[k]) for k in PARAMETERS):
                            raise RuntimeError("first-epoch independent original Adam state mismatch")
                elif epoch == 2:
                    reference, ref_w, ref_m, ref_v = frozen_two_epoch_step(
                        xb, yb, old_weights, old_m, old_v, step,
                    )
                    for name in reference:
                        if _array_receipt(reference[name]) != _array_receipt(stage[name]):
                            raise RuntimeError(f"frozen second-epoch mathematical parity differs at {r}/{step}/{name}")
                    for actual, baseline in ((weights, ref_w), (moments, ref_m), (variances, ref_v)):
                        if any(_array_receipt(actual[k]) != _array_receipt(baseline[k]) for k in PARAMETERS):
                            raise RuntimeError("frozen two-epoch Adam state continuation differs")
                epoch_receipt["batches"].append({
                    "step": step, "rows": target,
                    "indices_sha256": _index_hash(chosen, scope="selected-batch"),
                })
            end_state: dict[str, Any] = {}
            for k in PARAMETERS:
                for prefix, tensor in (
                    ("weight", weights[k]), ("moment", moments[k]),
                    ("variance", variances[k]),
                ):
                    field = f"{prefix}_{k}"
                    arrays[f"r{r}__e{epoch}__{field}"] = tensor
                    end_state[field] = _array_receipt(tensor)
            if epoch in EVALUATION_EPOCHS:
                predictions = _sigmoid_model(weights, x_test)
                if predictions.dtype != np.float32 or predictions.shape != (1200,):
                    raise RuntimeError("invalid fixed-checkpoint synthetic test prediction shape")
                auc = float(_auc_from_scores(
                    [int(x) for x in y_test.tolist()],
                    [float(x) for x in predictions.tolist()],
                ))
                for name, tensor in (("test_probabilities", predictions), ("test_labels", y_test)):
                    arrays[f"r{r}__e{epoch}__{name}"] = tensor
                    end_state[name] = _array_receipt(tensor)
                epoch_receipt["test_auc"] = auc
                epoch_receipt["test_advantage"] = float(_advantage(auc))
            epoch_receipt["epoch_end_receipts"] = end_state
            record["epochs"].append(epoch_receipt)
        replicas.append(record)
    if len(arrays) != 1176:
        raise RuntimeError("two new seeds, 32-epoch tensor inventory drift")
    with tensors_path.open("xb") as file:
        np.savez(file, **arrays)
    runtime = stable_numpy_runtime_profile()
    source = {
        "schema_version": 1, "protocol": PROTOCOL,
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "input_difference": 1,
        "replicas": replicas,
        "replicate_count": 2,
        "epochs_per_replica": 32,
        "adam_steps_per_replica": 704,
        "original_model_training_runs": 0,
        "phase2u_neural_training_runs": 0,
        "frozen_first_epoch_math_verified": True,
        "runtime_profile": runtime,
        "runtime_profile_sha256": _sha(_canonical(runtime)),
        "synthetic_complete_fits_per_kernel": 2,
        "evaluation_epochs": list(EVALUATION_EPOCHS),
        "scientific_verdict": "SYNTHETIC_32_EPOCH_NUMERICAL_CONTROL_NOT_CRYPTOGRAPHIC_VERDICT",
        "historical_phase2g_cause_established": False,
    }
    source["receipt_sha256"] = _sha(_canonical(source))
    return source




def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", choices=("Haswell","Nehalem"), required=True)
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    if a.npz.resolve() == a.output.resolve():
        parser.error("NPZ and receipt paths must be different")
    report = emit_full32_synthetic(a.npz)
    actual = report["runtime_profile"]["blas_libraries"]
    if len(actual) != 1 or actual[0].get("architecture") != a.kernel:
        raise RuntimeError("requested BLAS kernel does not match observed dynamic dispatch")
    with a.output.open("x", encoding="utf-8") as dst:
        json.dump(report, dst,sort_keys=True,indent=2,allow_nan=False)
        dst.write("\n")
    print("SYNTHETIC_32_EPOCH_SOURCE",a.kernel,
          "SEEDS", [r["model_seed"] for r in report["replicas"]],
          "CHECKPOINTS", EVALUATION_EPOCHS)

if __name__ == "__main__":
    main()
