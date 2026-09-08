"""RED-first tests for Phase 2F band and control invariants.

These tests deliberately require an independent fail-closed invariant gate before
scientific execution is authorized. No neural training is executed here.
"""

import inspect

from adversarial_sbox.phase2f_invariants import event_invariant_report
import adversarial_sbox.phase2f_terminal_freeze as terminal_freeze


def _event(*, arm: str = "B1") -> dict:
    group_kind = "exact_key" if arm == "O0" else "b1_contiguous_band"
    protected = [True, 104, -8, -56, 7]
    candidate_keys = {
        "cut": protected,
        "enter": [True, 102, -8, -56, 7],
    }
    assigned = {"cut": 0.20, "enter": 0.10}
    final = ["enter", "cut"] if arm != "C" else ["cut", "enter"]
    entered = ["enter"] if arm != "C" else []
    exited = ["cut"] if arm != "C" else []
    return {
        "event": "selection_boundary",
        "generation": 0,
        "stage": "shortlist",
        "cutoff": 1,
        "group_kind": group_kind,
        "boundary_opportunity": True,
        "selection_closed_before": False,
        "selection_closed_after": False,
        "cutoff_reference_fingerprint": "cut",
        "cutoff_reference_metrics": {
            "nonlinearity": 104,
            "differential_uniformity": 8,
            "max_linear_correlation": 56,
            "algebraic_degree": 7,
            "fingerprint": "cut",
        },
        "protected_key": protected,
        "group_start": 0,
        "group_end": 2,
        "base_group": ["cut", "enter"],
        "eligible_protected_keys": candidate_keys,
        "scored": True,
        "observational_only": False,
        "blocked_by_budget": False,
        "assigned_scores": assigned,
        "score_ordered_group": final,
        "final_group": final,
        "selected_before": ["cut"],
        "selected_after": [final[0]],
        "membership_changed": arm != "C",
        "ordering_changed": arm != "C",
        "cross_protected_key_membership_change": arm in {"B1", "SB1"},
        "score_caused_entered": entered,
        "entered": entered,
        "exited": exited,
    }


def test_valid_b1_event_passes_independent_invariant_gate():
    report = event_invariant_report(_event(), arm="B1")
    assert report["pass"] is True


def test_b1_out_of_band_candidate_fails_geometry_gate():
    event = _event()
    event["eligible_protected_keys"]["enter"] = [True, 100, -8, -56, 7]
    report = event_invariant_report(event, arm="B1")
    assert report["pass"] is False
    assert report["checks"]["band_geometry"] is False


def test_partial_group_scoring_fails_closed():
    event = _event()
    del event["assigned_scores"]["enter"]
    report = event_invariant_report(event, arm="B1")
    assert report["pass"] is False
    assert report["checks"]["complete_group_scoring"] is False


def test_o0_cannot_cross_protected_key_boundary():
    event = _event(arm="O0")
    event["eligible_protected_keys"]["enter"] = [True, 102, -8, -56, 7]
    event["cross_protected_key_membership_change"] = True
    report = event_invariant_report(event, arm="O0")
    assert report["pass"] is False
    assert report["checks"]["arm_geometry"] is False


def test_classical_control_cannot_record_neural_membership_or_order_change():
    event = _event(arm="C")
    event["membership_changed"] = True
    event["ordering_changed"] = True
    event["entered"] = ["enter"]
    event["exited"] = ["cut"]
    event["score_caused_entered"] = ["enter"]
    event["cross_protected_key_membership_change"] = True
    report = event_invariant_report(event, arm="C")
    assert report["pass"] is False
    assert report["checks"]["control_classical_only"] is False


def test_terminal_freeze_must_consume_independent_invariant_gate():
    source = inspect.getsource(terminal_freeze.freeze_terminals)
    assert "all_arm_invariants_report" in source
    assert '"band_invariants"' in source
