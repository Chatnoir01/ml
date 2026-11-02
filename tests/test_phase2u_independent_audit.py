"""Independent standard-library source auditor software-only regression tests."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

# This auditor is intentionally a standalone stdlib-only script outside
# the installed src/ package. Import it by its real checked-out path rather
# than silently adding the entire repository root to Python's module path.
import importlib.util

AUDITOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "phase2u_independent_audit.py"
spec = importlib.util.spec_from_file_location("phase2u_independent_audit", AUDITOR_PATH)
assert spec is not None and spec.loader is not None
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
AuditRejected = auditor.AuditRejected
REGISTERED_SEEDS = auditor.REGISTERED_SEEDS
audit_files = auditor.audit_files
audit_receipt = auditor.audit_receipt
classical_metrics = auditor.classical_metrics
xor_clone = auditor.xor_clone
from adversarial_sbox.phase2a_candidates import CANDIDATES


def make_receipt(seed, *, box=None, exhausted=False):
    r={
        "seed":seed,
        "source_version":"phase2u_source_v1",
        "design":"phase2u_bounded_unique_fallback_v1",
        "new_neural_training_count":0,
        "classical_evaluations":100 if exhausted else 340,
        "proposal_count":80 if exhausted else 320,
        "guided_proposal_count":64 if exhausted else 320,
        "random_swap_fallback_count":16 if exhausted else 0,
        "exact_metric_hits":1 if box is not None else 0,
    }
    if exhausted:
        r.update({"status":"source_exhausted","reason":"bounded_fallback_exhausted"})
    elif box is not None:
        m=classical_metrics(box)
        r.update({
            "status":"accepted",
            "fingerprint":hashlib.sha3_256(bytes(box)).hexdigest(),
            "metrics":m,
            "sbox":list(box),
        })
    else:
        r.update({"status":"ineligible","reason":"no_exact_metric_evaluated"})
    r["source_payload_sha256"]=hashlib.sha256(
        json.dumps(r,sort_keys=True,separators=(",",":"),
                   ensure_ascii=True,allow_nan=False).encode("ascii")
    ).hexdigest()
    return r


def write_zip(folder, receipt):
    file=folder/f"archive-{receipt['seed']}.zip"
    with ZipFile(file,"w") as z:
        z.writestr(f"seed-{receipt['seed']}.json",json.dumps(receipt))
    return file


def test_math_from_independent_implementation_matches_historical_sbox():
    box=list(CANDIDATES[0]["sbox"])
    metrics=classical_metrics(box)
    assert metrics=={
        "nonlinearity":100,
        "differential_uniformity":8,
        "max_linear_correlation":56,
        "algebraic_degree":7,
        "sac_score":CANDIDATES[0]["sac_score"],
    }


def test_single_source_receipt_and_prefix_are_checked(tmp_path):
    one=make_receipt(REGISTERED_SEEDS[0],box=list(CANDIDATES[0]["sbox"]))
    verified, box=audit_receipt(one)
    assert verified["status"]=="accepted"
    assert verified["source_sha256"]==one["source_payload_sha256"]
    assert len(box)==256
    result=audit_files([write_zip(tmp_path,one)])
    assert result["audited_seed_count"]==1
    assert result["new_source_candidates"]==1
    assert result["status"]=="PARTIAL_SOURCE_AUDIT_NO_NEURAL"


def test_ineligible_source_is_valid_negative_outcome(tmp_path):
    r=make_receipt(REGISTERED_SEEDS[0])
    data=audit_files([write_zip(tmp_path,r)])
    assert data["new_source_candidates"]==0
    assert data["rows"][0]["status"]=="ineligible"


def test_crypto_metrics_and_sha_are_not_just_trusted_metadata():
    r=make_receipt(REGISTERED_SEEDS[0],box=list(CANDIDATES[0]["sbox"]))
    q=deepcopy(r);q["metrics"]["nonlinearity"]=102
    with pytest.raises(AuditRejected,match="source SHA"):
        audit_receipt(q)
    q=deepcopy(r);q["fingerprint"]="0"*64
    q.pop("source_payload_sha256")
    q["source_payload_sha256"]=hashlib.sha256(
        json.dumps(q,sort_keys=True,separators=(",",":"),
                   ensure_ascii=True,allow_nan=False).encode("ascii")
    ).hexdigest()
    with pytest.raises(AuditRejected,match="SHA3-256"):
        audit_receipt(q)


def test_same_candidate_in_two_archives_is_rejected(tmp_path):
    box=list(CANDIDATES[0]["sbox"])
    a=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[0],box=box))
    b=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[1],box=box))
    with pytest.raises(AuditRejected,match="XOR clones"):
        audit_files([a,b])


def test_output_xor_copy_in_two_archives_is_rejected(tmp_path):
    box=list(CANDIDATES[0]["sbox"])
    a=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[0],box=box))
    b=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[1],
                                       box=[v^15 for v in box]))
    assert xor_clone(tuple(box),tuple(v^15 for v in box))
    with pytest.raises(AuditRejected,match="XOR clones"):
        audit_files([a,b])


def test_bad_source_order_and_duplicate_are_rejected(tmp_path):
    a=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[0]))
    b=write_zip(tmp_path,make_receipt(REGISTERED_SEEDS[2]))
    with pytest.raises(AuditRejected,match="registered prefix"):
        audit_files([a,b])
    with pytest.raises(AuditRejected,match="duplicated"):
        audit_files([a,a])


def test_source_exhausted_is_explicit_blocked(tmp_path):
    result=audit_files([write_zip(
        tmp_path,make_receipt(REGISTERED_SEEDS[0],exhausted=True)
    )])
    assert result["status"]=="SOURCE_BLOCKED"
    assert result["new_neural_trainings"]==0


def test_non_bijective_sbox_and_invalid_seed_fail_closed():
    box=list(CANDIDATES[0]["sbox"])
    box[0]=box[1]
    with pytest.raises(AuditRejected,match="bijective"):
        classical_metrics(box)
    r=make_receipt(REGISTERED_SEEDS[0])
    r["seed"]=31019
    with pytest.raises(AuditRejected,match="SHA-256"):
        audit_receipt(r)
