"""Phase 2R pre-training two-runner controls; NO neural training is performed.

Replays *only* Phase 2G's existing dataset generation and its checkpoint-zero
weight initialization recipe on the independently pinned synthetic 2R fixture.
This is NOT a reconstruction of historical Phase 2G S-Boxes or final weights.
The historical model source remains unmodified.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import platform
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from .neural_heterogeneity import BYTE_HIDDEN_1, BYTE_HIDDEN_2
from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from .phase2g_shared_model import build_shared_training_splits
from .phase2r_fixture import CURRICULUM_SHA256, FIXTURE_ID, load_phase2r_fixture
from .phase2r_observation import observe_checkpoint_zero
from .phase2r_serialization import hash_pair_split

DIFFERENCES = (1, 256)
REPLICATES = tuple(range(8))
SPLIT_NAMES = ("train", "validation", "test")
SPLIT_COUNTS = (5600, 1200, 1200)
THREAD_VARS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
STATUS = "PRETRAINING_ONLY_NO_NEURAL_UPDATE"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")




def stable_numpy_runtime_profile() -> dict[str, Any]:
    """Fingerprint numerically relevant runtime traits, NOT host-specific IDs.

    NumPy show_runtime() may include platform.uname() with a unique hostname.
    Its raw stdout hash is diagnostic only; it must never decide whether two
    numerical environments are scientifically comparable.
    """
    import numpy as np
    from numpy._core._multiarray_umath import (
        __cpu_baseline__, __cpu_dispatch__, __cpu_features__,
    )
    try:
        from threadpoolctl import threadpool_info
    except ImportError as exc:
        raise RuntimeError("threadpoolctl is required for actual BLAS provenance") from exc

    loaded_blas = [
        {name: info.get(name) for name in (
            "user_api", "internal_api", "version",
            "threading_layer", "architecture", "num_threads",
        )}
        for info in threadpool_info() if info.get("user_api") == "blas"
    ]
    if not loaded_blas:
        raise RuntimeError("BLAS provider must be observed, not guessed")
    if any(type(info["num_threads"]) is not int or info["num_threads"] != 1
           for info in loaded_blas):
        raise RuntimeError("actual BLAS threads must equal one")
    return {
        "schema_version": 1,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "os": platform.system(),
        "architecture": platform.machine(),
        "simd_baseline": sorted(str(x) for x in __cpu_baseline__),
        "simd_dispatch": sorted(str(x) for x in __cpu_dispatch__),
        "simd_available": sorted(
            str(k) for k, value in __cpu_features__.items() if bool(value)
        ),
        "blas_libraries": sorted(loaded_blas, key=lambda info: _canonical(info)),
    }


def checkpoint_zero_seeded_initialization(model_seed: int):
    """Copy the original 2G pre-epoch NumPy weight recipe; never call the trainer.

    The original _fit_shared_model_state_bytes initializes w1/b1/w2/b2/w3/b3
    exactly as below. Duplication is explicit and independently reviewable:
    it is not a patch to the frozen trainer.
    """
    import numpy as np
    if type(model_seed) is not int or model_seed not in TRAINING_MODEL_BASE_SEEDS:
        raise ValueError("unregistered historical checkpoint-zero model seed")
    rng = np.random.default_rng(model_seed)
    w1 = rng.normal(0.0, math.sqrt(1.0 / 12.0),
                    size=(12, BYTE_HIDDEN_1)).astype(np.float32)
    b1 = np.zeros(BYTE_HIDDEN_1, dtype=np.float32)
    w2 = rng.normal(0.0, math.sqrt(1.0 / BYTE_HIDDEN_1),
                    size=(BYTE_HIDDEN_1, BYTE_HIDDEN_2)).astype(np.float32)
    b2 = np.zeros(BYTE_HIDDEN_2, dtype=np.float32)
    w3 = rng.normal(0.0, math.sqrt(1.0 / BYTE_HIDDEN_2),
                    size=(BYTE_HIDDEN_2,)).astype(np.float32)
    b3 = np.float32(0.0)
    return {"w1": w1, "b1": b1, "w2": w2, "b2": b2, "w3": w3, "b3": b3}, rng


def one_pretraining_cell(curriculum: tuple[tuple[int, ...], ...],
                         *, difference: int, replicate: int) -> dict[str, Any]:
    """Hash real 2G-generated synthetic ciphertext input and zero-step weights."""
    if type(difference) is not int or difference not in DIFFERENCES:
        raise ValueError("difference not in prospective preflight grid")
    if type(replicate) is not int or replicate not in REPLICATES:
        raise ValueError("replicate not in prospective preflight grid")
    dataset_seed = TRAINING_DATASET_BASE_SEEDS[replicate]
    model_seed = TRAINING_MODEL_BASE_SEEDS[replicate]
    parts = build_shared_training_splits(
        curriculum, difference=difference, dataset_seed=dataset_seed
    )
    if tuple(len(p) for p in parts) != SPLIT_COUNTS:
        raise RuntimeError("Phase 2R split geometry changed")
    splits = {name: hash_pair_split(p, split=name)
              for name, p in zip(SPLIT_NAMES, parts)}
    if len(set(splits.values())) != len(splits):
        raise RuntimeError("colliding Phase 2R split digests")
    weights, rng = checkpoint_zero_seeded_initialization(model_seed)
    observed = observe_checkpoint_zero(tensors=weights, rng=rng)
    if observed["neural_training_performed"] is not False:
        raise RuntimeError("a synthetic observation may never train")
    return {
        "difference": difference,
        "replicate": replicate,
        "dataset_seed": dataset_seed,
        "model_seed": model_seed,
        "dataset_sha256": splits,
        "initialization_sha256": observed["initialization_sha256"],
        "rng_state_sha256": observed["rng_state_sha256"],
    }


def emit_pretraining_receipt(arm_label: str) -> dict[str, Any]:
    """One A- or F-labelled batch; label must not enter numerical generation."""
    import numpy as np

    if type(arm_label) is not str or arm_label not in ("A", "F"):
        raise ValueError("only metadata labels A/F are supported")
    threads = {key: os.environ.get(key) for key in THREAD_VARS}
    if any(v != "1" for v in threads.values()):
        raise ValueError("all five numeric thread limits must equal 1 before NumPy import")
    fixture = load_phase2r_fixture()
    records = [
        one_pretraining_cell(fixture, difference=d, replicate=r)
        for d in DIFFERENCES for r in REPLICATES
    ]
    runtime = io.StringIO()
    with redirect_stdout(runtime):
        np.show_runtime()
    stable_profile = stable_numpy_runtime_profile()
    result = {
        "schema_version": 1,
        "status": STATUS,
        "arm_label_metadata_only": arm_label,
        "fixture_id": FIXTURE_ID,
        "curriculum_sha256": CURRICULUM_SHA256,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "machine": platform.machine(),
        "runner_commit": os.environ.get("GITHUB_SHA", ""),
        "thread_limits": threads,
        "numpy_runtime_report_sha256": hashlib.sha256(runtime.getvalue().encode()).hexdigest(),
        "stable_runtime_profile": stable_profile,
        "stable_runtime_profile_sha256": hashlib.sha256(_canonical(stable_profile)).hexdigest(),
        "cells": records,
        "model_cell_count": len(records),
        "neural_training_performed": False,
        "historical_phase2g_artifacts_used": False,
        "historical_phase2g_anomaly_explained": False,
        "scientific_result": False,
    }
    result["receipt_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def compare_pretraining_receipts(left: dict[str, Any],
                                  right: dict[str, Any]) -> dict[str, Any]:
    """Require byte-identical 16-cell INPUT and INITIAL state receipts."""
    if type(left) is not dict or type(right) is not dict:
        raise ValueError("expected two original JSON receipt objects")
    examined = []
    for receipt in (left, right):
        copy = dict(receipt)
        got = copy.pop("receipt_sha256", None)
        if (type(got) is not str or _HEX64.fullmatch(got) is None or
                hashlib.sha256(_canonical(copy)).hexdigest() != got):
            raise ValueError("pretraining receipt integrity failure")
        if (receipt.get("schema_version") != 1 or receipt.get("status") != STATUS or
                receipt.get("fixture_id") != FIXTURE_ID or
                receipt.get("curriculum_sha256") != CURRICULUM_SHA256 or
                receipt.get("neural_training_performed") is not False or
                receipt.get("historical_phase2g_artifacts_used") is not False or
                receipt.get("scientific_result") is not False or
                receipt.get("historical_phase2g_anomaly_explained") is not False or
                receipt.get("model_cell_count") != 16 or
                not isinstance(receipt.get("cells"), list) or len(receipt["cells"]) != 16):
            raise ValueError("noncompliant pre-training receipt")
        if receipt.get("python_version") != "3.12.14" or receipt.get("numpy_version") != "2.5.3":
            raise ValueError("not the preregistered numerical environment")
        if (type(receipt.get("numpy_runtime_report_sha256")) is not str or
                _HEX64.fullmatch(receipt["numpy_runtime_report_sha256"]) is None):
            raise ValueError("missing NumPy runtime diagnostic digest")
        profile = receipt.get("stable_runtime_profile")
        if (type(profile) is not dict or profile.get("schema_version") != 1 or
                type(receipt.get("stable_runtime_profile_sha256")) is not str or
                _HEX64.fullmatch(receipt["stable_runtime_profile_sha256"]) is None or
                hashlib.sha256(_canonical(profile)).hexdigest() != receipt["stable_runtime_profile_sha256"]):
            raise ValueError("missing or mismatched stable numerical runtime fingerprint")
        if (type(receipt.get("runner_commit")) is not str or
                re.fullmatch(r"[0-9a-f]{40}", receipt["runner_commit"]) is None):
            raise ValueError("missing exact source commit")
        if type(receipt.get("machine")) is not str or not receipt["machine"]:
            raise ValueError("missing machine identity")
        if not isinstance(receipt.get("thread_limits"), dict) or any(
            receipt["thread_limits"].get(var) != "1" for var in THREAD_VARS
        ):
            raise ValueError("thread controls missing")
        idx = {}
        for row in receipt["cells"]:
            if type(row) is not dict or type(row.get("difference")) is not int or type(row.get("replicate")) is not int:
                raise ValueError("invalid cell identity")
            key = (row["difference"], row["replicate"])
            if key not in {(d, r) for d in DIFFERENCES for r in REPLICATES} or key in idx:
                raise ValueError("missing or duplicate pretraining cell")
            if (row.get("dataset_seed") != TRAINING_DATASET_BASE_SEEDS[key[1]]
                    or row.get("model_seed") != TRAINING_MODEL_BASE_SEEDS[key[1]]):
                raise ValueError("pretraining seed identity mismatch")
            split = row.get("dataset_sha256")
            if not isinstance(split, dict) or set(split) != set(SPLIT_NAMES):
                raise ValueError("incomplete dataset hashes")
            hashes = [*split.values(), row.get("initialization_sha256"), row.get("rng_state_sha256")]
            if any(type(h) is not str or _HEX64.fullmatch(h) is None for h in hashes):
                raise ValueError("invalid 64-hex pretraining digest")
            idx[key] = row
        examined.append(idx)
    if {left.get("arm_label_metadata_only"), right.get("arm_label_metadata_only")} != {"A", "F"}:
        raise ValueError("two independent A/F-labelled receipts required")
    if left["runner_commit"] != right["runner_commit"]:
        raise ValueError("source commit mismatch between independently emitted receipts")
    compared = [
        {
            "difference": d, "replicate": r,
            "dataset_bytes_match": examined[0][(d, r)]["dataset_sha256"] ==
                                   examined[1][(d, r)]["dataset_sha256"],
            "initialization_bytes_match": examined[0][(d, r)]["initialization_sha256"] ==
                                           examined[1][(d, r)]["initialization_sha256"],
            "rng_state_match": examined[0][(d, r)]["rng_state_sha256"] ==
                               examined[1][(d, r)]["rng_state_sha256"],
        } for d in DIFFERENCES for r in REPLICATES
    ]
    data = sum(x["dataset_bytes_match"] for x in compared)
    init = sum(x["initialization_bytes_match"] for x in compared)
    rng = sum(x["rng_state_match"] for x in compared)
    runtime_match = (
        left["stable_runtime_profile_sha256"] == right["stable_runtime_profile_sha256"]
        and left["machine"] == right["machine"]
    )
    exact_bytes_match = (data == init == rng == 16)
    if not runtime_match:
        status = "INCOMPARABLE_NUMERICAL_RUNTIME_PROFILE_MISMATCH"
    elif not exact_bytes_match:
        status = "FAIL_PRETRAINING_BYTES_DIVERGE"
    else:
        status = "PASS_PRETRAINING_TWO_RUNNER_BYTE_INVARIANCE"
    report = {
        "schema_version": 1,
        "comparison": "two_CI_jobs_A_vs_F_pretraining_only",
        "data_matches": data,
        "initialization_matches": init,
        "rng_matches": rng,
        "total_cells": 16,
        "numpy_runtime_report_hashes_match": left["numpy_runtime_report_sha256"] ==
                                              right["numpy_runtime_report_sha256"],
        "machine_identity_matches": left["machine"] == right["machine"],
        "stable_runtime_profile_hashes_match": (
            left["stable_runtime_profile_sha256"] == right["stable_runtime_profile_sha256"]
        ),
        "stable_runtime_profile_sha256_by_arm": {
            "A": left["stable_runtime_profile_sha256"] if left["arm_label_metadata_only"] == "A" else right["stable_runtime_profile_sha256"],
            "F": left["stable_runtime_profile_sha256"] if left["arm_label_metadata_only"] == "F" else right["stable_runtime_profile_sha256"],
        },
        "exact_pretraining_byte_invariance_observed": exact_bytes_match,
        "runtime_comparability_established": runtime_match,
        "status": status,
        "cells": compared,
        "neural_training_performed": False,
        "historical_discrepancy_explained": False,
        "scientific_result": False,
    }
    report["report_sha256"] = hashlib.sha256(_canonical(report)).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    emit = subs.add_parser("emit")
    emit.add_argument("--arm", choices=["A", "F"], required=True)
    emit.add_argument("--output", type=Path, required=True)
    audit = subs.add_parser("compare")
    audit.add_argument("--A", type=Path, required=True)
    audit.add_argument("--F", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "emit":
        result = emit_pretraining_receipt(args.arm)
    else:
        paths = (args.A.resolve(), args.F.resolve(), args.output.resolve())
        if len(set(paths)) != 3:
            raise SystemExit("input and output paths must differ")
        a = json.loads(args.A.read_text(encoding="utf-8"))
        f = json.loads(args.F.read_text(encoding="utf-8"))
        result = compare_pretraining_receipts(a, f)
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(result, file, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
    print(result["status"])
    if args.action == "compare" and result["status"] != "PASS_PRETRAINING_TWO_RUNNER_BYTE_INVARIANCE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
