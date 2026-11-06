"""No-Phase2U synthetic regressions for the bounded four NEW seed/two-epoch study."""
from __future__ import annotations

import hashlib
from unittest.mock import patch

import pytest
np = pytest.importorskip("numpy", reason="optional NumPy numerical research tests")

from adversarial_sbox.datasets import PairSample
from adversarial_sbox.neural100 import _auc_from_scores, _advantage
from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2r_first_adam_microstep import PARAMETERS, PARAM_SHAPES
from adversarial_sbox.phase2r_first_epoch import epoch_step
from adversarial_sbox.phase2r_eight_adam_steps import _index_hash
from adversarial_sbox.phase2r_forward_only_probe import _array_receipt
from adversarial_sbox.phase2r_initialization_preflight import _canonical
from adversarial_sbox.phase2r_four_fresh_seeds import (
    PROTOCOL, STEPS, TOTAL_PARAMETERS, bounded_historical_update,
    emit_four_fresh_seed_epochs, verify_four_fresh_seed_pair,
)


def _sha(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def _seal(r):
    r.pop("receipt_sha256",None)
    r["receipt_sha256"]=hashlib.sha256(_canonical(r)).hexdigest()


def _profile(core):
    return {
        "schema_version":1,"python_version":"3.12.14","numpy_version":"2.5.3",
        "os":"Linux","architecture":"x86_64",
        "simd_available":["AVX2"],"simd_baseline":["SSE2"],"simd_dispatch":["AVX2"],
        "blas_libraries":[{
            "user_api":"blas","internal_api":"openblas","version":"0.3.34.106.0",
            "threading_layer":"pthreads","architecture":core,"num_threads":1
        }]
    }


def _fake_pair(tmp_path, *, changed=None):
    source_arrays={}
    changed_arrays={}
    for r in (2,3,4,5):
        for step in range(1,45):
            for p in PARAMETERS:
                key=f"r{r}__s{step:02d}__{p}"
                source_arrays[key]=np.full(PARAM_SHAPES[p],.125,dtype=np.float32)
        for epoch in (1,2):
            for prefix in ("moment","variance"):
                for p in PARAMETERS:
                    source_arrays[f"r{r}__e{epoch}__{prefix}_{p}"]=np.full(
                        PARAM_SHAPES[p],.0125,dtype=np.float32,
                    )
            source_arrays[f"r{r}__e{epoch}__test_probabilities"]=np.linspace(
                .2,.8,1200,dtype=np.float32
            )
            source_arrays[f"r{r}__e{epoch}__test_labels"]=(
                np.arange(1200)%2).astype(np.float32)
    changed_arrays={k:v.copy() for k,v in source_arrays.items()}
    if changed:
        changed_arrays[changed].flat[0]=np.float32(.5)
    hfile,nfile=tmp_path/"haswell.npz",tmp_path/"nehalem.npz"
    np.savez(hfile,**source_arrays)
    np.savez(nfile,**changed_arrays)

    def receipt(core, data):
        reps=[]
        for rep in (2,3,4,5):
            updated={}
            epoch_list=[]
            for step in range(1,45):
                updated[f"s{step:02d}"]={
                    p:_array_receipt(data[f"r{rep}__s{step:02d}__{p}"]) for p in PARAMETERS
                }
            for e in (1,2):
                permutation=list(range(5600))
                extras={}
                for key in [*(f"moment_{p}" for p in PARAMETERS),
                            *(f"variance_{p}" for p in PARAMETERS),
                            "test_probabilities","test_labels"]:
                    extras[key]=_array_receipt(data[f"r{rep}__e{e}__{key}"])
                y=data[f"r{rep}__e{e}__test_labels"]
                x=data[f"r{rep}__e{e}__test_probabilities"]
                auc=float(_auc_from_scores([int(z) for z in y.tolist()],
                                            [float(z) for z in x.tolist()]))
                epoch_list.append({
                    "epoch":e,
                    "permutation_sha256":_index_hash(permutation,scope="entire-permutation"),
                    "permutation_indices":permutation,
                    "rng_after_permutation_sha256":_sha(f"rng-{e}"),
                    "batches":[{
                        "step":(e-1)*22+j+1,
                        "rows":256 if j<21 else 224,
                        "indices_sha256":_index_hash(permutation[j*256:(j+1)*256],
                                                     scope="selected-batch")
                    } for j in range(22)],
                    "epoch_end_receipts":extras,
                    "test_auc":auc,"test_advantage":float(_advantage(auc)),
                })
            reps.append({
                "replicate":rep,
                "dataset_seed":TRAINING_DATASET_BASE_SEEDS[rep],
                "model_seed":TRAINING_MODEL_BASE_SEEDS[rep],
                "dataset_sha256":{k:_sha(k+str(rep)) for k in ("train","validation","test")},
                "initialization_sha256":_sha(f"init{rep}"),
                "rng_before_epoch1_sha256":_sha(f"rng{rep}"),
                "epochs":epoch_list,
                "updated_weight_receipts":updated,
            })
        profile=_profile(core)
        r={
            "schema_version":1,"protocol":PROTOCOL,"source_commit":"a"*40,
            "fixture_sha256":CURRICULUM_SHA256,"input_difference":1,
            "replicas":reps,"replicate_count":4,"epochs_per_replica":2,
            "adam_steps_per_replica":44,"original_model_training_runs":0,
            "phase2u_neural_training_runs":0,"frozen_first_epoch_math_verified":True,
            "runtime_profile":profile,
            "runtime_profile_sha256":hashlib.sha256(_canonical(profile)).hexdigest(),
            "scientific_verdict":"EXPLORATORY_FOUR_FRESH_SEEDS_TWO_EPOCHS_NUMERICAL_CONTROL_ONLY",
            "historical_phase2g_cause_established":False,
        }
        _seal(r)
        return r
    return receipt("Haswell",source_arrays),receipt("Nehalem",changed_arrays),hfile,nfile


def test_step1_and_step22_are_bit_exact_against_frozen_original_epoch():
    rng=np.random.default_rng(1001)
    weights={
        "w1":rng.normal(0,.1,(12,48)).astype(np.float32),
        "b1":np.zeros(48,np.float32),
        "w2":rng.normal(0,.1,(48,24)).astype(np.float32),
        "b2":np.zeros(24,np.float32),
        "w3":rng.normal(0,.1,24).astype(np.float32),
        "b3":np.float32(0),
    }
    moments={k:np.zeros_like(v) if k!="b3" else np.float32(0) for k,v in weights.items()}
    variances={k:np.zeros_like(v) if k!="b3" else np.float32(0) for k,v in weights.items()}
    for step, rows in ((1,256),(22,224)):
        x=rng.normal(size=(rows,12)).astype(np.float32)
        y=rng.integers(0,2,size=rows).astype(np.float32)
        actual,w1,m1,v1=bounded_historical_update(x,y,weights,moments,variances,step)
        expected,w2,m2,v2=epoch_step(x,y,weights,moments,variances,step)
        assert {_k:_array_receipt(value) for _k,value in actual.items()} == {
            _k:_array_receipt(value) for _k,value in expected.items()
        }
        assert all(_array_receipt(w1[p])==_array_receipt(w2[p]) for p in PARAMETERS)
        assert all(_array_receipt(m1[p])==_array_receipt(m2[p]) for p in PARAMETERS)
        assert all(_array_receipt(v1[p])==_array_receipt(v2[p]) for p in PARAMETERS)


def test_second_epoch_preserves_global_adam_step_and_final_small_batch():
    rng=np.random.default_rng(1002)
    x=rng.normal(size=(256,12)).astype(np.float32)
    y=rng.integers(0,2,size=256).astype(np.float32)
    weights={
        "w1":rng.normal(0,.1,(12,48)).astype(np.float32),
        "b1":np.zeros(48,np.float32),
        "w2":rng.normal(0,.1,(48,24)).astype(np.float32),
        "b2":np.zeros(24,np.float32),
        "w3":rng.normal(0,.1,24).astype(np.float32),
        "b3":np.float32(0),
    }
    m={p:np.zeros_like(v) for p,v in weights.items()}
    v={p:np.zeros_like(w) for p,w in weights.items()}
    one,w,m,v=bounded_historical_update(x,y,weights,m,v,1)
    two,_,_,_=bounded_historical_update(x,y,w,m,v,23)
    restarted,_,_,_=bounded_historical_update(x,y,w,m,v,1)
    assert _array_receipt(two["updated_w1"]) != _array_receipt(restarted["updated_w1"])
    with pytest.raises(ValueError, match="outside two registered"):
        bounded_historical_update(x,y,w,m,v,45)
    lastx=x[:224]
    lasty=y[:224]
    step44,_,_,_=bounded_historical_update(lastx,lasty,w,m,v,44)
    assert step44["probabilities"].shape==(224,)


def test_registered_replicate_count_and_complete_source_hashes(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    r=verify_four_fresh_seed_pair(h,n,hp,npz)
    assert r["original_stage_sha256s_recomputed"]==2336
    assert r["steps_per_replica"]==44
    assert [z["replicate"] for z in r["replicates"]]==[2,3,4,5]
    assert all(len(z["per_step"])==44 for z in r["replicates"])
    assert all(len(z["epoch_checkpoints"])==2 for z in r["replicates"])
    assert r["phase2u_trainings"]==0
    assert r["historical_phase2g_cause_proven"] is False
    assert TOTAL_PARAMETERS==1825


def test_second_seed_second_epoch_weight_change_reported(tmp_path):
    field="r5__s44__w1"
    h,n,hp,npz=_fake_pair(tmp_path,changed=field)
    r=verify_four_fresh_seed_pair(h,n,hp,npz)
    assert r["replicates"][0]["per_step"][-1]["different_parameter_values"]==0
    assert r["replicates"][3]["per_step"][-1]["different_parameter_values"]==1
    assert r["replicates"][3]["per_step"][0]["different_parameter_values"]==0
    assert r["replicates"][3]["per_step"][-1]["relative_parameter_l2_delta"]>0


def test_original_permutation_contents_cannot_be_forged_by_resealing(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][0]["epochs"][1]["permutation_indices"][0]=5600
    _seal(n)
    with pytest.raises(ValueError,match="complete original permutation"):
        verify_four_fresh_seed_pair(h,n,hp,npz)
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][1]["epochs"][0]["batches"][2]["indices_sha256"]=_sha("fake")
    _seal(n)
    with pytest.raises(ValueError,match="source mini-batch indices"):
        verify_four_fresh_seed_pair(h,n,hp,npz)


def test_missing_npz_or_tampered_float32_fails_closed(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    with np.load(npz,allow_pickle=False) as z:
        data={k:z[k] for k in z.files}
    data["r2__s42__b3"]=np.float32(.9)
    np.savez(npz,**data)
    with pytest.raises(ValueError,match="original stage weight SHA"):
        verify_four_fresh_seed_pair(h,n,hp,npz)
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][1]["model_seed"]+=1
    with pytest.raises(ValueError,match="integrity mismatch"):
        verify_four_fresh_seed_pair(h,n,hp,npz)


def test_different_actual_blas_isa_or_missing_seed_rejected(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    n["runtime_profile"]["simd_available"].append("AVX512F")
    n["runtime_profile_sha256"]=hashlib.sha256(
        _canonical(n["runtime_profile"])).hexdigest()
    _seal(n)
    with pytest.raises(ValueError,match="CPU/BLAS drift"):
        verify_four_fresh_seed_pair(h,n,hp,npz)
    h,n,hp,npz=_fake_pair(tmp_path)
    n["replicas"][1]["dataset_seed"]+=1
    _seal(n)
    with pytest.raises(ValueError,match="wrong registered replica"):
        verify_four_fresh_seed_pair(h,n,hp,npz)


def test_emit_44_steps_two_seed_grid_and_first_epoch_parity(tmp_path):
    s0=PairSample(0x12345678,0xAA112233,0)
    s1=PairSample(0xDEADBEEF,0xFF445566,1)
    train=tuple((s0,s1)[i%2] for i in range(5600))
    split=tuple((s0,s1)[i%2] for i in range(1200))
    rt=_profile("Haswell")
    with (patch("adversarial_sbox.phase2r_four_fresh_seeds.load_phase2r_fixture",return_value=()),
          patch("adversarial_sbox.phase2r_four_fresh_seeds.build_shared_training_splits",
                return_value=(train,split,split)) as builder,
          patch("adversarial_sbox.phase2r_four_fresh_seeds.stable_numpy_runtime_profile",
                return_value=rt),
          patch.dict("os.environ",{
              "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
              "NUMEXPR_NUM_THREADS":"1","VECLIB_MAXIMUM_THREADS":"1",
              "GITHUB_SHA":"a"*40,
          })):
        receipt=emit_four_fresh_seed_epochs(tmp_path/"emitted.npz")
    assert builder.call_count==4
    assert receipt["replicate_count"]==4
    assert len(receipt["replicas"][0]["updated_weight_receipts"])==44
    assert all(e["batches"][-1]["rows"]==224 for r in receipt["replicas"] for e in r["epochs"])
    assert receipt["frozen_first_epoch_math_verified"] is True
    with np.load(tmp_path/"emitted.npz",allow_pickle=False) as z:
        assert len(z.files)==1168


def test_fresh_four_seed_cohort_excludes_previously_seen_zero_and_one(tmp_path):
    h,n,hp,npz=_fake_pair(tmp_path)
    assert [x["replicate"] for x in h["replicas"]]==[2,3,4,5]
    assert [x["dataset_seed"] for x in h["replicas"]]==[776031,776043,776059,776071]
    assert [x["model_seed"] for x in h["replicas"]]==[786033,786047,786061,786073]
    n["replicas"][0]["replicate"]=1
    _seal(n)
    with pytest.raises(ValueError,match="wrong registered replica"):
        verify_four_fresh_seed_pair(h,n,hp,npz)
