"""Synthetic-only 32-epoch CI tests, no historical/Phase2U source data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

np=pytest.importorskip("numpy",reason="scientific optional NumPy dependency")

from adversarial_sbox.phase2r_full32_twohosts import (
    PROTOCOL,REPLICATES,EPOCHS,STEPS,EVALUATION_EPOCHS,
    bounded_historical_update,
)
from adversarial_sbox.phase2r_full32_audit import compare_full32_original_receipts
from adversarial_sbox.phase2r_first_epoch import epoch_step as frozen_first_epoch
from adversarial_sbox.phase2r_four_fresh_seeds import bounded_historical_update as frozen_two_epoch_step
from adversarial_sbox.phase2r_first_adam_microstep import PARAMETERS,PARAM_SHAPES
from adversarial_sbox.phase2r_forward_only_probe import _array_receipt
from adversarial_sbox.phase2r_initialization_preflight import _canonical
from adversarial_sbox.phase2r_eight_adam_steps import _index_hash
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS,TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.neural100 import _auc_from_scores,_advantage


def _sha(v):
    return hashlib.sha256(str(v).encode()).hexdigest()


def _seal(r):
    r.pop("receipt_sha256",None)
    r["receipt_sha256"]=hashlib.sha256(_canonical(r)).hexdigest()


def _profile(core):
    return {
        "schema_version":1,"python_version":"3.12.14","numpy_version":"2.5.3",
        "os":"Linux","architecture":"x86_64","simd_available":["AVX2"],
        "simd_baseline":["SSE2"],"simd_dispatch":["AVX2"],
        "blas_libraries":[{"user_api":"blas","internal_api":"openblas",
         "architecture":core,"version":"0.3.34.106.0",
         "threading_layer":"pthreads","num_threads":1}],
    }


def _fake_pair(tmp_path, changed=None):
    raw={}
    for rep in REPLICATES:
        for epoch in range(1,EPOCHS+1):
            for prefix in ("weight","moment","variance"):
                for p in PARAMETERS:
                    raw[f"r{rep}__e{epoch}__{prefix}_{p}"]=np.full(
                        PARAM_SHAPES[p], 0.2 if prefix=="weight" else 0.01,dtype=np.float32
                    )
            if epoch in EVALUATION_EPOCHS:
                raw[f"r{rep}__e{epoch}__test_labels"]=(np.arange(1200)%2).astype(np.float32)
                raw[f"r{rep}__e{epoch}__test_probabilities"]=np.linspace(.2,.8,1200,dtype=np.float32)
    changed_raw={k:v.copy() for k,v in raw.items()}
    if changed is not None:
        changed_raw[changed].flat[0]=np.float32(0.5)
    hp,nn=tmp_path/"haswell.npz",tmp_path/"nehalem.npz"
    np.savez(hp,**raw);np.savez(nn,**changed_raw)
    def receipt(core,data):
        cells=[]
        for rep in REPLICATES:
            epochs=[]
            for epoch in range(1,EPOCHS+1):
                perm=list(range(5600))
                original={
                    "epoch":epoch,
                    "permutation_sha256":_index_hash(perm,scope="entire-permutation"),
                    "permutation_indices":perm,
                    "rng_after_permutation_sha256":_sha(f"rng-{rep}-{epoch}"),
                    "batches":[{
                        "step":(epoch-1)*22+j+1,
                        "rows":256 if j<21 else 224,
                        "indices_sha256":_index_hash(perm[j*256:(j+1)*256],scope="selected-batch")
                    } for j in range(22)],
                    "epoch_end_receipts":{
                        f"{prefix}_{p}":_array_receipt(data[f"r{rep}__e{epoch}__{prefix}_{p}"])
                        for prefix in ("weight","moment","variance") for p in PARAMETERS
                    },
                }
                if epoch in EVALUATION_EPOCHS:
                    y=data[f"r{rep}__e{epoch}__test_labels"]
                    z=data[f"r{rep}__e{epoch}__test_probabilities"]
                    auc=float(_auc_from_scores(y.astype(int).tolist(),z.astype(float).tolist()))
                    original["epoch_end_receipts"]["test_probabilities"]=_array_receipt(z)
                    original["epoch_end_receipts"]["test_labels"]=_array_receipt(y)
                    original["test_auc"]=auc
                    original["test_advantage"]=float(_advantage(auc))
                epochs.append(original)
            cells.append({
                "replicate":rep,
                "dataset_seed":TRAINING_DATASET_BASE_SEEDS[rep],
                "model_seed":TRAINING_MODEL_BASE_SEEDS[rep],
                "dataset_sha256":{k:_sha(f"{rep}:{k}") for k in ("train","validation","test")},
                "initialization_sha256":_sha("init"+str(rep)),
                "rng_before_epoch1_sha256":_sha("rng-init"+str(rep)),
                "epochs":epochs,
            })
        profile=_profile(core)
        d={
            "schema_version":1,"protocol":PROTOCOL,"source_commit":"a"*40,
            "fixture_sha256":CURRICULUM_SHA256,"input_difference":1,
            "replicas":cells,"replicate_count":2,"epochs_per_replica":32,
            "adam_steps_per_replica":704,"original_model_training_runs":0,
            "phase2u_neural_training_runs":0,"synthetic_complete_fits_per_kernel":2,
            "frozen_first_epoch_math_verified":True,
            "runtime_profile":profile,
            "runtime_profile_sha256":hashlib.sha256(_canonical(profile)).hexdigest(),
            "evaluation_epochs":list(EVALUATION_EPOCHS),
            "historical_phase2g_cause_established":False,
            "scientific_verdict":"SYNTHETIC_32_EPOCH_NUMERICAL_CONTROL_NOT_CRYPTOGRAPHIC_VERDICT",
        }
        _seal(d)
        return d
    return receipt("Haswell",raw),receipt("Nehalem",changed_raw),hp,nn


def _model(seed=1900):
    rng=np.random.default_rng(seed)
    weights={
        "w1":rng.normal(0,.1,(12,48)).astype(np.float32),
        "b1":np.zeros(48,np.float32),
        "w2":rng.normal(0,.1,(48,24)).astype(np.float32),
        "b2":np.zeros(24,np.float32),
        "w3":rng.normal(0,.1,24).astype(np.float32),
        "b3":np.float32(0),
    }
    m={k:np.zeros_like(v) if k!="b3" else np.float32(0) for k,v in weights.items()}
    v={k:np.zeros_like(v) if k!="b3" else np.float32(0) for k,v in weights.items()}
    return rng,weights,m,v


def test_epoch1_and_epoch2_exact_math_parity_to_frozen_separate_sources():
    rng,w,m,v=_model()
    for step in (1,22,23,44):
        n=224 if step%22==0 else 256
        x=rng.normal(size=(n,12)).astype(np.float32)
        y=rng.integers(0,2,n).astype(np.float32)
        actual,aw,am,av=bounded_historical_update(x,y,w,m,v,step)
        ref,rw,rm,rv=(frozen_first_epoch(x,y,w,m,v,step) if step<=22
                      else frozen_two_epoch_step(x,y,w,m,v,step))
        assert {k:_array_receipt(value) for k,value in actual.items()}=={
            k:_array_receipt(value) for k,value in ref.items()
        }
        for left,right in ((aw,rw),(am,rm),(av,rv)):
            assert all(_array_receipt(left[k])==_array_receipt(right[k]) for k in PARAMETERS)
        w,m,v=aw,am,av


def test_exact_seven_hundred_four_updates_and_stop_afterward():
    rng,w,m,v=_model()
    x=rng.normal(size=(224,12)).astype(np.float32)
    y=rng.integers(0,2,224).astype(np.float32)
    last,w,m,v=bounded_historical_update(x,y,w,m,v,704)
    assert last["batch_features"].shape==(224,12)
    assert len(last)==32
    with pytest.raises(ValueError,match="outside"):
        bounded_historical_update(x,y,w,m,v,705)


def test_original_npz_exact_2352_stage_sha_and_six_test_endpoints(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    z=compare_full32_original_receipts(h,n,hp,npz)
    assert z["source_array_digests_recomputed"]==2352
    assert z["epochs_per_model"]==32
    assert z["adam_steps_per_model"]==704
    assert [x["replicate"] for x in z["replicates"]]==[6,7]
    assert all(len(x["per_epoch"])==32 for x in z["replicates"])
    assert all(len(x["fixed_test_checkpoints"])==6 for x in z["replicates"])
    assert all(x["fixed_test_checkpoints"][-1]["signed_auc_difference"]==0.0 for x in z["replicates"])
    assert z["phase2u_prospective_neural_fits"]==0


def test_changed_epoch32_model_byte_is_counted_and_not_invented_in_epoch1(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path,changed="r7__e32__weight_w1")
    z=compare_full32_original_receipts(h,n,hp,npz)
    assert z["replicates"][0]["per_epoch"][-1]["bitwise_different_weights"]==0
    assert z["replicates"][1]["per_epoch"][-1]["bitwise_different_weights"]==1
    assert z["replicates"][1]["per_epoch"][0]["bitwise_different_weights"]==0


def test_wrong_original_permutation_content_fails_closed(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][0]["epochs"][20]["permutation_indices"][30]=5600
    _seal(n)
    with pytest.raises(ValueError,match="permutation"):
        compare_full32_original_receipts(h,n,hp,npz)


def test_changed_source_tensor_without_updated_receipt_fails_closed(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    with np.load(npz,allow_pickle=False) as source:
        vals={key:source[key] for key in source.files}
    vals["r6__e32__moment_w3"].flat[0]=np.float32(.12)
    np.savez(npz,**vals)
    with pytest.raises(ValueError,match="NPZ and recorded source stage SHA"):
        compare_full32_original_receipts(h,n,hp,npz)


def test_new_seed_list_and_runtime_drift_are_rejected(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][0]["model_seed"]=786073
    _seal(n)
    with pytest.raises(ValueError,match="fixed seed"):
        compare_full32_original_receipts(h,n,hp,npz)
    h,n,hp,npz=_fake_pair(tmp_path)
    n["runtime_profile"]["simd_available"].append("AVX512F")
    n["runtime_profile_sha256"]=hashlib.sha256(_canonical(n["runtime_profile"])).hexdigest()
    _seal(n)
    with pytest.raises(ValueError,match="CPU/SIMD/BLAS"):
        compare_full32_original_receipts(h,n,hp,npz)


def test_off_checkpoint_synthetic_auc_peeking_rejected(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][1]["epochs"][2]["test_auc"]=0.5
    _seal(n)
    with pytest.raises(ValueError,match="test peeking"):
        compare_full32_original_receipts(h,n,hp,npz)
