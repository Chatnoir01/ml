"""Artifact-only diagnostics for frozen Phase 2B Oracle pressure.

Phase 2C-A must never rerun evolution or neural scoring. This module accepts
only already-frozen Phase 2B arm payloads and reports what their schema can and
cannot establish.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from typing import Any, Sequence

from .phase2b import (
    EVOLUTION_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
)

ARMS = ("control", "oracle", "shuffled")
EXPECTED_CELLS = {(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS}
ALLOWED_EVENT_TYPES = {"oracle_cutoff_tie", "oracle_selection_budget_closed"}
ALLOWED_RECEIPT_ROLES = {"selection", "padding"}
ALLOWED_CUTOFFS = {8, 20}

# These fields are required to distinguish actual cutoff membership changes,
# temporal persistence, and terminal erasure without reconstructive guesses.
TIE_FIELDS_REQUIRED_FOR_CAUSAL_TRACE = (
    "generation",
    "group_start",
    "group_end",
    "selected_before",
    "selected_after",
)

NON_MEASURABLE_WITH_PHASE2B_SCHEMA = (
    "complete_opportunity_density_after_selection_budget_closure",
    "exact_cutoff_membership_flips",
    "per_generation_intervention_timing",
    "one_two_five_generation_persistence",
    "descendant_survival_to_terminal",
    "terminal_rule_erasure_of_specific_oracle_interventions",
)


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _as_finite_float(value: Any, *, field: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite {field}")
    return result


def _stable_score_order(fingerprints: list[str], assigned_scores: dict[str, Any]) -> list[str]:
    missing = set(fingerprints) - set(assigned_scores)
    extra = set(assigned_scores) - set(fingerprints)
    if missing or extra:
        raise ValueError("assigned-score fingerprint set mismatch")
    indexed = list(enumerate(fingerprints))
    return [
        fingerprint
        for _index, fingerprint in sorted(
            indexed,
            key=lambda item: (
                _as_finite_float(assigned_scores[item[1]], field="assigned score"),
                item[0],
            ),
        )
    ]


def _analyze_cell(payload: dict[str, Any]) -> dict[str, Any]:
    if str(payload.get("phase")) != "2B":
        raise ValueError("Phase 2C-A accepts only frozen Phase 2B arm payloads")
    if int(payload.get("schema_version", -1)) != 1:
        raise ValueError("unexpected Phase 2B arm schema version")

    arm = str(payload.get("arm"))
    seed = int(payload.get("seed", -1))
    if arm not in ARMS or seed not in EVOLUTION_SEEDS:
        raise ValueError("unexpected Phase 2B arm/seed cell")

    if int(payload.get("oracle_candidate_scores", -1)) != ORACLE_SCORE_BUDGET_PER_ARM_SEED:
        raise ValueError("Phase 2B Oracle candidate-score budget drift")
    if int(payload.get("oracle_fitness_trainings", -1)) != FITNESS_TRAININGS_PER_ARM_SEED:
        raise ValueError("Phase 2B Oracle training budget drift")

    receipts = list(payload.get("oracle_receipts", []))
    if len(receipts) != ORACLE_SCORE_BUDGET_PER_ARM_SEED:
        raise ValueError("Phase 2B Oracle receipt count drift")
    receipt_roles: list[str] = []
    receipt_fingerprints: list[str] = []
    for receipt in receipts:
        role = str(receipt.get("role"))
        if role not in ALLOWED_RECEIPT_ROLES:
            raise ValueError(f"unexpected Phase 2B receipt role {role!r}")
        fingerprint = str(receipt.get("fingerprint", ""))
        if not fingerprint:
            raise ValueError("Phase 2B receipt missing fingerprint")
        _as_finite_float(receipt.get("neural_advantage"), field="receipt neural advantage")
        receipt_roles.append(role)
        receipt_fingerprints.append(fingerprint)
    if len(set(receipt_fingerprints)) != len(receipt_fingerprints):
        raise ValueError("duplicate Phase 2B Oracle receipt fingerprint")

    role_counts = Counter(receipt_roles)
    events = list(payload.get("oracle_events", []))
    tie_events = []
    close_events = []
    missing_trace_fields: set[str] = set()
    order_changed = 0
    group_sizes: list[int] = []

    for event in events:
        event_type = str(event.get("event"))
        if event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"unexpected Phase 2B Oracle event {event_type!r}")
        cutoff = int(event.get("cutoff", -1))
        if cutoff not in ALLOWED_CUTOFFS:
            raise ValueError("unexpected Phase 2B cutoff")

        if event_type == "oracle_selection_budget_closed":
            group_size = int(event.get("group_size", -1))
            remaining = int(event.get("remaining", -1))
            if group_size < 2 or remaining < 0:
                raise ValueError("invalid Phase 2B budget-close event")
            close_events.append(
                {
                    "cutoff": cutoff,
                    "group_size": group_size,
                    "remaining": remaining,
                }
            )
            continue

        mode = str(event.get("mode"))
        if mode != arm:
            raise ValueError("Phase 2B tie-event arm drift")
        fingerprints = [str(value) for value in event.get("fingerprints", [])]
        if len(fingerprints) < 2 or len(set(fingerprints)) != len(fingerprints):
            raise ValueError("invalid Phase 2B cutoff-tie fingerprint group")
        assigned_scores = dict(event.get("assigned_scores", {}))
        reordered = _stable_score_order(fingerprints, assigned_scores)
        changed = arm != "control" and reordered != fingerprints
        order_changed += int(changed)
        group_sizes.append(len(fingerprints))
        missing_trace_fields.update(
            field for field in TIE_FIELDS_REQUIRED_FOR_CAUSAL_TRACE if field not in event
        )
        tie_events.append(
            {
                "cutoff": cutoff,
                "group_size": len(fingerprints),
                "order_changed": bool(changed),
            }
        )

    selection_receipts = int(role_counts.get("selection", 0))
    padding_receipts = int(role_counts.get("padding", 0))
    if selection_receipts + padding_receipts != ORACLE_SCORE_BUDGET_PER_ARM_SEED:
        raise ValueError("Phase 2B Oracle receipt role accounting drift")

    return {
        "arm": arm,
        "seed": seed,
        "tie_events": len(tie_events),
        "shortlist_tie_events": sum(event["cutoff"] == 8 for event in tie_events),
        "survival_tie_events": sum(event["cutoff"] == 20 for event in tie_events),
        "order_changed_tie_events": order_changed,
        "budget_close_events": len(close_events),
        "selection_receipts": selection_receipts,
        "padding_receipts": padding_receipts,
        "selection_budget_fraction": selection_receipts / ORACLE_SCORE_BUDGET_PER_ARM_SEED,
        "oracle_selection_closed": bool(payload.get("oracle_selection_closed", False)),
        "tie_group_sizes": group_sizes,
        "budget_close_details": close_events,
        "missing_trace_fields": sorted(missing_trace_fields),
    }


def analyze_phase2c_artifacts(arm_payloads: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Analyze exactly the frozen 27 Phase 2B arm cells, without any replay."""

    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in arm_payloads:
        analyzed = _analyze_cell(dict(raw))
        key = (analyzed["arm"], analyzed["seed"])
        if key in cells:
            raise ValueError(f"duplicate Phase 2B arm/seed cell {key!r}")
        cells[key] = analyzed

    actual = set(cells)
    if actual != EXPECTED_CELLS:
        missing = sorted(EXPECTED_CELLS - actual)
        extra = sorted(actual - EXPECTED_CELLS)
        raise ValueError(f"Phase 2C-A requires exact 27-cell Phase 2B set; missing={missing}, extra={extra}")

    ordered_cells = [cells[(arm, int(seed))] for arm in ARMS for seed in EVOLUTION_SEEDS]
    arm_summaries: dict[str, Any] = {}
    for arm in ARMS:
        selected = [cell for cell in ordered_cells if cell["arm"] == arm]
        all_group_sizes = [size for cell in selected for size in cell["tie_group_sizes"]]
        arm_summaries[arm] = {
            "cells": len(selected),
            "tie_events": sum(cell["tie_events"] for cell in selected),
            "shortlist_tie_events": sum(cell["shortlist_tie_events"] for cell in selected),
            "survival_tie_events": sum(cell["survival_tie_events"] for cell in selected),
            "order_changed_tie_events": sum(cell["order_changed_tie_events"] for cell in selected),
            "budget_close_events": sum(cell["budget_close_events"] for cell in selected),
            "selection_receipts": sum(cell["selection_receipts"] for cell in selected),
            "padding_receipts": sum(cell["padding_receipts"] for cell in selected),
            "mean_selection_budget_fraction": sum(cell["selection_budget_fraction"] for cell in selected)
            / len(selected),
            "tie_group_sizes": all_group_sizes,
        }

    missing_trace_fields = sorted(
        {
            field
            for cell in ordered_cells
            for field in cell["missing_trace_fields"]
        }
    )

    non_measurable = list(NON_MEASURABLE_WITH_PHASE2B_SCHEMA)
    if missing_trace_fields:
        classification = "phase2c_artifacts_insufficient"
        classification_reason = (
            "Frozen Phase 2B events omit fields required to distinguish exact cutoff-membership "
            "changes, intervention timing, lineage persistence, and terminal erasure without replay."
        )
    else:
        # Phase 2C-A deliberately refuses to invent causal thresholds here. If a future
        # artifact schema contains the required fields, a preregistered classification
        # rule must be added before using outcomes to select among causal categories.
        classification = "phase2c_artifacts_insufficient"
        classification_reason = (
            "Causal trace fields are present, but Phase 2C-A has no preregistered outcome threshold "
            "for selecting a stronger causal category; successor classification logic requires a new preregistration."
        )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2C-A",
        "source_phase": "2B",
        "source_scientific_sha": "59066ad943fc85f24a21b4c2941cbcee4d23aeae",
        "source_workflow_run_id": 34064310593,
        "cell_count": len(ordered_cells),
        "cells": ordered_cells,
        "arm_summaries": arm_summaries,
        "missing_trace_fields": missing_trace_fields,
        "non_measurable": non_measurable,
        "classification": classification,
        "classification_reason": classification_reason,
        "new_neural_trainings": 0,
        "new_evolution_runs": 0,
        "phase2b_replays": 0,
    }
    payload["diagnostic_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def dump_phase2c_diagnostics(payload: dict[str, Any]) -> str:
    """Return deterministic pretty JSON for byte-identity checks."""

    return json.dumps(payload, sort_keys=True, indent=2) + "\n"
