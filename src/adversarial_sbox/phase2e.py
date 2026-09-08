"""Deterministic artifact-only diagnostics for frozen Phase 2D receipts."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import hashlib
import json
from typing import Any

SOURCE_RUN_ID = 34147455097
EXPECTED_MARKER_SHA = "2cc913e33cc5848f12ae5493f992b49fa89bc3d2"
EXPECTED_TERMINAL_FREEZE_SHA256 = (
    "8b50e71ab8fc082d1c49fa9b7da0e896c3ecf0f851a82500617bc34927799107"
)
EXPECTED_AGGREGATE_SHA256 = (
    "51f41197482c5695ed00267c69dfc81b937cf12871336457308755f8e5e64e5c"
)
EVOLUTION_SEEDS = (
    426011,
    426023,
    426037,
    426049,
    426061,
    426073,
    426089,
    426101,
    426113,
)
ARMS = ("C", "O0", "OP1", "SP1")
PERSISTENCE_ARMS = ("OP1", "SP1")
LINEAGE_ARMS = ("O0", "OP1", "SP1")

CLASSICAL_EVALUATIONS = 340
CANDIDATE_SCORES = 32
FITNESS_TRAININGS = 512

VALID_STATUS = "phase2e_artifact_diagnostics_valid"
INCONCLUSIVE_STATUS = "phase2e_inconclusive_artifact_provenance"

_LINEAGE_METRICS = (
    "direct_plus_1",
    "direct_plus_2",
    "direct_plus_5",
    "descendant_plus_1",
    "descendant_plus_2",
    "descendant_plus_5",
    "terminal_self",
    "terminal_descendant",
)
_REPLACEMENT_BUCKETS = (
    "strictly_better_classical_key_present",
    "same_key_not_selected",
    "lineage_not_present",
    "not_reconstructible",
)


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha_matches(payload: dict[str, Any], field: str) -> bool:
    stored = str(payload.get(field, ""))
    if len(stored) != 64:
        return False
    clean = {key: value for key, value in payload.items() if key != field}
    return hashlib.sha256(_canonical(clean)).hexdigest() == stored


def _seal(payload: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(payload, sort_keys=True))
    result.pop("scientific_payload_sha256", None)
    result["scientific_payload_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def _stage_name(value: Any) -> str:
    return "shortlist" if str(value) == "terminal_shortlist" else str(value)


def _new_tag_record() -> dict[str, Any]:
    return {
        "score_caused_entry_occurrences": 0,
        "score_caused_entry_fingerprints": set(),
        "created_occurrences": 0,
        "created_fingerprints": set(),
        "active_tag_appearances": 0,
        "active_fingerprints": set(),
        "order_changed_tag_occurrences": 0,
        "order_changed_fingerprints": set(),
        "membership_changed_tag_occurrences": 0,
        "membership_changed_fingerprints": set(),
        "expired_without_order_or_membership_occurrences": 0,
        "expired_unused_fingerprints": set(),
    }


def _freeze_tag_record(record: dict[str, Any]) -> dict[str, Any]:
    entrants = int(record["score_caused_entry_occurrences"])
    created = int(record["created_occurrences"])
    return {
        "score_caused_entry_occurrences": entrants,
        "score_caused_entry_unique": len(record["score_caused_entry_fingerprints"]),
        "created_occurrences": created,
        "created_unique": len(record["created_fingerprints"]),
        "tag_creation_rate_per_score_caused_entry": (
            float(created / entrants) if entrants else 0.0
        ),
        "active_tag_appearances": int(record["active_tag_appearances"]),
        "active_unique": len(record["active_fingerprints"]),
        "order_changed_tag_occurrences": int(record["order_changed_tag_occurrences"]),
        "order_changed_unique": len(record["order_changed_fingerprints"]),
        "membership_changed_tag_occurrences": int(
            record["membership_changed_tag_occurrences"]
        ),
        "membership_changed_unique": len(record["membership_changed_fingerprints"]),
        "expired_without_order_or_membership_occurrences": int(
            record["expired_without_order_or_membership_occurrences"]
        ),
        "expired_without_order_or_membership_unique": len(
            record["expired_unused_fingerprints"]
        ),
    }


def _merge_tag_record(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in (
        "score_caused_entry_occurrences",
        "created_occurrences",
        "active_tag_appearances",
        "order_changed_tag_occurrences",
        "membership_changed_tag_occurrences",
        "expired_without_order_or_membership_occurrences",
    ):
        target[key] += int(source[key])
    for key in (
        "score_caused_entry_fingerprints",
        "created_fingerprints",
        "active_fingerprints",
        "order_changed_fingerprints",
        "membership_changed_fingerprints",
        "expired_unused_fingerprints",
    ):
        target[key].update(source[key])


def _tag_event_details(event: dict[str, Any]) -> tuple[set[str], set[str]]:
    active = {str(value) for value in event.get("active_tags", []) if str(value)}
    score_group = [str(value) for value in event.get("score_ordered_group", [])]
    final_group = [str(value) for value in event.get("final_group", [])]
    score_positions = {fp: index for index, fp in enumerate(score_group)}
    final_positions = {fp: index for index, fp in enumerate(final_group)}
    order_changed = {
        fp
        for fp in active
        if fp in score_positions
        and fp in final_positions
        and score_positions[fp] != final_positions[fp]
    }
    membership_changed: set[str] = set()
    try:
        quota = int(event.get("cutoff", 0)) - int(event.get("group_start", 0))
        if 0 <= quota <= len(score_group) and len(final_group) == len(score_group):
            membership_changed = active & (
                set(final_group[:quota]) - set(score_group[:quota])
            )
    except (TypeError, ValueError):
        membership_changed = set()
    return order_changed, membership_changed


def tag_utilization_summary(run: dict[str, Any]) -> dict[str, Any]:
    """Summarize score-caused entries and one-generation tag utilization."""

    by_stage = {"shortlist": _new_tag_record(), "survival": _new_tag_record()}
    overall = _new_tag_record()
    for event in run.get("selection_events", []):
        stage = _stage_name(event.get("stage", ""))
        if stage not in by_stage:
            continue
        record = by_stage[stage]
        entrants_list = [
            str(value) for value in event.get("score_caused_entered", []) if str(value)
        ]
        created_list = [str(value) for value in event.get("tag_created", []) if str(value)]
        active_list = [str(value) for value in event.get("active_tags", []) if str(value)]
        active = set(active_list)
        order_changed, membership_changed = _tag_event_details(event)
        unused = active - order_changed - membership_changed

        record["score_caused_entry_occurrences"] += len(entrants_list)
        record["score_caused_entry_fingerprints"].update(entrants_list)
        record["created_occurrences"] += len(created_list)
        record["created_fingerprints"].update(created_list)
        record["active_tag_appearances"] += len(active_list)
        record["active_fingerprints"].update(active)
        record["order_changed_tag_occurrences"] += len(order_changed)
        record["order_changed_fingerprints"].update(order_changed)
        record["membership_changed_tag_occurrences"] += len(membership_changed)
        record["membership_changed_fingerprints"].update(membership_changed)
        record["expired_without_order_or_membership_occurrences"] += len(unused)
        record["expired_unused_fingerprints"].update(unused)

    for record in by_stage.values():
        _merge_tag_record(overall, record)
    result = _freeze_tag_record(overall)
    result["by_stage"] = {
        stage: _freeze_tag_record(by_stage[stage]) for stage in ("shortlist", "survival")
    }
    return result


def _or_state(current: bool | None, incoming: bool | None) -> bool | None:
    if current is True or incoming is True:
        return True
    if current is False or incoming is False:
        return False
    return None


def lineage_fate_summary(run: dict[str, Any]) -> dict[str, Any]:
    """Apply logical OR across repeated score-caused fingerprint appearances."""

    states: dict[str, dict[str, bool | None]] = {}
    occurrence_entries = 0
    for event in run.get("lineage_diagnostics", []):
        for item in event.get("entered", []):
            fp = str(item.get("fingerprint", ""))
            if not fp:
                continue
            occurrence_entries += 1
            record = states.setdefault(fp, {metric: None for metric in _LINEAGE_METRICS})
            for metric in _LINEAGE_METRICS:
                raw = item.get(metric)
                incoming = None if raw is None else bool(raw)
                record[metric] = _or_state(record[metric], incoming)

    result: dict[str, Any] = {
        "occurrence_entries": int(occurrence_entries),
        "unique_fingerprints": int(len(states)),
    }
    for metric in _LINEAGE_METRICS:
        values = [record[metric] for record in states.values()]
        defined = [value for value in values if value is not None]
        true_count = sum(value is True for value in defined)
        false_count = sum(value is False for value in defined)
        result[metric] = {
            "defined_unique": len(defined),
            "true_unique": int(true_count),
            "false_unique": int(false_count),
            "undefined_unique": len(values) - len(defined),
            "rate": float(true_count / len(defined)) if defined else 0.0,
        }
    return result


def _generation_pool(run: dict[str, Any], generation: int, stage: str) -> set[str] | None:
    traces = {
        int(item.get("generation", -1)): item for item in run.get("generation_trace", [])
    }
    normalized = _stage_name(stage)
    trace = traces.get(int(generation))
    if trace is None and normalized == "shortlist" and traces:
        last_generation = max(traces)
        if int(generation) == last_generation + 1:
            return {str(value) for value in traces[last_generation].get("next_population", [])}
        return None
    if trace is None:
        return None
    pool = {str(value) for value in trace.get("population_before", [])}
    if normalized == "shortlist":
        return pool
    if normalized == "survival":
        for proposal in trace.get("proposals", []):
            if isinstance(proposal, dict):
                fp = str(proposal.get("proposal_fingerprint", ""))
                if fp:
                    pool.add(fp)
        return pool
    return None


def replacement_summary(run: dict[str, Any]) -> dict[str, Any]:
    """Conservatively classify every active-tag fate at its due stage."""

    counts = {name: 0 for name in _REPLACEMENT_BUCKETS}
    retained = 0
    active_occurrences = 0
    records: list[dict[str, Any]] = []

    for event in run.get("selection_events", []):
        active = sorted(str(value) for value in event.get("active_tags", []) if str(value))
        if not active:
            continue
        generation = int(event.get("generation", -1))
        stage = _stage_name(event.get("stage", ""))
        pool = _generation_pool(run, generation, stage)
        base_group = [str(value) for value in event.get("base_group", [])]
        final_group = [str(value) for value in event.get("final_group", base_group)]
        selected_raw = event.get("selected_after")
        selected_after = (
            {str(value) for value in selected_raw}
            if isinstance(selected_raw, list)
            else None
        )

        for fp in active:
            active_occurrences += 1
            classification: str
            if pool is None:
                classification = "not_reconstructible"
            elif fp not in pool:
                classification = "lineage_not_present"
            elif selected_after is not None and fp in selected_after:
                classification = "retained"
            elif selected_after is not None and fp in base_group:
                classification = "same_key_not_selected"
            elif selected_after is not None:
                classification = "strictly_better_classical_key_present"
            elif fp in base_group:
                try:
                    quota = int(event.get("cutoff", 0)) - int(event.get("group_start", 0))
                    index = final_group.index(fp)
                except (TypeError, ValueError):
                    classification = "not_reconstructible"
                else:
                    if not 0 <= quota <= len(final_group):
                        classification = "not_reconstructible"
                    elif index < quota:
                        classification = "retained"
                    else:
                        classification = "same_key_not_selected"
            else:
                classification = "not_reconstructible"

            if classification == "retained":
                retained += 1
            else:
                counts[classification] += 1
            records.append(
                {
                    "generation": generation,
                    "stage": stage,
                    "fingerprint": fp,
                    "classification": classification,
                }
            )

    records.sort(key=lambda item: (item["generation"], item["stage"], item["fingerprint"]))
    return {
        "active_tag_occurrences": int(active_occurrences),
        "retained_occurrences": int(retained),
        "loss_classifications": {name: int(counts[name]) for name in _REPLACEMENT_BUCKETS},
        "records": records,
    }


def _empty_budget_record() -> dict[str, int]:
    return {
        "boundary_opportunities": 0,
        "preclosure_opportunities": 0,
        "scored_opportunities": 0,
        "budget_closing_events": 0,
        "postclosure_observational_only": 0,
    }


def _freeze_budget_record(record: dict[str, int]) -> dict[str, Any]:
    total = int(record["boundary_opportunities"])
    scored = int(record["scored_opportunities"])
    return {
        **{key: int(value) for key, value in record.items()},
        "actionable_fraction": float(scored / total) if total else 0.0,
    }


def budget_geometry(run: dict[str, Any]) -> dict[str, Any]:
    by_stage = {"shortlist": _empty_budget_record(), "survival": _empty_budget_record()}
    overall = _empty_budget_record()
    for event in run.get("selection_events", []):
        if not bool(event.get("boundary_opportunity", False)):
            continue
        stage = _stage_name(event.get("stage", ""))
        if stage not in by_stage:
            continue
        for record in (by_stage[stage], overall):
            record["boundary_opportunities"] += 1
            if not bool(event.get("selection_closed_before", False)):
                record["preclosure_opportunities"] += 1
            if bool(event.get("scored", False)):
                record["scored_opportunities"] += 1
            if str(event.get("event", "")) == "score_budget_closed" or bool(
                event.get("blocked_by_budget", False)
            ):
                record["budget_closing_events"] += 1
            if bool(event.get("selection_closed_before", False)) and bool(
                event.get("observational_only", False)
            ):
                record["postclosure_observational_only"] += 1
    return {
        "overall": _freeze_budget_record(overall),
        "by_stage": {
            stage: _freeze_budget_record(by_stage[stage])
            for stage in ("shortlist", "survival")
        },
    }


def _expected_cells() -> set[tuple[int, str]]:
    return {(seed, arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _source_failures(
    arm_results: Sequence[dict[str, Any]],
    terminal_freeze: dict[str, Any],
    aggregate: dict[str, Any],
) -> list[str]:
    failures: set[str] = set()
    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}

    for run in arm_results:
        try:
            key = (int(run.get("seed", -1)), str(run.get("arm", "")))
        except (TypeError, ValueError):
            failures.add("invalid_cell_identity")
            continue
        if key not in expected:
            failures.add("unexpected_cell")
            continue
        if key in indexed:
            failures.add("duplicate_cell")
            continue
        indexed[key] = run
    if set(indexed) != expected or len(arm_results) != 36:
        failures.add("source_cell_set")

    for run in indexed.values():
        if str(run.get("phase", "")) != "2D":
            failures.add("phase_identity")
        if int(run.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS:
            failures.add("classical_budget")
        if int(run.get("oracle_candidate_scores", -1)) != CANDIDATE_SCORES:
            failures.add("score_budget")
        if int(run.get("oracle_fitness_trainings", -1)) != FITNESS_TRAININGS:
            failures.add("fitness_training_budget")
        if len(list(run.get("oracle_receipts", []))) != CANDIDATE_SCORES:
            failures.add("score_receipt_count")
        if not _sha_matches(run, "scientific_payload_sha256"):
            failures.add("arm_payload_sha")

    if str(terminal_freeze.get("terminal_freeze_sha256", "")) != EXPECTED_TERMINAL_FREEZE_SHA256:
        failures.add("terminal_freeze_identity")
    if str(terminal_freeze.get("phase", "")) != "2D-terminal-freeze":
        failures.add("terminal_freeze_phase")
    if int(terminal_freeze.get("cell_count", -1)) != 36:
        failures.add("terminal_freeze_cell_count")
    try:
        freeze_seeds = tuple(int(value) for value in terminal_freeze.get("evolution_seeds", []))
    except (TypeError, ValueError):
        freeze_seeds = ()
    if freeze_seeds != EVOLUTION_SEEDS:
        failures.add("terminal_freeze_seeds")
    if not bool(terminal_freeze.get("prerequisites", {}).get("pass", False)):
        failures.add("terminal_freeze_prerequisites")

    terminal_map: dict[tuple[int, str], dict[str, Any]] = {}
    for item in terminal_freeze.get("terminals", []):
        try:
            key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        except (TypeError, ValueError):
            failures.add("terminal_cell_identity")
            continue
        if key in terminal_map:
            failures.add("duplicate_terminal_cell")
        terminal_map[key] = item
    if set(terminal_map) != expected:
        failures.add("terminal_cell_set")
    for key in expected & set(indexed) & set(terminal_map):
        run = indexed[key]
        terminal = terminal_map[key]
        if str(terminal.get("arm_payload_sha256", "")) != str(
            run.get("scientific_payload_sha256", "")
        ):
            failures.add("terminal_arm_sha_binding")
        if str(terminal.get("terminal_fingerprint", "")) != str(
            run.get("terminal_fingerprint", "")
        ):
            failures.add("terminal_fingerprint_binding")

    if str(aggregate.get("aggregate_payload_sha256", "")) != EXPECTED_AGGREGATE_SHA256:
        failures.add("aggregate_identity")
    if str(aggregate.get("phase", "")) != "2D":
        failures.add("aggregate_phase")
    if not bool(aggregate.get("prerequisites", {}).get("pass", False)):
        failures.add("aggregate_prerequisites")
    return sorted(failures)


def _sum_lineage(summaries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(summaries)
    result: dict[str, Any] = {
        "occurrence_entries": sum(int(item.get("occurrence_entries", 0)) for item in values),
        "unique_fingerprints_cell_sum": sum(
            int(item.get("unique_fingerprints", 0)) for item in values
        ),
    }
    for metric in _LINEAGE_METRICS:
        defined = sum(int(item[metric]["defined_unique"]) for item in values)
        true_count = sum(int(item[metric]["true_unique"]) for item in values)
        false_count = sum(int(item[metric]["false_unique"]) for item in values)
        undefined = sum(int(item[metric]["undefined_unique"]) for item in values)
        result[metric] = {
            "defined_unique_cell_sum": defined,
            "true_unique_cell_sum": true_count,
            "false_unique_cell_sum": false_count,
            "undefined_unique_cell_sum": undefined,
            "rate": float(true_count / defined) if defined else 0.0,
        }
    return result


def _sum_tags(summaries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(summaries)
    keys = (
        "score_caused_entry_occurrences",
        "created_occurrences",
        "active_tag_appearances",
        "order_changed_tag_occurrences",
        "membership_changed_tag_occurrences",
        "expired_without_order_or_membership_occurrences",
    )
    result = {key: sum(int(item.get(key, 0)) for item in values) for key in keys}
    entrants = int(result["score_caused_entry_occurrences"])
    active = int(result["active_tag_appearances"])
    result["tag_creation_rate_per_score_caused_entry"] = (
        float(result["created_occurrences"] / entrants) if entrants else 0.0
    )
    result["order_utilization_rate"] = (
        float(result["order_changed_tag_occurrences"] / active) if active else 0.0
    )
    result["membership_utilization_rate"] = (
        float(result["membership_changed_tag_occurrences"] / active) if active else 0.0
    )
    return result


def _sum_replacements(summaries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(summaries)
    return {
        "active_tag_occurrences": sum(int(item["active_tag_occurrences"]) for item in values),
        "retained_occurrences": sum(int(item["retained_occurrences"]) for item in values),
        "loss_classifications": {
            name: sum(int(item["loss_classifications"][name]) for item in values)
            for name in _REPLACEMENT_BUCKETS
        },
    }


def _inconclusive(failures: Sequence[str], source_cell_count: int) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": 1,
            "phase": "2E",
            "status": INCONCLUSIVE_STATUS,
            "source_run_id": SOURCE_RUN_ID,
            "source_marker_sha": EXPECTED_MARKER_SHA,
            "expected_terminal_freeze_sha256": EXPECTED_TERMINAL_FREEZE_SHA256,
            "expected_aggregate_payload_sha256": EXPECTED_AGGREGATE_SHA256,
            "source_cell_count": int(source_cell_count),
            "provenance_failures": sorted(str(value) for value in failures),
            "diagnostics_interpreted": False,
        }
    )


def analyze_phase2e(
    arm_results: Sequence[dict[str, Any]],
    terminal_freeze: dict[str, Any],
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    """Produce Phase 2E diagnostics from frozen Phase 2D artifacts only."""

    failures = _source_failures(arm_results, terminal_freeze, aggregate)
    if failures:
        return _inconclusive(failures, len(arm_results))

    indexed = {
        (int(run["seed"]), str(run["arm"])): run
        for run in sorted(
            arm_results, key=lambda item: (int(item["seed"]), str(item["arm"]))
        )
    }
    per_cell: dict[tuple[int, str], dict[str, Any]] = {}
    for seed in EVOLUTION_SEEDS:
        for arm in ARMS:
            run = indexed[(seed, arm)]
            per_cell[(seed, arm)] = {
                "source_arm_payload_sha256": str(run["scientific_payload_sha256"]),
                "tags": tag_utilization_summary(run) if arm in PERSISTENCE_ARMS else None,
                "lineage": lineage_fate_summary(run) if arm in LINEAGE_ARMS else None,
                "replacement": replacement_summary(run) if arm in PERSISTENCE_ARMS else None,
                "budget": budget_geometry(run),
            }

    d5: dict[str, Any] = {}
    for arm in PERSISTENCE_ARMS:
        d5[arm] = {
            "tags": _sum_tags(per_cell[(seed, arm)]["tags"] for seed in EVOLUTION_SEEDS),
            "lineage": _sum_lineage(
                per_cell[(seed, arm)]["lineage"] for seed in EVOLUTION_SEEDS
            ),
            "replacement": _sum_replacements(
                per_cell[(seed, arm)]["replacement"] for seed in EVOLUTION_SEEDS
            ),
        }

    per_seed: list[dict[str, Any]] = []
    for seed in EVOLUTION_SEEDS:
        arms_payload: dict[str, Any] = {}
        for arm in ARMS:
            cell = per_cell[(seed, arm)]
            arms_payload[arm] = {
                "source_arm_payload_sha256": cell["source_arm_payload_sha256"],
                "tags": cell["tags"],
                "lineage": cell["lineage"],
                "replacement": cell["replacement"],
                "budget": cell["budget"],
            }
        per_seed.append({"seed": seed, "arms": arms_payload})

    source_shas = [
        {
            "seed": seed,
            "arm": arm,
            "sha256": per_cell[(seed, arm)]["source_arm_payload_sha256"],
        }
        for seed in EVOLUTION_SEEDS
        for arm in ARMS
    ]
    return _seal(
        {
            "schema_version": 1,
            "phase": "2E",
            "status": VALID_STATUS,
            "source_run_id": SOURCE_RUN_ID,
            "source_marker_sha": EXPECTED_MARKER_SHA,
            "terminal_freeze_sha256": EXPECTED_TERMINAL_FREEZE_SHA256,
            "phase2d_aggregate_payload_sha256": EXPECTED_AGGREGATE_SHA256,
            "source_cell_count": 36,
            "source_arm_payload_sha256": source_shas,
            "diagnostics_interpreted": True,
            "d5_op1_vs_sp1_descriptive": d5,
            "d6_per_seed": per_seed,
        }
    )
