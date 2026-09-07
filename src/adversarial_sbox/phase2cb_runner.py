"""Deterministic instrumented Phase 2C-B replay using frozen Phase 2B scores.

No neural scorer and no Block-V validator are imported here. Real replay of the
27 historical cells remains gated by research/PHASE2CB_EXECUTE.md.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Sequence

from .cryptoshield import improved_transparency_order, validate_sbox
from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    evaluate_classical,
    feasibility_rank,
)
from .pareto import ITOAwareMetrics, non_dominated_sort, select_nsga2
from .phase1m import ClassicalEvaluationLedger, _initial_population, _population_digest
from .phase1o import (
    MultiHotspotProposal,
    _proposal_audit_digest,
    multihotspot_walsh_swap_proposals,
)
from .phase2_evolution_seed_registry import phase2b_evolution_seeds_are_fresh
from .phase2b import (
    CLASSICAL_BUDGET_PER_ARM_SEED,
    EVOLUTION_GENERATIONS,
    EVOLUTION_SEEDS,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    PARENT_COUNT,
    POPULATION_SIZE,
    PROPOSALS_PER_GENERATION,
    PROPOSALS_PER_PARENT,
    SHORTLIST_SIZE,
    SHUFFLE_SEED_OFFSET,
)
from .phase2cb_replay import (
    FrozenScoreReplayCache,
    FrozenScoreReplayError,
    instrumented_cutoff_order,
)
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
ARMS = ("control", "oracle", "shuffled")
EXPECTED_CELLS = {(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS}


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _metrics_payload(metrics: ClassicalMetrics) -> dict[str, Any]:
    return {
        "nonlinearity": int(metrics.nonlinearity),
        "differential_uniformity": int(metrics.differential_uniformity),
        "max_linear_correlation": int(metrics.max_linear_correlation),
        "sac_score": float(metrics.sac_score),
        "algebraic_degree": int(metrics.algebraic_degree),
        "fingerprint": str(metrics.fingerprint),
    }


def _collect_unique_batch_with_parents(
    parents: Sequence[SBox],
    rng: random.Random,
    *,
    seen_ever: set[SBox],
) -> tuple[list[SBox], list[MultiHotspotProposal], list[dict[str, str]]]:
    """Exact Phase-1O batch generation plus observational parent links."""

    batch: list[SBox] = []
    audit: list[MultiHotspotProposal] = []
    links: list[dict[str, str]] = []
    parent_index = 0
    stalled = 0
    while len(batch) < PROPOSALS_PER_GENERATION:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(batch))
        generated = multihotspot_walsh_swap_proposals(parent, rng, count=needed)
        added = 0
        for record in generated:
            if record.sbox in seen_ever:
                continue
            seen_ever.add(record.sbox)
            batch.append(record.sbox)
            audit.append(record)
            links.append(
                {
                    "proposal_fingerprint": fingerprint_sbox(record.sbox),
                    "parent_fingerprint": fingerprint_sbox(parent),
                }
            )
            added += 1
            if len(batch) == PROPOSALS_PER_GENERATION:
                break
        stalled = stalled + 1 if added == 0 else 0
        if stalled > 512:
            raise RuntimeError("unable to generate globally unique Phase 2C-B proposals")
    return batch, audit, links


def _has_ancestor(
    candidate: str,
    ancestor: str,
    parent_map: dict[str, str],
) -> bool:
    """Return whether candidate has ancestor in the realized unique-parent tree."""

    current = candidate
    seen: set[str] = set()
    while current in parent_map:
        if current in seen:
            raise RuntimeError("cycle in Phase 2C-B realized parent map")
        seen.add(current)
        current = parent_map[current]
        if current == ancestor:
            return True
    return False


def _lineage_diagnostics(
    *,
    trace_events: Sequence[dict[str, Any]],
    generation_records: Sequence[dict[str, Any]],
    parent_map: dict[str, str],
    terminal_fingerprint: str,
    mode: str,
) -> list[dict[str, Any]]:
    if mode != "oracle":
        return []

    populations: dict[int, set[str]] = {
        int(record["generation"]): set(record["population_before"])
        for record in generation_records
    }
    if generation_records:
        populations[EVOLUTION_GENERATIONS] = set(generation_records[-1]["next_population"])

    results: list[dict[str, Any]] = []
    for event_index, event in enumerate(trace_events):
        entered = list(event.get("entered", []))
        if not event.get("membership_changed") or not entered:
            continue
        generation = int(event["generation"])
        entered_records: list[dict[str, Any]] = []
        for fingerprint in entered:
            record: dict[str, Any] = {"fingerprint": fingerprint}
            for offset in (1, 2, 5):
                target = generation + offset
                population = populations.get(target)
                if population is None:
                    record[f"direct_plus_{offset}"] = None
                    record[f"descendant_plus_{offset}"] = None
                    continue
                record[f"direct_plus_{offset}"] = fingerprint in population
                record[f"descendant_plus_{offset}"] = any(
                    candidate != fingerprint
                    and _has_ancestor(candidate, fingerprint, parent_map)
                    for candidate in population
                )
            record["terminal_self"] = terminal_fingerprint == fingerprint
            record["terminal_descendant"] = _has_ancestor(
                terminal_fingerprint, fingerprint, parent_map
            )
            entered_records.append(record)
        results.append(
            {
                "event_index": event_index,
                "generation": generation,
                "stage": str(event["stage"]),
                "entered": entered_records,
            }
        )
    return results


def _identity_checks(
    *,
    original: dict[str, Any],
    initial_digest: str,
    classical_evaluations: int,
    consumed_selection: Sequence[str],
    legacy_events: Sequence[dict[str, Any]],
    proposal_digest: str,
    terminal: SBox,
    terminal_metrics: ClassicalMetrics,
    selection_closed: bool,
) -> dict[str, bool]:
    expected_selection = [
        str(receipt.get("fingerprint", ""))
        for receipt in original.get("oracle_receipts", [])
        if str(receipt.get("role")) == "selection"
    ]
    return {
        "initial_population_digest": initial_digest
        == str(original.get("initial_population_digest_sha256", "")),
        "classical_evaluations": int(classical_evaluations)
        == int(original.get("classical_evaluations", -1))
        == CLASSICAL_BUDGET_PER_ARM_SEED,
        "selection_score_sequence": list(consumed_selection) == expected_selection,
        "legacy_oracle_events": list(legacy_events) == list(original.get("oracle_events", [])),
        "proposal_audit": proposal_digest == str(original.get("proposal_audit_sha256", "")),
        "terminal_fingerprint": fingerprint_sbox(terminal)
        == str(original.get("terminal_fingerprint", "")),
        "terminal_sbox": list(terminal) == list(original.get("terminal_sbox", [])),
        "terminal_classical": _metrics_payload(terminal_metrics)
        == dict(original.get("terminal_classical", {})),
        "oracle_selection_closed": bool(selection_closed)
        == bool(original.get("oracle_selection_closed", False)),
    }


def _cell_diagnostic_summary(trace_events: Sequence[dict[str, Any]]) -> dict[str, int]:
    opportunities = [event for event in trace_events if event.get("boundary_opportunity")]
    return {
        "selection_calls": len(trace_events),
        "boundary_opportunities": len(opportunities),
        "preclosure_opportunities": sum(
            not bool(event.get("selection_closed_before")) for event in opportunities
        ),
        "postclosure_opportunities": sum(
            bool(event.get("selection_closed_before")) for event in opportunities
        ),
        "membership_flip_events": sum(
            bool(event.get("membership_changed")) for event in opportunities
        ),
        "ordering_only_events": sum(
            bool(event.get("order_changed")) and not bool(event.get("membership_changed"))
            for event in opportunities
        ),
        "budget_block_events": sum(
            bool(event.get("blocked_by_budget")) for event in opportunities
        ),
    }


def _run_replay_cell_strict(original: dict[str, Any]) -> dict[str, Any]:
    if str(original.get("phase")) != "2B" or int(original.get("schema_version", -1)) != 1:
        raise ValueError("Phase 2C-B accepts only frozen Phase 2B schema-1 arm payloads")
    seed = int(original.get("seed", -1))
    mode = str(original.get("arm", ""))
    if seed not in EVOLUTION_SEEDS or mode not in ARMS:
        raise ValueError("unexpected Phase 2B arm/seed cell")
    if not phase2b_evolution_seeds_are_fresh(EVOLUTION_SEEDS):
        raise RuntimeError("Phase 2C-B evolution seed provenance gate failed")
    if int(original.get("oracle_candidate_scores", -1)) != ORACLE_SCORE_BUDGET_PER_ARM_SEED:
        raise ValueError("Phase 2B frozen score-count prerequisite drift")

    constraints = HardConstraints()
    initial = _initial_population(seed)
    initial_digest = _population_digest(initial)
    ledger = ClassicalEvaluationLedger(
        evaluate_classical, budget=CLASSICAL_BUDGET_PER_ARM_SEED
    )
    score_cache = FrozenScoreReplayCache(
        list(original.get("oracle_receipts", [])),
        budget=ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    )
    shuffle_rng = random.Random(seed + SHUFFLE_SEED_OFFSET) if mode == "shuffled" else None
    rng = random.Random(seed)
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    proposal_audit: list[MultiHotspotProposal] = []
    legacy_events: list[dict[str, Any]] = []
    trace_events: list[dict[str, Any]] = []
    generation_records: list[dict[str, Any]] = []
    parent_map: dict[str, str] = {}

    for candidate in population:
        ledger.evaluate(candidate)

    def with_ito(candidate: SBox) -> ITOAwareMetrics:
        cached = ito_cache.get(candidate)
        if cached is None:
            cached = ITOAwareMetrics.from_classical(
                ledger.evaluate(candidate),
                improved_transparency_order_value=improved_transparency_order(candidate),
            )
            ito_cache[candidate] = cached
        return cached

    for generation in range(EVOLUTION_GENERATIONS):
        population_before = list(population)
        ranked = instrumented_cutoff_order(
            population,
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=SHORTLIST_SIZE,
            mode=mode,
            score_cache=score_cache,
            shuffle_rng=shuffle_rng,
            generation=generation,
            stage="shortlist",
            legacy_events=legacy_events,
            trace_events=trace_events,
        )
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_metrics = tuple(with_ito(candidate) for candidate in shortlist)
        parent_indices = select_nsga2(shortlist_metrics, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in parent_indices)
        proposals, audit, links = _collect_unique_batch_with_parents(
            parents, rng, seen_ever=seen_ever
        )
        proposal_audit.extend(audit)
        for link in links:
            child = link["proposal_fingerprint"]
            if child in parent_map:
                raise RuntimeError("duplicate realized proposal parent in Phase 2C-B")
            parent_map[child] = link["parent_fingerprint"]
        for proposal in proposals:
            ledger.evaluate(proposal)
        next_population = instrumented_cutoff_order(
            [*population, *proposals],
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=POPULATION_SIZE,
            mode=mode,
            score_cache=score_cache,
            shuffle_rng=shuffle_rng,
            generation=generation,
            stage="survival",
            legacy_events=legacy_events,
            trace_events=trace_events,
        )[:POPULATION_SIZE]
        generation_records.append(
            {
                "generation": generation,
                "population_before": [fingerprint_sbox(candidate) for candidate in population_before],
                "shortlist": [fingerprint_sbox(candidate) for candidate in shortlist],
                "parents": [fingerprint_sbox(candidate) for candidate in parents],
                "proposals": links,
                "next_population": [fingerprint_sbox(candidate) for candidate in next_population],
            }
        )
        population = list(next_population)

    if ledger.evaluations != CLASSICAL_BUDGET_PER_ARM_SEED:
        raise RuntimeError("Phase 2C-B classical budget drift")

    final_ranked = instrumented_cutoff_order(
        population,
        metrics=ledger.cache,
        constraints=constraints,
        cutoff=SHORTLIST_SIZE,
        mode=mode,
        score_cache=score_cache,
        shuffle_rng=shuffle_rng,
        generation=EVOLUTION_GENERATIONS,
        stage="terminal_shortlist",
        legacy_events=legacy_events,
        trace_events=trace_events,
    )
    final_shortlist = tuple(final_ranked[:SHORTLIST_SIZE])
    final_ito = tuple(with_ito(candidate) for candidate in final_shortlist)
    front_indices = non_dominated_sort(final_ito)[0]
    terminal_front = tuple(final_shortlist[index] for index in front_indices)
    terminal = max(
        terminal_front,
        key=lambda candidate: feasibility_rank(ledger.cache[candidate], constraints),
    )
    terminal_metrics = ledger.cache[terminal]
    proposal_digest = _proposal_audit_digest(proposal_audit)

    checks = _identity_checks(
        original=original,
        initial_digest=initial_digest,
        classical_evaluations=ledger.evaluations,
        consumed_selection=score_cache.selection_consumed_fingerprints,
        legacy_events=legacy_events,
        proposal_digest=proposal_digest,
        terminal=terminal,
        terminal_metrics=terminal_metrics,
        selection_closed=score_cache.selection_closed,
    )
    status = (
        "phase2cb_replay_valid"
        if all(checks.values())
        else "phase2cb_replay_provenance_failure"
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2C-B",
        "source_phase": "2B",
        "seed": seed,
        "arm": mode,
        "status": status,
        "identity_checks": checks,
        "source_scientific_payload_sha256": str(
            original.get("scientific_payload_sha256", "")
        ),
        "initial_population_digest_sha256": initial_digest,
        "classical_evaluations": ledger.evaluations,
        "selection_score_fingerprints": list(
            score_cache.selection_consumed_fingerprints
        ),
        "legacy_oracle_events": legacy_events,
        "proposal_audit_sha256": proposal_digest,
        "terminal_fingerprint": fingerprint_sbox(terminal),
        "terminal_sbox": list(terminal),
        "terminal_classical": _metrics_payload(terminal_metrics),
        "oracle_selection_closed": score_cache.selection_closed,
        "trace_events": trace_events,
        "generation_records": generation_records,
        "parent_map": dict(sorted(parent_map.items())),
        "diagnostic_summary": _cell_diagnostic_summary(trace_events),
        "new_neural_trainings": 0,
        "block_v_scores": 0,
        "instrumented_replay_runs": 1,
    }
    payload["lineage_diagnostics"] = (
        _lineage_diagnostics(
            trace_events=trace_events,
            generation_records=generation_records,
            parent_map=parent_map,
            terminal_fingerprint=payload["terminal_fingerprint"],
            mode=mode,
        )
        if status == "phase2cb_replay_valid"
        else []
    )
    payload["replay_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def run_replay_cell(original: dict[str, Any]) -> dict[str, Any]:
    """Run one frozen-score replay cell and fail scientifically closed on cache drift."""

    seed = int(original.get("seed", -1))
    arm = str(original.get("arm", ""))
    try:
        return _run_replay_cell_strict(dict(original))
    except FrozenScoreReplayError as exc:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "phase": "2C-B",
            "source_phase": "2B",
            "seed": seed,
            "arm": arm,
            "status": "phase2cb_replay_provenance_failure",
            "identity_checks": {},
            "replay_error_type": type(exc).__name__,
            "replay_error": str(exc),
            "new_neural_trainings": 0,
            "block_v_scores": 0,
            "instrumented_replay_runs": 1,
            "lineage_diagnostics": [],
        }
        payload["replay_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
        return payload


def aggregate_replay_cells(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in cells:
        arm = str(raw.get("arm", ""))
        seed = int(raw.get("seed", -1))
        key = (arm, seed)
        if key in indexed:
            raise ValueError(f"duplicate Phase 2C-B cell {key!r}")
        indexed[key] = dict(raw)
    if set(indexed) != EXPECTED_CELLS:
        missing = sorted(EXPECTED_CELLS - set(indexed))
        extra = sorted(set(indexed) - EXPECTED_CELLS)
        raise ValueError(
            f"Phase 2C-B requires exact 27-cell set; missing={missing}, extra={extra}"
        )

    ordered = [indexed[(arm, int(seed))] for arm in ARMS for seed in EVOLUTION_SEEDS]
    all_valid = all(cell.get("status") == "phase2cb_replay_valid" for cell in ordered)
    status = "phase2cb_replay_valid" if all_valid else "phase2cb_replay_provenance_failure"

    arm_summaries: dict[str, Any] = {}
    if all_valid:
        for arm in ARMS:
            selected = [cell for cell in ordered if cell["arm"] == arm]
            arm_summaries[arm] = {
                "cells": len(selected),
                "boundary_opportunities": sum(
                    int(cell["diagnostic_summary"]["boundary_opportunities"])
                    for cell in selected
                ),
                "preclosure_opportunities": sum(
                    int(cell["diagnostic_summary"]["preclosure_opportunities"])
                    for cell in selected
                ),
                "postclosure_opportunities": sum(
                    int(cell["diagnostic_summary"]["postclosure_opportunities"])
                    for cell in selected
                ),
                "membership_flip_events": sum(
                    int(cell["diagnostic_summary"]["membership_flip_events"])
                    for cell in selected
                ),
                "ordering_only_events": sum(
                    int(cell["diagnostic_summary"]["ordering_only_events"])
                    for cell in selected
                ),
                "budget_block_events": sum(
                    int(cell["diagnostic_summary"]["budget_block_events"])
                    for cell in selected
                ),
            }

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2C-B",
        "status": status,
        "source_phase2b_scientific_sha": "59066ad943fc85f24a21b4c2941cbcee4d23aeae",
        "source_phase2b_workflow_run_id": 34064310593,
        "cell_count": len(ordered),
        "identity_pass_count": sum(
            cell.get("status") == "phase2cb_replay_valid" for cell in ordered
        ),
        "cells": ordered,
        "arm_summaries": arm_summaries,
        "new_neural_trainings": 0,
        "block_v_scores": 0,
        "instrumented_replay_runs": len(ordered),
    }
    payload["replay_aggregate_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def dump_phase2cb_result(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"
