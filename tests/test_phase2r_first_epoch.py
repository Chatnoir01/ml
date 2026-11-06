"""Synthetic-only fidelity and anti-tamper tests for 22 original first-epoch Adam steps."""
from __future__ import annotations

import copy
import hashlib
from unittest.mock import patch

import pytest

np = pytest.importorskip("numpy", reason="optional NumPy required for scientific test lane")

from adversarial_sbox.datasets import PairSample
from adversarial_sbox.neural100 import _auc_from_scores, _advantage, BATCH_SIZE
from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2r_first_adam_microstep import PARAMETERS, STAGES, SHAPES, _normalized
from adversarial_sbox.phase2r_eight_adam_steps import one_historical_batch
from adversarial_sbox.phase2r_forward_only_probe import _array_receipt
from adversarial_sbox.phase2r_initialization_preflight import _canonical
from adversarial_sbox.phase2r_first_epoch import (
    PROTOCOL, STEPS, LAST_ROWS, TEST_ROWS, _expected_shape,
    epoch_step, emit_first_epoch, compare_first_epoch,
)


def _hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _seal(o):
    o.pop("receipt_sha256", None)
    o["receipt_sha256"] = hashlib.sha256(_canonical(o)).hexdigest()


def _seeded_model(seed=123):
    rng = np.random.default_rng(seed)
    parameters = {
        "w1": rng.normal(0, 0.1, (12, 48)).astype(np.float32),
        "b1": np.zeros(48, dtype=np.float32),
        "w2": rng.normal(0, 0.1, (48, 24)).astype(np.float32),
        "b2": np.zeros(24, dtype=np.float32),
        "w3": rng.normal(0, 0.1, 24).astype(np.float32),
        "b3": np.float32(0.0),
    }
    m = {k: np.zeros_like(v) if k != "b3" else np.float32(0.0) for k, v in parameters.items()}
    var = {k: np.zeros_like(v) if k != "b3" else np.float32(0.0) for k, v in parameters.items()}
    return rng, parameters, m, var


def _fake_original(kernel, tensors):
    profile = {
        "schema_version": 1, "python_version": "3.12.14", "numpy_version": "2.5.3",
        "os": "Linux", "architecture": "x86_64",
        "simd_available": ["AVX2"], "simd_baseline": ["SSE2"],
        "simd_dispatch": ["AVX2"],
        "blas_libraries": [{
            "internal_api": "openblas", "user_api": "blas",
            "version": "0.3.34.106.0", "threading_layer": "pthreads",
            "architecture": kernel, "num_threads": 1,
        }],
    }
    probs = tensors["synthetic_test_probabilities"]
    labels = tensors["synthetic_test_labels"]
    auc = float(_auc_from_scores(labels.astype(int).tolist(), probs.astype(float).tolist()))
    receipt = {
        "schema_version": 1, "protocol": PROTOCOL,
        "source_commit": "a" * 40,
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
        "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
        "dataset_sha256": {k: _hash(k) for k in ("train","validation","test")},
        "initialization_sha256": _hash("init"),
        "rng_before_permutation_sha256": _hash("rng-before"),
        "rng_after_permutation_sha256": _hash("rng-after"),
        "first_epoch_permutation_sha256": _hash("permutation"),
        "first_epoch_batch_info": [
            {"step":i,"size":256 if i<22 else LAST_ROWS,"indices_sha256":_hash(f"batch-{i}")}
            for i in range(1,23)
        ],
        "steps_completed": STEPS, "training_examples_seen":5600,
        "training_examples_per_epoch":5600,
        "original_eight_step_math_parity_verified":True,
        "stages":{f"s{i:02d}": {
            name:_array_receipt(tensors[f"s{i:02d}__{name}"])
            for name in STAGES
        } for i in range(1,23)},
        "test_probabilities":_array_receipt(probs),
        "test_labels":_array_receipt(labels),
        "test_auc":auc,"test_advantage":float(_advantage(auc)),
        "test_sample_count":1200,
        "runtime_profile":profile,
        "runtime_profile_sha256":hashlib.sha256(_canonical(profile)).hexdigest(),
        "one_epoch_completed":True,
        "historical_32_epoch_fit_performed":False,
        "phase2u_neural_trainings_performed":0,
        "historic_phase2g_cause_established":False,
        "research_status":"N1_SYNTHETIC_ONE_EPOCH_NUMERICAL_DIAGNOSTIC_ONLY",
    }
    _seal(receipt)
    return receipt


