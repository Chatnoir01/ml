"""Independent linkage checks between Phase 2F score events and Block-G receipts.

The evolutionary arm payload contains both the frozen neural receipts and the
selection-event assignments that claim to use them.  This module fails closed
unless those two views are exactly linked.  It never imports held-out Block X.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .phase2f import ARMS


def _finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _same_float(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-15)


def arm_score_linkage_report(run: Mapping[str, Any]) -> dict[str, Any]:
    """Verify that every recorded score assignment is backed by a Block-G receipt."""

    arm = str(run.get("arm", ""))
    checks = {
        "arm_known": arm in ARMS,
        "receipt_index_unique": True,
        "scored_candidates_have_receipts": True,
        "assigned_scores_match_receipts": True,
        "selection_receipts_are_exercised": True,
        "score_caused_entries_have_receipts": True,
    }

    receipts_raw = run.get("oracle_receipts", [])
    if not isinstance(receipts_raw, list):
        receipts_raw = []
        checks["receipt_index_unique"] = False

    receipt_scores: dict[str, float] = {}
    receipt_roles: dict[str, str] = {}
    for receipt in receipts_raw:
        if not isinstance(receipt, Mapping):
            checks["receipt_index_unique"] = False
            continue
        fp = str(receipt.get("fingerprint", ""))
        score = _finite(receipt.get("neural_advantage"))
        role = str(receipt.get("role", ""))
        if not fp or score is None or fp in receipt_scores:
            checks["receipt_index_unique"] = False
            continue
        receipt_scores[fp] = score
        receipt_roles[fp] = role

    exercised: set[str] = set()
    entered_by_score: set[str] = set()
    scored_event_count = 0

    events_raw = run.get("selection_events", [])
    events = events_raw if isinstance(events_raw, list) else []
    for event in events:
        if not isinstance(event, Mapping) or not bool(event.get("scored")):
            continue
        scored_event_count += 1
        group = [str(value) for value in event.get("base_group", [])]
        assigned_raw = event.get("assigned_scores", {})
        if not isinstance(assigned_raw, Mapping):
            checks["scored_candidates_have_receipts"] = False
            checks["assigned_scores_match_receipts"] = False
            continue

        assigned: dict[str, float] = {}
        for name, raw_value in assigned_raw.items():
            fp = str(name)
            value = _finite(raw_value)
            if value is None:
                checks["assigned_scores_match_receipts"] = False
                continue
            assigned[fp] = value

        if set(group) != set(assigned):
            checks["assigned_scores_match_receipts"] = False

        missing = [fp for fp in group if fp not in receipt_scores]
        if missing:
            checks["scored_candidates_have_receipts"] = False
        exercised.update(fp for fp in group if fp in receipt_scores)

        if arm == "SB1":
            if not missing and set(group) == set(assigned):
                actual = sorted(assigned[fp] for fp in group)
                expected = sorted(receipt_scores[fp] for fp in group)
                if len(actual) != len(expected) or any(
                    not _same_float(left, right) for left, right in zip(actual, expected)
                ):
                    checks["assigned_scores_match_receipts"] = False
        else:
            for fp in group:
                if fp not in assigned or fp not in receipt_scores:
                    continue
                if not _same_float(assigned[fp], receipt_scores[fp]):
                    checks["assigned_scores_match_receipts"] = False

        for fp in event.get("score_caused_entered", []):
            name = str(fp)
            entered_by_score.add(name)
            if name not in receipt_scores:
                checks["score_caused_entries_have_receipts"] = False

    selection_receipts = {
        fp for fp, role in receipt_roles.items() if role == "selection"
    }
    checks["selection_receipts_are_exercised"] = bool(
        selection_receipts == exercised
        or (not selection_receipts and scored_event_count == 0)
    )

    return {
        "pass": all(checks.values()),
        "arm": arm,
        "seed": int(run.get("seed", -1)),
        "checks": checks,
        "scored_event_count": int(scored_event_count),
        "selection_receipt_count": int(len(selection_receipts)),
        "exercised_receipt_count": int(len(exercised)),
        "score_caused_entry_count": int(len(entered_by_score)),
    }


def all_score_linkage_report(
    arm_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Verify event/receipt linkage for every supplied Phase 2F arm cell."""

    cells = [arm_score_linkage_report(run) for run in arm_results]
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
