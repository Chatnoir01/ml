"""Read-only source-bound audit of two 32-epoch synthetic BLAS kernel models.

Verifies original GitHub JSON receipts, every NumPy float32 NPZ stage, every
stored epoch permutation, fixed synthetic test AUC, and numerical deltas.
NO model training is performed by this auditor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from .neural100 import BATCH_SIZE, _auc_from_scores, _advantage
from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from .phase2r_fixture import CURRICULUM_SHA256
from .phase2r_first_adam_microstep import PARAMETERS, PARAM_SHAPES, _normalized
from .phase2r_eight_adam_steps import _index_hash
from .phase2r_forward_only_probe import _array_receipt
from .phase2r_initialization_preflight import _canonical
from .phase2r_full32_twohosts import (
    PROTOCOL, REPLICATES, EPOCHS, BATCHES_PER_EPOCH, STEPS,
    EVALUATION_EPOCHS, TOTAL_PARAMETERS,
)

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
CORE_PAIR = ("Haswell", "Nehalem")
FINAL_STATES = tuple(f"{prefix}_{key}" for prefix in
                     ("weight", "moment", "variance") for key in PARAMETERS)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_sha(value: Any, label: str) -> None:
    if type(value) is not str or not _HEX64.fullmatch(value):
        raise ValueError(f"missing/malformed SHA: {label}")


def _check_original_source(source: dict[str, Any], core: str) -> None:
    if type(source) is not dict:
        raise ValueError("source receipt is not an object")
    signed = dict(source)
    seal = signed.pop("receipt_sha256", None)
    if seal != _sha(_canonical(signed)):
        raise ValueError("original source canonical SHA integrity failure")
    fixed = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "fixture_sha256": CURRICULUM_SHA256,
        "input_difference": 1,
        "replicate_count": 2,
        "epochs_per_replica": 32,
        "adam_steps_per_replica": 704,
        "original_model_training_runs": 0,
        "phase2u_neural_training_runs": 0,
        "synthetic_complete_fits_per_kernel": 2,
        "frozen_first_epoch_math_verified": True,
        "historical_phase2g_cause_established": False,
        "evaluation_epochs": list(EVALUATION_EPOCHS),
    }
    if any(source.get(k) != v for k, v in fixed.items()):
        raise ValueError("unregistered 32-epoch synthetic scientific protocol")
    if (type(source.get("source_commit")) is not str or
            not _HEX40.fullmatch(source["source_commit"])):
        raise ValueError("unverifiable source Git checkout")
    profile = source.get("runtime_profile")
    if (type(profile) is not dict or
            source.get("runtime_profile_sha256") != _sha(_canonical(profile)) or
            profile.get("python_version") != "3.12.14" or
            profile.get("numpy_version") != "2.5.3" or
            len(profile.get("blas_libraries", [])) != 1 or
            profile["blas_libraries"][0].get("internal_api") != "openblas" or
            profile["blas_libraries"][0].get("architecture") != core or
            profile["blas_libraries"][0].get("num_threads") != 1):
        raise ValueError("unregistered runtime or actual BLAS kernel")
    if type(source.get("replicas")) is not list or len(source["replicas"]) != len(REPLICATES):
        raise ValueError("missing two original seed receipts")
    for index, actual_index in enumerate(REPLICATES):
        cell = source["replicas"][index]
        if (cell.get("replicate") != actual_index or
                cell.get("dataset_seed") != TRAINING_DATASET_BASE_SEEDS[actual_index] or
                cell.get("model_seed") != TRAINING_MODEL_BASE_SEEDS[actual_index]):
            raise ValueError("wrong original fixed seed pair")
        if (type(cell.get("dataset_sha256")) is not dict or
                set(cell["dataset_sha256"]) != {"train", "validation", "test"}):
            raise ValueError("incomplete source split identity")
        for name, val in cell["dataset_sha256"].items():
            _require_sha(val, name + " split")
        for key in ("initialization_sha256", "rng_before_epoch1_sha256"):
            _require_sha(cell.get(key), key)
        if type(cell.get("epochs")) is not list or len(cell["epochs"]) != EPOCHS:
            raise ValueError("not exactly 32 original epochs")
        for epoch, row in enumerate(cell["epochs"], 1):
            if row.get("epoch") != epoch:
                raise ValueError("wrong epoch index")
            _require_sha(row.get("permutation_sha256"), "full epoch permutation")
            _require_sha(row.get("rng_after_permutation_sha256"), "original RNG state")
            perm = row.get("permutation_indices")
            if (type(perm) is not list or len(perm) != 5600 or
                    any(type(v) is not int for v in perm) or
                    sorted(perm) != list(range(5600)) or
                    _index_hash(perm, scope="entire-permutation") != row["permutation_sha256"]):
                raise ValueError("full source permutation not authentic to its SHA")
            batches = row.get("batches")
            if type(batches) is not list or len(batches) != BATCHES_PER_EPOCH:
                raise ValueError("incomplete 22 source minibatches")
            for j, batch in enumerate(batches):
                expected_step = (epoch-1)*BATCHES_PER_EPOCH + j + 1
                expected_size = BATCH_SIZE if j < BATCHES_PER_EPOCH-1 else 224
                if batch.get("step") != expected_step or batch.get("rows") != expected_size:
                    raise ValueError("historical original global Adam step or batch size drift")
                if batch.get("indices_sha256") != _index_hash(
                    perm[j*BATCH_SIZE:(j+1)*BATCH_SIZE], scope="selected-batch",
                ):
                    raise ValueError("minibatch digest does not match actual source indices")
            receipts = row.get("epoch_end_receipts")
            allowed = set(FINAL_STATES) | (
                {"test_probabilities", "test_labels"} if epoch in EVALUATION_EPOCHS
                else set()
            )
            if type(receipts) is not dict or set(receipts) != allowed:
                raise ValueError("wrong epoch-end original float32 inventory")
            if epoch in EVALUATION_EPOCHS:
                auc, advantage = row.get("test_auc"), row.get("test_advantage")
                if (type(auc) is not float or not math.isfinite(auc) or
                        not 0.0 <= auc <= 1.0 or
                        type(advantage) is not float or advantage != _advantage(auc)):
                    raise ValueError("invalid preregistered synthetic AUC receipt")
            elif "test_auc" in row or "test_advantage" in row:
                raise ValueError("unregistered synthetic test peeking at off-checkpoint epoch")


def _expected_keys() -> set[str]:
    keys = {
        f"r{rep}__e{epoch}__{field}"
        for rep in REPLICATES for epoch in range(1, EPOCHS+1)
        for field in FINAL_STATES
    }
    keys |= {
        f"r{rep}__e{epoch}__{field}"
        for rep in REPLICATES for epoch in EVALUATION_EPOCHS
        for field in ("test_probabilities","test_labels")
    }
    if len(keys) != 1176:
        raise RuntimeError("internal 32-epoch stage inventory changed")
    return keys


def compare_full32_original_receipts(
    haswell: dict[str, Any], nehalem: dict[str, Any],
    haswell_npz: Path, nehalem_npz: Path,
) -> dict[str, Any]:
    import numpy as np
    _check_original_source(haswell,"Haswell")
    _check_original_source(nehalem,"Nehalem")
    if haswell["source_commit"] != nehalem["source_commit"]:
        raise ValueError("same-host kernel subprocess source commit differs")
    if _normalized(haswell["runtime_profile"]) != _normalized(nehalem["runtime_profile"]):
        raise ValueError("same-host CPU/SIMD/BLAS profiles differ beyond selected core")
    for i, rep in enumerate(REPLICATES):
        h, n = haswell["replicas"][i], nehalem["replicas"][i]
        for field in ("replicate", "dataset_seed", "model_seed", "dataset_sha256",
                      "initialization_sha256", "rng_before_epoch1_sha256"):
            if h[field] != n[field]:
                raise ValueError("synthetic split or model initialization differs")
        for epoch in range(EPOCHS):
            for field in ("permutation_sha256", "permutation_indices",
                          "rng_after_permutation_sha256", "batches"):
                if h["epochs"][epoch][field] != n["epochs"][epoch][field]:
                    raise ValueError("original paired seeded minibatches differ")

    expected = _expected_keys()
    per_replica = []
    with np.load(haswell_npz,allow_pickle=False) as hs, \
         np.load(nehalem_npz,allow_pickle=False) as ns:
        if set(hs.files) != expected or set(ns.files) != expected:
            raise ValueError("missing or extra original NPZ source arrays")
        for index, rep in enumerate(REPLICATES):
            hc = haswell["replicas"][index]
            nc = nehalem["replicas"][index]
            epochs = []
            fixed_checkpoints = []
            for epoch in range(1, EPOCHS+1):
                hr, nr = hc["epochs"][epoch-1], nc["epochs"][epoch-1]
                model_vectors=[[],[]]
                parameter_bits=0
                max_delta=0.0
                moments_changed={"moment":0,"variance":0}
                for prefix in ("weight", "moment", "variance"):
                    for key in PARAMETERS:
                        name=f"{prefix}_{key}"
                        full=f"r{rep}__e{epoch}__{name}"
                        a,b=hs[full],ns[full]
                        if (a.dtype != np.float32 or b.dtype != np.float32 or
                                a.shape != PARAM_SHAPES[key] or b.shape != PARAM_SHAPES[key] or
                                not np.isfinite(a).all() or not np.isfinite(b).all()):
                            raise ValueError("wrong original model/Adam dtype, scalar or shape")
                        if (_array_receipt(a) != hr["epoch_end_receipts"][name] or
                                _array_receipt(b) != nr["epoch_end_receipts"][name]):
                            raise ValueError("original NPZ and recorded source stage SHA disagree")
                        changed=int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)))
                        if prefix=="weight":
                            parameter_bits+=changed
                            max_delta=max(max_delta,float(np.max(np.abs(a.astype(np.float64)-b.astype(np.float64)))))
                            model_vectors[0].append(a.astype(np.float64).reshape(-1))
                            model_vectors[1].append(b.astype(np.float64).reshape(-1))
                        else:
                            moments_changed[prefix]+=changed
                v1=np.concatenate(model_vectors[0]);v2=np.concatenate(model_vectors[1])
                if v1.size != TOTAL_PARAMETERS:
                    raise ValueError("wrong 1825-dimensional model vector")
                d=np.abs(v1-v2)
                current={
                    "epoch":epoch,"after_step":epoch*BATCHES_PER_EPOCH,
                    "bitwise_different_weights":parameter_bits,
                    "max_abs_weight_difference":max_delta,
                    "mean_abs_weight_difference":float(d.mean()),
                    "relative_l2_weight_difference":float(np.linalg.norm(v1-v2)/np.linalg.norm(v1)),
                    "moment_float_values_different":moments_changed["moment"],
                    "variance_float_values_different":moments_changed["variance"],
                }
                epochs.append(current)
                if epoch in EVALUATION_EPOCHS:
                    original_pred=[]; original_labels=[]
                    for src, archive in ((hr,hs),(nr,ns)):
                        pred=archive[f"r{rep}__e{epoch}__test_probabilities"]
                        label=archive[f"r{rep}__e{epoch}__test_labels"]
                        if (pred.dtype != np.float32 or label.dtype != np.float32 or
                                pred.shape != (1200,) or label.shape != (1200,) or
                                not np.isfinite(pred).all() or
                                not np.all((label==0)|(label==1))):
                            raise ValueError("wrong original test tensor or label geometry")
                        if (_array_receipt(pred)!=src["epoch_end_receipts"]["test_probabilities"] or
                                _array_receipt(label)!=src["epoch_end_receipts"]["test_labels"]):
                            raise ValueError("original fixed test stage SHA mismatch")
                        auc=float(_auc_from_scores(label.astype(int).tolist(),pred.astype(float).tolist()))
                        if auc != src["test_auc"] or float(_advantage(auc)) != src["test_advantage"]:
                            raise ValueError("independently recomputed tie-aware AUC differs")
                        original_pred.append(pred);original_labels.append(label)
                    if not np.array_equal(original_labels[0],original_labels[1]):
                        raise ValueError("test labels differ across numerical kernels")
                    a,b=original_pred
                    dif=np.abs(a.astype(np.float64)-b.astype(np.float64))
                    positive=np.where(original_labels[0]==1)[0]
                    negative=np.where(original_labels[0]==0)[0]
                    rel_a=np.sign(a[positive,None]-a[None,negative])
                    rel_b=np.sign(b[positive,None]-b[None,negative])
                    changed_rel=int(np.count_nonzero(rel_a!=rel_b))
                    fixed_checkpoints.append({
                        "epoch":epoch,
                        "auc_haswell":hr["test_auc"],
                        "auc_nehalem":nr["test_auc"],
                        "signed_auc_difference":hr["test_auc"]-nr["test_auc"],
                        "predicted_float32_values_different":int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),
                        "max_abs_prediction_difference":float(dif.max()),
                        "mean_abs_prediction_difference":float(dif.mean()),
                        "changed_positive_negative_rank_or_tie_pairs":changed_rel,
                    })
            per_replica.append({
                "replicate":rep,"dataset_seed":hc["dataset_seed"],"model_seed":hc["model_seed"],
                "per_epoch":epochs,
                "fixed_test_checkpoints":fixed_checkpoints,
            })
    report={
        "schema_version":1,"protocol":PROTOCOL,
        "source_commit":haswell["source_commit"],
        "kernel_pair":list(CORE_PAIR),
        "replicates":per_replica,
        "observed_runner_profile":haswell["runtime_profile"],
        "same_host_numerical_profile_comparable":True,
        "epochs_per_model":32,"adam_steps_per_model":STEPS,
        "source_array_digests_recomputed":2352,
        "fixed_evaluation_epochs":list(EVALUATION_EPOCHS),
        "source_receipts_sha256s":{"Haswell":haswell["receipt_sha256"],"Nehalem":nehalem["receipt_sha256"]},
        "source_npz_sha256s":{"Haswell":_sha(haswell_npz.read_bytes()),"Nehalem":_sha(nehalem_npz.read_bytes())},
        "synthetic_complete_model_fits":4,
        "original_phase2g_scientific_fits":0,
        "phase2u_prospective_neural_fits":0,
        "historical_phase2g_root_cause_established":False,
        "research_scope":"TWO_NEW_TO_PHASE2R_SEEDS_32_EPOCHS_SYNTHETIC_NUMERICAL_CONTROL_ONLY",
    }
    report["report_sha256"]=_sha(_canonical(report))
    return report


def main() -> None:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--haswell-json",type=Path,required=True)
    cli.add_argument("--nehalem-json",type=Path,required=True)
    cli.add_argument("--haswell-npz",type=Path,required=True)
    cli.add_argument("--nehalem-npz",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    a=cli.parse_args()
    inputs=(a.haswell_json,a.nehalem_json,a.haswell_npz,a.nehalem_npz,a.output)
    if len({p.resolve() for p in inputs})!=5:
        cli.error("all source and output paths must be different")
    result=compare_full32_original_receipts(
        json.loads(a.haswell_json.read_text(encoding="utf-8")),
        json.loads(a.nehalem_json.read_text(encoding="utf-8")),
        a.haswell_npz,a.nehalem_npz,
    )
    with a.output.open("x",encoding="utf-8") as out:
        json.dump(result,out,sort_keys=True,indent=2,allow_nan=False)
        out.write("\n")
    for row in result["replicates"]:
        for cp in row["fixed_test_checkpoints"]:
            if cp["epoch"] in (2,16,32):
                e=row["per_epoch"][cp["epoch"]-1]
                print("EPOCH",row["replicate"],cp["epoch"],
                      "BITWISE_WEIGHTS",e["bitwise_different_weights"],
                      "RELATIVE_L2",e["relative_l2_weight_difference"],
                      "AUC_DELTA",cp["signed_auc_difference"],
                      "RANK_TIE_CHANGES",cp["changed_positive_negative_rank_or_tie_pairs"])


if __name__=="__main__":
    main()
