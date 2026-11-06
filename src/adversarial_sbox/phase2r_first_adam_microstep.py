"""One *training microstep* of the ORIGINAL Phase 2G byte_tanh_mlp, synthetic only.

This is deliberately NOT part of the observation-only PR #161. It performs
one original gradient and one Adam update for six tensors, not an epoch, model
fit, held-out validation, full training, or Phase 2U experiment.

No historical Phase 2G source or frozen scientific result is modified.
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
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero

PROTOCOL = "phase2r_first_historical_adam_step_v1"
PARAMETERS = ("w1", "b1", "w2", "b2", "w3", "b3")
FORWARD = ("first_linear", "first_tanh", "second_linear",
           "second_tanh", "logits", "probabilities")
GRADIENTS = tuple("grad_" + x for x in PARAMETERS)
UPDATED = tuple("updated_" + x for x in PARAMETERS)
MOMENTS = tuple("moment_" + x for x in PARAMETERS)
VARIANCES = tuple("variance_" + x for x in PARAMETERS)
STAGES = ("batch_features", "batch_labels", *FORWARD, *GRADIENTS,
          *UPDATED, *MOMENTS, *VARIANCES)
SHAPES = {
    "batch_features": (BATCH_SIZE, 12),
    "batch_labels": (BATCH_SIZE,),
    "first_linear": (BATCH_SIZE, 48),
    "first_tanh": (BATCH_SIZE, 48),
    "second_linear": (BATCH_SIZE, 24),
    "second_tanh": (BATCH_SIZE, 24),
    "logits": (BATCH_SIZE,),
    "probabilities": (BATCH_SIZE,),
}
PARAM_SHAPES = {"w1": (12, 48), "b1": (48,), "w2": (48, 24),
                "b2": (24,), "w3": (24,), "b3": ()}
for _prefix in ("grad_", "updated_", "moment_", "variance_"):
    SHAPES.update({_prefix + k: v for k, v in PARAM_SHAPES.items()})


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _arrays_float32(values: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    if set(values) != set(STAGES):
        raise ValueError("microstep must produce exactly the frozen stage list")
    for name, shape in SHAPES.items():
        arr = np.asarray(values[name])
        if arr.shape != shape or arr.dtype != np.dtype("float32") or not np.isfinite(arr).all():
            raise ValueError(f"bad original dtype, shape or nonfinite values at {name}")
    return values


def original_first_step_tensors(xb: Any, yb: Any, initial: dict[str, Any]) -> dict[str, Any]:
    """Transcribe ONLY the first historical Phase 2G training minibatch math.

    Keep operations/order identical to phase2g_shared_model._fit_shared_model_state_bytes.
    This function deliberately invokes the original _adam_update implementation.
    """
    import numpy as np

    if tuple(initial) != PARAMETERS:
        raise ValueError("wrong initial six weight tensors or parameter order")
    w1, b1, w2, b2, w3, b3 = (initial[k] for k in PARAMETERS)
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
    tensors: dict[str, Any] = {
        "batch_features": xb,
        "batch_labels": yb,
        "first_linear": first_linear,
        "first_tanh": h1,
        "second_linear": second_linear,
        "second_tanh": h2,
        "logits": logits,
        "probabilities": probabilities,
    }
    for key in PARAMETERS:
        tensors["grad_" + key] = grads[key]
    for key in PARAMETERS:
        p = initial[key]
        moment = np.zeros_like(p) if key != "b3" else np.float32(0.0)
        variance = np.zeros_like(p) if key != "b3" else np.float32(0.0)
        updated, first_moment, second_moment = _adam_update(
            p, moment, variance, grads[key], 1, BYTE_LEARNING_RATE
        )
        tensors["updated_" + key] = updated
        tensors["moment_" + key] = first_moment
        tensors["variance_" + key] = second_moment
    return _arrays_float32(tensors)


def emit_first_microstep(tensors_path: Path) -> dict[str, Any]:
    """One fixed, original permutation minibatch on synthetic S-Boxes only."""
    import numpy as np

    if any(os.environ.get(v) != "1" for v in THREAD_VARS):
        raise ValueError("numerical thread limits must all be one before NumPy import")
    fixture = load_phase2r_fixture()
    dataset_seed, model_seed = TRAINING_DATASET_BASE_SEEDS[0], TRAINING_MODEL_BASE_SEEDS[0]
    train, validation, test = build_shared_training_splits(
        fixture, difference=1, dataset_seed=dataset_seed,
    )
    if (len(train), len(validation), len(test)) != (5600, 1200, 1200):
        raise ValueError("synthetic 2R fixture split geometry drift")
    x_train, y_train = _samples_to_byte_arrays(train)
    # Original trainer materializes these before the first optimizer step.
    _samples_to_byte_arrays(validation)
    _samples_to_byte_arrays(test)

    weights, rng = checkpoint_zero_seeded_initialization(model_seed)
    init = observe_checkpoint_zero(tensors=weights, rng=rng)
    order = rng.permutation(len(x_train))
    chosen = order[:BATCH_SIZE]
    if len(chosen) != BATCH_SIZE or len(set(chosen.tolist())) != BATCH_SIZE:
        raise RuntimeError("unexpected first original minibatch permutation")
    xb, yb = x_train[chosen], y_train[chosen]
    post_shuffle_rng_sha = _sha(_canonical(rng.bit_generator.state))
    raw_indices = np.asarray(chosen, dtype="<i8").tobytes(order="C")
    batch_indices_sha = _sha(b"phase2r-original-first-permutation-v1\0" + raw_indices)

    stages = original_first_step_tensors(xb, yb, weights)
    # These are the exact tensors actually used and returned by the microstep.
    with tensors_path.open("xb") as handle:
        np.savez(handle, **stages)

    runtime = stable_numpy_runtime_profile()
    receipt = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": dataset_seed, "model_seed": model_seed,
        "original_training_rows": 5600,
        "first_minibatch_size": BATCH_SIZE,
        "original_rng_permutation_used": True,
        "first_batch_index_sha256": batch_indices_sha,
        "initialization_sha256": init["initialization_sha256"],
        "rng_pre_permutation_sha256": init["rng_state_sha256"],
        "rng_post_permutation_sha256": post_shuffle_rng_sha,
        "stages": {name: _array_receipt(stages[name]) for name in STAGES},
        "runtime_profile": runtime,
        "runtime_profile_sha256": _sha(_canonical(runtime)),
        "one_adam_step_executed": True,
        "adam_step_index": 1,
        "parameter_updates_executed": len(PARAMETERS),
        "full_neural_training_performed": False,
        "phase2u_neural_trainings_performed": 0,
        "historical_phase2g_anomaly_explained": False,
        "scientific_status": "EXPLORATORY_SYNTHETIC_SINGLE_ADAM_STEP_ONLY",
    }
    receipt["receipt_sha256"] = _sha(_canonical(receipt))
    return receipt


def _normalized(profile: dict[str, Any]) -> dict[str, Any]:
    return {**profile, "blas_libraries": [
        {k: v for k, v in lib.items() if k != "architecture"}
        for lib in profile["blas_libraries"]
    ]}


def compare_original_microstep_receipts(
    haswell: dict[str, Any], nehalem: dict[str, Any],
    haswell_npz: Path, nehalem_npz: Path,
) -> dict[str, Any]:
    """Fail closed on any source/rng/input drift; compare ORIGINAL NPZ values."""
    import numpy as np

    for name, r in (("Haswell", haswell), ("Nehalem", nehalem)):
        if type(r) is not dict:
            raise ValueError(f"{name} receipt must be an object")
        fields = dict(r)
        signed = fields.pop("receipt_sha256", None)
        if signed != _sha(_canonical(fields)):
            raise ValueError("microstep receipt integrity violation")
        if (r.get("schema_version") != 1 or r.get("protocol") != PROTOCOL
                or r.get("fixture_sha256") != CURRICULUM_SHA256
                or r.get("difference") != 1 or r.get("replicate") != 0
                or r.get("dataset_seed") != TRAINING_DATASET_BASE_SEEDS[0]
                or r.get("model_seed") != TRAINING_MODEL_BASE_SEEDS[0]
                or r.get("original_training_rows") != 5600
                or r.get("first_minibatch_size") != BATCH_SIZE
                or r.get("original_rng_permutation_used") is not True
                or r.get("one_adam_step_executed") is not True
                or r.get("adam_step_index") != 1
                or r.get("parameter_updates_executed") != 6
                or r.get("full_neural_training_performed") is not False
                or r.get("phase2u_neural_trainings_performed") != 0
                or r.get("historical_phase2g_anomaly_explained") is not False):
            raise ValueError("unregistered training microstep scope or original seed drift")
        if (type(r.get("source_commit")) is not str or
                re.fullmatch(r"[0-9a-f]{40}", r["source_commit"]) is None):
            raise ValueError("unverifiable Git source commit")
        profile = r.get("runtime_profile")
        if (not isinstance(profile, dict) or
                _sha(_canonical(profile)) != r.get("runtime_profile_sha256")
                or profile.get("python_version") != "3.12.14"
                or profile.get("numpy_version") != "2.5.3"
                or not isinstance(profile.get("blas_libraries"), list)
                or len(profile["blas_libraries"]) != 1
                or profile["blas_libraries"][0].get("internal_api") != "openblas"
                or profile["blas_libraries"][0].get("num_threads") != 1
                or profile["blas_libraries"][0].get("architecture") != name):
            raise ValueError("wrong selected OpenBLAS core or numerical environment")
        if (not isinstance(r.get("stages"), dict) or set(r["stages"]) != set(STAGES)):
            raise ValueError("missing/extra original tensor stages")
        for key in ("first_batch_index_sha256", "initialization_sha256",
                    "rng_pre_permutation_sha256", "rng_post_permutation_sha256"):
            if (type(r.get(key)) is not str or
                    re.fullmatch(r"[0-9a-f]{64}", r[key]) is None):
                raise ValueError(f"invalid {key}")

    prereq = ("source_commit", "dataset_seed", "model_seed",
              "first_batch_index_sha256", "initialization_sha256",
              "rng_pre_permutation_sha256", "rng_post_permutation_sha256")
    if any(haswell[k] != nehalem[k] for k in prereq):
        raise ValueError("microstep input, permutation or initialized state differs")
    if _normalized(haswell["runtime_profile"]) != _normalized(nehalem["runtime_profile"]):
        raise ValueError("same-host CPU/BLAS profile changed beyond requested kernel")

    actual_differences = []
    with np.load(haswell_npz, allow_pickle=False) as hs, \
         np.load(nehalem_npz, allow_pickle=False) as ns:
        if set(hs.files) != set(STAGES) or set(ns.files) != set(STAGES):
            raise ValueError("NPZ tensor source set differs")
        for stage in STAGES:
            a, b = hs[stage], ns[stage]
            if (a.shape != SHAPES[stage] or b.shape != SHAPES[stage]
                    or a.dtype != np.float32 or b.dtype != np.float32):
                raise ValueError("unexpected historical float32 stage tensor shape")
            if (_array_receipt(a) != haswell["stages"][stage] or
                    _array_receipt(b) != nehalem["stages"][stage]):
                raise ValueError("NPZ stage does not match its original receipt digest")
            mismatches = int(np.count_nonzero(a.view(np.uint32) != b.view(np.uint32)))
            delta = np.abs(a.astype(np.float64) - b.astype(np.float64))
            actual_differences.append({
                "stage": stage, "values": int(a.size),
                "differing_float32_values": mismatches,
                "maximum_absolute_difference": float(delta.max()),
                "mean_absolute_difference": float(delta.mean()),
            })
    if any(x["differing_float32_values"] for x in actual_differences[:2]):
        raise ValueError("microstep input features or labels are not byte-identical")

    gradient_records = [x for x in actual_differences if x["stage"] in GRADIENTS]
    updated_records = [x for x in actual_differences if x["stage"] in UPDATED]
    first_gradient = next((x["stage"] for x in gradient_records if x["differing_float32_values"]), None)
    first_updated = next((x["stage"] for x in updated_records if x["differing_float32_values"]), None)
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "scope": "one_first_minibatch_adam_step_synthetic_only",
        "source_commit": haswell["source_commit"],
        "kernel_pair": ["Haswell", "Nehalem"],
        "first_different_gradient": first_gradient,
        "first_different_updated_parameter": first_updated,
        "gradient_stage_changes": sum(bool(x["differing_float32_values"]) for x in gradient_records),
        "updated_parameter_changes": sum(bool(x["differing_float32_values"]) for x in updated_records),
        "total_stages": len(actual_differences),
        "all_stage_measurements": actual_differences,
        "observed_outcome": ("GRADIENT_OR_PARAMETER_BIT_DIFFERENCE_OBSERVED"
                             if first_gradient or first_updated
                             else "NO_DIFFERENCE_IN_FIRST_GRADIENT_OR_PARAMETER_STEP"),
        "original_receipt_sha256s": {
            "haswell": haswell["receipt_sha256"],
            "nehalem": nehalem["receipt_sha256"],
        },
        "original_npz_sha256s": {
            "haswell": _sha(haswell_npz.read_bytes()),
            "nehalem": _sha(nehalem_npz.read_bytes()),
        },
        "one_adam_step_executed": True,
        "full_neural_training_performed": False,
        "phase2u_neural_trainings_performed": 0,
        "historical_phase2g_cause_identified": False,
        "scientific_status": "EXPLORATORY_SYNTHETIC_SINGLE_ADAM_STEP_ONLY",
    }
    report["report_sha256"] = _sha(_canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", choices=("haswell", "nehalem"))
    parser.add_argument("--haswell-json", type=Path)
    parser.add_argument("--nehalem-json", type=Path)
    parser.add_argument("--haswell-npz", type=Path)
    parser.add_argument("--nehalem-npz", type=Path)
    parser.add_argument("--npz", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.kernel:
        if args.npz is None or any([args.haswell_json, args.nehalem_json, args.haswell_npz, args.nehalem_npz]):
            parser.error("emit needs --kernel and --npz only")
        report = emit_first_microstep(args.npz)
    else:
        if args.npz is not None or not all([
            args.haswell_json, args.nehalem_json, args.haswell_npz, args.nehalem_npz
        ]):
            parser.error("compare needs both source JSON and NPZ paths")
        report = compare_original_microstep_receipts(
            json.loads(args.haswell_json.read_text(encoding="utf-8")),
            json.loads(args.nehalem_json.read_text(encoding="utf-8")),
            args.haswell_npz, args.nehalem_npz,
        )
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(report.get("observed_outcome", report.get("protocol")))


if __name__ == "__main__":
    main()
