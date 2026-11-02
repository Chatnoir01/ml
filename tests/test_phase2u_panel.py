"""Synthetic Phase 2U source-panel verification tests — NOT new scientific results."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.provenance import fingerprint_sbox
from adversarial_sbox.phase2u_generate import (
    DESIGN, SOURCE_VERSION, PUBLIC_SEEDS, digest,
)
from adversarial_sbox.phase2u_panel import (
    AdmissionRejected, aggregate, exclusion_history,
    simple_xor_clone, verify_source,
)


def fake_receipt(seed, *, box=None, exhausted=False):
    data={
        "source_version":SOURCE_VERSION,"design":DESIGN,"seed":seed,
        "classical_evaluations":100 if exhausted else 340,
        "required_classical_evaluations":340,
        "original_population_sha256":"a"*64,
        "proposal_transcript_sha256":"b"*64,
        "proposal_count":80 if exhausted else 320,
        "guided_proposal_count":64 if exhausted else 304,
        "random_swap_fallback_count":16,
        "exact_metric_hits":1 if box is not None else 0,
        "new_neural_training_count":0,
    }
    if exhausted:
        data.update({"status":"source_exhausted",
                     "reason":"bounded_fallback_exhausted"})
    elif box is None:
        data.update({"status":"ineligible",
                     "reason":"no_exact_metric_evaluated"})
    else:
        m=evaluate_classical(box)
        data.update({
            "status":"accepted","fingerprint":m.fingerprint,
            "sbox":list(box),"metrics":{
                "nonlinearity":m.nonlinearity,
                "differential_uniformity":m.differential_uniformity,
                "max_linear_correlation":m.max_linear_correlation,
                "algebraic_degree":m.algebraic_degree,
                "sac_score":m.sac_score,
            },
        })
    data["source_payload_sha256"]=digest(data)
    return data


def reseal(receipt):
    receipt.pop("source_payload_sha256",None)
    receipt["source_payload_sha256"]=digest(receipt)
    return receipt


def test_original_six_and_blocked_v1_two_are_excluded():
    refs=exclusion_history()
    assert len(refs)==8
    assert len({fingerprint_sbox(s) for s in refs})==8
    assert all(len(s)==256 and len(set(s))==256 for s in refs)


def test_v1_clones_rejected_even_if_not_exact_copy():
    refs=exclusion_history()
    box=tuple(v ^ 17 for v in refs[-1])
    assert fingerprint_sbox(box)!=fingerprint_sbox(refs[-1])
    assert simple_xor_clone(box, refs)
    assert not simple_xor_clone(tuple(range(256)), refs)


def test_acceptance_classifier_recomputes_exact_metrics():
    box=tuple(CANDIDATES[0]["sbox"])
    r=fake_receipt(PUBLIC_SEEDS[0],box=box)
    actual=verify_source(r,PUBLIC_SEEDS[0])
    assert actual["status"]=="accepted"
    assert actual["metrics"]["nonlinearity"]==100
    assert actual["metrics"]["differential_uniformity"]==8
    assert actual["metrics"]["algebraic_degree"]==7
    assert actual["metrics"]["max_linear_correlation"]==56


def test_source_tampering_or_wrong_seed_fails_closed():
    r=fake_receipt(PUBLIC_SEEDS[0])
    r["proposal_count"]=319
    with pytest.raises(AdmissionRejected,match="hash"):
        verify_source(r,PUBLIC_SEEDS[0])
    reseal(r)
    with pytest.raises(AdmissionRejected,match="budget"):
        verify_source(r,PUBLIC_SEEDS[0])
    r=fake_receipt(PUBLIC_SEEDS[0])
    with pytest.raises(AdmissionRejected,match="version/seed"):
        verify_source(r,PUBLIC_SEEDS[1])


def test_false_completed_seed_and_false_ineligibility_rejected():
    r=fake_receipt(PUBLIC_SEEDS[0])
    r["classical_evaluations"]=339
    reseal(r)
    with pytest.raises(AdmissionRejected,match="340"):
        verify_source(r,PUBLIC_SEEDS[0])
    r=fake_receipt(PUBLIC_SEEDS[0])
    r["exact_metric_hits"]=2
    reseal(r)
    with pytest.raises(AdmissionRejected,match="false ineligible"):
        verify_source(r,PUBLIC_SEEDS[0])


def test_partial_source_exhaustion_is_a_blocking_record():
    r=fake_receipt(PUBLIC_SEEDS[0],exhausted=True)
    assert verify_source(r,PUBLIC_SEEDS[0])["status"]=="source_exhausted"
    result=aggregate([r])
    assert result["status"]=="SOURCE_EXHAUSTED_BLOCKED"
    assert result["new_neural_trainings"]==0
    assert len(result["panel_receipt_sha256"])==64
    assert result["selected_candidates"]==[]


def test_single_ineligible_seed_cannot_form_a_panel():
    r=fake_receipt(PUBLIC_SEEDS[0])
    p=aggregate([r])
    assert p["status"]=="SOURCE_PREFIX_PARTIAL_DO_NOT_PREDICT"
    assert p["selected_count"]==0
    assert p["examined_seed_count"]==1
    assert p["source_receipt_sha256_ordered"]==[r["source_payload_sha256"]]


def test_source_ledger_cannot_skip_seeds_or_mix_phase2t():
    with pytest.raises(AdmissionRejected,match="contiguous"):
        aggregate([fake_receipt(PUBLIC_SEEDS[1])])
    r=fake_receipt(PUBLIC_SEEDS[0])
    r["source_version"]="phase2t_frozen_v1"
    reseal(r)
    with pytest.raises(AdmissionRejected,match="version"):
        aggregate([r])


def test_exact_historical_candidate_is_a_blocker_not_new_success():
    r=fake_receipt(PUBLIC_SEEDS[0],box=tuple(CANDIDATES[0]["sbox"]))
    p=aggregate([r])
    assert p["status"]=="SOURCE_FAMILY_DUPLICATE_BLOCKED"
    assert p["selected_count"]==0


def test_output_xor_clone_is_a_blocker_not_new_success():
    old=tuple(CANDIDATES[0]["sbox"])
    box=tuple(v ^ 0x5A for v in old)
    r=fake_receipt(PUBLIC_SEEDS[0],box=box)
    p=aggregate([r])
    assert p["status"]=="SOURCE_FAMILY_CLONE_BLOCKED"


def test_synthetic_successful_panel_flow_stops_on_twelfth_without_neural_labels():
    # Synthetic proxies, not scientifically independent candidates. Mock ONLY
    # the previously observed-family filter to exercise collection semantics.
    old=tuple(CANDIDATES[0]["sbox"])
    receipts=[fake_receipt(seed,box=tuple(v ^ (i+1) for v in old))
              for i,seed in enumerate(PUBLIC_SEEDS[:12])]
    with patch("adversarial_sbox.phase2u_panel.simple_xor_clone",return_value=False):
        result=aggregate(receipts)
    assert result["status"]=="PANEL_COMPLETE_NO_NEURAL_OUTCOMES"
    assert result["selected_count"]==12
    assert len(result["selected_candidates"])==12
    assert result["new_neural_trainings"]==0
    assert all("test_auc" not in str(x) for x in result["selected_candidates"])
    with pytest.raises(AdmissionRejected,match="continued"):
        with patch("adversarial_sbox.phase2u_panel.simple_xor_clone",
                   return_value=False):
            aggregate(receipts+[fake_receipt(PUBLIC_SEEDS[12])])


def test_exhausted_24_seed_prefix_is_not_a_complete_panel():
    receipts=[fake_receipt(seed) for seed in PUBLIC_SEEDS]
    result=aggregate(receipts)
    assert result["status"]=="PANEL_INCOMPLETE_DO_NOT_PREDICT"
    assert result["selected_count"]==0
    assert result["examined_seed_count"]==24


def test_two_new_candidate_xor_equivalents_cannot_count_as_independent():
    original=tuple(CANDIDATES[0]["sbox"])
    a=fake_receipt(PUBLIC_SEEDS[0],box=tuple(v ^ 11 for v in original))
    b=fake_receipt(PUBLIC_SEEDS[1],box=tuple(v ^ 29 for v in original))
    # Synthetic fixtures are historically related; blank the old-reference
    # registry ONLY here to isolate the NEW-vs-NEW clone restriction.
    with patch("adversarial_sbox.phase2u_panel.exclusion_history",return_value=()):
        result=aggregate([a,b])
    assert result["status"]=="SOURCE_FAMILY_CLONE_BLOCKED"
    assert result["selected_count"]==1
