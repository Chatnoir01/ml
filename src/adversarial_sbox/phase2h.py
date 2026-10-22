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
from .phase2h_h1_gate import assess_h1_receipt_feasibility
from .phase2h_baseline import audit_checkpoint0_baseline

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
    """Direct primary coordinates only; never infer missing admissibility."""
    try:
        nl = float(raw["nonlinearity"])
        du = float(raw["differential_uniformity"])
        # The frozen Phase-2G evaluation ledger uses max_abs_lat; some
        # in-memory ClassicalMetrics objects use max_linear_correlation.
        correlation = raw["max_abs_lat"] if "max_abs_lat" in raw else raw["max_linear_correlation"]
        lc = float(correlation)
        degree = float(raw["algebraic_degree"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in (nl, du, lc, degree)):
        return None
    return (nl, -du, -lc, degree)


def _componentwise_comparison(
    entrant: tuple[float, ...], displaced: tuple[float, ...]
) -> str:
    """Partial order over explicit coordinates, not an invented total ranking."""
    if entrant == displaced:
        return "equal"
    if all(a >= b for a, b in zip(entrant, displaced)):
        return "better"
    if all(a <= b for a, b in zip(entrant, displaced)):
        return "worse"
    return "incomparable"


def _exact_fingerprints(raw: object) -> set[str] | None:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        return None
    if any(not isinstance(value, str) or not value for value in raw):
        return None
    result = set(raw)
    return result if len(result) == len(raw) else None


def _classical_distortion(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Conservatively compare *sets* of score-caused entrants and exits.

    The frozen 2G receipts contain `exited`, NOT `score_caused_exited`.
    Neither event schema nor scientific protocol defines an entrant-to-exit
    pairing, so lexicographically zipping fingerprints fabricates a mapping.
    Report dominance only when every entrant has the same componentwise
    relation to every displaced candidate; otherwise report incomparable.
    """
    source = raw.get("classical_evaluation_ledger")
    ledger: dict[str, Mapping[str, Any]] = {}
    invalid_ledger = False
    if isinstance(source, Mapping):
        ledger = {str(key): value for key, value in source.items() if isinstance(value, Mapping)}
        invalid_ledger = len(ledger) != len(source)
    elif isinstance(source, Sequence) and not isinstance(source, (str, bytes, bytearray)):
        for row in source:
            if not isinstance(row, Mapping) or not isinstance(row.get("fingerprint"), str):
                invalid_ledger = True
                continue
            fingerprint = row["fingerprint"]
            if not fingerprint or fingerprint in ledger:
                invalid_ledger = True
                continue
            ledger[fingerprint] = row
    else:
        invalid_ledger = True

    categories = (
        "collectively_worse",
        "collectively_better",
        "equal",
        "mixed_or_incomparable",
        "missing_metrics",
        "invalid_event_semantics",
    )
    counts = {name: 0 for name in categories}
    by_generation: dict[str, dict[str, int]] = {}
    examined = 0

    for event in _selection_events(raw):
        score_entered = _exact_fingerprints(event.get("score_caused_entered"))
        if score_entered is not None and len(score_entered) == 0:
            continue
        # Synthetic/incomplete receipts without score-caused changes are
        # not promoted to proven distortion.
        if score_entered is None and "score_caused_entered" not in event:
            continue
        examined += 1
        generation = str(int(event.get("generation", -1)))
        row = by_generation.setdefault(generation, {name: 0 for name in categories})
        before = _exact_fingerprints(event.get("selected_before"))
        after = _exact_fingerprints(event.get("selected_after"))
        entered = _exact_fingerprints(event.get("entered"))
        exited = _exact_fingerprints(event.get("exited"))
        if (
            score_entered is None
            or before is None or after is None
            or entered is None or exited is None
            or not bool(event.get("neural_selection_enabled"))
            or not bool(event.get("boundary_opportunity"))
            or score_entered != entered
            or entered != after - before
            or exited != before - after
            or len(entered) != len(exited)
            or not entered
        ):
            label = "invalid_event_semantics"
        elif invalid_ledger:
            label = "missing_metrics"
        else:
            values_in = [_classical_tuple(ledger.get(fp, {})) for fp in sorted(entered)]
            values_out = [_classical_tuple(ledger.get(fp, {})) for fp in sorted(exited)]
            if any(value is None for value in (*values_in, *values_out)):
                label = "missing_metrics"
            else:
                relations = {
                    _componentwise_comparison(a, b)
                    for a in values_in for b in values_out
                }
                if relations == {"worse"}:
                    label = "collectively_worse"
                elif relations == {"better"}:
                    label = "collectively_better"
                elif relations == {"equal"}:
                    label = "equal"
                else:
                    label = "mixed_or_incomparable"
        counts[label] += 1
        row[label] += 1

    return {
        "examined_score_caused_events": examined,
        "set_comparison_counts": counts,
        "by_generation": by_generation,
        "individual_pairing_authorized": False,
        "paired_membership_changes": 0,
        "warning": (
            "No causal entrant-to-exit pairing is present in Phase-2G receipts. "
            "Only conservative all-cross-pair componentwise dominance is reported; "
            "admissibility is not reconstructed."
        ),
    }


def _checkpoint_fingerprints(
    checkpoint: Mapping[str, Any], field: str
) -> frozenset[str] | None:
    """Unavailable checkpoint evidence is unknown, never an empty identical set."""
    raw = checkpoint.get(field)
    if raw is None or raw == []:
        return None
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError(f"malformed {field} evidence")
    if any(not isinstance(fp, str) or not fp for fp in raw):
        raise ValueError(f"malformed {field} fingerprint")
    if len(set(raw)) != len(raw):
        raise ValueError(f"duplicate {field} fingerprint")
    return frozenset(raw)


def _fingerprint_relation(left: frozenset[str] | None, right: frozenset[str] | None) -> dict[str, Any]:
    if left is None or right is None:
        return {"comparable": False, "jaccard": None, "identical": None, "intersection_size": None}
    union = left | right
    return {
        "comparable": True,
        "jaccard": float(len(left & right) / len(union)) if union else 1.0,
        "identical": left == right,
        "intersection_size": len(left & right),
    }


def _recurrence(raw: Mapping[str, Any]) -> dict[str, Any]:
    cps = _checkpoints(raw)
    curricula = {g: _checkpoint_fingerprints(cps[g], "curriculum_fingerprints")
                 for g in CHECKPOINT_GENERATIONS}
    populations = {g: _checkpoint_fingerprints(cps[g], "population_after_fingerprints")
                   for g in CHECKPOINT_GENERATIONS}
    # All six unordered pairs are retained, including adverse/null comparisons.
    matrix = []
    for i, left in enumerate(CHECKPOINT_GENERATIONS):
        for right in CHECKPOINT_GENERATIONS[i + 1:]:
            curr = _fingerprint_relation(curricula[left], curricula[right])
            pop = _fingerprint_relation(populations[left], populations[right])
            matrix.append({
                "left_generation": int(left),
                "right_generation": int(right),
                "adjacent": (right == CHECKPOINT_GENERATIONS[i + 1]),
                "curriculum_comparable": curr["comparable"],
                "curriculum_jaccard": curr["jaccard"],
                "curriculum_identical": curr["identical"],
                "curriculum_shared_fingerprint_count": curr["intersection_size"],
                "population_comparable": pop["comparable"],
                "population_jaccard": pop["jaccard"],
                "population_identical": pop["identical"],
                "population_shared_fingerprint_count": pop["intersection_size"],
            })
    digest_groups: dict[str, list[int]] = {}
    for generation in CHECKPOINT_GENERATIONS:
        digest_groups.setdefault(str(cps[generation]["curriculum_digest_sha256"]), []).append(int(generation))
    exact_pairs = [
        {"digest_sha256": digest, "generations": generations}
        for digest, generations in sorted(digest_groups.items())
        if len(generations) > 1
    ]
    return {
        "checkpoint_fingerprint_recurrence_matrix": matrix,
        "checkpoint_pair_count": len(matrix),
        "curriculum_pairs_comparable": sum(int(row["curriculum_comparable"]) for row in matrix),
        "population_pairs_comparable": sum(int(row["population_comparable"]) for row in matrix),
        "nonadjacent_checkpoint_overlap": [
            {
                "left_generation": row["left_generation"],
                "right_generation": row["right_generation"],
                "curriculum_jaccard": row["curriculum_jaccard"],
                "population_jaccard": row["population_jaccard"],
            }
            for row in matrix if not row["adjacent"]
        ],
        "exact_curriculum_digest_recurrence": bool(exact_pairs),
        "exact_curriculum_digest_recurrence_groups": exact_pairs,
    }


def _rank_reversals(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Only time-separated same-stage rankings can constitute rank reversal.

    A shortlist-vs-survivor disagreement at the same generation is a distinct
    selection context, not evidence that a model or curriculum reversed over time.
    Evidence contradicting itself within the same generation and stage remains
    ambiguous rather than silently creating a reversal.
    """
    observations: dict[tuple[str, str, str], dict[int, set[int]]] = {}
    comparable_events = 0
    for event in sorted(_selection_events(raw), key=_event_key):
        order = _rank_order(event)
        if order is None or len(set(order)) != len(order):
            continue
        stage = str(event.get("stage", ""))
        if not stage:
            continue
        comparable_events += 1
        positions = {fp: i for i, fp in enumerate(order)}
        generation = int(event.get("generation", -1))
        for i, left in enumerate(order):
            for right in order[i + 1:]:
                pair = tuple(sorted((left, right)))
                direction = 1 if positions[pair[0]] < positions[pair[1]] else -1
                observations.setdefault((stage, pair[0], pair[1]), {}).setdefault(
                    generation, set()
                ).add(direction)

    reversals = []
    ambiguous = []
    for (stage, a, b), by_generation in sorted(observations.items()):
        if any(len(directions) != 1 for directions in by_generation.values()):
            ambiguous.append({
                "stage": stage, "pair": [a, b],
                "conflicting_generations": sorted(
                    g for g, directions in by_generation.items() if len(directions) != 1
                ),
            })
            continue
        values = sorted((generation, next(iter(directions)))
                        for generation, directions in by_generation.items())
        if len(values) >= 2 and len({direction for _, direction in values}) > 1:
            reversals.append({
                "stage": stage,
                "pair": [a, b],
                "observations": [
                    {"generation": generation, "direction": direction}
                    for generation, direction in values
                ],
            })
    return {
        "comparable_event_count": comparable_events,
        "pairwise_reversal_count": len(reversals),
        "pairwise_reversals": reversals,
        "ambiguous_pair_stage_count": len(ambiguous),
        "ambiguous_pairs": ambiguous,
        "comparison_scope": "same_stage_distinct_generation",
        "true_rank_reversal_observed": bool(reversals),
    }


def _h2_motion_classification(raw: Mapping[str, Any]) -> dict[str, Any]:
    recurrence = _recurrence(raw)
    reversal = _rank_reversals(raw)
    drift = _curriculum_drift(raw)
    exact = bool(recurrence["exact_curriculum_digest_recurrence"])
    reversed_rank = bool(reversal["true_rank_reversal_observed"])
    moved = int(drift["transition_change_count"]) > 0
    if reversed_rank:
        classification = "rank_direction_reversal_observed"
    elif exact:
        classification = "exact_recurrence_without_rank_reversal"
    elif moved:
        classification = "drift_without_recurrence_or_rank_reversal"
    else:
        classification = "stable_no_motion"
    return {
        "classification": classification,
        "curriculum_moved": moved,
        "exact_recurrence_observed": exact,
        "rank_direction_reversal_observed": reversed_rank,
        "cycling_supported_by_receipts": exact and reversed_rank,
        "note": "movement alone is not classified as cycling",
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
            "A_H1_feasibility": assess_h1_receipt_feasibility(adaptive),
            "F_H1_feasibility": assess_h1_receipt_feasibility(fixed),
            "A_curriculum": _curriculum_drift(adaptive),
            "F_curriculum": _curriculum_drift(fixed),
            "A_mechanism": _mechanism_events(adaptive),
            "F_mechanism": _mechanism_events(fixed),
            "A_vs_F_rank": _rank_diagnostics(adaptive, fixed),
            "A_classical_distortion": _classical_distortion(adaptive),
            "F_classical_distortion": _classical_distortion(fixed),
            "A_recurrence": _recurrence(adaptive),
            "F_recurrence": _recurrence(fixed),
            "A_rank_reversal": _rank_reversals(adaptive),
            "F_rank_reversal": _rank_reversals(fixed),
            "A_H2_motion": _h2_motion_classification(adaptive),
            "F_H2_motion": _h2_motion_classification(fixed),
            "A_vs_F_timeline": build_divergence_timeline(adaptive, fixed),
            "A_vs_F_checkpoint0_provenance": audit_checkpoint0_baseline(adaptive, fixed),
        }

    ordering_summary = {
        "single_signal_first_count": 0,
        "checkpoint_tie_count": 0,
        "unresolved_count": 0,
        "baseline_equivalent_seed_count": 0,
        "baseline_non_equivalent_seed_count": 0,
        "baseline_unknown_seed_count": 0,
        "baseline_non_equivalent_seeds": [],
        "claims": {},
    }
    for seed, row in seeds.items():
        timeline = row["A_vs_F_timeline"]
        baseline = timeline.get("initial_baseline_equivalent")
        if baseline is True:
            ordering_summary["baseline_equivalent_seed_count"] += 1
        elif baseline is False:
            ordering_summary["baseline_non_equivalent_seed_count"] += 1
            ordering_summary["baseline_non_equivalent_seeds"].append(int(seed))
        else:
            ordering_summary["baseline_unknown_seed_count"] += 1
        claim = timeline.get("ordering_claim")
        if claim is not None:
            ordering_summary["single_signal_first_count"] += 1
            ordering_summary["claims"][seed] = claim
        elif (
            timeline.get("earliest_divergence_generation") is None
            or timeline.get("ordering_unresolved_due_to_missing_evidence")
            or timeline.get("ordering_unresolved_due_to_baseline")
        ):
            ordering_summary["unresolved_count"] += 1
            ordering_summary["claims"][seed] = None
        else:
            ordering_summary["checkpoint_tie_count"] += 1
            ordering_summary["claims"][seed] = None

    h1_complete_hash_grids = sum(
        int(row[f"{arm}_H1_feasibility"]["hash_receipt_grid_complete"])
        for row in seeds.values()
        for arm in PRIMARY_ARMS
    )
    h1_evaluated_cells = len(seeds) * len(PRIMARY_ARMS)

    checkpoint0_counts: dict[str, int] = {}
    checkpoint0_model_mismatch_count = 0
    checkpoint0_mismatched_seed_details: list[dict[str, Any]] = []
    for seed, row in sorted(seeds.items(), key=lambda pair: int(pair[0])):
        audit = row["A_vs_F_checkpoint0_provenance"]
        status = str(audit["status"])
        checkpoint0_counts[status] = checkpoint0_counts.get(status, 0) + 1
        if status == "MATCHED_DECLARED_INPUTS_DIFFERENT_MODEL_HASHES":
            checkpoint0_model_mismatch_count += 1
            checkpoint0_mismatched_seed_details.append({
                "seed": int(seed),
                "different_model_state_sha256_count": audit["model_state_sha256_mismatches"],
                "mismatches_by_difference": audit["mismatches_by_difference"],
            })

    motion_counts: dict[str, int] = {}
    cycling_seeds: list[int] = []
    reversal_seeds: list[int] = []
    for seed, row in seeds.items():
        motion = row["A_H2_motion"]
        classification = str(motion["classification"])
        motion_counts[classification] = motion_counts.get(classification, 0) + 1
        if bool(motion["cycling_supported_by_receipts"]):
            cycling_seeds.append(int(seed))
        if bool(motion["rank_direction_reversal_observed"]):
            reversal_seeds.append(int(seed))

    if cycling_seeds:
        mechanism_verdict = "phase2h_receipt_level_cycling_evidence_observed"
    elif reversal_seeds:
        mechanism_verdict = "phase2h_rank_reversal_without_cycling_evidence"
    elif motion_counts.get("drift_without_recurrence_or_rank_reversal", 0):
        mechanism_verdict = "phase2h_drift_without_cycling_evidence"
    else:
        mechanism_verdict = "phase2h_no_adaptive_motion_evidence"

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2H-diagnostics",
        "mode": "frozen_phase2g_receipts_only",
        "parent_phase2g_commit": PARENT_PHASE2G_COMMIT,
        "parent_phase2g_aggregate_sha256": PARENT_AGGREGATE_SHA256,
        "evolution_seeds": [int(seed) for seed in EVOLUTION_SEEDS],
        "primary_arms": list(PRIMARY_ARMS),
        "diagnostics": seeds,
        "mechanism_verdict": mechanism_verdict,
        "mechanism_verdict_basis": {
            "A_motion_classification_counts": motion_counts,
            "cycling_seed_count": len(cycling_seeds),
            "cycling_seeds": sorted(cycling_seeds),
            "rank_reversal_seed_count": len(reversal_seeds),
            "rank_reversal_seeds": sorted(reversal_seeds),
            "scope": "receipt_level_diagnostics_only",
            "does_not_modify_phase2g_verdict": True,
        },
        "A_vs_F_ordering_summary": ordering_summary,
        "checkpoint0_provenance_summary": {
            "seed_count": len(seeds),
            "statuses": dict(sorted(checkpoint0_counts.items())),
            "same_declared_inputs_model_mismatch_seed_count": checkpoint0_model_mismatch_count,
            "same_declared_inputs_model_mismatch_details": checkpoint0_mismatched_seed_details,
            "causal_explanation_established": False,
            "scope": "official_frozen_phase2g_checkpoint0_metadata_only",
        },
        "H1_evidence_summary": {
            "arm_cells_checked": h1_evaluated_cells,
            "complete_hash_receipt_grid_cells": h1_complete_hash_grids,
            "forgetting_matrix_supported_cells": 0,
            "status": "NO_GO_FROM_FROZEN_ARM_RECEIPTS",
            "scope": "receipt_only_no_retraining",
        },
        "causal_interpretation": {
            "causal_claim_supported": False,
            "reason": (
                "checkpoint ordering is observational; receipts do not identify "
                "an intervention isolating curriculum, population, or model effects"
            ),
        },
        "availability": {
            "curriculum_digest_drift": True,
            "A_vs_F_rank_turnover": True,
            "selection_mechanism_counts": True,
            "forgetting_matrix": False,
            "h1_feasibility_audited": True,
            "reason_for_missing_forgetting_matrix": (
                "frozen 2G arm receipts contain model SHA-256 identities and seed "
                "metadata, not independently verified checkpoint model state "
                "snapshots and cross-checkpoint immutable probe evaluations; "
                "must not re-train or invent missing H1 evidence"
            ),
            "candidate_level_classical_distortion": False,
            "event_set_classical_comparison": True,
            "event_set_classical_comparison_source": (
                "frozen Phase-2G events provide score_caused_entered, entered, exited, "
                "selected_before, selected_after and classical_evaluation_ledger; "
                "individual pairing and admissibility are not available"
            ),
        },
    }
    payload["diagnostic_sha256"] = _sha256(payload)
    return payload
