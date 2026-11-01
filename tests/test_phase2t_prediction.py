"""Phase 2T predictive lock / sealed evaluation — synthetic fixtures only.

The test panel consists of affine copies of historical S-boxes; these are NOT
independent science candidates. A positive admission test temporarily mocks
the historical-clone rejection to exercise other contracts. The production
admission function must keep its real clone filter enabled.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.provenance import fingerprint_sbox
from adversarial_sbox.phase2t_predict import (
    DESIGN, GENERATING_ALGORITHM, PROSPECTIVE_SEEDS,
    TARGET_CANDIDATES, PredictionRejected,
    admit_panel, check_frozen, classical_signal, digest, freeze,
)
from adversarial_sbox.phase2t_generate import aggregate_attempts
from adversarial_sbox.phase2t_evaluate import (
    DATASET_SEEDS, MODEL_SEEDS, EXPECTED_TOTAL_NEURAL_TRAININGS,
    evaluate, validate_neural_outcomes, spearman,
)


def _fake_panel():
    """Deterministic fake panel — only to test validation and IO contracts."""
    base = tuple(CANDIDATES[0]["sbox"])
    attempts = []
    for index, seed in enumerate(PROSPECTIVE_SEEDS[:TARGET_CANDIDATES]):
        # XOR-output translates are affine-related historical copies: the real
        # independent candidate filter MUST reject them.
        box = [(v ^ (index + 1)) for v in base]
        attempts.append({
            "seed":seed, "status":"accepted", "evaluations":340,
            "fingerprint":fingerprint_sbox(box), "sbox":box,
        })
    return {"design":DESIGN,"generator":GENERATING_ALGORITHM,
            "attempts":attempts,"status":"SYNTHETIC_TEST_ONLY"}


def _fake_feature(sbox, difference):
    index=sbox[0] % 256
    return {"difference":difference, "bit":index % 32,
            "signed_holdout_advantage":(index+1)/400.0}


def _freeze_fixture():
    with patch("adversarial_sbox.phase2t_predict._known_simple_copy",
               return_value=False):
        with patch("adversarial_sbox.phase2t_predict.classical_signal",
                   side_effect=_fake_feature):
            return freeze(_fake_panel())


def _fake_outcomes(receipt, *, reverse=False):
    runs=[]
    for index, row in enumerate(receipt["predictions"]):
        # If feature-score order is permuted, assign the outcome by its score
        # rank rather than source index: this creates a controlled positive
        # synthetic association without testing real neural training.
        positions=sorted(x["classical_feature_score"] for x in receipt["predictions"])
        score_rank=positions.index(row["classical_feature_score"])
        if reverse:
            score_rank=TARGET_CANDIDATES-1-score_rank
        auc=0.5 + (.08+.02*score_rank)/2
        for delta in (1,256):
            for rep in range(len(DATASET_SEEDS)):
                runs.append({
                    "fingerprint":row["fingerprint"],
                    "difference":delta, "replicate":rep,
                    "dataset_seed":DATASET_SEEDS[rep],
                    "model_seed":MODEL_SEEDS[rep],
                    "test_auc":auc,
                    "null_auc":.5,
                    "dataset_fingerprint_sha256":sha256(
                        f"fake_dataset_{index}_{delta}_{rep}".encode()).hexdigest(),
                    "model_init_fingerprint_sha256":sha256(
                        f"fake_init_{rep}".encode()).hexdigest(),
                    "runner_commit_sha256":sha256(b"TEST_RUNNER_NOT_REAL").hexdigest(),
                })
    return {
        "schema_version":1,"experiment":"phase2t_fresh_12_neural_only",
        "protocol":"phase2t-4round-byte-tanh-v1",
        "prediction_receipt_sha256":receipt["receipt_sha256"],
        "panel_sha256":receipt["source_panel_sha256"],
        "runs":runs,
    }


def test_synthetic_affine_clones_rejected_by_real_admission():
    with pytest.raises(PredictionRejected, match="clone"):
        admit_panel(_fake_panel())


def test_panel_seed_order_and_fixed_count_enforced():
    p=_fake_panel()
    p["attempts"][1]["seed"]=50000
    with pytest.raises(PredictionRejected, match="seed order"):
        admit_panel(p)
    p=_fake_panel()
    p["attempts"].pop()
    with pytest.raises(PredictionRejected, match="panel incomplete"):
        admit_panel(p)


def test_duplicate_old_candidate_rejected():
    p=_fake_panel()
    box=CANDIDATES[0]["sbox"]
    p["attempts"][0]["fingerprint"]=fingerprint_sbox(box)
    p["attempts"][0]["sbox"]=list(box)
    with pytest.raises(PredictionRejected, match="historical"):
        admit_panel(p)


def test_gate_checks_real_classical_metrics_independent_of_claimed_metadata():
    p=_fake_panel()
    p["attempts"][0]["sbox"][0]=p["attempts"][0]["sbox"][1]
    p["attempts"][0]["fingerprint"]=fingerprint_sbox(p["attempts"][0]["sbox"])
    with pytest.raises(PredictionRejected):
        with patch("adversarial_sbox.phase2t_predict._known_simple_copy",
                   return_value=False):
            admit_panel(p)


def test_fake_panel_has_matching_real_metrics_only_after_independence_mock():
    with patch("adversarial_sbox.phase2t_predict._known_simple_copy",
               return_value=False):
        selected=admit_panel(_fake_panel())
    assert len(selected)==12
    assert len({s["fingerprint"] for s in selected})==12
    assert all(s["classical_metrics"]==(100,8,56,7) for s in selected)


def test_freeze_predictor_never_reads_synthetic_neural_scores():
    locked=_freeze_fixture()
    check_frozen(locked)
    assert locked["neural_labels_available"] is False
    assert locked["new_neural_trainings"]==0
    assert locked["candidate_count"]==12
    assert len(locked["ranking_best_first"])==12
    assert "neural_advantage" not in json.dumps(locked)
    assert len(locked["receipt_sha256"])==64


def test_sealed_receipt_rejects_posthoc_ranking_or_score_rewrite():
    locked=_freeze_fixture()
    changed=deepcopy(locked)
    changed["ranking_best_first"].reverse()
    with pytest.raises(PredictionRejected, match="digest"):
        check_frozen(changed)
    changed=deepcopy(locked)
    changed["predictions"][0]["classical_feature_score"]+=.02
    changed["receipt_sha256"]=digest({k:v for k,v in changed.items()
                                      if k!="receipt_sha256"})
    with pytest.raises(PredictionRejected, match="ranking"):
        check_frozen(changed)


def test_valid_real_classical_signal_on_historical_candidate_for_algorithm_smoke():
    # This is merely a one-bit function regression using OLD S-Box data.
    output=classical_signal(tuple(CANDIDATES[0]["sbox"]),1)
    assert 0 <= output["bit"] < 32
    assert -1 <= output["signed_holdout_advantage"] <= 1


def test_neural_result_count_and_dataset_seed_lock():
    locked=_freeze_fixture()
    outcomes=_fake_outcomes(locked)
    assert len(outcomes["runs"])==EXPECTED_TOTAL_NEURAL_TRAININGS==96
    assert len(validate_neural_outcomes(locked,outcomes))==12
    modified=deepcopy(outcomes)
    modified["runs"][0]["dataset_seed"]+=1
    with pytest.raises(PredictionRejected,match="seed"):
        validate_neural_outcomes(locked,modified)
    modified=deepcopy(outcomes)
    modified["runs"].pop()
    with pytest.raises(PredictionRejected,match="count"):
        validate_neural_outcomes(locked,modified)


def test_synthetic_perfect_ranking_passes_gate_but_is_not_scientific_evidence():
    locked=_freeze_fixture()
    result=evaluate(locked,_fake_outcomes(locked))
    assert result["candidate_count"]==12
    assert result["spearman_rho"]==pytest.approx(1)
    assert result["preregistered_gate_pass"] is True
    assert result["scientific_verdict"]=="SUPPORTED_WITHIN_PINNED_TOY_CIPHER_PANEL"
    assert result["one_sided_permutation_p"] < .05
    assert len(result["receipt_sha256"])==64


def test_synthetic_reversed_ranking_fails_without_refitting():
    locked=_freeze_fixture()
    result=evaluate(locked,_fake_outcomes(locked,reverse=True))
    assert result["spearman_rho"]==pytest.approx(-1)
    assert result["preregistered_gate_pass"] is False
    assert result["scientific_verdict"]=="NOT_SUPPORTED_OR_INCONCLUSIVE"


def test_fake_outcome_mismatched_prediction_digest_fails():
    locked=_freeze_fixture()
    outcomes=_fake_outcomes(locked)
    outcomes["prediction_receipt_sha256"]="0"*64
    with pytest.raises(PredictionRejected,match="unbound"):
        validate_neural_outcomes(locked,outcomes)


def test_no_exaggerated_success_from_missing_provenance():
    locked=_freeze_fixture()
    outcomes=_fake_outcomes(locked)
    outcomes["runs"][0]["dataset_fingerprint_sha256"]=None
    with pytest.raises(PredictionRejected,match="provenance"):
        validate_neural_outcomes(locked,outcomes)


def test_no_success_from_duplicated_replicate():
    locked=_freeze_fixture()
    outcomes=_fake_outcomes(locked)
    outcomes["runs"][1]=deepcopy(outcomes["runs"][0])
    with pytest.raises(PredictionRejected,match="duplicate"):
        validate_neural_outcomes(locked,outcomes)


def test_zero_variance_returns_inconclusive_correlation():
    assert spearman([.1]*12,list(range(12))) is None


def test_frozen_seed_registry_is_disjoint_from_prior_phase1o():
    from adversarial_sbox.experiment_seeds import (
        PHASE1O_DEV_SEEDS,PHASE1O_CONFIRM_RESERVED_SEEDS,
    )
    assert not set(PROSPECTIVE_SEEDS).intersection(
        PHASE1O_DEV_SEEDS+PHASE1O_CONFIRM_RESERVED_SEEDS
    )


def test_aggregate_partial_prefix_is_not_a_complete_panel():
    runs=[]
    for seed in PROSPECTIVE_SEEDS[:2]:
        result={
            "seed":seed,"status":"ineligible","reason":"no_exact_metric_terminal",
            "evaluations":340, "initial_population_sha256":"1"*64,
            "proposal_audit_sha256":"2"*64,
            "exact_metric_hits_in_ledger":0,
            "method":"fixed_budget_340_phase1o_multihotspot_classical_only",
            "neural_training_count":0,
        }
        result["source_payload_sha256"]=digest(result)
        runs.append(result)
    panel=aggregate_attempts(runs)
    assert panel["status"]=="PARTIAL_SEED_LEDGER_DO_NOT_RUN_NEURAL"
    assert panel["selected_count"]==0
    with pytest.raises(PredictionRejected):
        admit_panel(panel)
    reversed_ledger=list(reversed(runs))
    with pytest.raises(ValueError,match="reordered"):
        aggregate_attempts(reversed_ledger)
