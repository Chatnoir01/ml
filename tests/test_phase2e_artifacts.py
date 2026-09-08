from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from adversarial_sbox.phase2e import (
    ARMS,
    EVOLUTION_SEEDS,
    EXPECTED_AGGREGATE_SHA256,
    EXPECTED_MARKER_SHA,
    EXPECTED_TERMINAL_FREEZE_SHA256,
    SOURCE_RUN_ID,
    analyze_phase2e,
    budget_geometry,
    lineage_fate_summary,
    replacement_summary,
    tag_utilization_summary,
)


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _seal(payload: dict, field: str) -> dict:
    clean = copy.deepcopy(payload)
    clean.pop(field, None)
    clean[field] = hashlib.sha256(_canonical(clean)).hexdigest()
    return clean


def _run(seed: int, arm: str) -> dict:
    payload = {
        "schema_version": 1,
        "phase": "2D",
        "seed": seed,
        "arm": arm,
        "initial_population_digest_sha256": f"{seed:064x}"[-64:],
        "terminal_fingerprint": f"terminal-{arm}-{seed}",
        "terminal_sbox": list(range(256)),
        "terminal_classical": {},
        "classical_evaluations": 340,
        "oracle_candidate_scores": 32,
        "oracle_fitness_trainings": 512,
        "oracle_selection_closed": True,
        "oracle_receipts": [{"fingerprint": f"fp-{i}"} for i in range(32)],
        "selection_events": [],
        "generation_trace": [],
        "parent_map": {},
        "proposal_audit_sha256": "a" * 64,
        "persistence_state_at_end": [],
        "lineage_diagnostics": [],
    }
    return _seal(payload, "scientific_payload_sha256")


def _sources() -> tuple[list[dict], dict, dict]:
    runs = [_run(seed, arm) for seed in EVOLUTION_SEEDS for arm in ARMS]
    terminals = [
        {
            "seed": run["seed"],
            "arm": run["arm"],
            "terminal_fingerprint": run["terminal_fingerprint"],
            "terminal_sbox": run["terminal_sbox"],
            "terminal_classical": run["terminal_classical"],
            "arm_payload_sha256": run["scientific_payload_sha256"],
        }
        for run in runs
    ]
    freeze = {
        "schema_version": 1,
        "phase": "2D-terminal-freeze",
        "cell_count": 36,
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "prerequisites": {
            "fresh_evolution_seeds": True,
            "exact_budgets": True,
            "receipt_integrity": True,
            "same_initial_population": True,
            "pass": True,
        },
        "terminals": sorted(terminals, key=lambda item: (item["seed"], item["arm"])),
    }
    # Unit fixtures use the frozen external identity rather than trying to reproduce
    # the real 36-cell freeze bytes.
    freeze["terminal_freeze_sha256"] = EXPECTED_TERMINAL_FREEZE_SHA256
    aggregate = {
        "phase": "2D",
        "aggregate_payload_sha256": EXPECTED_AGGREGATE_SHA256,
        "prerequisites": {"pass": True},
        "support": {"verdict": "phase2d_bounded_persistence_not_supported"},
    }
    return runs, freeze, aggregate


def test_phase2e_source_constants_are_frozen() -> None:
    assert SOURCE_RUN_ID == 34147455097
    assert EXPECTED_MARKER_SHA == "2cc913e33cc5848f12ae5493f992b49fa89bc3d2"
    assert EXPECTED_TERMINAL_FREEZE_SHA256 == "8b50e71ab8fc082d1c49fa9b7da0e896c3ecf0f851a82500617bc34927799107"
    assert EXPECTED_AGGREGATE_SHA256 == "51f41197482c5695ed00267c69dfc81b937cf12871336457308755f8e5e64e5c"
    assert EVOLUTION_SEEDS == (426011, 426023, 426037, 426049, 426061, 426073, 426089, 426101, 426113)
    assert ARMS == ("C", "O0", "OP1", "SP1")


def test_phase2e_validates_exact_cells_hashes_and_budgets() -> None:
    runs, freeze, aggregate = _sources()
    result = analyze_phase2e(runs, freeze, aggregate)
    assert result["status"] == "phase2e_artifact_diagnostics_valid"
    assert result["source_cell_count"] == 36
    assert len(result["source_arm_payload_sha256"]) == 36

    missing = analyze_phase2e(runs[:-1], freeze, aggregate)
    assert missing["status"] == "phase2e_inconclusive_artifact_provenance"

    duplicate = analyze_phase2e([*runs, copy.deepcopy(runs[0])], freeze, aggregate)
    assert duplicate["status"] == "phase2e_inconclusive_artifact_provenance"

    bad_budget = copy.deepcopy(runs)
    bad_budget[0]["oracle_candidate_scores"] = 31
    bad_budget[0] = _seal(bad_budget[0], "scientific_payload_sha256")
    failed = analyze_phase2e(bad_budget, freeze, aggregate)
    assert failed["status"] == "phase2e_inconclusive_artifact_provenance"

    bad_hash = copy.deepcopy(runs)
    bad_hash[0]["terminal_fingerprint"] = "tampered"
    failed = analyze_phase2e(bad_hash, freeze, aggregate)
    assert failed["status"] == "phase2e_inconclusive_artifact_provenance"


def test_phase2e_is_input_order_invariant() -> None:
    runs, freeze, aggregate = _sources()
    forward = analyze_phase2e(runs, freeze, aggregate)
    reverse = analyze_phase2e(list(reversed(runs)), freeze, aggregate)
    assert _canonical(forward) == _canonical(reverse)


def test_lineage_unique_fingerprints_use_logical_or_and_report_denominators() -> None:
    run = _run(EVOLUTION_SEEDS[0], "OP1")
    run["lineage_diagnostics"] = [
        {
            "event_index": 1,
            "generation": 1,
            "stage": "shortlist",
            "entered": [
                {
                    "fingerprint": "x",
                    "direct_plus_1": False,
                    "descendant_plus_1": False,
                    "direct_plus_2": None,
                    "descendant_plus_2": False,
                    "direct_plus_5": None,
                    "descendant_plus_5": None,
                    "terminal_self": False,
                    "terminal_descendant": False,
                }
            ],
        },
        {
            "event_index": 2,
            "generation": 2,
            "stage": "survival",
            "entered": [
                {
                    "fingerprint": "x",
                    "direct_plus_1": True,
                    "descendant_plus_1": True,
                    "direct_plus_2": True,
                    "descendant_plus_2": True,
                    "direct_plus_5": None,
                    "descendant_plus_5": None,
                    "terminal_self": False,
                    "terminal_descendant": True,
                },
                {
                    "fingerprint": "y",
                    "direct_plus_1": None,
                    "descendant_plus_1": None,
                    "direct_plus_2": None,
                    "descendant_plus_2": None,
                    "direct_plus_5": None,
                    "descendant_plus_5": None,
                    "terminal_self": False,
                    "terminal_descendant": False,
                },
            ],
        },
    ]
    summary = lineage_fate_summary(run)
    assert summary["occurrence_entries"] == 3
    assert summary["unique_fingerprints"] == 2
    assert summary["descendant_plus_2"]["defined_unique"] == 1
    assert summary["descendant_plus_2"]["true_unique"] == 1
    assert summary["descendant_plus_2"]["undefined_unique"] == 1
    assert summary["terminal_descendant"]["defined_unique"] == 2
    assert summary["terminal_descendant"]["true_unique"] == 1


def test_tag_summary_separates_raw_occurrences_unique_and_membership_use() -> None:
    run = _run(EVOLUTION_SEEDS[0], "OP1")
    run["selection_events"] = [
        {
            "generation": 1,
            "stage": "shortlist",
            "cutoff": 2,
            "group_start": 1,
            "group_end": 3,
            "boundary_opportunity": True,
            "selection_closed_before": False,
            "scored": True,
            "observational_only": False,
            "blocked_by_budget": False,
            "base_group": ["a", "b"],
            "score_ordered_group": ["b", "a"],
            "final_group": ["b", "a"],
            "active_tags": [],
            "tag_created": ["b"],
            "score_caused_entered": ["b"],
            "tag_used": False,
        },
        {
            "generation": 2,
            "stage": "shortlist",
            "cutoff": 2,
            "group_start": 1,
            "group_end": 3,
            "boundary_opportunity": True,
            "selection_closed_before": False,
            "scored": True,
            "observational_only": False,
            "blocked_by_budget": False,
            "base_group": ["b", "c"],
            "score_ordered_group": ["c", "b"],
            "final_group": ["b", "c"],
            "active_tags": ["b"],
            "tag_created": [],
            "score_caused_entered": [],
            "tag_used": True,
        },
    ]
    summary = tag_utilization_summary(run)
    assert summary["created_occurrences"] == 1
    assert summary["created_unique"] == 1
    assert summary["active_tag_appearances"] == 1
    assert summary["order_changed_tag_occurrences"] == 1
    assert summary["membership_changed_tag_occurrences"] == 1
    assert summary["expired_without_order_or_membership_occurrences"] == 0


def test_replacement_summary_uses_explicit_unknown_bucket() -> None:
    run = _run(EVOLUTION_SEEDS[0], "OP1")
    run["generation_trace"] = [
        {
            "generation": 1,
            "population_before": ["same", "worse", "keep"],
            "shortlist": [],
            "parents": [],
            "proposals": [],
            "next_population": ["same", "keep"],
        }
    ]
    run["selection_events"] = [
        {
            "generation": 1,
            "stage": "shortlist",
            "cutoff": 1,
            "group_start": 0,
            "group_end": 2,
            "boundary_opportunity": True,
            "base_group": ["keep", "same"],
            "final_group": ["keep", "same"],
            "active_tags": ["same", "gone", "worse"],
            "selected_after": ["keep"],
        }
    ]
    summary = replacement_summary(run)
    assert summary["loss_classifications"]["same_key_not_selected"] == 1
    assert summary["loss_classifications"]["lineage_not_present"] == 1
    assert summary["loss_classifications"]["strictly_better_classical_key_present"] == 1
    assert summary["loss_classifications"]["not_reconstructible"] == 0


def test_budget_geometry_counts_preclose_close_and_postclose() -> None:
    run = _run(EVOLUTION_SEEDS[0], "O0")
    run["selection_events"] = [
        {"stage": "shortlist", "boundary_opportunity": True, "selection_closed_before": False, "scored": True, "observational_only": False, "blocked_by_budget": False, "event": "selection_boundary"},
        {"stage": "shortlist", "boundary_opportunity": True, "selection_closed_before": False, "scored": False, "observational_only": True, "blocked_by_budget": True, "event": "score_budget_closed"},
        {"stage": "survival", "boundary_opportunity": True, "selection_closed_before": True, "scored": False, "observational_only": True, "blocked_by_budget": False, "event": "selection_boundary"},
    ]
    summary = budget_geometry(run)
    assert summary["overall"]["boundary_opportunities"] == 3
    assert summary["overall"]["preclosure_opportunities"] == 2
    assert summary["overall"]["scored_opportunities"] == 1
    assert summary["overall"]["budget_closing_events"] == 1
    assert summary["overall"]["postclosure_observational_only"] == 1
    assert summary["overall"]["actionable_fraction"] == pytest.approx(1 / 3)


def test_phase2e_module_has_no_neural_or_validation_import_path() -> None:
    source = Path("src/adversarial_sbox/phase2e.py").read_text(encoding="utf-8")
    assert "phase2d_oracle" not in source
    assert "phase2d_validation" not in source
    assert "score_fitness_candidate" not in source
    assert "score_validation_candidate" not in source
