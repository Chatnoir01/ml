"""Only entirely synthetic Phase 2U neural receipts; NEVER train a model."""
from __future__ import annotations

import copy
from hashlib import sha256
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2u_neural_contract import (
    CANDIDATES, DATASET_SEEDS, DIFFERENCES, MODEL_SEEDS, NEURAL_ROWS,
    PREDICTION_SHA256, PROTOCOL, PROTOCOL_SHA256,
    SOURCE_PANEL_CANONICAL_SHA256,
    Phase2UOutcomeRejected, validate_phase2u_neural_receipts,
    analyze_supplied_phase2u_receipts,
)


def _hash(s: str) -> str:
    return sha256(s.encode("utf-8")).hexdigest()


def _synthetic() -> tuple[dict, dict]:
    prediction = {
        "prediction_receipt_sha256": PREDICTION_SHA256,
        "predictions": [
            {"fingerprint": _hash(f"synthetic-candidate-{i}"),
             "classical_feature_score": 0.100 + i * 0.01}
            for i in range(CANDIDATES)
        ],
    }
    runs = []
    for candidate in prediction["predictions"]:
        fp = candidate["fingerprint"]
        for difference in DIFFERENCES:
            for rep in range(len(DATASET_SEEDS)):
                runs.append({
                    "fingerprint": fp,
                    "difference": difference,
                    "replicate": rep,
                    "dataset_seed": DATASET_SEEDS[rep],
                    "model_seed": MODEL_SEEDS[rep],
                    "dataset_sha256": {name: _hash(f"{fp}:{difference}:{rep}:{name}")
                                       for name in ("train", "validation", "test")},
                    "initialization_sha256": _hash(f"same-seed-init:{rep}"),
                    "final_state_sha256": _hash(f"{fp}:{difference}:{rep}:state"),
                    "rng_state_sha256": _hash(f"{fp}:{difference}:{rep}:rng"),
                    "runtime_manifest_sha256": _hash("synthetic-runtime"),
                    "dependency_lock_sha256": _hash("synthetic-lock"),
                    "runner_commit_sha": "a" * 40,
                    "test_auc": 0.55 + candidate["classical_feature_score"] / 3,
                    "null_auc": 0.501,
                })
    assert len(runs) == NEURAL_ROWS
    outcome = {
        "schema_version": 1,
        "experiment": PROTOCOL["experiment"],
        "protocol_sha256": PROTOCOL_SHA256,
        "prediction_receipt_sha256": PREDICTION_SHA256,
        "source_panel_canonical_sha256": SOURCE_PANEL_CANONICAL_SHA256,
        "runs": runs,
    }
    return prediction, outcome


def _check(prediction, outcome):
    # The real executable calls the real verifier BEFORE comparing fixed SHA.
    # Unit tests intentionally substitute a synthetic prediction structure:
    # they cannot impersonate the actual original 2U SHA-256 precommit.
    with patch("adversarial_sbox.phase2u_neural_contract.verify_prediction_receipt"):
        return validate_phase2u_neural_receipts(prediction, outcome)


def test_complete_synthetic_receipts_are_structurally_accepted_not_authenticated():
    p, o = _synthetic()
    result = _check(p, o)
    assert len(result) == 12
    assert all(row["replicate_count"] == 8 for row in result)


def test_original_sealed_prediction_identity_is_mandatory():
    p, o = _synthetic()
    p["prediction_receipt_sha256"] = _hash("different or post-hoc ranking")
    with pytest.raises(Phase2UOutcomeRejected, match="originally frozen"):
        _check(p, o)


def test_protocol_and_original_source_identity_must_match():
    p, o = _synthetic()
    o["protocol_sha256"] = _hash("unregistered protocol")
    with pytest.raises(Phase2UOutcomeRejected, match="bound"):
        _check(p, o)
    p, o = _synthetic()
    o["source_panel_canonical_sha256"] = _hash("wrong panel")
    with pytest.raises(Phase2UOutcomeRejected, match="bound"):
        _check(p, o)


def test_missing_or_duplicate_neural_cells_rejected():
    p, o = _synthetic()
    o["runs"].pop()
    with pytest.raises(Phase2UOutcomeRejected, match="96"):
        _check(p, o)
    p, o = _synthetic()
    o["runs"][1] = copy.deepcopy(o["runs"][0])
    with pytest.raises(Phase2UOutcomeRejected, match="duplicate"):
        _check(p, o)


def test_seed_drift_and_missing_dataset_split_rejected():
    p, o = _synthetic()
    o["runs"][0]["model_seed"] += 1
    with pytest.raises(Phase2UOutcomeRejected, match="seed"):
        _check(p, o)
    p, o = _synthetic()
    o["runs"][0]["dataset_sha256"].pop("test")
    with pytest.raises(Phase2UOutcomeRejected, match="three dataset"):
        _check(p, o)


def test_false_auc_and_provenance_rejected():
    p, o = _synthetic()
    o["runs"][0]["test_auc"] = True
    with pytest.raises(Phase2UOutcomeRejected, match="AUC"):
        _check(p, o)
    p, o = _synthetic()
    o["runs"][0]["runner_commit_sha"] = "invalid"
    with pytest.raises(Phase2UOutcomeRejected, match="commit"):
        _check(p, o)
    p, o = _synthetic()
    o["runs"][0]["initialization_sha256"] = None
    with pytest.raises(Phase2UOutcomeRejected, match="initialization"):
        _check(p, o)


def test_reversed_rows_do_not_change_sorted_candidate_summary():
    p, o = _synthetic()
    first = _check(p, o)
    o["runs"].reverse()
    second = _check(p, o)
    assert first == second


def test_statistics_never_promote_synthetic_receipts_to_scientific_result():
    p, o = _synthetic()
    with patch("adversarial_sbox.phase2u_neural_contract.verify_prediction_receipt"):
        report = analyze_supplied_phase2u_receipts(p, o)
    assert report["supplied_outcome_row_count"] == 96
    assert report["candidate_count"] == 12
    assert report["authorizes_neural_training"] is False
    assert report["phase2r_provenance_gate_established"] is False
    assert report["scientific_validation_status"] == (
        "UNAUTHENTICATED_SUPPLIED_RECEIPTS_NOT_SCIENTIFIC_VERDICT"
    )


def test_mixed_runtime_or_source_revision_rejected():
    """A 96-row aggregate must not silently mix computational environments."""
    for field, message in (
        ("runtime_manifest_sha256", "runtime"),
        ("dependency_lock_sha256", "dependency"),
        ("runner_commit_sha", "commit"),
    ):
        p, o = _synthetic()
        o["runs"][-1][field] = (
            "b" * 40 if field == "runner_commit_sha"
            else _hash("different-" + field)
        )
        with pytest.raises(Phase2UOutcomeRejected, match="mixed " + ".*"):
            _check(p, o)


def test_identical_model_seed_requires_identical_initial_tensors():
    """Same explicitly fixed seed cannot produce candidate-specific initial weights."""
    p, o = _synthetic()
    o["runs"][-1]["initialization_sha256"] = _hash("different-init-but-same-seed")
    with pytest.raises(Phase2UOutcomeRejected, match="same model seed"):
        _check(p, o)


def test_dataset_split_hash_collision_rejected():
    p, o = _synthetic()
    o["runs"][0]["dataset_sha256"]["test"] = o["runs"][0]["dataset_sha256"]["train"]
    with pytest.raises(Phase2UOutcomeRejected, match="must be distinct"):
        _check(p, o)