def _pair(tmp_path, *, mutated=None):
    stages = {
        f"s{i:02d}__{name}":np.zeros(_expected_shape(name,i),dtype=np.float32)
        for i in range(1,23) for name in STAGES
    }
    stages["synthetic_test_probabilities"]=np.full(1200,0.5,dtype=np.float32)
    stages["synthetic_test_labels"]=(np.arange(1200)%2).astype(np.float32)
    changed={k:v.copy() for k,v in stages.items()}
    if mutated:
        changed[mutated].flat[0]=np.float32(0.125)
    h_path,n_path=tmp_path/"haswell.npz",tmp_path/"nehalem.npz"
    np.savez(h_path,**stages)
    np.savez(n_path,**changed)
    return _fake_original("Haswell",stages),_fake_original("Nehalem",changed),h_path,n_path


def test_first_eight_steps_match_prior_frozen_32_stage_reference():
    rng,weights,m,v=_seeded_model()
    for step in range(1,9):
        x=rng.normal(size=(256,12)).astype(np.float32)
        y=(rng.integers(0,2,256)).astype(np.float32)
        actual,w_new,m_new,v_new=epoch_step(x,y,weights,m,v,step)
        expected,ew,em,ev=one_historical_batch(x,y,weights,m,v,step)
        assert {k:_array_receipt(actual[k]) for k in STAGES} == {
            k:_array_receipt(expected[k]) for k in STAGES
        }
        for a,b in ((w_new,ew),(m_new,em),(v_new,ev)):
            assert {k:_array_receipt(a[k]) for k in PARAMETERS} == {
                k:_array_receipt(b[k]) for k in PARAMETERS
            }
        weights,m,v=w_new,m_new,v_new


def test_last_partial_minibatch_is_224_rows_without_moment_reset():
    rng,weights,m,v=_seeded_model()
    x=rng.normal(size=(LAST_ROWS,12)).astype(np.float32)
    y=(rng.integers(0,2,LAST_ROWS)).astype(np.float32)
    stage,weights,m,v=epoch_step(x,y,weights,m,v,22)
    assert stage["batch_features"].shape==(224,12)
    assert stage["first_tanh"].shape==(224,48)
    assert stage["grad_w2"].shape==(48,24)
    assert stage["updated_w3"].shape==(24,)
    assert len(stage)==32
    with pytest.raises(ValueError,match="minibatch shape"):
        epoch_step(np.zeros((256,12),np.float32),np.zeros(256,np.float32),weights,m,v,22)


def test_original_second_epoch_or_step23_is_refused():
    rng,w,m,v=_seeded_model()
    with pytest.raises(ValueError,match="1..22"):
        epoch_step(np.zeros((256,12),np.float32),np.zeros(256,np.float32),w,m,v,23)


