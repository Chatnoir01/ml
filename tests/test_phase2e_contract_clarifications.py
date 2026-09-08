from __future__ import annotations

import pytest

from adversarial_sbox.phase2e import budget_geometry, tag_utilization_summary


def test_tag_summary_reports_score_caused_entries_and_creation_rates() -> None:
    run = {
        "selection_events": [
            {
                "generation": 1,
                "stage": "shortlist",
                "cutoff": 2,
                "group_start": 1,
                "group_end": 3,
                "boundary_opportunity": True,
                "selection_closed_before": False,
                "scored": True,
                "observational_only": False,
                "blocked_by_budget": False,
                "base_group": ["a", "b"],
                "score_ordered_group": ["b", "a"],
                "final_group": ["b", "a"],
                "active_tags": [],
                "score_caused_entered": ["b", "c"],
                "tag_created": ["b"],
                "tag_used": False,
            }
        ]
    }
    summary = tag_utilization_summary(run)
    assert summary["score_caused_entry_occurrences"] == 2
    assert summary["score_caused_entry_unique"] == 2
    assert summary["created_occurrences"] == 1
    assert summary["created_unique"] == 1
    assert summary["tag_creation_rate_per_score_caused_entry"] == pytest.approx(0.5)
    assert summary["tag_creation_unique_rate"] == pytest.approx(0.5)
    assert summary["by_stage"]["shortlist"]["score_caused_entry_occurrences"] == 2


def test_budget_geometry_reports_preclosure_and_scored_fractions_separately() -> None:
    run = {
        "selection_events": [
            {"stage": "shortlist", "boundary_opportunity": True, "selection_closed_before": False, "scored": True, "observational_only": False, "blocked_by_budget": False, "event": "selection_boundary"},
            {"stage": "shortlist", "boundary_opportunity": True, "selection_closed_before": False, "scored": False, "observational_only": True, "blocked_by_budget": True, "event": "score_budget_closed"},
            {"stage": "survival", "boundary_opportunity": True, "selection_closed_before": True, "scored": False, "observational_only": True, "blocked_by_budget": False, "event": "selection_boundary"},
        ]
    }
    overall = budget_geometry(run)["overall"]
    assert overall["preclosure_fraction"] == pytest.approx(2 / 3)
    assert overall["scored_fraction"] == pytest.approx(1 / 3)
    assert overall["actionable_fraction"] == pytest.approx(1 / 3)
