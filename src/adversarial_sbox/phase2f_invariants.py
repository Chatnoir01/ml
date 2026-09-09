"""Independent fail-closed invariant checks for preregistered Phase 2F.

The evolutionary runner emits detailed selection instrumentation.  This module
re-validates that instrumentation without importing held-out Block X, so a
malformed/tampered arm cannot reach terminal freeze merely because its budgets
and neural receipts look valid.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .phase2f import ARMS, B1_DU_RADIUS, B1_LAT_RADIUS, B1_NL_RADIUS, EVOLUTION_GENERATIONS


def _key(value: Sequence[Any]) -> tuple[Any, int, int, int, int] | None:
    try:
        if len(value) != 5:
            return None
        return (
            bool(value[0]),
            int(value[1]),
            int(value[2]),
            int(value[3]),
            int(value[4]),
        )
    except (TypeError, ValueError):
        return None


def _same_members(left: Sequence[str], right: Sequence[str]) -> bool:
    return len(left) == len(right) and set(left) == set(right)


def event_invariant_report(event: Mapping[str, Any], *, arm: str) -> dict[str, Any]:
    """Re-check one recorded shortlist/survival boundary event.

    The checks intentionally use only the frozen classical instrumentation and
    Block-G score assignments already present in the arm result.
    """

    checks = {
        "arm_geometry": True,
        "band_geometry": True,
        "group_shape": True,
        "boundary_semantics": True,
        "complete_group_scoring": True,
        "no_outside_crossing": True,
        "ordering_semantics": True,
        "membership_accounting": True,
        "cross_key_flag_consistency": True,
        "control_classical_only": True,
        "budget_state": True,
    }

    if arm not in ARMS:
        checks["arm_geometry"] = False
        return {"pass": False, "checks": checks}

    try:
        generation = int(event.get("generation", -1))
        stage = str(event.get("stage", ""))
        cutoff = int(event.get("cutoff", -1))
        start = int(event.get("group_start", -1))
        end = int(event.get("group_end", -1))
        base_group = [str(value) for value in event.get("base_group", [])]
        final_group = [str(value) for value in event.get("final_group", [])]
        score_group = [str(value) for value in event.get("score_ordered_group", [])]
        reference_fp = str(event.get("cutoff_reference_fingerprint", ""))
        protected = _key(event.get("protected_key", ()))
        raw_keys = event.get("eligible_protected_keys", {})
        if not isinstance(raw_keys, Mapping):
            raw_keys = {}
        candidate_keys = {str(name): _key(value) for name, value in raw_keys.items()}
    except (TypeError, ValueError):
        for name in checks:
            checks[name] = False
        return {"pass": False, "checks": checks}

    checks["group_shape"] = bool(
        0 <= generation < EVOLUTION_GENERATIONS
        and stage in {"shortlist", "survival"}
        and cutoff >= 1
        and 0 <= start <= cutoff - 1 < end
        and end - start == len(base_group)
        and len(base_group) == len(set(base_group))
        and reference_fp in base_group
        and protected is not None
        and set(candidate_keys) == set(base_group)
        and all(value is not None for value in candidate_keys.values())
    )

    expected_opportunity = bool(start < cutoff < end)
    checks["boundary_semantics"] = bool(
        bool(event.get("boundary_opportunity")) == expected_opportunity
    )

    expected_kind = "exact_key" if arm == "O0" else "b1_contiguous_band"
    checks["arm_geometry"] = str(event.get("group_kind", "")) == expected_kind

    if checks["group_shape"]:
        assert protected is not None
        if arm == "O0":
            checks["arm_geometry"] = bool(
                checks["arm_geometry"]
                and all(value == protected for value in candidate_keys.values())
            )
        else:
            band_ok = True
            for value in candidate_keys.values():
                assert value is not None
                band_ok &= bool(
                    value[0] == protected[0]
                    and abs(value[1] - protected[1]) <= B1_NL_RADIUS
                    and abs(value[2] - protected[2]) <= B1_DU_RADIUS
                    and abs(value[3] - protected[3]) <= B1_LAT_RADIUS
                    and value[4] == protected[4]
                )
            band_ok &= candidate_keys.get(reference_fp) == protected
            checks["band_geometry"] = bool(band_ok)
    else:
        checks["band_geometry"] = False

    scored = bool(event.get("scored"))
    assigned = event.get("assigned_scores", {})
    if scored:
        if not isinstance(assigned, Mapping):
            checks["complete_group_scoring"] = False
            assigned = {}
        else:
            try:
                finite = all(math.isfinite(float(value)) for value in assigned.values())
            except (TypeError, ValueError):
                finite = False
            checks["complete_group_scoring"] = bool(
                set(str(name) for name in assigned) == set(base_group) and finite
            )
    else:
        checks["complete_group_scoring"] = "assigned_scores" not in event or not assigned

    checks["no_outside_crossing"] = bool(
        _same_members(base_group, final_group)
        and _same_members(base_group, score_group)
    )

    if scored and checks["complete_group_scoring"] and arm != "C":
        assigned_float = {str(name): float(value) for name, value in assigned.items()}
        expected_final = sorted(base_group, key=lambda candidate: assigned_float[candidate])
        checks["ordering_semantics"] = final_group == expected_final
    elif arm == "C":
        checks["ordering_semantics"] = final_group == base_group

    if scored:
        selected_before = {str(value) for value in event.get("selected_before", [])}
        selected_after = {str(value) for value in event.get("selected_after", [])}
        entered = {str(value) for value in event.get("entered", [])}
        exited = {str(value) for value in event.get("exited", [])}
        expected_entered = selected_after - selected_before
        expected_exited = selected_before - selected_after
        checks["membership_accounting"] = bool(
            entered == expected_entered
            and exited == expected_exited
            and bool(event.get("membership_changed")) == bool(selected_before != selected_after)
            and entered.issubset(set(base_group))
            and exited.issubset(set(base_group))
        )

        if checks["group_shape"]:
            assert protected is not None
            expected_cross = any(candidate_keys[name] != protected for name in entered)
            checks["cross_key_flag_consistency"] = bool(
                bool(event.get("cross_protected_key_membership_change")) == expected_cross
            )
            if arm == "O0":
                checks["arm_geometry"] = bool(checks["arm_geometry"] and not expected_cross)
    else:
        checks["membership_accounting"] = not bool(event.get("membership_changed"))
        checks["cross_key_flag_consistency"] = not bool(
            event.get("cross_protected_key_membership_change")
        )

    if arm == "C":
        checks["control_classical_only"] = bool(
            not bool(event.get("membership_changed"))
            and not bool(event.get("ordering_changed"))
            and not bool(event.get("cross_protected_key_membership_change"))
            and not list(event.get("score_caused_entered", []))
            and final_group == base_group
        )

    if str(event.get("event", "")) == "score_budget_closed":
        checks["budget_state"] = bool(
            not scored
            and bool(event.get("blocked_by_budget"))
            and bool(event.get("observational_only"))
            and bool(event.get("selection_closed_after"))
        )
    elif bool(event.get("selection_closed_before")) and bool(event.get("boundary_opportunity")):
        checks["budget_state"] = bool(
            not scored
            and bool(event.get("observational_only"))
            and bool(event.get("selection_closed_after"))
        )

    return {"pass": all(checks.values()), "checks": checks}


def _lineage_instrumentation_ok(run: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> bool:
    diagnostics = run.get("lineage_diagnostics", [])
    if not isinstance(diagnostics, list):
        return False
    indexed = {
        int(item.get("event_index", -1)): item
        for item in diagnostics
        if isinstance(item, Mapping)
    }
    expected_indices = [
        index for index, event in enumerate(events) if list(event.get("score_caused_entered", []))
    ]
    if set(indexed) != set(expected_indices):
        return False
    for index in expected_indices:
        event = events[index]
        item = indexed[index]
        if int(item.get("generation", -1)) != int(event.get("generation", -2)):
            return False
        if str(item.get("stage", "")) != str(event.get("stage", "missing")):
            return False
        entered_records = item.get("entered", [])
        if not isinstance(entered_records, list):
            return False
        fps = {str(record.get("fingerprint", "")) for record in entered_records if isinstance(record, Mapping)}
        if fps != {str(value) for value in event.get("score_caused_entered", [])}:
            return False
        for record in entered_records:
            if not isinstance(record, Mapping):
                return False
            for key in (
                "direct_plus_1",
                "descendant_plus_1",
                "direct_plus_2",
                "descendant_plus_2",
                "direct_plus_5",
                "descendant_plus_5",
                "terminal_self",
                "terminal_descendant",
            ):
                if key not in record:
                    return False
    return True


def arm_invariant_report(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one complete Phase 2F arm result independent of its SHA receipt."""

    arm = str(run.get("arm", ""))
    events_raw = run.get("selection_events", [])
    events = [event for event in events_raw if isinstance(event, Mapping)] if isinstance(events_raw, list) else []
    expected_schedule = {
        (generation, stage)
        for generation in range(EVOLUTION_GENERATIONS)
        for stage in ("shortlist", "survival")
    }
    actual_schedule = {
        (int(event.get("generation", -1)), str(event.get("stage", "")))
        for event in events
    }
    event_reports = [event_invariant_report(event, arm=arm) for event in events]

    closure_ok = True
    closed = False
    for event in events:
        before = bool(event.get("selection_closed_before"))
        after = bool(event.get("selection_closed_after"))
        if before != closed:
            closure_ok = False
        if closed and bool(event.get("scored")):
            closure_ok = False
        closed = after

    generation_trace = run.get("generation_trace", [])
    trace_ok = bool(
        isinstance(generation_trace, list)
        and len(generation_trace) == EVOLUTION_GENERATIONS
        and [int(item.get("generation", -1)) for item in generation_trace if isinstance(item, Mapping)]
        == list(range(EVOLUTION_GENERATIONS))
    )

    terminal_ok = bool(
        str(run.get("terminal_selection_rule", "")) == "historical_classical_only"
        and str(run.get("terminal_fingerprint", ""))
        and isinstance(run.get("terminal_classical"), Mapping)
    )
    checks = {
        "event_schedule": bool(
            len(events) == 2 * EVOLUTION_GENERATIONS
            and actual_schedule == expected_schedule
        ),
        "event_invariants": bool(event_reports and all(item["pass"] for item in event_reports)),
        "budget_closure_monotonic": bool(closure_ok),
        "generation_trace": trace_ok,
        "lineage_instrumentation": _lineage_instrumentation_ok(run, events),
        "terminal_instrumentation": terminal_ok,
    }
    return {
        "pass": all(checks.values()),
        "arm": arm,
        "seed": int(run.get("seed", -1)),
        "checks": checks,
        "failed_event_indices": [
            index for index, report in enumerate(event_reports) if not report["pass"]
        ],
    }


def all_arm_invariants_report(arm_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate all supplied Phase 2F arm results and return a compact receipt."""

    cells = [arm_invariant_report(run) for run in arm_results]
    failed = [
        {"seed": int(cell["seed"]), "arm": str(cell["arm"])}
        for cell in cells
        if not bool(cell["pass"])
    ]
    return {
        "pass": bool(cells) and not failed,
        "cell_count": len(cells),
        "failed_cells": failed,
        "cells": cells,
    }
