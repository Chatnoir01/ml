from __future__ import annotations

import inspect

import pytest

import adversarial_sbox.phase2c_diagnostics as phase2c_module
from adversarial_sbox.phase2b import EVOLUTION_SEEDS
from adversarial_sbox.phase2c_diagnostics import (
    ARMS,
    analyze_phase2c_artifacts,
    dump_phase2c_diagnostics,
)


def _cell(arm: str, seed: int, *, selection_receipts: int = 2) -> dict:
    fingerprints = [f"{arm}-{seed}-{index:02d}" for index in range(32)]
    receipts = [
        {
            "fingerprint": fingerprint,
            "neural_advantage": 0.01 + index / 1000.0,
            "role": "selection" if index < selection_receipts else "padding",
        }
        for index, fingerprint in enumerate(fingerprints)
    ]
    tie_fingerprints = fingerprints[:2]
    if arm == "control":
        assigned = {tie_fingerprints[0]: 0.1, tie_fingerprints[1]: 0.2}
    else:
        assigned = {tie_fingerprints[0]: 0.2, tie_fingerprints[1]: 0.1}
    return {
        "schema_version": 1,
        "phase": "2B",
        "seed": seed,
        "arm": arm,
        "oracle_candidate_scores": 32,
        "oracle_fitness_trainings": 512,
        "oracle_selection_closed": True,
        "oracle_receipts": receipts,
        "oracle_events": [
            {
                "event": "oracle_cutoff_tie",
                "mode": arm,
                "cutoff": 8,
                "protected_key": [1, 2, 3, 4, 5],
                "fingerprints": tie_fingerprints,
                "assigned_scores": assigned,
            },
            {
                "event": "oracle_selection_budget_closed",
                "cutoff": 20,
                "group_size": 3,
                "remaining": 1,
            },
        ],
    }


def _all_cells() -> list[dict]:
    return [_cell(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS]


def test_phase2c_artifact_only_diagnostics_are_deterministic_and_insufficient() -> None:
    payload = analyze_phase2c_artifacts(_all_cells())

    assert payload["cell_count"] == 27
    assert payload["classification"] == "phase2c_artifacts_insufficient"
    assert payload["new_neural_trainings"] == 0
    assert payload["new_evolution_runs"] == 0
    assert payload["phase2b_replays"] == 0
    assert "generation" in payload["missing_trace_fields"]
    assert "selected_before" in payload["missing_trace_fields"]
    assert payload["arm_summaries"]["control"]["tie_events"] == 9
    assert payload["arm_summaries"]["oracle"]["order_changed_tie_events"] == 9
    assert payload["arm_summaries"]["shuffled"]["order_changed_tie_events"] == 9
    assert payload["arm_summaries"]["oracle"]["selection_receipts"] == 18
    assert payload["arm_summaries"]["oracle"]["padding_receipts"] == 270

    first = dump_phase2c_diagnostics(payload)
    second = dump_phase2c_diagnostics(analyze_phase2c_artifacts(list(reversed(_all_cells()))))
    assert first == second


def test_phase2c_rejects_missing_and_duplicate_cells() -> None:
    cells = _all_cells()
    with pytest.raises(ValueError, match="exact 27-cell"):
        analyze_phase2c_artifacts(cells[:-1])

    duplicate = [*cells, dict(cells[0])]
    with pytest.raises(ValueError, match="duplicate"):
        analyze_phase2c_artifacts(duplicate)


def test_phase2c_rejects_unexpected_receipt_role_and_event() -> None:
    cells = _all_cells()
    cells[0]["oracle_receipts"][0]["role"] = "rescored"
    with pytest.raises(ValueError, match="receipt role"):
        analyze_phase2c_artifacts(cells)

    cells = _all_cells()
    cells[0]["oracle_events"][0]["event"] = "invented_event"
    with pytest.raises(ValueError, match="Oracle event"):
        analyze_phase2c_artifacts(cells)


def test_phase2c_analyzer_has_no_neural_or_validation_import_path() -> None:
    source = inspect.getsource(phase2c_module)
    assert "phase2b_oracle" not in source
    assert "phase2b_validation" not in source
    assert "score_fitness_candidate" not in source
    assert "run_arm" not in source
