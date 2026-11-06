"""Synthetic-only regression tests of the preregistered eight-step CPU probe."""
from __future__ import annotations

import copy
import hashlib

import pytest

np = pytest.importorskip("numpy", reason="NumPy is optional outside scientific CI")

from adversarial_sbox.phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS
from adversarial_sbox.phase2r_fixture import CURRICULUM_SHA256
from adversarial_sbox.phase2r_first_adam_microstep import (
    PARAMETERS, SHAPES, STAGES, original_first_step_tensors,
)
from adversarial_sbox.phase2r_forward_only_probe import _array_receipt
from adversarial_sbox.phase2r_initialization_preflight import _canonical
from adversarial_sbox.phase2r_eight_adam_steps import (
    PROTOCOL, STEPS, _index_hash, one_historical_batch,
    compare_eight_step_original_receipts,
)


def _h(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def _seal(obj):
    obj.pop("receipt_sha256", None)
    obj["receipt_sha256"] = hashlib.sha256(_canonical(obj)).hexdigest()


def _model(rng):
    weights = {
        "w1": rng.normal(0, 0.1, (12, 48)).astype(np.float32),
        "b1": np.zeros(48, dtype=np.float32),
        "w2": rng.normal(0, 0.1, (48, 24)).astype(np.float32),
        "b2": np.zeros(24, dtype=np.float32),
        "w3": rng.normal(0, 0.1, 24).astype(np.float32),
        "b3": np.float32(0.0),
    }
    zeros = {k: np.zeros_like(v) for k, v in weights.items()}
    return weights, zeros, copy.deepcopy(zeros)


def _source(arch, arrays):
    runtime = {
        "schema_version": 1, "python_version": "3.12.14",
        "numpy_version": "2.5.3", "os": "Linux", "architecture": "x86_64",
        "simd_available": ["AVX2"], "simd_baseline": ["SSE2"],
        "simd_dispatch": ["AVX2"],
        "blas_libraries": [{
            "user_api": "blas", "internal_api": "openblas",
            "version": "0.3.34.106.0", "threading_layer": "pthreads",
            "architecture": arch, "num_threads": 1,
        }],
    }
    obj = {
        "schema_version": 1, "protocol": PROTOCOL, "source_commit": "a" * 40,
        "fixture_sha256": CURRICULUM_SHA256,
        "difference": 1, "replicate": 0,
        "dataset_seed": TRAINING_DATASET_BASE_SEEDS[0],
        "model_seed": TRAINING_MODEL_BASE_SEEDS[0],
        "dataset_sha256": {k: _h(k) for k in ("train", "validation", "test")},
        "initialization_sha256": _h("initial"), 
        "rng_before_permutation_sha256": _h("pre"),
        "rng_after_permutation_sha256": _h("post"),
        "first_epoch_permutation_sha256": _h("permutation"),
        "first_epoch_batch_info": [
            {"step": i, "indices_sha256": _h(f"step-{i}")}
            for i in range(1, STEPS + 1)
        ],
        "steps_completed": STEPS,
        "samples_seen": STEPS * 256,
        "model_updates_per_step": 6,
        "first_step_exact_original_math_parity": True,
        "stages": {
            f"s{i:02d}": {
                name: _array_receipt(arrays[f"s{i:02d}__{name}"])
                for name in STAGES
            } for i in range(1, STEPS + 1)
        },
        "runtime_profile": runtime,
        "runtime_profile_sha256": hashlib.sha256(_canonical(runtime)).hexdigest(),
        "full_epoch_completed": False,
        "full_neural_training_performed": False,
        "phase2u_trainings_performed": 0,
        "historical_phase2g_root_cause_established": False,
        "scientific_status": "SYNTHETIC_EIGHT_ADAM_STEPS_NUMERICAL_INTERVENTION_ONLY",
    }
    _seal(obj)
    return obj


def _fake_pair(tmp_path, *, change_step=None, change_name="updated_w1"):
    original = {
        f"s{i:02d}__{k}": np.zeros(SHAPES[k], dtype=np.float32)
        for i in range(1, STEPS+1) for k in STAGES
    }
    altered = {k: v.copy() for k,v in original.items()}
    if change_step:
        altered[f"s{change_step:02d}__{change_name}"].flat[0] = np.float32(0.125)
    pa, pb = tmp_path/"a.npz", tmp_path/"b.npz"
    np.savez(pa,**original)
    np.savez(pb,**altered)
    return _source("Haswell",original),_source("Nehalem",altered),pa,pb


def test_step_one_matches_original_frozen_reference_on_all_32_stages():
    rng=np.random.default_rng(1301)
    x=rng.normal(size=(256,12)).astype(np.float32)
    y=np.asarray([0.,1.]*128,dtype=np.float32)
    w,m,v=_model(rng)
    actual,_,_,_=one_historical_batch(x,y,w,m,v,1)
    reference=original_first_step_tensors(x,y,w)
    assert set(actual)==set(reference)==set(STAGES)
    assert {k:_array_receipt(value) for k,value in actual.items()}=={
        k:_array_receipt(value) for k,value in reference.items()
    }


def test_second_batch_retains_adam_moments_not_resets():
    rng=np.random.default_rng(1302)
    x=rng.normal(size=(256,12)).astype(np.float32)
    y=np.asarray([0.,1.]*128,dtype=np.float32)
    w,m,v=_model(rng)
    _,w,m,v=one_historical_batch(x,y,w,m,v,1)
    assert np.any(m["w1"])
    step2,_,_,_=one_historical_batch(x,y,w,m,v,2)
    other,_,_,_=one_historical_batch(
        x,y,w,{k:np.zeros_like(val) for k,val in m.items()},
        {k:np.zeros_like(val) for k,val in v.items()},2
    )
    assert _array_receipt(step2["updated_w1"]) != _array_receipt(other["updated_w1"])


def test_more_than_eight_steps_is_refused():
    rng=np.random.default_rng(1303)
    w,m,v=_model(rng)
    with pytest.raises(ValueError, match="unregistered"):
        one_historical_batch(np.zeros((256,12),np.float32),
                             np.zeros(256,np.float32),w,m,v,9)


def test_all_512_stage_hashes_and_all_inputs_matching(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path)
    result=compare_eight_step_original_receipts(a,b,pa,pb)
    assert result["steps"]==8
    assert result["tensor_pairs_rechecked"]==8*32
    assert result["individual_original_tensor_hashes_rechecked"]==8*32*2
    assert result["eighth_step_has_any_parameter_difference"] is False
    assert result["phase2u_neural_trainings_performed"]==0


def test_eighth_step_weight_change_is_localized_not_backfilled(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path,change_step=8)
    result=compare_eight_step_original_receipts(a,b,pa,pb)
    assert result["first_step_updated_parameter_changes"]==0
    assert result["eighth_step_updated_parameter_changes"]==1
    assert result["eighth_step_changed_parameter_elements"]==1
    assert result["per_step"][7]["updated_by_parameter"]["w1"]["maximum_absolute_difference"]==0.125


def test_wrong_index_or_dataset_hash_even_resealed_fails_closed(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path)
    b["first_epoch_batch_info"][2]["indices_sha256"]=_h("altered")
    _seal(b)
    with pytest.raises(ValueError, match="permutation"):
        compare_eight_step_original_receipts(a,b,pa,pb)
    a,b,pa,pb=_fake_pair(tmp_path)
    b["dataset_sha256"]["train"]=_h("different")
    _seal(b)
    with pytest.raises(ValueError, match="data"):
        compare_eight_step_original_receipts(a,b,pa,pb)


def test_numpy_npz_byte_change_without_receipt_update_rejected(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path)
    with np.load(pb,allow_pickle=False) as source:
        changed={key:source[key] for key in source.files}
    changed["s03__grad_w3"].flat[0]=np.float32(1)
    np.savez(pb,**changed)
    with pytest.raises(ValueError,match="NPZ original tensor"):
        compare_eight_step_original_receipts(a,b,pa,pb)


def test_runtime_or_selected_core_change_is_not_ignored(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path)
    b["runtime_profile"]["blas_libraries"][0]["architecture"]="Haswell"
    b["runtime_profile_sha256"]=hashlib.sha256(_canonical(b["runtime_profile"])).hexdigest()
    _seal(b)
    with pytest.raises(ValueError, match="different or unpinned numerical backend"):
        compare_eight_step_original_receipts(a,b,pa,pb)
    a,b,pa,pb=_fake_pair(tmp_path)
    b["runtime_profile"]["simd_available"].append("AVX512F")
    b["runtime_profile_sha256"]=hashlib.sha256(_canonical(b["runtime_profile"])).hexdigest()
    _seal(b)
    with pytest.raises(ValueError, match="same-host CPU/BLAS"):
        compare_eight_step_original_receipts(a,b,pa,pb)


def test_unregistered_protocol_or_incomplete_stage_grid_rejected(tmp_path):
    a,b,pa,pb=_fake_pair(tmp_path)
    b["steps_completed"]=9
    _seal(b)
    with pytest.raises(ValueError, match="unregistered eight-step"):
        compare_eight_step_original_receipts(a,b,pa,pb)
    a,b,pa,pb=_fake_pair(tmp_path)
    b["stages"]["s07"].pop("moment_w2")
    _seal(b)
    with pytest.raises(ValueError, match="missing or duplicated"):
        compare_eight_step_original_receipts(a,b,pa,pb)


def test_mathematical_identical_batches_share_same_index_receipt():
    np.testing.assert_array_equal(np.arange(10,dtype=np.int64),np.arange(10))
    assert _index_hash(np.arange(256),scope="selected-batch")==_index_hash(
        np.arange(256,dtype=np.int64),scope="selected-batch"
    )
