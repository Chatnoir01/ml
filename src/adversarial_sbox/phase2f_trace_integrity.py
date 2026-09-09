"""Independent structural validation of the realized Phase 2F evolution trace."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .phase1m import _initial_population
from .phase2f import (
    ARMS,
    CLASSICAL_BUDGET_PER_ARM_SEED,
    EVOLUTION_GENERATIONS,
    EVOLUTION_SEEDS,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    PARENT_COUNT,
    POPULATION_SIZE,
    PROPOSALS_PER_GENERATION,
    SHORTLIST_SIZE,
)
from .provenance import fingerprint_sbox


def generation_record_report(
    record: Mapping[str, Any],
    *,
    expected_generation: int,
    prior_candidates: set[str],
) -> dict[str, Any]:
    """Validate one generation record without trusting the runner's control flow."""

    checks = {
        "generation_index": True,
        "population_shape": True,
        "shortlist_membership": True,
        "parent_membership": True,
        "proposal_shape": True,
        "proposal_parentage": True,
        "proposal_uniqueness": True,
        "survivor_pool": True,
    }
    try:
        generation = int(record.get("generation", -1))
        population = [str(value) for value in record.get("population_before", [])]
        shortlist = [str(value) for value in record.get("shortlist", [])]
        parents = [str(value) for value in record.get("parents", [])]
        proposals_raw = record.get("proposals", [])
        next_population = [str(value) for value in record.get("next_population", [])]
    except (TypeError, ValueError):
        for name in checks:
            checks[name] = False
        return {"pass": False, "checks": checks, "proposal_children": []}

    checks["generation_index"] = generation == int(expected_generation)
    checks["population_shape"] = bool(
        len(population) == POPULATION_SIZE
        and len(set(population)) == POPULATION_SIZE
        and all(population)
    )
    checks["shortlist_membership"] = bool(
        len(shortlist) == SHORTLIST_SIZE
        and len(set(shortlist)) == SHORTLIST_SIZE
        and set(shortlist).issubset(set(population))
    )
    checks["parent_membership"] = bool(
        len(parents) == PARENT_COUNT
        and len(set(parents)) == PARENT_COUNT
        and set(parents).issubset(set(shortlist))
    )

    proposals = proposals_raw if isinstance(proposals_raw, list) else []
    checks["proposal_shape"] = len(proposals) == PROPOSALS_PER_GENERATION
    children: list[str] = []
    proposal_parents: list[str] = []
    for link in proposals:
        if not isinstance(link, Mapping):
            checks["proposal_shape"] = False
            continue
        child = str(link.get("proposal_fingerprint", ""))
        parent = str(link.get("parent_fingerprint", ""))
        if not child or not parent:
            checks["proposal_shape"] = False
        children.append(child)
        proposal_parents.append(parent)

    checks["proposal_parentage"] = bool(
        len(proposal_parents) == PROPOSALS_PER_GENERATION
        and all(parent in set(parents) for parent in proposal_parents)
    )
    checks["proposal_uniqueness"] = bool(
        len(children) == PROPOSALS_PER_GENERATION
        and len(set(children)) == PROPOSALS_PER_GENERATION
        and set(children).isdisjoint(set(population))
        and set(children).isdisjoint(set(prior_candidates))
    )
    survivor_pool = set(population) | set(children)
    checks["survivor_pool"] = bool(
        len(next_population) == POPULATION_SIZE
        and len(set(next_population)) == POPULATION_SIZE
        and set(next_population).issubset(survivor_pool)
    )
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "proposal_children": children,
    }


def arm_trace_integrity_report(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the full realized 20-generation trace and deterministic padding."""

    try:
        seed = int(run.get("seed", -1))
        arm = str(run.get("arm", ""))
    except (TypeError, ValueError):
        seed, arm = -1, ""

    checks = {
        "registered_cell": seed in EVOLUTION_SEEDS and arm in ARMS,
        "trace_length": True,
        "initial_population_fingerprints": True,
        "generation_records": True,
        "population_continuity": True,
        "classical_candidate_geometry": True,
        "parent_map": True,
        "terminal_in_final_population": True,
        "score_receipts_from_evaluated_candidates": True,
        "deterministic_padding": True,
        "selection_closed": bool(run.get("oracle_selection_closed")),
        "proposal_audit_digest_shape": True,
    }

    try:
        initial_fps = [fingerprint_sbox(candidate) for candidate in _initial_population(seed)]
    except Exception:
        initial_fps = []
        checks["registered_cell"] = False

    trace_raw = run.get("generation_trace", [])
    trace = trace_raw if isinstance(trace_raw, list) else []
    checks["trace_length"] = len(trace) == EVOLUTION_GENERATIONS

    prior_candidates = set(initial_fps)
    expected_population = list(initial_fps)
    realized_parent_map: dict[str, str] = {}
    failed_generations: list[int] = []

    for expected_generation, record in enumerate(trace):
        if not isinstance(record, Mapping):
            checks["generation_records"] = False
            failed_generations.append(expected_generation)
            continue
        population = [str(value) for value in record.get("population_before", [])]
        if expected_generation == 0:
            checks["initial_population_fingerprints"] &= population == initial_fps
        checks["population_continuity"] &= population == expected_population

        report = generation_record_report(
            record,
            expected_generation=expected_generation,
            prior_candidates=prior_candidates,
        )
        if not bool(report["pass"]):
            checks["generation_records"] = False
            failed_generations.append(expected_generation)

        for link in record.get("proposals", []) if isinstance(record.get("proposals", []), list) else []:
            if not isinstance(link, Mapping):
                continue
            child = str(link.get("proposal_fingerprint", ""))
            parent = str(link.get("parent_fingerprint", ""))
            if child:
                if child in realized_parent_map:
                    checks["parent_map"] = False
                realized_parent_map[child] = parent
        prior_candidates.update(str(value) for value in report["proposal_children"])
        expected_population = [str(value) for value in record.get("next_population", [])]

    checks["classical_candidate_geometry"] = bool(
        len(prior_candidates) == CLASSICAL_BUDGET_PER_ARM_SEED
        and int(run.get("classical_evaluations", -1)) == CLASSICAL_BUDGET_PER_ARM_SEED
    )
    claimed_parent_map = run.get("parent_map", {})
    checks["parent_map"] &= bool(
        isinstance(claimed_parent_map, Mapping)
        and {str(key): str(value) for key, value in claimed_parent_map.items()} == realized_parent_map
        and len(realized_parent_map) == EVOLUTION_GENERATIONS * PROPOSALS_PER_GENERATION
    )

    terminal_fp = str(run.get("terminal_fingerprint", ""))
    checks["terminal_in_final_population"] = bool(
        terminal_fp and terminal_fp in set(expected_population)
    )

    receipts_raw = run.get("oracle_receipts", [])
    receipts = receipts_raw if isinstance(receipts_raw, list) else []
    receipt_fps: list[str] = []
    selection_fps: list[str] = []
    padding_fps: list[str] = []
    roles: list[str] = []
    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            checks["score_receipts_from_evaluated_candidates"] = False
            continue
        fp = str(receipt.get("fingerprint", ""))
        role = str(receipt.get("role", ""))
        receipt_fps.append(fp)
        roles.append(role)
        if role == "selection":
            selection_fps.append(fp)
        elif role == "padding":
            padding_fps.append(fp)
        else:
            checks["deterministic_padding"] = False

    checks["score_receipts_from_evaluated_candidates"] &= bool(
        len(receipt_fps) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
        and len(set(receipt_fps)) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
        and set(receipt_fps).issubset(prior_candidates)
    )

    first_padding = next((index for index, role in enumerate(roles) if role == "padding"), len(roles))
    checks["deterministic_padding"] &= all(
        role == "selection" for role in roles[:first_padding]
    ) and all(role == "padding" for role in roles[first_padding:])
    required_padding = ORACLE_SCORE_BUDGET_PER_ARM_SEED - len(selection_fps)
    candidates_for_padding = sorted(
        prior_candidates - {terminal_fp} - set(selection_fps)
    )
    expected_padding = candidates_for_padding[:required_padding]
    checks["deterministic_padding"] &= bool(
        required_padding >= 0
        and padding_fps == expected_padding
        and terminal_fp not in set(padding_fps)
    )

    audit_digest = str(run.get("proposal_audit_sha256", ""))
    checks["proposal_audit_digest_shape"] = bool(
        len(audit_digest) == 64
        and all(character in "0123456789abcdef" for character in audit_digest)
    )

    return {
        "pass": all(checks.values()),
        "seed": seed,
        "arm": arm,
        "checks": checks,
        "failed_generations": failed_generations,
        "realized_candidate_count": len(prior_candidates),
        "realized_parent_count": len(realized_parent_map),
    }


def all_trace_integrity_report(
    arm_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    cells = [arm_trace_integrity_report(run) for run in arm_results]
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
