"""Checkpoint-zero forward-only numerical probe (no gradients, epochs or optimizer).

Uses the frozen synthetic 2R curriculum and a fixed first batch from the
existing Phase 2G dataset generator. Never loads historical held-out H and
never touches the original Phase 2G training implementation or frozen results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
from pathlib import Path
from typing import Any

from .neural100 import BATCH_SIZE
from .neural_heterogeneity import _samples_to_byte_arrays, _sigmoid
from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from .phase2g_shared_model import build_shared_training_splits
from .phase2r_fixture import CURRICULUM_SHA256, load_phase2r_fixture
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero

_DIFF = 1
_REP = 0
_STAGES = ("input_features", "first_linear", "first_tanh",
           "second_linear", "second_tanh", "logits", "probabilities")


def _array_receipt(value: Any) -> dict[str, Any]:
    """Hash versioned exact float32 bytes, preserving shape and row order."""
    import numpy as np

    arr = np.asarray(value)
    if arr.dtype != np.dtype("float32") or not np.isfinite(arr).all():
        raise ValueError("forward probe stage must contain finite native float32")
    little = np.ascontiguousarray(arr.astype("<f4", copy=False))
    dimensions = tuple(int(i) for i in arr.shape)
    header = b"phase2r-forward-f32-v1\0" + struct.pack("<I", len(dimensions))
    header += b"".join(struct.pack("<I", i) for i in dimensions)
    return {
        "shape": list(dimensions),
        "dtype": "float32",
        "sha256": hashlib.sha256(header + little.tobytes(order="C")).hexdigest(),
    }


def forward_only_probe() -> dict[str, Any]:
    """Run only tensor arithmetic corresponding to first forward batch, NO updates."""
    import numpy as np

    if any(os.environ.get(k) != "1" for k in THREAD_VARS):
        raise ValueError("five BLAS-related thread environment variables must all be one")
    fixture = load_phase2r_fixture()
    train, validation, test = build_shared_training_splits(
        fixture, difference=_DIFF, dataset_seed=TRAINING_DATASET_BASE_SEEDS[_REP]
    )
    if (len(train), len(validation), len(test)) != (5600, 1200, 1200):
        raise RuntimeError("synthetic fixture dataset sizes drifted")
    x_train, _labels = _samples_to_byte_arrays(train)
    xb = x_train[:BATCH_SIZE]
    weights, rng = checkpoint_zero_seeded_initialization(TRAINING_MODEL_BASE_SEEDS[_REP])
    initialization = observe_checkpoint_zero(tensors=weights, rng=rng)
    w1, b1, w2, b2, w3, b3 = (
        weights[k] for k in ("w1", "b1", "w2", "b2", "w3", "b3")
    )
    # Match the forward tensor operations from _fit_shared_model_state_bytes,
    # but NEVER call its epoch loop or perform a parameter/optimizer update.
    linear1 = xb @ w1 + b1
    h1 = np.tanh(linear1)
    linear2 = h1 @ w2 + b2
    h2 = np.tanh(linear2)
    logits = h2 @ w3 + b3
    probs = _sigmoid(logits)
    arrays = (xb, linear1, h1, linear2, h2, logits, probs)
    stages = {name: _array_receipt(arr) for name, arr in zip(_STAGES, arrays)}
    runtime = stable_numpy_runtime_profile()
    receipt = {
        "schema_version": 1,
        "purpose": "phase2r_first_forward_batch_without_training",
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": _DIFF,
        "replicate": _REP,
        "model_seed": TRAINING_MODEL_BASE_SEEDS[_REP],
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[_REP],
        "batch_size": BATCH_SIZE,
        "initialization_sha256": initialization["initialization_sha256"],
        "rng_state_sha256": initialization["rng_state_sha256"],
        "runtime_profile_sha256": hashlib.sha256(_canonical(runtime)).hexdigest(),
        "runtime_profile": runtime,
        "stages": stages,
        "neural_training_performed": False,
        "gradient_computed": False,
        "optimizer_update_performed": False,
        "historical_phase2g_anomaly_explained": False,
    }
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()
    return receipt


def compare_forward_probes(a: dict[str, Any], f: dict[str, Any]) -> dict[str, Any]:
    """Compute the first mismatched forward tensor. This is observational only."""
    for name, record in (("A", a), ("F", f)):
        if not isinstance(record, dict):
            raise ValueError(f"{name} receipt must be object")
        stripped = dict(record)
        got = stripped.pop("receipt_sha256", None)
        if hashlib.sha256(_canonical(stripped)).hexdigest() != got:
            raise ValueError("forward receipt integrity mismatch")
        if (record.get("schema_version") != 1 or
                record.get("purpose") != "phase2r_first_forward_batch_without_training"
                or record.get("fixture_sha256") != CURRICULUM_SHA256
                or record.get("neural_training_performed") is not False
                or record.get("gradient_computed") is not False
                or record.get("optimizer_update_performed") is not False
                or record.get("historical_phase2g_anomaly_explained") is not False):
            raise ValueError("invalid forward-only scope contract")
        if (type(record.get("source_commit")) is not str or
                re.fullmatch(r"[0-9a-f]{40}", record["source_commit"]) is None or
                record.get("model_seed") != TRAINING_MODEL_BASE_SEEDS[_REP] or
                record.get("dataset_seed") != TRAINING_DATASET_BASE_SEEDS[_REP]):
            raise ValueError("incorrect registered source and seed identity")
        if not isinstance(record.get("runtime_profile"), dict):
            raise ValueError("missing normalized runtime profile")
        if hashlib.sha256(_canonical(record["runtime_profile"])).hexdigest() != record.get("runtime_profile_sha256"):
            raise ValueError("unbound numerical runtime metadata")
        numerical = record["runtime_profile"]
        if (numerical.get("schema_version") != 1 or
                numerical.get("python_version") != "3.12.14" or
                numerical.get("numpy_version") != "2.5.3" or
                not isinstance(numerical.get("simd_available"), list) or
                not isinstance(numerical.get("blas_libraries"), list) or
                not numerical["blas_libraries"] or
                any(type(info.get("num_threads")) is not int or
                    info["num_threads"] != 1 for info in numerical["blas_libraries"])):
            raise ValueError("numerical runtime not pinned or fully observed")
        if not isinstance(record.get("stages"), dict) or set(record["stages"]) != set(_STAGES):
            raise ValueError("missing forward stages")
        for stage in _STAGES:
            v = record["stages"][stage]
            if (not isinstance(v, dict) or v.get("dtype") != "float32"
                    or not isinstance(v.get("shape"), list)
                    or type(v.get("sha256")) is not str or len(v["sha256"]) != 64
                    or any(c not in "0123456789abcdef" for c in v["sha256"])):
                raise ValueError("invalid forward stage digest")
        if record.get("batch_size") != BATCH_SIZE or record.get("difference") != _DIFF or record.get("replicate") != _REP:
            raise ValueError("different forward-only cell or batch")
    for field in ("source_commit", "model_seed", "dataset_seed",
                  "initialization_sha256", "rng_state_sha256"):
        if not a.get(field) or a[field] != f.get(field):
            raise ValueError(f"pre-training prerequisite differs: {field}")
    by_stage = [{
        "name": stage,
        "same_shape": a["stages"][stage]["shape"] == f["stages"][stage]["shape"],
        "byte_sha256_equal": a["stages"][stage]["sha256"] == f["stages"][stage]["sha256"],
    } for stage in _STAGES]
    earliest = next((r["name"] for r in by_stage if not r["same_shape"] or not r["byte_sha256_equal"]), None)
    same_cpu = a["runtime_profile_sha256"] == f["runtime_profile_sha256"]
    result = {
        "schema_version": 1,
        "scope": "first_batch_inference_tensors_only_no_training",
        "stage_count": len(by_stage),
        "by_stage": by_stage,
        "earliest_different_stage": earliest,
        "all_stage_bytes_equal": earliest is None,
        "normalized_runtime_profiles_identical": same_cpu,
        "blas_architecture_by_arm": {
            "A": [x.get("architecture") for x in a["runtime_profile"]["blas_libraries"]],
            "F": [x.get("architecture") for x in f["runtime_profile"]["blas_libraries"]],
        },
        "status": ("IDENTICAL_FORWARD_BYTES_UNDER_INCOMPARABLE_RUNNERS" if earliest is None and not same_cpu
                   else "DIFFERENT_FORWARD_BYTES_UNDER_INCOMPARABLE_RUNNERS" if not same_cpu
                   else "IDENTICAL_FORWARD_BYTES_SAMPLED" if earliest is None
                   else "DIFFERENT_FORWARD_BYTES_SAMPLED"),
        "neural_training_performed": False,
        "causal_explanation_of_phase2g_established": False,
        "scientific_verdict": "EXPLORATORY_NUMERICAL_PROBE_ONLY",
    }
    result["report_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("A", "F"))
    parser.add_argument("--compare-A", type=Path)
    parser.add_argument("--compare-F", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.arm and not args.compare_A and not args.compare_F:
        report = forward_only_probe()
    elif not args.arm and args.compare_A and args.compare_F:
        report = compare_forward_probes(json.loads(args.compare_A.read_text()),
                                         json.loads(args.compare_F.read_text()))
    else:
        parser.error("specify either an arm to emit or both receipt inputs")
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
    print(report.get("status", report.get("purpose")))


if __name__ == "__main__":
    main()
