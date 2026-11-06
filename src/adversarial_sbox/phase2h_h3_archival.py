"""Frozen Phase-2G classical membership-change audit for Phase 2H H3.

Receipt-only, train-free and held-out blind. Historical producer fields are
`entered`, `exited`, `score_caused_entered`, `max_abs_lat`.
Never pair entrants and exits arbitrarily by fingerprint order.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any


COORDINATES = ("nonlinearity", "differential_uniformity", "max_abs_lat", "algebraic_degree")


def _candidate_set(raw: Any, field: str) -> set[str]:
    if not isinstance(raw, (list, tuple)) or any(not isinstance(x, str) or not x for x in raw):
        raise ValueError(f"H3 invalid or missing {field} fingerprint list")
    if len(raw) != len(set(raw)):
        raise ValueError(f"H3 duplicate {field} fingerprints")
    return set(raw)


def _favorable_tuple(row: Mapping[str, Any]) -> tuple[float, float, float, float]:
    if not isinstance(row, Mapping):
        raise ValueError("H3 missing candidate classical ledger record")
    metrics: list[float] = []
    for key in COORDINATES:
        value = row.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"H3 missing/nonnumeric historical classical coordinate {key}")
        number = float(value)
        if not isfinite(number):
            raise ValueError(f"H3 nonfinite historical classical coordinate {key}")
        metrics.append(number)
    return (metrics[0], -metrics[1], -metrics[2], metrics[3])


def _ledger_index(raw: Any) -> dict[str, tuple[float, float, float, float]]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("H3 original classical evaluation ledger is absent or empty")
    index: dict[str, tuple[float, float, float, float]] = {}
    for row in raw:
        if not isinstance(row, Mapping):
            raise ValueError("H3 malformed classical ledger row")
        fp = row.get("fingerprint")
        if not isinstance(fp, str) or not fp or fp in index:
            raise ValueError("H3 duplicate/invalid classical ledger fingerprint")
        index[fp] = _favorable_tuple(row)
    return index


def _classify(left: list[tuple[float, ...]], right: list[tuple[float, ...]]) -> dict[str, Any]:
    better = sum(a > b for a, b in zip(left, right))
    worse = sum(a < b for a, b in zip(left, right))
    equal = sum(a == b for a, b in zip(left, right))
    if better and worse:
        classification = "mixed"
    elif better:
        classification = "all_better_or_equal"
    elif worse:
        classification = "all_worse_or_equal"
    else:
        classification = "all_equal"
    if not left:
        pareto = "equal"
    else:
        mean_l = [sum(t[i] for t in left) / len(left) for i in range(4)]
        mean_r = [sum(t[i] for t in right) / len(right) for i in range(4)]
        ge = all(a >= b for a, b in zip(mean_l, mean_r))
        le = all(a <= b for a, b in zip(mean_l, mean_r))
        pareto = "equal" if ge and le else "pareto_better" if ge else "pareto_worse" if le else "mixed"
    return {
        "n_order_stat_better": better,
        "n_order_stat_worse": worse,
        "n_order_stat_equal": equal,
        "order_stat_classification": classification,
        "mean_coordinate_pareto_classification": pareto,
    }


def classical_distortion_from_frozen_receipts(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate only actually available original evidence; reject partial/tampered inputs.

    Synthetic older Phase-2H fixtures supply no ledger/selected sets: return
    explicit unavailable instead of a false zero or a fabricated successful test.
    """
    events = raw.get("selection_events")
    if not isinstance(events, (list, tuple)):
        raise ValueError("H3 selection event collection absent")
    ledger_raw = raw.get("classical_evaluation_ledger")
    fields = ("selected_before", "selected_after", "entered", "exited", "score_caused_entered")
    event_schema = [isinstance(e, Mapping) and all(f in e for f in fields) for e in events]
    if ledger_raw is None and not any(event_schema):
        return {
            "available": False,
            "reason": "missing original historical selected sets and classical evaluation ledger",
            "paired_membership_changes": None,
            "entered_worse_primary_tuple": None,
            "entered_better_primary_tuple": None,
            "equal_primary_tuple": None,
            "unavailable_pairs": None,
            "by_generation": {},
            "event_records": [],
        }
    if ledger_raw is None or not events or not all(event_schema):
        raise ValueError("H3 partial original archival event/ledger schema; refuse incomplete result")
    ledger = _ledger_index(ledger_raw)
    if len(ledger) != 340:
        raise ValueError("H3 original Phase-2G ledger must contain 340 unique candidates")
    if len(events) != 40:
        raise ValueError("H3 original Phase-2G receipt requires 40 event rows")
    seen: set[tuple[int, str]] = set()
    event_rows: list[dict[str, Any]] = []
    outcome_counts: Counter[str] = Counter()
    pareto_counts: Counter[str] = Counter()
    by_generation: dict[str, dict[str, int]] = {}
    for idx, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise ValueError("H3 malformed event")
        generation = int(event.get("generation", -1))
        stage = str(event.get("stage", ""))
        identity = (generation, stage)
        if generation not in range(20) or stage not in ("shortlist", "survival") or identity in seen:
            raise ValueError("H3 duplicate/unknown event generation/stage")
        seen.add(identity)
        before = _candidate_set(event.get("selected_before"), "selected_before")
        after = _candidate_set(event.get("selected_after"), "selected_after")
        entered = _candidate_set(event.get("entered"), "entered")
        exited = _candidate_set(event.get("exited"), "exited")
        caused = _candidate_set(event.get("score_caused_entered"), "score_caused_entered")
        cutoff = int(event.get("cutoff", -1))
        if len(before) != cutoff or len(after) != cutoff:
            raise ValueError("H3 malformed selection cutoff")
        if entered != after - before or exited != before - after or len(entered) != len(exited):
            raise ValueError("H3 entered/exited sets contradict source selected_before/after")
        if bool(entered) != bool(event.get("membership_changed")):
            raise ValueError("H3 event membership_changed flag mismatch")
        eligible = bool(event.get("neural_selection_enabled")) and bool(event.get("boundary_opportunity"))
        if caused != entered if eligible else bool(caused or entered):
            raise ValueError("H3 score_caused_entered not consistent with frozen event")
        for fp in before | after:
            if fp not in ledger:
                raise ValueError("H3 selected fingerprint missing from original ledger")
        left = sorted((ledger[fp] for fp in entered), reverse=True)
        right = sorted((ledger[fp] for fp in exited), reverse=True)
        label = _classify(left, right)
        outcome_counts[label["order_stat_classification"]] += 1
        pareto_counts[label["mean_coordinate_pareto_classification"]] += 1
        generation_row = by_generation.setdefault(str(generation), {
            "event_count": 0, "changed_candidate_slots": 0,
            "entered_worse": 0, "entered_better": 0, "equal": 0,
        })
        generation_row["event_count"] += 1
        generation_row["changed_candidate_slots"] += len(left)
        generation_row["entered_worse"] += label["n_order_stat_worse"]
        generation_row["entered_better"] += label["n_order_stat_better"]
        generation_row["equal"] += label["n_order_stat_equal"]
        event_rows.append({
            "generation": generation, "stage": stage, "event_index": idx,
            "swapped_candidate_slots": len(left), **label,
        })
    if len(seen) != 40:
        raise ValueError("H3 missing generation/stage event pair")
    return {
        "available": True,
        "source": "original Phase2G selected set difference + 340-row max_abs_lat ledger",
        "pairing_semantics": "rank-sorted independent classical tuple multisets; not fingerprint pair-matching",
        "event_count": len(event_rows),
        "nonzero_event_count": sum(e["swapped_candidate_slots"] > 0 for e in event_rows),
        "paired_membership_changes": sum(e["swapped_candidate_slots"] for e in event_rows),
        "entered_worse_primary_tuple": sum(e["n_order_stat_worse"] for e in event_rows),
        "entered_better_primary_tuple": sum(e["n_order_stat_better"] for e in event_rows),
        "equal_primary_tuple": sum(e["n_order_stat_equal"] for e in event_rows),
        "unavailable_pairs": 0,
        "event_classifications": dict(sorted(outcome_counts.items())),
        "pareto_classifications": dict(sorted(pareto_counts.items())),
        "by_generation": by_generation,
        "event_records": event_rows,
        "causal_claim_supported": False,
    }
