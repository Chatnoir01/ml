"""Phase 2F terminal-freeze gate using fitness Block-G receipts only.

This module is intentionally held-out blind. It verifies all 36 arm cells and
freezes terminal identity before any Block-X validation module or seed constant
is imported.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from typing import Any

from .phase2_evolution_seed_registry import phase2f_evolution_seeds_are_fresh
from .phase2f import (
    ARCHITECTURE,
    ARMS,
    CLASSICAL_BUDGET_PER_ARM_SEED,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
)
from .phase2f_invariants import all_arm_invariants_report
from .phase2f_provenance import all_arm_provenance_report
from .phase2f_receipt_linkage import all_score_linkage_report
from .phase2f_trace_integrity import all_trace_integrity_report


def _sha_matches(payload: dict[str, Any], field: str) -> bool:
    stored = str(payload.get(field, ""))
    if len(stored) != 64:
        return False
    clean = {key: value for key, value in payload.items() if key != field}
    blob = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest() == stored


def _fitness_score_payload_integrity(payload: dict[str, Any]) -> bool:
    try:
        if str(payload.get("purpose", "")) != "fitness":
            return False
        if str(payload.get("architecture", "")) != ARCHITECTURE:
            return False
        if int(payload.get("depth", -1)) != DEPTH:
            return False
        if tuple(int(value) for value in payload.get("differences", ())) != DIFFERENCES:
            return False
        if int(payload.get("pair_count", -1)) != PAIR_COUNT:
            return False
        if tuple(int(value) for value in payload.get("split_sizes", ())) != SPLIT_SIZES:
            return False
        if int(payload.get("training_count", -1)) != ORACLE_TRAININGS_PER_SCORE:
            return False
        if not _sha_matches(payload, "scientific_payload_sha256"):
            return False

        dataset_seeds = tuple(int(value) for value in FITNESS_DATASET_SEEDS)
        model_seeds = tuple(int(value) for value in FITNESS_MODEL_SEEDS)
        runs = list(payload.get("runs", []))
        if len(dataset_seeds) != 8 or len(model_seeds) != 8:
            return False
        if len(runs) != ORACLE_TRAININGS_PER_SCORE:
            return False
        expected = {(int(diff), replicate) for diff in DIFFERENCES for replicate in range(8)}
        seen: set[tuple[int, int]] = set()
        neural: list[float] = []
        null: list[float] = []
        for run in runs:
            key = (int(run.get("difference", -1)), int(run.get("replicate", -1)))
            if key not in expected or key in seen:
                return False
            seen.add(key)
            replicate = key[1]
            if int(run.get("dataset_seed", -1)) != dataset_seeds[replicate]:
                return False
            if int(run.get("model_seed", -1)) != model_seeds[replicate]:
                return False
            sizes = (
                int(run.get("train_size", -1)),
                int(run.get("validation_size", -1)),
                int(run.get("test_size", -1)),
            )
            if sizes != SPLIT_SIZES:
                return False
            advantage = float(run.get("neural_advantage", float("nan")))
            null_advantage = float(run.get("null_advantage", float("nan")))
            if not math.isfinite(advantage) or not math.isfinite(null_advantage):
                return False
            neural.append(advantage)
            null.append(null_advantage)
        if seen != expected:
            return False
        return bool(
            math.isclose(
                float(payload.get("neural_advantage")),
                sum(neural) / len(neural),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            and math.isclose(
                float(payload.get("null_advantage")),
                sum(null) / len(null),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
        )
    except (TypeError, ValueError, KeyError, IndexError):
        return False


def _expected_cells() -> set[tuple[int, str]]:
    return {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _index_arm_results(
    arm_results: Sequence[dict[str, Any]],
) -> dict[tuple[int, str], dict[str, Any]]:
    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for item in arm_results:
        key = (int(item.get("seed", -1)), str(item.get("arm", "")))
        if key not in expected or key in indexed:
            raise ValueError(f"invalid or duplicate Phase 2F arm record {key!r}")
        indexed[key] = item
    if set(indexed) != expected:
        raise ValueError("Phase 2F requires exact 9-seed × 4-arm records")
    return indexed


def freeze_terminals(arm_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Freeze all 36 terminals without importing any held-out validation code."""

    arms = _index_arm_results(arm_results)
    invariant_report = all_arm_invariants_report(arm_results)
    linkage_report = all_score_linkage_report(arm_results)
    provenance_report = all_arm_provenance_report(arm_results)
    trace_report = all_trace_integrity_report(arm_results)
    exact_budgets = True
    receipt_integrity = True
    same_initial_population = True
    terminal_rule = True
    terminals: list[dict[str, Any]] = []

    for seed in EVOLUTION_SEEDS:
        per_seed = [arms[(int(seed), arm)] for arm in ARMS]
        digests = {str(item.get("initial_population_digest_sha256", "")) for item in per_seed}
        same_initial_population &= len(digests) == 1 and "" not in digests

        for arm in ARMS:
            run = arms[(int(seed), arm)]
            receipts = list(run.get("oracle_receipts", []))
            exact_budgets &= bool(
                str(run.get("phase")) == "2F"
                and int(run.get("classical_evaluations", -1)) == CLASSICAL_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_candidate_scores", -1))
                == ORACLE_SCORE_BUDGET_PER_ARM_SEED
                and int(run.get("oracle_fitness_trainings", -1))
                == FITNESS_TRAININGS_PER_ARM_SEED
                and len(receipts) == ORACLE_SCORE_BUDGET_PER_ARM_SEED
            )
            terminal_rule &= (
                str(run.get("terminal_selection_rule", "")) == "historical_classical_only"
            )
            receipt_integrity &= _sha_matches(run, "scientific_payload_sha256")

            seen_fp: set[str] = set()
            for receipt in receipts:
                fp = str(receipt.get("fingerprint", ""))
                score = receipt.get("score_payload", {})
                ok = isinstance(score, dict) and _fitness_score_payload_integrity(score)
                ok &= fp != "" and fp not in seen_fp
                seen_fp.add(fp)
                ok &= str(score.get("fingerprint", "")) == fp
                ok &= str(receipt.get("payload_sha256", "")) == str(
                    score.get("scientific_payload_sha256", "")
                )
                ok &= int(receipt.get("training_count", -1)) == ORACLE_TRAININGS_PER_SCORE
                ok &= str(receipt.get("role", "")) in {"selection", "padding"}
                receipt_integrity &= bool(ok)

            terminals.append(
                {
                    "seed": int(seed),
                    "arm": arm,
                    "terminal_fingerprint": str(run.get("terminal_fingerprint", "")),
                    "terminal_sbox": list(run.get("terminal_sbox", [])),
                    "terminal_classical": dict(run.get("terminal_classical", {})),
                    "arm_payload_sha256": str(run.get("scientific_payload_sha256", "")),
                }
            )

    prerequisites = {
        "fresh_evolution_seeds": bool(phase2f_evolution_seeds_are_fresh(EVOLUTION_SEEDS)),
        "exact_budgets": bool(exact_budgets),
        "receipt_integrity": bool(receipt_integrity),
        "same_initial_population": bool(same_initial_population),
        "terminal_classical_only": bool(terminal_rule),
        "band_invariants": bool(invariant_report["pass"]),
        "score_event_receipt_linkage": bool(linkage_report["pass"]),
        "arm_provenance": bool(provenance_report["pass"]),
        "trace_integrity": bool(trace_report["pass"]),
    }
    prerequisites["pass"] = all(prerequisites.values())

    invariant_blob = json.dumps(
        invariant_report, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    linkage_blob = json.dumps(
        linkage_report, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    provenance_blob = json.dumps(
        provenance_report, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    trace_blob = json.dumps(
        trace_report, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2F-terminal-freeze",
        "cell_count": 36,
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "prerequisites": prerequisites,
        "band_invariant_report_sha256": hashlib.sha256(invariant_blob).hexdigest(),
        "band_invariant_failed_cells": list(invariant_report["failed_cells"]),
        "score_linkage_report_sha256": hashlib.sha256(linkage_blob).hexdigest(),
        "score_linkage_failed_cells": list(linkage_report["failed_cells"]),
        "arm_provenance_report_sha256": hashlib.sha256(provenance_blob).hexdigest(),
        "arm_provenance_failed_cells": list(provenance_report["failed_cells"]),
        "trace_integrity_report_sha256": hashlib.sha256(trace_blob).hexdigest(),
        "trace_integrity_failed_cells": list(trace_report["failed_cells"]),
        "terminals": sorted(terminals, key=lambda item: (item["seed"], item["arm"])),
    }
    payload["terminal_freeze_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload
