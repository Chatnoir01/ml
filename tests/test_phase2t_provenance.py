"""No-neural-training provenance checks using historical S-Boxes for smoke only."""
import hashlib
from pathlib import Path

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.phase2t_provenance import (
    audit_paired_sources, digest_pairs, model_initial_state_fingerprint,
    source_receipt,
)


def test_paired_sources_stable_across_independent_sbox_ciphertexts():
    candidates=[CANDIDATES[0]["sbox"],CANDIDATES[1]["sbox"]]
    a,b=audit_paired_sources(
        sboxes=candidates,difference=1,seed=930101,pair_count=128,
    )
    for field in ("plain_source_sha256","train_source_sha256",
                  "validation_source_sha256","test_source_sha256"):
        assert a[field]==b[field]
        assert len(a[field])==64
    assert a["cipher_dataset_sha256"]!=b["cipher_dataset_sha256"]
    assert a["split_sizes"]==b["split_sizes"]


def test_paired_sources_repeat_identical_for_fixed_seed():
    s=CANDIDATES[0]["sbox"]
    a=source_receipt(sbox=s,difference=256,seed=930113,pair_count=128)
    b=source_receipt(sbox=s,difference=256,seed=930113,pair_count=128)
    assert a==b
    assert sum(a["split_sizes"])==128
    c=source_receipt(sbox=s,difference=256,seed=930127,pair_count=128)
    assert c["plain_source_sha256"] != a["plain_source_sha256"]


def test_both_phase2t_differences_have_paired_plaintext_sources():
    s=[CANDIDATES[0]["sbox"],CANDIDATES[1]["sbox"]]
    for d in (1,256):
        result=audit_paired_sources(sboxes=s,difference=d,seed=930139,pair_count=64)
        assert len(result)==2
        assert all(x["pair_count"]==64 for x in result)


def test_invalid_seeds_differences_and_unpaired_audit_fail():
    s=CANDIDATES[0]["sbox"]
    with pytest.raises(ValueError,match="difference"):
        source_receipt(sbox=s,difference=2,seed=1,pair_count=64)
    with pytest.raises(ValueError,match="seed"):
        source_receipt(sbox=s,difference=1,seed=True,pair_count=64)
    with pytest.raises(ValueError,match="dataset"):
        source_receipt(sbox=s,difference=1,seed=1,pair_count=3)
    with pytest.raises(ValueError,match="at least two"):
        audit_paired_sources(sboxes=[s],difference=1,seed=1,pair_count=64)


def test_model_init_provenance_matches_actual_source_and_is_deterministic():
    pytest.importorskip("numpy")
    a=model_initial_state_fingerprint(940101)
    b=model_initial_state_fingerprint(940101)
    c=model_initial_state_fingerprint(940113)
    assert a==b
    assert a["initial_state_sha256"]!=c["initial_state_sha256"]
    assert a["training_executed"] is False
    assert a["architecture"]=="byte_tanh_mlp"
    assert len(a["initial_state_sha256"])==64
    source=Path(__file__).resolve().parents[1]/"src"/"adversarial_sbox"/"neural_heterogeneity.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest()==a["trainer_source_sha256"]


def test_invalid_model_seed_rejected_without_training():
    with pytest.raises(ValueError,match="seed"):
        model_initial_state_fingerprint(-1)
    with pytest.raises(ValueError,match="seed"):
        model_initial_state_fingerprint(True)
