"""Frozen Phase-2G set-replacement semantics for Phase-2H H3 diagnostics."""

from __future__ import annotations

from adversarial_sbox.phase2h import _classical_distortion, _classical_tuple


def _metrics(
    fp: str,
    nl: int = 108,
    du: int = 4,
    lat: int = 32,
    degree: int = 7,
) -> dict:
    return {
        "fingerprint": fp,
        "nonlinearity": nl,
        "differential_uniformity": du,
        # Exact serialized Phase-2G ledger field.
        "max_abs_lat": lat,
        "algebraic_degree": degree,
    }


def _payload(
    *,
    entered: list[str] | None = None,
    exited: list[str] | None = None,
    ledger: list[dict] | None = None,
) -> dict:
    entrants = ["e"] if entered is None else entered
    leavers = ["x"] if exited is None else exited
    return {
        "selection_events": [
            {
                "generation": 5,
                "stage": "survivor",
                "neural_selection_enabled": True,
                "boundary_opportunity": True,
                "selected_before": ["shared", *leavers],
                "selected_after": ["shared", *entrants],
                "entered": entrants,
                "exited": leavers,
                "score_caused_entered": entrants,
            }
        ],
        "classical_evaluation_ledger": (
            [_metrics("e"), _metrics("x", nl=100, du=8, lat=64, degree=6)]
            if ledger is None
            else ledger
        ),
    }


def test_reads_real_frozen_ledger_and_exited_schema() -> None:
    result = _classical_distortion(_payload())
    assert result["examined_score_caused_events"] == 1
    assert result["set_comparison_counts"]["collectively_better"] == 1
    assert result["individual_pairing_authorized"] is False
    assert result["paired_membership_changes"] == 0
    assert result["by_generation"]["5"]["collectively_better"] == 1


def test_legacy_in_memory_correlation_name_is_explicitly_supported() -> None:
    assert _classical_tuple(
        {
            "nonlinearity": 110,
            "differential_uniformity": 4,
            "max_linear_correlation": 32,
            "algebraic_degree": 7,
        }
    ) == (110.0, -4.0, -32.0, 7.0)


def test_never_invents_pairing_when_multiple_replacements_are_mixed() -> None:
    payload = _payload(
        entered=["e1", "e2"],
        exited=["x1", "x2"],
        ledger=[
            _metrics("e1", nl=110, du=4, lat=32),
            _metrics("e2", nl=95, du=12, lat=80),
            _metrics("x1", nl=100, du=8, lat=64),
            _metrics("x2", nl=101, du=8, lat=64),
        ],
    )
    result = _classical_distortion(payload)
    assert result["set_comparison_counts"]["mixed_or_incomparable"] == 1
    assert result["set_comparison_counts"]["collectively_better"] == 0
    assert result["set_comparison_counts"]["collectively_worse"] == 0


def test_missing_exited_field_never_produces_a_comparison() -> None:
    payload = _payload()
    payload["selection_events"][0].pop("exited")
    payload["selection_events"][0]["score_caused_exited"] = ["x"]
    result = _classical_distortion(payload)
    assert result["set_comparison_counts"]["invalid_event_semantics"] == 1
    assert result["set_comparison_counts"]["collectively_better"] == 0


def test_missing_or_nonfinite_metric_remains_unavailable() -> None:
    payload = _payload(ledger=[_metrics("e"), _metrics("x", lat=64)])
    payload["classical_evaluation_ledger"][1]["max_abs_lat"] = float("nan")
    result = _classical_distortion(payload)
    assert result["set_comparison_counts"]["missing_metrics"] == 1


def test_event_set_membership_must_match_frozen_selection() -> None:
    payload = _payload()
    payload["selection_events"][0]["score_caused_entered"] = ["other"]
    result = _classical_distortion(payload)
    assert result["set_comparison_counts"]["invalid_event_semantics"] == 1


def test_duplicate_evidence_is_not_silently_collapsed() -> None:
    payload = _payload()
    payload["classical_evaluation_ledger"].append(_metrics("e"))
    result = _classical_distortion(payload)
    assert result["set_comparison_counts"]["missing_metrics"] == 1