def test_one_full_22_step_synthetic_emission_and_first_eight_parity(tmp_path):
    s0=PairSample(0x12340000,0x56780000,0)
    s1=PairSample(0x12340001,0x56780001,1)
    train=tuple((s0,s1)[i%2] for i in range(5600))
    validation=tuple((s0,s1)[i%2] for i in range(1200))
    test=tuple((s0,s1)[i%2] for i in range(1200))
    runtime={
        "schema_version":1,"python_version":"3.12.14","numpy_version":"2.5.3",
        "blas_libraries":[{"architecture":"Haswell","num_threads":1}],
    }
    with (patch("adversarial_sbox.phase2r_first_epoch.load_phase2r_fixture",return_value=()),
          patch("adversarial_sbox.phase2r_first_epoch.build_shared_training_splits",
                return_value=(train,validation,test)),
          patch("adversarial_sbox.phase2r_first_epoch.stable_numpy_runtime_profile",
                return_value=runtime),
          patch.dict("os.environ", {
              "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1",
              "NUMEXPR_NUM_THREADS":"1","VECLIB_MAXIMUM_THREADS":"1",
              "GITHUB_SHA":"a"*40
          })):
        report=emit_first_epoch(tmp_path/"synthetic.npz")
    assert report["steps_completed"]==22 and report["training_examples_seen"]==5600
    assert report["first_epoch_batch_info"][-1]["size"]==224
    assert report["first_epoch_batch_info"][0]["size"]==256
    assert report["original_eight_step_math_parity_verified"] is True
    assert report["test_sample_count"]==1200
    assert report["phase2u_neural_trainings_performed"]==0
    with np.load(tmp_path/"synthetic.npz",allow_pickle=False) as z:
        assert len(z.files)==22*32+2
        assert z["s22__first_linear"].shape==(224,48)


def test_full_1408_hashes_and_synthetic_auc_recompute(tmp_path):
    a,b,ha,nb=_pair(tmp_path)
    z=compare_first_epoch(a,b,ha,nb)
    assert z["source_array_hashes_recomputed"]==22*32*2+4
    assert len(z["per_step"])==22
    assert z["final_updated_parameter_element_difference"]==0
    assert z["test_output_comparison"]["signed_auc_difference"]==0.0
    assert z["historic_phase2g_cause_established"] is False


def test_changed_final_weight_counted_not_backfilled_into_earlier_batches(tmp_path):
    a,b,ha,nb=_pair(tmp_path,mutated="s22__updated_w1")
    z=compare_first_epoch(a,b,ha,nb)
    assert z["per_step"][0]["updated"]["elements_changed"]==0
    assert z["per_step"][-1]["updated"]["elements_changed"]==1


def test_test_probability_changes_can_preserve_auc(tmp_path):
    a,b,ha,nb=_pair(tmp_path,mutated="synthetic_test_probabilities")
    z=compare_first_epoch(a,b,ha,nb)
    assert z["test_output_comparison"]["different_probability_values"]==1
    assert z["test_output_comparison"]["signed_auc_difference"]==0.0


def test_changed_npz_bytes_or_bad_receipt_rejected(tmp_path):
    a,b,ha,nb=_pair(tmp_path)
    with np.load(nb,allow_pickle=False) as z:
        tensors={k:z[k] for k in z.files}
    tensors["s19__grad_w3"].flat[0]=np.float32(0.25)
    np.savez(nb,**tensors)
    with pytest.raises(ValueError,match="source tensor SHA"):
        compare_first_epoch(a,b,ha,nb)
    a,b,ha,nb=_pair(tmp_path)
    b["model_seed"]+=1
    with pytest.raises(ValueError,match="receipt digest"):
        compare_first_epoch(a,b,ha,nb)


def test_bad_last_minibatch_size_or_different_cpu_fails_closed(tmp_path):
    a,b,ha,nb=_pair(tmp_path)
    b["first_epoch_batch_info"][-1]["size"]=256
    _seal(b)
    with pytest.raises(ValueError,match="batch geometry"):
        compare_first_epoch(a,b,ha,nb)
    a,b,ha,nb=_pair(tmp_path)
    b["runtime_profile"]["simd_available"].append("AVX512F")
    b["runtime_profile_sha256"]=hashlib.sha256(_canonical(b["runtime_profile"])).hexdigest()
    _seal(b)
    with pytest.raises(ValueError,match="CPU/BLAS drift"):
        compare_first_epoch(a,b,ha,nb)
