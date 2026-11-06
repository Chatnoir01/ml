"""Eight (and only eight) historical Phase 2G Adam minibatch updates, synthetic-only.

This is a bounded N=1 computational experiment, NOT a full model fit,
original Phase 2G rerun, original Phase 2R observation-only helper, or any
Phase 2U prospective neural training. Parent historical source is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .neural100 import BATCH_SIZE, WEIGHT_DECAY
from .neural_heterogeneity import (
    BYTE_LEARNING_RATE, _adam_update, _samples_to_byte_arrays, _sigmoid,
)
from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from .phase2g_shared_model import build_shared_training_splits
from .phase2r_fixture import CURRICULUM_SHA256, load_phase2r_fixture
from .phase2r_first_adam_microstep import (
    PARAMETERS, SHAPES, STAGES, original_first_step_tensors, _normalized,
)
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero
from .phase2r_serialization import hash_pair_split

PROTOCOL = "phase2r_first_eight_consecutive_adam_steps_v1"
STEPS = 8
SOURCES = ("train", "validation", "test")
_EXPECTED_LENGTHS = (5600, 1200, 1200)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _index_hash(indices: Any, *, scope: str) -> str:
    import numpy as np
    data = np.asarray(indices, dtype="<i8").tobytes(order="C")
    return _sha(("phase2r-e8-" + scope + "-v1\0").encode() + data)


def one_historical_batch(
    xb: Any, yb: Any, weights: dict[str, Any],
    moments: dict[str, Any], variances: dict[str, Any], step: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Clone exact arithmetic sequence of original _fit_shared_model_state_bytes.

    Do not call its full-trainer function. Reuse its original _adam_update,
    persist the six moments and variances, and stop at preregistered step eight.
    """
    import numpy as np
    if type(step) is not int or step not in range(1, STEPS + 1):
        raise ValueError("unregistered number of Adam updates")
    if any(tuple(mapping) != PARAMETERS for mapping in (weights, moments, variances)):
        raise ValueError("exact six parameters and moments required")
    w1, b1, w2, b2, w3, b3 = (weights[k] for k in PARAMETERS)
    first_linear = xb @ w1 + b1
    h1 = np.tanh(first_linear)
    second_linear = h1 @ w2 + b2
    h2 = np.tanh(second_linear)
    logits = h2 @ w3 + b3
    probabilities = _sigmoid(logits)

    batch_size = float(len(xb))
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
    grads = {
        "w1": grad_w1, "b1": grad_b1,
        "w2": grad_w2, "b2": grad_b2,
        "w3": grad_w3, "b3": grad_b3,
    }
    stage = {
        "batch_features": xb,
        "batch_labels": yb,
        "first_linear": first_linear,
        "first_tanh": h1,
        "second_linear": second_linear,
        "second_tanh": h2,
        "logits": logits,
        "probabilities": probabilities,
    }
    updated, next_m, next_v = {}, {}, {}
    for key in PARAMETERS:
        stage["grad_" + key] = grads[key]
    for key in PARAMETERS:
        up, mo, va = _adam_update(
            weights[key], moments[key], variances[key],
            grads[key], step, BYTE_LEARNING_RATE,
        )
        updated[key], next_m[key], next_v[key] = up, mo, va
        stage["updated_" + key] = up
        stage["moment_" + key] = mo
        stage["variance_" + key] = va
    if set(stage) != set(STAGES):
        raise RuntimeError("original 32-stage microstep definition drift")
    for key in STAGES:
        array = np.asarray(stage[key])
        if (array.shape != SHAPES[key] or array.dtype != np.float32
                or not np.isfinite(array).all()):
            raise RuntimeError(f"nonfinite or changed float32 tensor shape: {key}")
    return stage, updated, next_m, next_v


