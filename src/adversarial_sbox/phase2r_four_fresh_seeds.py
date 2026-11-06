"""Two original synthetic first epochs, FOUR FRESH registered seeds, and two BLAS cores.

Prospective fixed N=4 NEW seeds (replicates 2,3,4,5) numerical intervention. Exactly 44 historical Adam updates
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
from .phase2r_first_adam_microstep import _normalized as comparable_runtime
from .phase2r_eight_adam_steps import _index_hash
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import (
    THREAD_VARS, _canonical, checkpoint_zero_seeded_initialization,
    stable_numpy_runtime_profile,
)
from .phase2r_observation import observe_checkpoint_zero
from .phase2r_serialization import hash_pair_split

PROTOCOL = "phase2r_four_fresh_seeds_two_epochs_v1"
REPLICATES = (2, 3, 4, 5)
EPOCHS = 2
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


def emit_four_fresh_seed_epochs(tensors_path: Path) -> dict[str, Any]:
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
            "updated_weight_receipts": {},
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
                d: dict[str, Any] = {}
                for k in PARAMETERS:
                    key = f"r{r}__s{step:02d}__{k}"
                    arrays[key] = weights[k]
                    d[k] = _array_receipt(weights[k])
                record["updated_weight_receipts"][f"s{step:02d}"] = d
                epoch_receipt["batches"].append({
                    "step": step, "rows": target,
                    "indices_sha256": _index_hash(chosen, scope="selected-batch"),
                })
            predictions = _sigmoid_model(weights, x_test)
            if predictions.dtype != np.float32 or predictions.shape != (1200,):
                raise RuntimeError("invalid test-only output dtype or geometry")
            auc = float(_auc_from_scores(
                [int(x) for x in y_test.tolist()],
                [float(x) for x in predictions.tolist()],
            ))
            extras = {}
            for k in PARAMETERS:
                for prefix, tensor in (("moment", moments[k]), ("variance", variances[k])):
                    field = f"{prefix}_{k}"
                    arrays[f"r{r}__e{epoch}__{field}"] = tensor
                    extras[field] = _array_receipt(tensor)
            for name, tensor in (("test_probabilities", predictions), ("test_labels", y_test)):
                arrays[f"r{r}__e{epoch}__{name}"] = tensor
                extras[name] = _array_receipt(tensor)
            epoch_receipt["epoch_end_receipts"] = extras
            epoch_receipt["test_auc"] = auc
            epoch_receipt["test_advantage"] = float(_advantage(auc))
            record["epochs"].append(epoch_receipt)
        replicas.append(record)
    if len(arrays) != 1168:
        raise RuntimeError("four-new-seed, two-epoch tensor inventory drift")
    with tensors_path.open("xb") as file:
        np.savez(file, **arrays)
    runtime = stable_numpy_runtime_profile()
    source = {
        "schema_version": 1, "protocol": PROTOCOL,
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "fixture_sha256": CURRICULUM_SHA256,
        "input_difference": 1,
        "replicas": replicas,
        "replicate_count": 4,
        "epochs_per_replica": 2,
        "adam_steps_per_replica": 44,
        "original_model_training_runs": 0,
        "phase2u_neural_training_runs": 0,
        "frozen_first_epoch_math_verified": True,
        "runtime_profile": runtime,
        "runtime_profile_sha256": _sha(_canonical(runtime)),
        "scientific_verdict": "EXPLORATORY_FOUR_FRESH_SEEDS_TWO_EPOCHS_NUMERICAL_CONTROL_ONLY",
        "historical_phase2g_cause_established": False,
    }
    source["receipt_sha256"] = _sha(_canonical(source))
    return source


def _require_sha(text: Any, label: str) -> None:
    if type(text) is not str or not _HEX64.fullmatch(text):
        raise ValueError("invalid " + label)


def verify_four_fresh_seed_pair(
    haswell: dict[str, Any], nehalem: dict[str, Any],
    haswell_npz: Path, nehalem_npz: Path,
) -> dict[str, Any]:
    import numpy as np
    for name, r in (("Haswell", haswell), ("Nehalem", nehalem)):
        if type(r) is not dict:
            raise ValueError("malformed original receipt")
        signed = dict(r)
        digest = signed.pop("receipt_sha256", None)
        if digest != _sha(_canonical(signed)):
            raise ValueError("original source receipt SHA integrity mismatch")
        fixed = {
            "schema_version": 1, "protocol": PROTOCOL,
            "fixture_sha256": CURRICULUM_SHA256,
            "input_difference": 1, "replicate_count": 4,
            "epochs_per_replica": 2, "adam_steps_per_replica": 44,
            "original_model_training_runs": 0,
            "phase2u_neural_training_runs": 0,
            "frozen_first_epoch_math_verified": True,
            "historical_phase2g_cause_established": False,
        }
        if any(r.get(k) != v for k, v in fixed.items()):
            raise ValueError("not a preregistered original two-epoch research receipt")
        if type(r.get("source_commit")) is not str or not _HEX40.fullmatch(r["source_commit"]):
            raise ValueError("unverifiable source commit")
        profile = r.get("runtime_profile")
        if (type(profile) is not dict or
                r.get("runtime_profile_sha256") != _sha(_canonical(profile)) or
                profile.get("python_version") != "3.12.14" or
                profile.get("numpy_version") != "2.5.3" or
                len(profile.get("blas_libraries", [])) != 1 or
                profile["blas_libraries"][0].get("internal_api") != "openblas" or
                profile["blas_libraries"][0].get("architecture") != name or
                profile["blas_libraries"][0].get("num_threads") != 1):
            raise ValueError("runtime is not pinned or expected OpenBLAS kernel not selected")
        if type(r.get("replicas")) is not list or len(r["replicas"]) != 4:
            raise ValueError("missing four new preregistered seed replicas")
        for idx, cell in enumerate(r["replicas"]):
            fresh_rep = REPLICATES[idx]
            if (cell.get("replicate") != fresh_rep or
                    cell.get("dataset_seed") != TRAINING_DATASET_BASE_SEEDS[fresh_rep] or
                    cell.get("model_seed") != TRAINING_MODEL_BASE_SEEDS[fresh_rep] or
                    type(cell.get("epochs")) is not list or len(cell["epochs"]) != 2):
                raise ValueError("wrong registered replica seed and epoch")
            if type(cell.get("dataset_sha256")) is not dict or set(cell["dataset_sha256"]) != {"train","validation","test"}:
                raise ValueError("incomplete dataset split hashes")
            for val in cell["dataset_sha256"].values():
                _require_sha(val, "dataset SHA")
            _require_sha(cell.get("initialization_sha256"), "initial model SHA")
            _require_sha(cell.get("rng_before_epoch1_sha256"), "initial RNG SHA")
            if (type(cell.get("updated_weight_receipts")) is not dict or
                    set(cell["updated_weight_receipts"]) != {f"s{s:02d}" for s in range(1, 45)}):
                raise ValueError("missing one or more weight-update stage receipts")
            for weights in cell["updated_weight_receipts"].values():
                if type(weights) is not dict or set(weights) != set(PARAMETERS):
                    raise ValueError("missing weight tensors in original stage receipts")
            for e, part in enumerate(cell["epochs"], 1):
                if part.get("epoch") != e:
                    raise ValueError("missing original epoch identity")
                _require_sha(part.get("permutation_sha256"), "full permutation SHA")
                perm = part.get("permutation_indices")
                if (type(perm) is not list or len(perm) != 5600 or
                        any(type(i) is not int for i in perm) or
                        sorted(perm) != list(range(5600)) or
                        _index_hash(perm, scope="entire-permutation") != part["permutation_sha256"]):
                    raise ValueError("missing or invalid complete original permutation indices")
                _require_sha(part.get("rng_after_permutation_sha256"), "RNG after permutation")
                batches = part.get("batches")
                if type(batches) is not list or len(batches) != 22:
                    raise ValueError("incomplete 22 original minibatches")
                for j, batch in enumerate(batches):
                    if (batch.get("step") != (e-1)*22+j+1 or
                            batch.get("rows") != (256 if j<21 else 224)):
                        raise ValueError("original minibatch order/size drift")
                    _require_sha(batch.get("indices_sha256"), "source minibatch indices")
                    if _index_hash(perm[j*BATCH_SIZE:(j+1)*BATCH_SIZE],
                                   scope="selected-batch") != batch["indices_sha256"]:
                        raise ValueError("source mini-batch indices do not match full permutation")
                extra = part.get("epoch_end_receipts")
                if type(extra) is not dict or set(extra) != set(_EPOCH_END):
                    raise ValueError("missing epoch end moments, variance or test prediction SHA")
                auc, adv = part.get("test_auc"), part.get("test_advantage")
                if (type(auc) is not float or not math.isfinite(auc) or
                        not 0 <= auc <= 1 or
                        type(adv) is not float or adv != _advantage(auc)):
                    raise ValueError("unregistered or non-finite synthetic test AUC")
    if haswell["source_commit"] != nehalem["source_commit"]:
        raise ValueError("different source commits")
    if comparable_runtime(haswell["runtime_profile"]) != comparable_runtime(nehalem["runtime_profile"]):
        raise ValueError("host CPU/BLAS drift beyond selected core")
    for index, r in enumerate(REPLICATES):
        a, b = haswell["replicas"][index], nehalem["replicas"][index]
        for field in ("replicate", "dataset_seed", "model_seed", "dataset_sha256",
                      "initialization_sha256", "rng_before_epoch1_sha256"):
            if a[field] != b[field]:
                raise ValueError("source seed/dataset/initialization differs between kernels")
        for e in range(EPOCHS):
            for field in ("permutation_sha256", "permutation_indices", "rng_after_permutation_sha256", "batches"):
                if a["epochs"][e][field] != b["epochs"][e][field]:
                    raise ValueError("different original per-epoch index permutation or RNG state")
    expected_keys = {
        f"r{rep}__s{s:02d}__{key}"
        for rep in REPLICATES for s in range(1, STEPS+1) for key in PARAMETERS
    } | {
        f"r{rep}__e{e}__{name}"
        for rep in REPLICATES for e in range(1, EPOCHS+1) for name in _EPOCH_END
    }
    if len(expected_keys) != 1168:
        raise RuntimeError("internal source tensor inventory changed")
    per_replica = []
    with np.load(haswell_npz, allow_pickle=False) as hh, np.load(nehalem_npz, allow_pickle=False) as nn:
        if set(hh.files) != expected_keys or set(nn.files) != expected_keys:
            raise ValueError("missing/extra exact original tensor source bytes")
        for index, rep in enumerate(REPLICATES):
            h, n = haswell["replicas"][index], nehalem["replicas"][index]
            step_stats: list[dict[str, Any]] = []
            for step in range(1, STEPS+1):
                vectors = [[], []]
                diff_count = 0
                max_abs = 0.0
                for key in PARAMETERS:
                    field = f"r{rep}__s{step:02d}__{key}"
                    a, b = hh[field], nn[field]
                    if (a.shape != PARAM_SHAPES[key] or b.shape != PARAM_SHAPES[key] or
                            a.dtype != np.float32 or b.dtype != np.float32 or
                            not np.isfinite(a).all() or not np.isfinite(b).all()):
                        raise ValueError("wrong exact float32 scalar or parameter shape")
                    if (_array_receipt(a) != h["updated_weight_receipts"][f"s{step:02d}"][key] or
                            _array_receipt(b) != n["updated_weight_receipts"][f"s{step:02d}"][key]):
                        raise ValueError("original stage weight SHA vs NPZ bytes mismatch")
                    diff_count += int(np.count_nonzero(a.view(np.uint32) != b.view(np.uint32)))
                    delta = np.abs(a.astype(np.float64)-b.astype(np.float64))
                    max_abs = max(max_abs, float(delta.max()))
                    vectors[0].append(a.astype(np.float64).reshape(-1))
                    vectors[1].append(b.astype(np.float64).reshape(-1))
                v1 = np.concatenate(vectors[0])
                v2 = np.concatenate(vectors[1])
                if v1.size != TOTAL_PARAMETERS:
                    raise ValueError("full model vector length drift")
                d = np.abs(v1-v2)
                step_stats.append({
                    "step":step, "different_parameter_values":diff_count,
                    "max_abs_weight_delta":max_abs,
                    "mean_abs_weight_delta":float(d.mean()),
                    "relative_parameter_l2_delta":float(np.linalg.norm(v1-v2)/np.linalg.norm(v1)),
                })
            epoch_stats = []
            for epoch in (1, 2):
                h_e, n_e = h["epochs"][epoch-1], n["epochs"][epoch-1]
                moments_by_kernel = {}
                for prefix in ("moment","variance"):
                    changed = 0
                    for p in PARAMETERS:
                        field_name = f"{prefix}_{p}"
                        key=f"r{rep}__e{epoch}__{field_name}"
                        a,b=hh[key],nn[key]
                        if (a.shape != PARAM_SHAPES[p] or b.shape != PARAM_SHAPES[p]
                                or a.dtype != np.float32 or b.dtype != np.float32):
                            raise ValueError("wrong original Adam state shape")
                        if (_array_receipt(a) != h_e["epoch_end_receipts"][field_name] or
                                _array_receipt(b) != n_e["epoch_end_receipts"][field_name]):
                            raise ValueError("original epoch-end moment or variance SHA invalid")
                        changed += int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)))
                    moments_by_kernel[prefix+"_different_values"]=changed
                labels=[]
                predictions=[]
                for source, stored, item in ((h_e,hh,"Haswell"),(n_e,nn,"Nehalem")):
                    p=stored[f"r{rep}__e{epoch}__test_probabilities"]
                    y=stored[f"r{rep}__e{epoch}__test_labels"]
                    if (p.dtype != np.float32 or y.dtype != np.float32 or
                            p.shape != (1200,) or y.shape != (1200,) or
                            not np.isfinite(p).all()):
                        raise ValueError("test prediction/label dtype or shape wrong")
                    if (_array_receipt(p) != source["epoch_end_receipts"]["test_probabilities"] or
                            _array_receipt(y) != source["epoch_end_receipts"]["test_labels"]):
                        raise ValueError("source epoch-end test arrays SHA invalid")
                    if not np.all((y == 0) | (y == 1)):
                        raise ValueError("synthetic labels are not binary")
                    original_auc=float(_auc_from_scores([int(v) for v in y.tolist()],
                                                        [float(v) for v in p.tolist()]))
                    if original_auc != source["test_auc"] or _advantage(original_auc) != source["test_advantage"]:
                        raise ValueError("synthetic AUC cannot be independently recomputed")
                    labels.append(y)
                    predictions.append(p)
                if not np.array_equal(labels[0],labels[1]):
                    raise ValueError("different paired synthetic test labels")
                d=np.abs(predictions[0].astype(np.float64)-predictions[1].astype(np.float64))
                epoch_stats.append({
                    "epoch":epoch, "after_step":epoch*22,
                    **moments_by_kernel,
                    "test_auc_by_kernel":{"Haswell":h_e["test_auc"],"Nehalem":n_e["test_auc"]},
                    "auc_difference":h_e["test_auc"]-n_e["test_auc"],
                    "test_probability_bit_differences":int(np.count_nonzero(
                        predictions[0].view(np.uint32)!=predictions[1].view(np.uint32))),
                    "max_abs_test_probability_delta":float(d.max()),
                    "mean_abs_test_probability_delta":float(d.mean()),
                })
            per_replica.append({
                "replicate":rep, "dataset_seed":h["dataset_seed"],
                "model_seed":h["model_seed"],
                "per_step":step_stats, "epoch_checkpoints":epoch_stats,
            })
    result={
        "schema_version":1, "protocol":PROTOCOL,
        "source_commit":haswell["source_commit"],
        "scope":"TWO_SEEDS_TWO_EPOCHS_SYNTHETIC_ONLY",
        "replicates":per_replica,
        "epochs_per_replica":2,"steps_per_replica":44,
        "original_stage_sha256s_recomputed":2336,
        "original_receipt_sha256s":{"Haswell":haswell["receipt_sha256"],
                                    "Nehalem":nehalem["receipt_sha256"]},
        "original_npz_sha256s":{"Haswell":_sha(haswell_npz.read_bytes()),
                                "Nehalem":_sha(nehalem_npz.read_bytes())},
        "historical_phase2g_cause_proven":False,
        "phase2u_trainings":0,
        "scientific_verdict":"EXPLORATORY_SYNTHETIC_COMPUTATIONAL_CONTROL_ONLY",
    }
    result["report_sha256"]=_sha(_canonical(result))
    return result


def main() -> None:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--kernel",choices=("Haswell","Nehalem"))
    cli.add_argument("--npz",type=Path)
    cli.add_argument("--haswell-json",type=Path)
    cli.add_argument("--nehalem-json",type=Path)
    cli.add_argument("--haswell-npz",type=Path)
    cli.add_argument("--nehalem-npz",type=Path)
    cli.add_argument("--output",type=Path,required=True)
    a=cli.parse_args()
    if a.kernel:
        if a.npz is None or any((a.haswell_json,a.nehalem_json,a.haswell_npz,a.nehalem_npz)):
            cli.error("emit requires --kernel and --npz only")
        result=emit_four_fresh_seed_epochs(a.npz)
    else:
        if a.npz is not None or not all((a.haswell_json,a.nehalem_json,a.haswell_npz,a.nehalem_npz)):
            cli.error("compare requires both original kernel receipts and tensors")
        result=verify_four_fresh_seed_pair(
            json.loads(a.haswell_json.read_text(encoding="utf-8")),
            json.loads(a.nehalem_json.read_text(encoding="utf-8")),
            a.haswell_npz,a.nehalem_npz,
        )
    with a.output.open("x",encoding="utf-8") as file:
        json.dump(result,file,sort_keys=True,indent=2,allow_nan=False)
        file.write("\n")
    print(result.get("scientific_verdict"))

if __name__=="__main__":
    main()
