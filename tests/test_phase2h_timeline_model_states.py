"""Audit actual A/F model-state receipts rather than arm-tagged training receipts."""
from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2h_timeline import build_divergence_timeline


def _models(digest: str) -> list[dict]:
    return [
        {
            "difference": difference, "replicate": replicate,
            "dataset_seed": 776003 + replicate,
            "model_seed": 786009 + replicate,
            "state_sha256": digest,
        }
        for difference in (1, 256)
        for replicate in range(8)
    ]


def _arm(tag: str) -> dict:
    return {"checkpoints": [
        {
            "generation": generation,
            "curriculum_fingerprints": ["same"] if generation == 0 else [tag, str(generation)],
            "population_after_fingerprints": ["same"] if generation == 0 else [tag],
            "model_receipts": _models("a" * 64),
            # This intentionally differs between arms despite byte-identical model states:
            "training_receipt_sha256": (tag * 64)[:64],
        }
        for generation in (0, 5, 10, 15)
    ]}


def test_arm_scoped_receipts_differ_but_actual_model_states_match() -> None:
    a, f = _arm("a"), _arm("f")
    result = build_divergence_timeline(a, f)
    assert result["first_model_divergence_generation"] is None
    assert result["first_curriculum_divergence_generation"] == 5
    assert result["first_population_divergence_generation"] == 5
    assert result["earliest_divergence_generation"] == 5
    assert result["ordering_claim_available"] is False
    assert all(row["model_state_sha256_differing_count"] == 0 for row in result["checkpoints"])


def test_genuine_one_state_mismatch_is_detected_without_arm_receipt_guessing() -> None:
    a, f = _arm("a"), _arm("f")
    a["checkpoints"][0]["model_receipts"][0]["state_sha256"] = "b" * 64
    result = build_divergence_timeline(a, f)
    assert result["first_model_divergence_generation"] == 0
    assert result["checkpoints"][0]["model_state_sha256_differing_count"] == 1
    assert result["ordering_claim"] == "model_diverges_first"


@pytest.mark.parametrize("bad", [
    "missing_one", "duplicate_identity", "unequal_identity",
    "missing_one_arm", "invalid_state_hash", "missing_required_key",
])
def test_malformed_or_asymmetric_state_receipts_are_rejected(bad: str) -> None:
    a, f = _arm("a"), _arm("f")
    first = a["checkpoints"][0]["model_receipts"]
    if bad == "missing_one":
        first.pop()
    elif bad == "duplicate_identity":
        first[1] = copy.deepcopy(first[0])
    elif bad == "unequal_identity":
        first[0]["dataset_seed"] += 7
    elif bad == "missing_one_arm":
        a["checkpoints"][0].pop("model_receipts")
    elif bad == "invalid_state_hash":
        first[0]["state_sha256"] = "xyz"
    elif bad == "missing_required_key":
        first[0].pop("difference")
    with pytest.raises((ValueError, KeyError)):
        build_divergence_timeline(a, f)


def test_missing_both_actual_model_states_reports_unknown_not_equal() -> None:
    a, f = _arm("a"), _arm("f")
    for cp in a["checkpoints"] + f["checkpoints"]:
        cp.pop("model_receipts")
    result = build_divergence_timeline(a, f)
    assert result["first_model_divergence_generation"] is None
    assert result["checkpoints"][0]["model_same"] is None
    assert result["ordering_claim_available"] is False
    assert "unavailable" in result["ordering_note"]
