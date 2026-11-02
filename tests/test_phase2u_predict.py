"""Only synthetic controls for Phase 2U sealed classical predictions.

No source evolution, no new neural training, no scientific discovery claim.
"""
from copy import deepcopy
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.phase2u_generate import SOURCE_VERSION, DESIGN, digest
from adversarial_sbox.phase2u_predict import (
    PredictionRejected, freeze_from_raw_seed_receipts,
    verify_prediction_receipt,
)


def _synthetic_complete_source():
    base=tuple(CANDIDATES[0]["sbox"])
    # The candidate list is deliberately a set of historical XOR copies and
    # MUST NEVER be accepted by the real panel admission function.
    candidates=[]
    for i in range(12):
        candidates.append({
            "seed":41003+i, "sha256":f"{i+1:064x}",
            "fingerprint":f"{i+20:064x}",
            "sbox":[x^(i+1) for x in base],
        })
    return {
        "status":"PANEL_COMPLETE_NO_NEURAL_OUTCOMES",
        "selected_count":12,
        "selected_candidates":candidates,
        "panel_receipt_sha256":"a"*64,
        "source_receipt_sha256_ordered":[x["sha256"] for x in candidates],
    }


def _fake_classical_signal(box, difference):
    return {
        "difference":difference,
        "bit":box[0]%32,
        "signed_holdout_advantage":(box[0]+difference%3)/400.0,
    }


def _make_fixture():
    with patch("adversarial_sbox.phase2u_predict.aggregate",
               return_value=_synthetic_complete_source()):
        with patch("adversarial_sbox.phase2u_predict.classical_signal",
                   side_effect=_fake_classical_signal):
            return freeze_from_raw_seed_receipts([{"fake":"RAW_TEST_ONLY"}])


def _reseal(d):
    d.pop("prediction_receipt_sha256",None)
    d["prediction_receipt_sha256"]=digest(d)
    return d


def test_fake_complete_source_produces_consistent_sealed_rank_without_neural_data():
    d=_make_fixture()
    verify_prediction_receipt(d)
    assert d["source_version"]==SOURCE_VERSION
    assert d["source_design"]==DESIGN
    assert d["candidate_count"]==12
    assert d["new_neural_trainings"]==0
    assert d["neural_outcomes_accessed"] is False
    assert d["scientific_status"]=="PRECOMMITTED_PREDICTION_UNEVALUATED"
    assert len(d["best_first_fingerprints"])==12
    assert len(d["prediction_receipt_sha256"])==64
    assert "test_auc" not in str(d)


def test_no_partial_source_ledger_can_be_promoted_to_frozen_prediction():
    source=_synthetic_complete_source()
    source["selected_count"]=11
    source["status"]="SOURCE_PREFIX_PARTIAL_DO_NOT_PREDICT"
    with patch("adversarial_sbox.phase2u_predict.aggregate",return_value=source):
        with pytest.raises(PredictionRejected,match="all twelve"):
            freeze_from_raw_seed_receipts([{"fake":"RAW_TEST_ONLY"}])


def test_seal_breaks_when_any_prediction_score_is_changed():
    d=_make_fixture()
    d["predictions"][0]["classical_feature_score"]=0.02
    with pytest.raises(PredictionRejected,match="integrity"):
        verify_prediction_receipt(d)


def test_cannot_reseal_a_ranking_that_contradicts_scores():
    d=_make_fixture()
    d["best_first_fingerprints"].reverse()
    _reseal(d)
    with pytest.raises(PredictionRejected,match="ranking"):
        verify_prediction_receipt(d)


def test_cannot_reseal_false_feature_arithmetic():
    d=_make_fixture()
    d["predictions"][0]["classical_feature_score"]+=0.01
    _reseal(d)
    with pytest.raises(PredictionRejected,match="feature rule"):
        verify_prediction_receipt(d)


def test_cannot_change_version_or_claim_neural_outcomes_after_freeze():
    d=_make_fixture()
    d["neural_outcomes_accessed"]=True
    _reseal(d)
    with pytest.raises(PredictionRejected,match="unblinded"):
        verify_prediction_receipt(d)
    d=_make_fixture()
    d["source_version"]="phase2t_frozen_v1"
    _reseal(d)
    with pytest.raises(PredictionRejected,match="unblinded"):
        verify_prediction_receipt(d)