def eight_consecutive_adam_steps(tensors_path: Path) -> dict[str, Any]:
    """One seeded permutation, exactly eight *consecutive* minibatches."""
    import numpy as np

    if any(os.environ.get(k) != "1" for k in THREAD_VARS):
        raise ValueError("five numerical thread environment variables must be one")
    fixture = load_phase2r_fixture()
    dataset_seed = TRAINING_DATASET_BASE_SEEDS[0]
    model_seed = TRAINING_MODEL_BASE_SEEDS[0]
    splits = build_shared_training_splits(fixture, difference=1, dataset_seed=dataset_seed)
    if tuple(len(x) for x in splits) != _EXPECTED_LENGTHS:
        raise RuntimeError("historical synthetic dataset geometry drift")
    split_hashes = {
        name: hash_pair_split(sample, split=name)
        for name, sample in zip(SOURCES, splits)
    }
    x_train, y_train = _samples_to_byte_arrays(splits[0])
    _samples_to_byte_arrays(splits[1])
    _samples_to_byte_arrays(splits[2])

    initial, rng = checkpoint_zero_seeded_initialization(model_seed)
    original_init = observe_checkpoint_zero(tensors=initial, rng=rng)
    order = rng.permutation(len(x_train))
    if len(order) != _EXPECTED_LENGTHS[0] or len(set(order[:STEPS * BATCH_SIZE].tolist())) != STEPS * BATCH_SIZE:
        raise RuntimeError("missing or repeated index in original permutation")
    batch_infos = []
    weights = initial
    moments = {k: np.zeros_like(v) if k != "b3" else np.float32(0.0) for k, v in initial.items()}
    variances = {k: np.zeros_like(v) if k != "b3" else np.float32(0.0) for k, v in initial.items()}
    all_tensors = {}
    step_hashes = {}
    rng_post = _sha(_canonical(rng.bit_generator.state))
    for step in range(1, STEPS + 1):
        positions = order[(step - 1) * BATCH_SIZE:step * BATCH_SIZE]
        xb, yb = x_train[positions], y_train[positions]
        stage, weights, moments, variances = one_historical_batch(
            xb, yb, weights, moments, variances, step
        )
        if step == 1:
            # Fail closed if we accidentally modified the already-validated
            # original one-step math while implementing the eight-step study.
            baseline = original_first_step_tensors(xb, yb, initial)
            for name in STAGES:
                if _array_receipt(stage[name]) != _array_receipt(baseline[name]):
                    raise RuntimeError(f"first-step original implementation differs at {name}")
        batch_infos.append({
            "step": step,
            "indices_sha256": _index_hash(positions, scope="selected-batch"),
        })
        receipts = {}
        for name in STAGES:
            key = f"s{step:02d}__{name}"
            all_tensors[key] = stage[name]
            receipts[name] = _array_receipt(stage[name])
        step_hashes[f"s{step:02d}"] = receipts
    with tensors_path.open("xb") as handle:
        np.savez(handle, **all_tensors)
    runtime = stable_numpy_runtime_profile()
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": dataset_seed, "model_seed": model_seed,
        "dataset_sha256": split_hashes,
        "initialization_sha256": original_init["initialization_sha256"],
        "rng_before_permutation_sha256": original_init["rng_state_sha256"],
        "rng_after_permutation_sha256": rng_post,
        "first_epoch_permutation_sha256": _index_hash(order, scope="entire-permutation"),
        "first_epoch_batch_info": batch_infos,
        "steps_completed": STEPS,
        "samples_seen": STEPS * BATCH_SIZE,
        "model_updates_per_step": len(PARAMETERS),
        "first_step_exact_original_math_parity": True,
        "stages": step_hashes,
        "runtime_profile": runtime,
        "runtime_profile_sha256": _sha(_canonical(runtime)),
        "full_epoch_completed": False,
        "full_neural_training_performed": False,
        "phase2u_trainings_performed": 0,
        "historical_phase2g_root_cause_established": False,
        "scientific_status": "SYNTHETIC_EIGHT_ADAM_STEPS_NUMERICAL_INTERVENTION_ONLY",
    }
    report["receipt_sha256"] = _sha(_canonical(report))
    return report


