"""H3 historical schema repair: synthetic integrity and no-false-zero controls."""
from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2h_h3_archival import classical_distortion_from_frozen_receipts


def _fixture() -> dict:
    ledger = [
        {
            "fingerprint": f"p{i:03d}",
            "nonlinearity": 94 if i == 0 else 96 if i == 1 else 95,
            "differential_uniformity": 10,
            "max_abs_lat": 72,
            "algebraic_degree": 7,
        }
        for i in range(340)
    ]
    events = []
    for g in range(20):
        for stage in ("shortlist", "survival"):
            swap = g == 0 and stage == "shortlist"
            before = ["p001", "p002"]
            after = ["p000", "p002"] if swap else before[:]
            events.append({
                "generation": g,
                "stage": stage,
                "cutoff": 2,
                "neural_selection_enabled": True,
                "boundary_opportunity": True,
                "membership_changed": swap,
                "selected_before": before,
                "selected_after": after,
                "entered": ["p000"] if swap else [],
                "exited": ["p001"] if swap else [],
                "score_caused_entered": ["p000"] if swap else [],
            })
    return {"selection_events": events, "classical_evaluation_ledger": ledger}


def test_original_historical_field_names_produce_real_comparisons() -> None:
    result = classical_distortion_from_frozen_receipts(_fixture())
    assert result["available"] is True
    assert result["event_count"] == 40
    assert result["nonzero_event_count"] == 1
    assert result["paired_membership_changes"] == 1
    assert result["entered_worse_primary_tuple"] == 1
    assert result["entered_better_primary_tuple"] == 0
    assert result["event_classifications"] == {
        "all_equal": 39,
        "all_worse_or_equal": 1,
    }
    assert result["pareto_classifications"] == {"equal": 39, "pareto_worse": 1}
    assert result["causal_claim_supported"] is False


def test_unknown_fixture_without_original_evidence_is_unavailable_not_zero() -> None:
    result = classical_distortion_from_frozen_receipts({
        "selection_events": [{"score_caused_entered": ["dummy"]}]
    })
    assert result["available"] is False
    assert result["paired_membership_changes"] is None
    assert "missing" in result["reason"]


@pytest.mark.parametrize("tamper", [
    "missing_exited",
    "missing_max_abs_lat",
    "wrong_entered",
    "wrong_exited",
    "wrong_caused",
    "wrong_cutoff",
    "missing_selected_after",
    "duplicate_selected_before",
    "duplicate_ledger",
    "missing_ledger_candidate",
    "nonfinite_metric",
    "duplicate_generation_stage",
])
def test_original_inconsistent_schema_fails_closed(tamper: str) -> None:
    raw = _fixture()
    first = raw["selection_events"][0]
    if tamper == "missing_exited":
        first.pop("exited")
    elif tamper == "missing_max_abs_lat":
        raw["classical_evaluation_ledger"][0].pop("max_abs_lat")
    elif tamper == "wrong_entered":
        first["entered"] = []
    elif tamper == "wrong_exited":
        first["exited"] = []
    elif tamper == "wrong_caused":
        first["score_caused_entered"] = []
    elif tamper == "wrong_cutoff":
        first["cutoff"] = 3
    elif tamper == "missing_selected_after":
        first.pop("selected_after")
    elif tamper == "duplicate_selected_before":
        first["selected_before"] = ["p001", "p001"]
    elif tamper == "duplicate_ledger":
        raw["classical_evaluation_ledger"][-1]["fingerprint"] = "p000"
    elif tamper == "missing_ledger_candidate":
        raw["classical_evaluation_ledger"][0]["fingerprint"] = "missing"
    elif tamper == "nonfinite_metric":
        raw["classical_evaluation_ledger"][0]["max_abs_lat"] = float("nan")
    elif tamper == "duplicate_generation_stage":
        raw["selection_events"][1]["stage"] = "shortlist"
    with pytest.raises(ValueError, match="H3"):
        classical_distortion_from_frozen_receipts(raw)


def test_fingerprint_renaming_cannot_change_quality_aggregation() -> None:
    source = _fixture()
    renamed = copy.deepcopy(source)
    mapping = {f"p{i:03d}": f"renamed{i:03d}" for i in range(340)}
    for row in renamed["classical_evaluation_ledger"]:
        row["fingerprint"] = mapping[row["fingerprint"]]
    fields = ("selected_before", "selected_after", "entered", "exited", "score_caused_entered")
    for event in renamed["selection_events"]:
        for field in fields:
            event[field] = [mapping[fingerprint] for fingerprint in event[field]]
    original = classical_distortion_from_frozen_receipts(source)
    changed = classical_distortion_from_frozen_receipts(renamed)
    assert original == changed


def test_event_list_order_independence_for_aggregate_counters() -> None:
    source = _fixture()
    reversed_input = copy.deepcopy(source)
    reversed_input["selection_events"] = list(reversed(reversed_input["selection_events"]))
    original = classical_distortion_from_frozen_receipts(source)
    changed = classical_distortion_from_frozen_receipts(reversed_input)
    for key in ("paired_membership_changes", "entered_worse_primary_tuple",
                "entered_better_primary_tuple", "event_classifications",
                "pareto_classifications", "by_generation"):
        assert original[key] == changed[key]
