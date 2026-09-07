from __future__ import annotations

from pathlib import Path

import pytest

from adversarial_sbox.phase2b import EVOLUTION_SEEDS
from adversarial_sbox.phase2cb_runner import (
    ARMS,
    _has_ancestor,
    aggregate_replay_cells,
    dump_phase2cb_result,
)


def _valid_cell(arm: str, seed: int) -> dict:
    return {
        "schema_version": 1,
        "phase": "2C-B",
        "arm": arm,
        "seed": seed,
        "status": "phase2cb_replay_valid",
        "identity_checks": {"all": True},
        "diagnostic_summary": {
            "selection_calls": 41,
            "boundary_opportunities": 2,
            "preclosure_opportunities": 1,
            "postclosure_opportunities": 1,
            "membership_flip_events": 1 if arm == "oracle" else 0,
            "ordering_only_events": 0,
            "budget_block_events": 1,
        },
        "new_neural_trainings": 0,
        "block_v_scores": 0,
        "instrumented_replay_runs": 1,
    }


def test_runner_source_has_no_neural_or_block_v_path() -> None:
    replay_source = Path("src/adversarial_sbox/phase2cb_replay.py").read_text()
    runner_source = Path("src/adversarial_sbox/phase2cb_runner.py").read_text()
    source = replay_source + "\n" + runner_source
    forbidden = (
        "phase2b_oracle",
        "phase2b_validation",
        "score_fitness_candidate",
        "validate_terminal_candidate",
        "VALIDATION_DATASET_SEEDS",
        "VALIDATION_MODEL_SEEDS",
    )
    assert all(token not in source for token in forbidden)


def test_realized_parent_map_ancestry_is_unique_and_transitive() -> None:
    parent_map = {
        "child": "parent",
        "grandchild": "child",
    }
    assert _has_ancestor("child", "parent", parent_map) is True
    assert _has_ancestor("grandchild", "parent", parent_map) is True
    assert _has_ancestor("parent", "child", parent_map) is False


def test_parent_map_cycle_fails_closed() -> None:
    with pytest.raises(RuntimeError):
        _has_ancestor("a", "missing", {"a": "b", "b": "a"})


def test_aggregate_requires_exact_27_cells() -> None:
    cells = [_valid_cell(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS]
    aggregate = aggregate_replay_cells(cells)
    assert aggregate["status"] == "phase2cb_replay_valid"
    assert aggregate["cell_count"] == 27
    assert aggregate["identity_pass_count"] == 27
    assert aggregate["new_neural_trainings"] == 0
    assert aggregate["block_v_scores"] == 0
    assert aggregate["arm_summaries"]["oracle"]["membership_flip_events"] == 9

    with pytest.raises(ValueError):
        aggregate_replay_cells(cells[:-1])


def test_aggregate_is_input_order_independent_and_byte_deterministic() -> None:
    cells = [_valid_cell(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS]
    forward = aggregate_replay_cells(cells)
    reverse = aggregate_replay_cells(list(reversed(cells)))
    assert forward == reverse
    assert dump_phase2cb_result(forward) == dump_phase2cb_result(reverse)


def test_one_failed_cell_blocks_all_interpretive_arm_summaries() -> None:
    cells = [_valid_cell(arm, int(seed)) for arm in ARMS for seed in EVOLUTION_SEEDS]
    cells[0] = {**cells[0], "status": "phase2cb_replay_provenance_failure"}
    aggregate = aggregate_replay_cells(cells)
    assert aggregate["status"] == "phase2cb_replay_provenance_failure"
    assert aggregate["identity_pass_count"] == 26
    assert aggregate["arm_summaries"] == {}
