"""Phase 2H deterministic diagnostics over frozen Phase-2G receipts.

No training, GA evolution, held-out opening, or Phase-2G mutation is performed here.
The module only derives diagnostics from already frozen Phase-2G arm-result payloads.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from .phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from .phase2h_timeline import build_divergence_timeline
from .phase2h_evidence import verify_evidence_manifest

PARENT_PHASE2G_COMMIT = "ba1aec133c50ddac246a54a70bb3ff2f0994df3a"
PARENT_AGGREGATE_SHA256 = "1df1812bc58e088c6a639d7ccbb94e1f3a02feb0ebd9f8b04e4ac81b1ea983d2"
PRIMARY_ARMS = ("A", "F")


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _checkpoints(raw: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    values = raw.get("checkpoints", ())
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ValueError("Phase-2H requires Phase-2G checkpoint receipts")
    out: dict[int, Mapping[str, Any]] = {}
    for item in values:
        if not isinstance(item, Mapping):
            raise ValueError("malformed Phase-2G checkpoint receipt")
        generation = int(item.get("generation", -1))
        if generation not in CHECKPOINT_GENERATIONS or generation in out:
            raise ValueError("Phase-2G checkpoint identity drift")
        digest = str(item.get("curriculum_digest_sha256", ""))
        if len(digest) != 64:
            raise ValueError("Phase-2G curriculum digest unavailable")
        out[generation] = item
    if set(out) != set(CHECKPOINT_GENERATIONS):
        raise ValueError("incomplete Phase-2G checkpoint set")
    return out


def _selection_events(raw: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    values = raw.get("selection_events", ())
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ValueError("Phase-2G selection events unavailable")
    if any(not isinstance(item, Mapping) for item in values):
        raise ValueError("malformed Phase-2G selection event")
    return tuple(values)


def _event_key(event: Mapping[str, Any]) -> tuple[int, str, tuple[str, ...]]:
    group = event.get("b1_group", ())
    if not isinstance(group, Sequence) or isinstance(group, (str, bytes, bytearray)):
        group = ()
    return (
        int(event.get("generation", -1)),
        str(event.get("stage", "")),
        tuple(sorted(str(value) for value in group)),
    )


def _rank_order(event: Mapping[str, Any]) -> tuple[str, ...] | None:
    group = event.get("b1_group", ())
    scores = event.get("assigned_scores")
    if not isinstance(group, Sequence) or isinstance(group, (str, bytes, bytearray)):
        return None
    group = tuple(str(value) for value in group)
    if not group or not isinstance(scores, Mapping):
        return None
    if int(event.get("scored_candidate_count", -1)) != len(group):
        return None
    try:
        numeric = {fp: float(scores[fp]) for fp in group}
    except (KeyError, TypeError, ValueError):
        return None
    if any(not math.isfinite(value) for value in numeric.values()):
        return None
    return tuple(sorted(group, key=lambda fp: (numeric[fp], fp)))


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(str(v) for v in left), set(str(v) for v in right)
    union = a | b
    return float(len(a & b) / len(union)) if union else 1.0


def _curriculum_drift(raw: Mapping[str, Any]) -> dict[str, Any]:
    cps = _checkpoints(raw)
    initial = str(cps[0]["curriculum_digest_sha256"])
    sequence = [str(cps[g]["curriculum_digest_sha256"]) for g in CHECKPOINT_GENERATIONS]
    transitions = [
        {
            "from_generation": int(left),
            "to_generation": int(right),
            "changed": str(cps[left]["curriculum_digest_sha256"])
            != str(cps[right]["curriculum_digest_sha256"]),
        }
        for left, right in zip(CHECKPOINT_GENERATIONS, CHECKPOINT_GENERATIONS[1:])
    ]
    return {
        "initial_digest_sha256": initial,
        "checkpoint_digest_sha256": {
            str(g): str(cps[g]["curriculum_digest_sha256"]) for g in CHECKPOINT_GENERATIONS
        },
        "changed_from_initial_count": sum(value != initial for value in sequence[1:]),
        "transition_change_count": sum(bool(item["changed"]) for item in transitions),
        "transitions": transitions,
    }


def _rank_diagnostics(adaptive: Mapping[str, Any], fixed: Mapping[str, Any]) -> dict[str, Any]:
    a = {_event_key(event): _rank_order(event) for event in _selection_events(adaptive)}
    f = {_event_key(event): _rank_order(event) for event in _selection_events(fixed)}
    shared = sorted(key for key in set(a) & set(f) if a[key] is not None and f[key] is not None)
    comparable = 0
    changed = 0
    by_generation: dict[str, dict[str, int]] = {}
    for key in shared:
        if set(a[key] or ()) != set(f[key] or ()):
            continue
        comparable += 1
        generation = str(key[0])
        row = by_generation.setdefault(generation, {"comparable": 0, "different_order": 0})
        row["comparable"] += 1
        if a[key] != f[key]:
            changed += 1
            row["different_order"] += 1
    return {
        "comparable_event_count": comparable,
        "different_order_count": changed,
        "different_order_fraction": float(changed / comparable) if comparable else None,
        "by_generation": by_generation,
    }


def _mechanism_events(raw: Mapping[str, Any]) -> dict[str, Any]:
    enabled = boundary = cross = caused = 0
    generations: set[int] = set()
    for event in _selection_events(raw):
        if bool(event.get("neural_selection_enabled", False)):
            enabled += 1
        if bool(event.get("boundary_opportunity", False)):
            boundary += 1
        if bool(event.get("cross_protected_key_membership_change", False)):
            cross += 1
        entered = event.get("score_caused_entered", ())
        if (
            isinstance(entered, Sequence)
            and not isinstance(entered, (str, bytes, bytearray))
            and len(entered) > 0
        ):
            caused += 1
            generations.add(int(event.get("generation", -1)))
    return {
        "neural_enabled_event_count": enabled,
        "boundary_opportunity_count": boundary,
        "cross_key_membership_change_count": cross,
        "score_caused_entry_event_count": caused,
        "score_caused_entry_generations": sorted(g for g in generations if g >= 0),
    }



def _classical_tuple(raw: Mapping[str, Any]) -> tuple[float, ...] | None:
    """Return the frozen primary-security tuple from a serialized ledger row."""
    try:
        nl = float(raw["nonlinearity"])
        du = float(raw["differential_uniformity"])
        lc = float(raw["max_linear_correlation"])
        degree = float(raw["algebraic_degree"])
    except (KeyError, TypeError, ValueError):
        return None
    # Admissibility is deliberately not reconstructed here: the artifact may omit
    # the frozen constraint object. Primary coordinates remain directly auditable.
    return (nl, -du, -lc, degree)


def _classical_distortion(raw: Mapping[str, Any]) -> dict[str, Any]:
    ledger_raw = raw.get("classical_evaluation_ledger", {})
    if isinstance(ledger_raw, Sequence) and not isinstance(ledger_raw, (str, bytes, bytearray)):
        ledger = {
            str(row.get("fingerprint", "")): row
            for row in ledger_raw
            if isinstance(row, Mapping) and row.get("fingerprint")
        }
    elif isinstance(ledger_raw, Mapping):
        ledger = {str(k): v for k, v in ledger_raw.items() if isinstance(v, Mapping)}
    else:
        ledger = {}

    paired = worse = better = equal = unavailable = 0
    by_generation: dict[str, dict[str, int]] = {}
    for event in _selection_events(raw):
        entered = event.get("score_caused_entered", ())
        exited = event.get("score_caused_exited", ())
        if not isinstance(entered, Sequence) or isinstance(entered, (str, bytes, bytearray)):
            continue
        if not isinstance(exited, Sequence) or isinstance(exited, (str, bytes, bytearray)):
            continue
        generation = str(int(event.get("generation", -1)))
        row = by_generation.setdefault(
            generation, {"paired": 0, "entered_worse": 0, "entered_better": 0, "equal": 0, "unavailable": 0}
        )
        for entrant, displaced in zip(sorted(map(str, entered)), sorted(map(str, exited))):
            left = _classical_tuple(ledger.get(entrant, {}))
            right = _classical_tuple(ledger.get(displaced, {}))
            if left is None or right is None:
                unavailable += 1
                row["unavailable"] += 1
                continue
            paired += 1
            row["paired"] += 1
            if left < right:
                worse += 1
                row["entered_worse"] += 1
            elif left > right:
                better += 1
                row["entered_better"] += 1
            else:
                equal += 1
                row["equal"] += 1
    return {
        "paired_membership_changes": paired,
        "entered_worse_primary_tuple": worse,
        "entered_better_primary_tuple": better,
        "equal_primary_tuple": equal,
        "unavailable_pairs": unavailable,
        "by_generation": by_generation,
        "warning": "entrant/exit pairing is deterministic fingerprint order; use only when event semantics are set replacement",
    }


def _recurrence(raw: Mapping[str, Any]) -> dict[str, Any]:
    cps = _checkpoints(raw)
    curriculum_sets = {
        g: set(map(str, cps[g].get("curriculum_fingerprints", ()))) for g in CHECKPOINT_GENERATIONS
    }
    population_sets = {
        g: set(map(str, cps[g].get("population_after_fingerprints", ()))) for g in CHECKPOINT_GENERATIONS
    }
    nonadjacent = []
    for i, left in enumerate(CHECKPOINT_GENERATIONS):
        for right in CHECKPOINT_GENERATIONS[i + 2 :]:
            c_union = curriculum_sets[left] | curriculum_sets[right]
            p_union = population_sets[left] | population_sets[right]
            nonadjacent.append({
                "left_generation": int(left),
                "right_generation": int(right),
                "curriculum_jaccard": float(len(curriculum_sets[left] & curriculum_sets[right]) / len(c_union)) if c_union else 1.0,
                "population_jaccard": float(len(population_sets[left] & population_sets[right]) / len(p_union)) if p_union else 1.0,
            })
    return {
        "nonadjacent_checkpoint_overlap": nonadjacent,
        "exact_curriculum_digest_recurrence": len({
            str(cps[g]["curriculum_digest_sha256"]) for g in CHECKPOINT_GENERATIONS
        }) < len(CHECKPOINT_GENERATIONS),
    }

def diagnose_phase2g_receipts(
    arm_results: Sequence[Mapping[str, Any]],
    *,
    phase2g_aggregate_sha256: str,
    evidence_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive the preregistered receipt-only subset of Phase-2H diagnostics."""

    if evidence_manifest is None:
        raise ValueError("Phase-2H requires a frozen evidence manifest")
    verify_evidence_manifest(arm_results, evidence_manifest)
    if str(evidence_manifest.get("parent_phase2g_commit", "")) != PARENT_PHASE2G_COMMIT:
        raise ValueError("Phase-2H evidence manifest parent commit mismatch")
    if str(evidence_manifest.get("parent_phase2g_aggregate_sha256", "")) != PARENT_AGGREGATE_SHA256:
        raise ValueError("Phase-2H evidence manifest parent aggregate mismatch")

    if str(phase2g_aggregate_sha256) != PARENT_AGGREGATE_SHA256:
        raise ValueError("Phase-2H parent aggregate binding failure")

    indexed: dict[tuple[int, str], Mapping[str, Any]] = {}
    for raw in arm_results:
        if not isinstance(raw, Mapping):
            raise ValueError("Phase-2H input must contain mappings")
        key = (int(raw.get("seed", -1)), str(raw.get("arm", "")))
        if key in indexed:
            raise ValueError("duplicate Phase-2G arm receipt")
        indexed[key] = raw

    expected = {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in PRIMARY_ARMS}
    missing = sorted(expected - set(indexed))
    if missing:
        raise ValueError(f"Phase-2H missing primary A/F receipts: {missing!r}")

    seeds: dict[str, Any] = {}
    for seed in EVOLUTION_SEEDS:
        frozen = int(seed)
        adaptive = indexed[(frozen, "A")]
        fixed = indexed[(frozen, "F")]
        seeds[str(frozen)] = {
            "A_curriculum": _curriculum_drift(adaptive),
            "F_curriculum": _curriculum_drift(fixed),
            "A_mechanism": _mechanism_events(adaptive),
            "F_mechanism": _mechanism_events(fixed),
            "A_vs_F_rank": _rank_diagnostics(adaptive, fixed),
            "A_classical_distortion": _classical_distortion(adaptive),
            "F_classical_distortion": _classical_distortion(fixed),
            "A_recurrence": _recurrence(adaptive),
            "F_recurrence": _recurrence(fixed),
            "A_vs_F_timeline": build_divergence_timeline(adaptive, fixed),
        }

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2H-diagnostics",
        "mode": "frozen_phase2g_receipts_only",
        "parent_phase2g_commit": PARENT_PHASE2G_COMMIT,
        "parent_phase2g_aggregate_sha256": PARENT_AGGREGATE_SHA256,
        "evolution_seeds": [int(seed) for seed in EVOLUTION_SEEDS],
        "primary_arms": list(PRIMARY_ARMS),
        "diagnostics": seeds,
        "availability": {
            "curriculum_digest_drift": True,
            "A_vs_F_rank_turnover": True,
            "selection_mechanism_counts": True,
            "forgetting_matrix": False,
            "reason_for_missing_forgetting_matrix": (
                "requires immutable probe evaluation of checkpoint model states; "
                "must not be reconstructed from absent evidence"
            ),
            "candidate_level_classical_distortion": True,
            "candidate_level_classical_distortion_source": (
                "official arm artifacts contain classical_evaluation_ledger plus score-caused entrants/exits"
            ),
        },
    }
    payload["diagnostic_sha256"] = _sha256(payload)
    return payload