def compare_eight_step_original_receipts(
    haswell: dict[str, Any], nehalem: dict[str, Any],
    haswell_npz: Path, nehalem_npz: Path,
) -> dict[str, Any]:
    import numpy as np
    for name, receipt in (("Haswell", haswell), ("Nehalem", nehalem)):
        if type(receipt) is not dict:
            raise ValueError("receipt must be object")
        body = dict(receipt)
        digest = body.pop("receipt_sha256", None)
        if digest != _sha(_canonical(body)):
            raise ValueError("original receipt integrity mismatch")
        fields = {
            "protocol": PROTOCOL, "schema_version": 1,
            "fixture_sha256": CURRICULUM_SHA256,
            "difference": 1, "replicate": 0,
            "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
            "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
            "steps_completed": STEPS,
            "samples_seen": STEPS * BATCH_SIZE,
            "model_updates_per_step": 6,
            "first_step_exact_original_math_parity": True,
            "full_epoch_completed": False,
            "full_neural_training_performed": False,
            "phase2u_trainings_performed": 0,
            "historical_phase2g_root_cause_established": False,
        }
        if any(receipt.get(k) != v for k, v in fields.items()):
            raise ValueError("unregistered eight-step scientific scope")
        if (type(receipt.get("source_commit")) is not str or
                re.fullmatch(r"[0-9a-f]{40}", receipt["source_commit"]) is None):
            raise ValueError("unidentified source commit")
        if (type(receipt.get("first_epoch_batch_info")) is not list or
                len(receipt["first_epoch_batch_info"]) != STEPS
                or any(row.get("step") != i + 1 or
                       not re.fullmatch(r"[0-9a-f]{64}", str(row.get("indices_sha256")))
                       for i, row in enumerate(receipt["first_epoch_batch_info"]))):
            raise ValueError("wrong or incomplete seeded minibatch identity")
        for field in ("initialization_sha256", "rng_before_permutation_sha256",
                      "rng_after_permutation_sha256", "first_epoch_permutation_sha256"):
            if (type(receipt.get(field)) is not str or
                    re.fullmatch(r"[0-9a-f]{64}", receipt[field]) is None):
                raise ValueError("missing original state or RNG digest")
        if (not isinstance(receipt.get("dataset_sha256"), dict)
                or set(receipt["dataset_sha256"]) != set(SOURCES)
                or any(not re.fullmatch(r"[0-9a-f]{64}", str(x))
                       for x in receipt["dataset_sha256"].values())):
            raise ValueError("unregistered data split digests")
        profile = receipt.get("runtime_profile")
        if (not isinstance(profile, dict)
                or receipt.get("runtime_profile_sha256") != _sha(_canonical(profile))
                or profile.get("python_version") != "3.12.14"
                or profile.get("numpy_version") != "2.5.3"
                or len(profile.get("blas_libraries", [])) != 1
                or profile["blas_libraries"][0].get("internal_api") != "openblas"
                or profile["blas_libraries"][0].get("architecture") != name
                or profile["blas_libraries"][0].get("num_threads") != 1):
            raise ValueError("different or unpinned numerical backend")
        stages = receipt.get("stages")
        if (type(stages) is not dict or set(stages) !=
                {f"s{i:02d}" for i in range(1, STEPS + 1)}
                or any(type(v) is not dict or set(v) != set(STAGES) for v in stages.values())):
            raise ValueError("missing or duplicated original 8x32 stage receipts")
    gate = (
        "source_commit", "fixture_sha256", "dataset_seed", "model_seed",
        "dataset_sha256", "initialization_sha256",
        "rng_before_permutation_sha256", "rng_after_permutation_sha256",
        "first_epoch_permutation_sha256", "first_epoch_batch_info",
    )
    if any(haswell.get(k) != nehalem.get(k) for k in gate):
        raise ValueError("original data, permutation, initial weights or RNG mismatch")
    if _normalized(haswell["runtime_profile"]) != _normalized(nehalem["runtime_profile"]):
        raise ValueError("same-host CPU/BLAS changed beyond deliberate kernel")
    step_summaries = []
    with np.load(haswell_npz, allow_pickle=False) as h, \
         np.load(nehalem_npz, allow_pickle=False) as n:
        expected = {f"s{i:02d}__{name}" for i in range(1, STEPS + 1) for name in STAGES}
        if set(h.files) != expected or set(n.files) != expected:
            raise ValueError("NPZ missing/extra original experiment tensor")
        for step in range(1, STEPS + 1):
            per_name = {}
            for name in STAGES:
                key = f"s{step:02d}__{name}"
                a, b = h[key], n[key]
                if (a.dtype != np.float32 or b.dtype != np.float32 or
                        a.shape != SHAPES[name] or b.shape != SHAPES[name]):
                    raise ValueError("unexpected original tensor dtype or stage shape")
                if (_array_receipt(a) != haswell["stages"][f"s{step:02d}"][name]
                        or _array_receipt(b) != nehalem["stages"][f"s{step:02d}"][name]):
                    raise ValueError("NPZ original tensor and SHA-256 receipt mismatch")
                nchanged = int(np.count_nonzero(a.view(np.uint32) != b.view(np.uint32)))
                delta = np.abs(a.astype(np.float64) - b.astype(np.float64))
                per_name[name] = {
                    "elements": int(a.size),
                    "changed": nchanged,
                    "maximum_absolute_difference": float(delta.max()),
                    "mean_absolute_difference": float(delta.mean()),
                }
            if any(per_name[x]["changed"] for x in ("batch_features", "batch_labels")):
                raise ValueError("first-epoch original minibatch input/label bytes differ")
            stats = {}
            for prefix in ("grad_", "updated_", "moment_", "variance_"):
                vals = [per_name[prefix + p] for p in PARAMETERS]
                stats[prefix.rstrip("_")] = {
                    "tensors_changed": sum(v["changed"] > 0 for v in vals),
                    "elements_changed": sum(v["changed"] for v in vals),
                    "maximum_absolute_difference": max(v["maximum_absolute_difference"] for v in vals),
                    "mean_absolute_difference_weighted": (
                        sum(v["mean_absolute_difference"] * v["elements"] for v in vals) /
                        sum(v["elements"] for v in vals)
                    ),
                }
            step_summaries.append({
                "step": step,
                "grad": stats["grad"], "updated": stats["updated"],
                "moment": stats["moment"], "variance": stats["variance"],
                "updated_by_parameter": {
                    p: per_name["updated_" + p] for p in PARAMETERS
                },
            })
    first, last = step_summaries[0], step_summaries[-1]
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "source_commit": haswell["source_commit"],
        "comparison": "same-host_forced_Haswell_vs_Nehalem_8_consecutive_original_batches",
        "steps": STEPS,
        "sample_count": STEPS * BATCH_SIZE,
        "tensor_pairs_rechecked": STEPS * len(STAGES),
        "individual_original_tensor_hashes_rechecked": STEPS * len(STAGES) * 2,
        "per_step": step_summaries,
        "first_step_updated_parameter_changes": first["updated"]["tensors_changed"],
        "eighth_step_updated_parameter_changes": last["updated"]["tensors_changed"],
        "eighth_step_changed_parameter_elements": last["updated"]["elements_changed"],
        "first_step_maximum_parameter_delta": first["updated"]["maximum_absolute_difference"],
        "eighth_step_maximum_parameter_delta": last["updated"]["maximum_absolute_difference"],
        "first_step_weighted_mean_abs_parameter_delta": first["updated"]["mean_absolute_difference_weighted"],
        "eighth_step_weighted_mean_abs_parameter_delta": last["updated"]["mean_absolute_difference_weighted"],
        "eighth_step_has_any_parameter_difference": bool(last["updated"]["elements_changed"]),
        "first_step_original_math_parity": True,
        "original_receipt_sha256s": {
            "Haswell": haswell["receipt_sha256"],
            "Nehalem": nehalem["receipt_sha256"],
        },
        "source_npz_sha256s": {
            "Haswell": _sha(haswell_npz.read_bytes()),
            "Nehalem": _sha(nehalem_npz.read_bytes()),
        },
        "full_epoch_completed": False,
        "full_neural_training_performed": False,
        "phase2u_neural_trainings_performed": 0,
        "historical_phase2g_cause_identified": False,
        "scientific_verdict": "ONE_PAIRED_SYNTHETIC_EIGHT_STEP_NUMERICAL_CONTROL_ONLY",
    }
    report["report_sha256"] = _sha(_canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", choices=("Haswell", "Nehalem"))
    parser.add_argument("--npz", type=Path)
    parser.add_argument("--haswell-json", type=Path)
    parser.add_argument("--nehalem-json", type=Path)
    parser.add_argument("--haswell-npz", type=Path)
    parser.add_argument("--nehalem-npz", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    a = parser.parse_args()
    if a.kernel:
        if a.npz is None or any((a.haswell_json,a.nehalem_json,a.haswell_npz,a.nehalem_npz)):
            parser.error("emit requires --kernel and --npz only")
        result = eight_consecutive_adam_steps(a.npz)
    else:
        if a.npz is not None or not all((a.haswell_json,a.nehalem_json,a.haswell_npz,a.nehalem_npz)):
            parser.error("compare requires two receipt JSON and NPZ inputs")
        result = compare_eight_step_original_receipts(
            json.loads(a.haswell_json.read_text(encoding="utf-8")),
            json.loads(a.nehalem_json.read_text(encoding="utf-8")),
            a.haswell_npz, a.nehalem_npz,
        )
    with a.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, sort_keys=True, indent=2, allow_nan=False)
        out.write("\n")
    print(result.get("scientific_verdict", result.get("protocol")))


if __name__ == "__main__":
    main()
