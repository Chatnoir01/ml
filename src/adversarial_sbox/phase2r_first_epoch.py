"""Exactly ONE first-epoch Phase 2G training comparison on synthetic Phase 2R fixture.

Bounded 22 original minibatches (21x256 + 1x224) under two BLAS kernels.
Not a full historical 32-epoch fit, original Phase 2G rerun or Phase 2U.
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
from .phase2r_first_adam_microstep import PARAMETERS, SHAPES, STAGES, _normalized
from .phase2r_eight_adam_steps import (
    _index_hash, one_historical_batch as frozen_first_eight_batch,
)
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero
from .phase2r_serialization import hash_pair_split

PROTOCOL = "phase2r_first_full_epoch_22_adam_batches_v1"
STEPS = 22
LAST_ROWS = 224
TEST_ROWS = 1200
_SAMPLE_DEPENDENT = (
    "batch_features", "batch_labels", "first_linear", "first_tanh",
    "second_linear", "second_tanh", "logits", "probabilities",
)
_EXPECTED_SPLITS = (5600, 1200, 1200)
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expected_shape(stage: str, step: int) -> tuple[int, ...]:
    if stage not in SHAPES or step not in range(1, STEPS + 1):
        raise ValueError("unknown original phase2r epoch stage or step")
    shape = SHAPES[stage]
    if stage in _SAMPLE_DEPENDENT and step == STEPS:
        return (LAST_ROWS,) + shape[1:]
    return shape


def epoch_step(xb: Any, yb: Any, weights: dict[str, Any],
               moments: dict[str, Any], variances: dict[str, Any],
               step: int) -> tuple[dict[str, Any], dict[str, Any],
                                   dict[str, Any], dict[str, Any]]:
    """Same operation ordering as historical _fit_shared_model_state_bytes."""
    import numpy as np
    if type(step) is not int or not (1 <= step <= STEPS):
        raise ValueError("one epoch allows only steps 1..22")
    if any(tuple(mapping) != PARAMETERS for mapping in (weights, moments, variances)):
        raise ValueError("six exact initialized trainable parameters and moments required")
    if tuple(xb.shape) != _expected_shape("batch_features", step) or tuple(yb.shape) != _expected_shape("batch_labels", step):
        raise ValueError("first-epoch minibatch shape drift")
    w1, b1, w2, b2, w3, b3 = (weights[k] for k in PARAMETERS)
    linear1 = xb @ w1 + b1
    h1 = np.tanh(linear1)
    linear2 = h1 @ w2 + b2
    h2 = np.tanh(linear2)
    logits = h2 @ w3 + b3
    probabilities = _sigmoid(logits)
    dlogits = (probabilities - yb) / float(len(xb))
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
        "w1": grad_w1, "b1": grad_b1, "w2": grad_w2,
        "b2": grad_b2, "w3": grad_w3, "b3": grad_b3,
    }
    stage = {
        "batch_features": xb, "batch_labels": yb,
        "first_linear": linear1, "first_tanh": h1,
        "second_linear": linear2, "second_tanh": h2,
        "logits": logits, "probabilities": probabilities,
    }
    updated, next_m, next_v = {}, {}, {}
    for key in PARAMETERS:
        stage["grad_" + key] = grads[key]
    for key in PARAMETERS:
        new_param, moment, variance = _adam_update(
            weights[key], moments[key], variances[key],
            grads[key], step, BYTE_LEARNING_RATE,
        )
        updated[key], next_m[key], next_v[key] = new_param, moment, variance
        stage["updated_" + key] = new_param
        stage["moment_" + key] = moment
        stage["variance_" + key] = variance
    if set(stage) != set(STAGES):
        raise RuntimeError("unexpected original phase2r epoch stage set")
    for key in STAGES:
        arr = np.asarray(stage[key])
        if arr.dtype != np.float32 or arr.shape != _expected_shape(key, step) or not np.isfinite(arr).all():
            raise RuntimeError(f"invalid historical epoch stage array {key}")
    return stage, updated, next_m, next_v


def emit_first_epoch(npz_path: Path) -> dict[str, Any]:
    """One and only one 5600-row synthetic first epoch."""
    import numpy as np
    if any(os.environ.get(v) != "1" for v in THREAD_VARS):
        raise ValueError("numeric thread limits must all be 1")
    dataset_seed = TRAINING_DATASET_BASE_SEEDS[0]
    model_seed = TRAINING_MODEL_BASE_SEEDS[0]
    fixture = load_phase2r_fixture()
    splits = build_shared_training_splits(
        fixture, difference=1, dataset_seed=dataset_seed,
    )
    if tuple(len(s) for s in splits) != _EXPECTED_SPLITS:
        raise ValueError("synthetic dataset sizes do not match original Phase 2G")
    split_sha = {
        name: hash_pair_split(split, split=name)
        for name, split in zip(("train", "validation", "test"), splits)
    }
    x_train, y_train = _samples_to_byte_arrays(splits[0])
    _samples_to_byte_arrays(splits[1])
    x_test, y_test = _samples_to_byte_arrays(splits[2])
    weights, rng = checkpoint_zero_seeded_initialization(model_seed)
    initial = observe_checkpoint_zero(tensors=weights, rng=rng)
    order = rng.permutation(len(x_train))
    if len(order) != 5600 or sorted(order.tolist()) != list(range(5600)):
        raise RuntimeError("first epoch original permutation invalid")
    post_rng = _sha(_canonical(rng.bit_generator.state))
    moments = {k: np.zeros_like(p) if k != "b3" else np.float32(0.0)
               for k, p in weights.items()}
    variances = {k: np.zeros_like(p) if k != "b3" else np.float32(0.0)
                 for k, p in weights.items()}
    all_tensors: dict[str, Any] = {}
    receipts, batch_receipts = {}, []
    for step in range(1, STEPS + 1):
        offset = (step - 1) * BATCH_SIZE
        selected = order[offset:offset + BATCH_SIZE]
        target = BATCH_SIZE if step < STEPS else LAST_ROWS
        if len(selected) != target:
            raise RuntimeError("wrong final smaller historical minibatch")
        xb, yb = x_train[selected], y_train[selected]
        original_weights, original_m, original_v = weights, moments, variances
        stage, weights, moments, variances = epoch_step(
            xb, yb, weights, moments, variances, step
        )
        if step <= 8:
            frozen, expected_weights, expected_m, expected_v = frozen_first_eight_batch(
                xb, yb, original_weights, original_m, original_v, step
            )
            for name in STAGES:
                if _array_receipt(stage[name]) != _array_receipt(frozen[name]):
                    raise RuntimeError(f"historical eight-step parity violated: s{step:02d}.{name}")
            for produced, expected in ((weights, expected_weights), (moments, expected_m), (variances, expected_v)):
                if any(_array_receipt(produced[k]) != _array_receipt(expected[k]) for k in PARAMETERS):
                    raise RuntimeError("original eight-step state carryover differs")
        batch_receipts.append({
            "step": step, "size": target,
            "indices_sha256": _index_hash(selected, scope="selected-batch"),
        })
        cell = {}
        for name in STAGES:
            all_tensors[f"s{step:02d}__{name}"] = stage[name]
            cell[name] = _array_receipt(stage[name])
        receipts[f"s{step:02d}"] = cell
    if len(batch_receipts) != STEPS or sum(x["size"] for x in batch_receipts) != 5600:
        raise RuntimeError("first epoch did not consume exactly all original training examples")

    # Preregistered SECONDARY synthetic diagnostic; no test samples are trained.
    w1, b1, w2, b2, w3, b3 = (weights[k] for k in PARAMETERS)
    probabilities = _sigmoid(
        np.tanh(np.tanh(x_test @ w1 + b1) @ w2 + b2) @ w3 + b3
    )
    if probabilities.shape != (TEST_ROWS,) or probabilities.dtype != np.float32:
        raise ValueError("wrong final synthetic test predictions")
    score = _auc_from_scores([int(v) for v in y_test.tolist()],
                             [float(v) for v in probabilities.tolist()])
    all_tensors["synthetic_test_probabilities"] = probabilities
    all_tensors["synthetic_test_labels"] = y_test
    with npz_path.open("xb") as file:
        np.savez(file, **all_tensors)
    runtime = stable_numpy_runtime_profile()
    record: dict[str, Any] = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": dataset_seed, "model_seed": model_seed,
        "dataset_sha256": split_sha,
        "initialization_sha256": initial["initialization_sha256"],
        "rng_before_permutation_sha256": initial["rng_state_sha256"],
        "rng_after_permutation_sha256": post_rng,
        "first_epoch_permutation_sha256": _index_hash(order, scope="entire-permutation"),
        "first_epoch_batch_info": batch_receipts,
        "steps_completed": STEPS, "training_examples_seen": 5600,
        "training_examples_per_epoch": 5600,
        "original_eight_step_math_parity_verified": True,
        "stages": receipts,
        "test_probabilities": _array_receipt(probabilities),
        "test_labels": _array_receipt(y_test),
        "test_auc": float(score),
        "test_advantage": float(_advantage(score)),
        "test_sample_count": TEST_ROWS,
        "runtime_profile": runtime,
        "runtime_profile_sha256": _sha(_canonical(runtime)),
        "one_epoch_completed": True,
        "historical_32_epoch_fit_performed": False,
        "phase2u_neural_trainings_performed": 0,
        "historic_phase2g_cause_established": False,
        "research_status": "N1_SYNTHETIC_ONE_EPOCH_NUMERICAL_DIAGNOSTIC_ONLY",
    }
    record["receipt_sha256"] = _sha(_canonical(record))
    return record


def _require_hex(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise ValueError(f"missing or invalid {label}")


def compare_first_epoch(h: dict[str, Any], n: dict[str, Any],
                        hp: Path, npz: Path) -> dict[str, Any]:
    """Recompute source-bound original 1,408 stage SHA and test-set AUC."""
    import numpy as np
    for core, source in (("Haswell", h), ("Nehalem", n)):
        if type(source) is not dict:
            raise ValueError("invalid original source object")
        body = dict(source)
        signed = body.pop("receipt_sha256", None)
        if signed != _sha(_canonical(body)):
            raise ValueError("original first-epoch receipt digest invalid")
        fixed = {
            "schema_version": 1, "protocol": PROTOCOL,
            "fixture_sha256": CURRICULUM_SHA256,
            "difference": 1, "replicate": 0,
            "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
            "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
            "steps_completed": STEPS, "training_examples_seen": 5600,
            "training_examples_per_epoch": 5600,
            "original_eight_step_math_parity_verified": True,
            "one_epoch_completed": True,
            "historical_32_epoch_fit_performed": False,
            "phase2u_neural_trainings_performed": 0,
            "historic_phase2g_cause_established": False,
            "test_sample_count": TEST_ROWS,
        }
        if any(source.get(k) != v for k, v in fixed.items()):
            raise ValueError("first epoch's preregistered scope changed")
        if type(source.get("source_commit")) is not str or re.fullmatch(r"[0-9a-f]{40}", source["source_commit"]) is None:
            raise ValueError("invalid source revision")
        for field in ("initialization_sha256", "rng_before_permutation_sha256",
                      "rng_after_permutation_sha256", "first_epoch_permutation_sha256"):
            _require_hex(source.get(field), field)
        if not isinstance(source.get("dataset_sha256"), dict) or set(source["dataset_sha256"]) != {"train", "validation", "test"}:
            raise ValueError("missing dataset split SHA values")
        for x in source["dataset_sha256"].values():
            _require_hex(x, "original dataset split SHA")
        profile = source.get("runtime_profile")
        if (not isinstance(profile, dict) or
            _sha(_canonical(profile)) != source.get("runtime_profile_sha256") or
            profile.get("python_version") != "3.12.14" or
            profile.get("numpy_version") != "2.5.3" or
            len(profile.get("blas_libraries", [])) != 1 or
            profile["blas_libraries"][0].get("internal_api") != "openblas" or
            profile["blas_libraries"][0].get("architecture") != core or
            profile["blas_libraries"][0].get("num_threads") != 1):
            raise ValueError("CPU/BLAS original backend not faithfully recorded")
        if type(source.get("first_epoch_batch_info")) is not list or len(source["first_epoch_batch_info"]) != STEPS:
            raise ValueError("missing or incomplete 22 minibatch source identities")
        for i, row in enumerate(source["first_epoch_batch_info"]):
            if row.get("step") != i+1 or row.get("size") != (BATCH_SIZE if i < STEPS-1 else LAST_ROWS):
                raise ValueError("first epoch batch geometry drift")
            _require_hex(row.get("indices_sha256"), "original minibatch index SHA")
        stages = source.get("stages")
        if (type(stages) is not dict or set(stages) != {f"s{i:02d}" for i in range(1, STEPS + 1)} or
            any(type(v) is not dict or set(v) != set(STAGES) for v in stages.values())):
            raise ValueError("missing full 22x32 original SHA grid")
        for x in ("test_probabilities","test_labels"):
            if not isinstance(source.get(x),dict):
                raise ValueError("missing synthetic test stage")
        auc = source.get("test_auc")
        adv = source.get("test_advantage")
        if (type(auc) is not float or not math.isfinite(auc) or not 0 <= auc <= 1 or
            type(adv) is not float or not math.isfinite(adv) or adv != _advantage(auc)):
            raise ValueError("invalid secondary original test AUC diagnostic")
    constraints = (
        "source_commit", "dataset_sha256", "fixture_sha256", "dataset_seed",
        "model_seed", "initialization_sha256",
        "rng_before_permutation_sha256", "rng_after_permutation_sha256",
        "first_epoch_permutation_sha256", "first_epoch_batch_info",
    )
    if any(h[k] != n[k] for k in constraints):
        raise ValueError("different original train/test input, initial weights or minibatch RNG")
    if _normalized(h["runtime_profile"]) != _normalized(n["runtime_profile"]):
        raise ValueError("CPU/BLAS drift beyond chosen OpenBLAS core")
    per_step = []
    probability_diffs = {}
    with np.load(hp, allow_pickle=False) as ha, np.load(npz, allow_pickle=False) as na:
        expected = {f"s{i:02d}__{stage}" for i in range(1, STEPS+1) for stage in STAGES}
        expected |= {"synthetic_test_probabilities", "synthetic_test_labels"}
        if set(ha.files) != expected or set(na.files) != expected:
            raise ValueError("missing / extra original epoch tensor bytes")
        for i in range(1, STEPS+1):
            stages = {}
            for name in STAGES:
                key = f"s{i:02d}__{name}"
                a, b = ha[key], na[key]
                target = _expected_shape(name, i)
                if (a.shape != target or b.shape != target or
                    a.dtype != np.float32 or b.dtype != np.float32):
                    raise ValueError("unexpected original epoch float32/last-batch geometry")
                if (_array_receipt(a) != h["stages"][f"s{i:02d}"][name] or
                    _array_receipt(b) != n["stages"][f"s{i:02d}"][name]):
                    raise ValueError("original shape-bound source tensor SHA does not match NPZ")
                num = int(np.count_nonzero(a.view(np.uint32) != b.view(np.uint32)))
                delta = np.abs(a.astype(np.float64)-b.astype(np.float64))
                stages[name] = {
                    "changed": num, "total": int(a.size),
                    "maximum_absolute_difference": float(delta.max()),
                    "mean_absolute_difference": float(delta.mean()),
                }
            if any(stages[x]["changed"] for x in ("batch_features", "batch_labels")):
                raise ValueError("synthetic training batch input bytes are different")
            by_group = {}
            for prefix in ("grad_", "updated_", "moment_", "variance_"):
                d = [stages[prefix + x] for x in PARAMETERS]
                by_group[prefix.removesuffix("_")] = {
                    "tensors_changed": sum(v["changed"] > 0 for v in d),
                    "elements_changed": sum(v["changed"] for v in d),
                    "max_abs_delta": max(v["maximum_absolute_difference"] for v in d),
                    "mean_abs_delta": sum(v["mean_absolute_difference"]*v["total"] for v in d)/sum(v["total"] for v in d),
                }
            per_step.append({"step":i,**by_group})
        labels = []
        preds = []
        for source, z in ((h,ha),(n,na)):
            pred=z["synthetic_test_probabilities"]
            label=z["synthetic_test_labels"]
            if pred.dtype!=np.float32 or label.dtype!=np.float32 or pred.shape!=(TEST_ROWS,) or label.shape!=(TEST_ROWS,):
                raise ValueError("non-float32 or wrong synthetic test geometry")
            if _array_receipt(pred)!=source["test_probabilities"] or _array_receipt(label)!=source["test_labels"]:
                raise ValueError("synthetic test output and original SHA mismatch")
            independent_auc=float(_auc_from_scores([int(y) for y in label.tolist()],[float(x) for x in pred.tolist()]))
            if independent_auc!=source["test_auc"] or _advantage(independent_auc)!=source["test_advantage"]:
                raise ValueError("synthetic test AUC does not recompute from original evidence")
            labels.append(label)
            preds.append(pred)
        if not np.array_equal(labels[0], labels[1]):
            raise ValueError("different synthetic fixed test labels")
        x, y = preds
        delta = np.abs(x.astype(np.float64)-y.astype(np.float64))
        probability_diffs = {
            "different_probability_values": int(np.count_nonzero(x.view(np.uint32)!=y.view(np.uint32))),
            "maximum_absolute_probability_difference": float(delta.max()),
            "mean_absolute_probability_difference": float(delta.mean()),
            "test_auc_by_kernel": {"Haswell":h["test_auc"],"Nehalem":n["test_auc"]},
            "test_advantage_by_kernel": {"Haswell":h["test_advantage"],"Nehalem":n["test_advantage"]},
            "signed_auc_difference": h["test_auc"]-n["test_auc"],
        }
    result = {
        "schema_version":1,"protocol":PROTOCOL,
        "source_commit":h["source_commit"],
        "scope":"ONE_EPOCH_N1_SYNTHETIC_NUMERICAL_CONTRAST_ONLY",
        "completed_steps":STEPS,"samples_seen":5600,
        "source_array_hashes_recomputed":2*STEPS*len(STAGES)+4,
        "per_step":per_step,
        "final_updated_parameter_element_difference":per_step[-1]["updated"]["elements_changed"],
        "final_updated_parameter_max_abs_delta":per_step[-1]["updated"]["max_abs_delta"],
        "test_output_comparison":probability_diffs,
        "original_receipt_sha256":{"Haswell":h["receipt_sha256"],"Nehalem":n["receipt_sha256"]},
        "original_npz_sha256":{"Haswell":_sha(hp.read_bytes()),"Nehalem":_sha(npz.read_bytes())},
        "historical_32_epoch_fit_performed":False,
        "phase2u_neural_trainings_performed":0,
        "historic_phase2g_cause_established":False,
        "scientific_status":"EXPLORATORY_NUMERICAL_REPRODUCIBILITY_ONLY",
    }
    result["report_sha256"] = _sha(_canonical(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", choices=("Haswell","Nehalem"))
    parser.add_argument("--npz",type=Path)
    parser.add_argument("--haswell-json",type=Path)
    parser.add_argument("--nehalem-json",type=Path)
    parser.add_argument("--haswell-npz",type=Path)
    parser.add_argument("--nehalem-npz",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.kernel:
        if args.npz is None or any((args.haswell_json,args.nehalem_json,args.haswell_npz,args.nehalem_npz)):
            parser.error("source emission needs --kernel and --npz")
        result = emit_first_epoch(args.npz)
    else:
        if args.npz is not None or not all((args.haswell_json,args.nehalem_json,args.haswell_npz,args.nehalem_npz)):
            parser.error("read-only comparison requires both original JSON + NPZ")
        result = compare_first_epoch(
            json.loads(args.haswell_json.read_text(encoding="utf-8")),
            json.loads(args.nehalem_json.read_text(encoding="utf-8")),
            args.haswell_npz,args.nehalem_npz
        )
    with args.output.open("x",encoding="utf-8") as out:
        json.dump(result,out,sort_keys=True,indent=2,allow_nan=False)
        out.write("\n")
    print(result.get("scientific_status"))


if __name__=="__main__":
    main()
