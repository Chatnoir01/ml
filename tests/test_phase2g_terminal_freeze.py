"""RED contract for Phase 2G terminal freeze and held-out H blindness.

These tests are synthetic only. They do not train models, run evolution, or touch
held-out data. The implementation under test must freeze all 36 terminal cells
before any held-out H evaluation can be authorized.
"""

from __future__ import annotations

import copy
import hashlib

import pytest

from adversarial_sbox.phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2g_terminal_freeze import (
    CLASSICAL_EVALUATIONS_PER_CELL,
    freeze_phase2g_terminals,
    heldout_h_authorized,
)


def _sbox(offset: int) -> list[int]:
    return list(range(offset, 256)) + list(range(offset))


def _fingerprint(sbox: list[int]) -> str:
    return hashlib.sha256(bytes(sbox)).hexdigest()


def _cell(seed: int, arm: str, arm_index: int) -> dict[str, object]:
    sbox = _sbox((seed + arm_index) % 256)
    checkpoints = [
        {
            "generation": generation,
            "training_count": 16,
            "training_receipt_sha256": hashlib.sha256(
                f"{seed}:{arm}:{generation}:training".encode("utf-8")
            ).hexdigest(),
        }
        for generation in CHECKPOINT_GENERATIONS
    ]
    return {
        "phase": "2G",
        "seed": seed,
        "arm": arm,
        "classical_evaluations": 340,
        "checkpoint_trainings": 64,
        "checkpoints": checkpoints,
        "terminal_selection_rule": "historical_classical_only",
        "terminal_fingerprint": _fingerprint(sbox),
        "terminal_sbox": sbox,
        "terminal_classical": {
            "admissible": True,
            "nonlinearity": 100 + arm_index,
            "differential_uniformity": 8,
            "max_abs_lat": 32,
            "algebraic_degree": 7,
        },
    }


def _cells() -> list[dict[str, object]]:
    return [
        _cell(seed, arm, arm_index)
        for seed in EVOLUTION_SEEDS
        for arm_index, arm in enumerate(ARMS)
    ]


def test_frozen_budget_identity_is_exact() -> None:
    assert CLASSICAL_EVALUATIONS_PER_CELL == 340
    assert len(ARMS) * len(EVOLUTION_SEEDS) == 36


def test_freeze_requires_exact_36_cells_and_is_deterministic() -> None:
    cells = _cells()
    forward = freeze_phase2g_terminals(cells)
    reverse = freeze_phase2g_terminals(list(reversed(cells)))

    assert forward == reverse
    assert forward["phase"] == "2G-terminal-freeze"
    assert forward["cell_count"] == 36
    assert forward["checkpoint_training_count"] == 36 * 64
    assert forward["heldout_training_count"] == 0
    assert forward["heldout_accessed"] is False
    assert len(forward["terminal_freeze_sha256"]) == 64
    assert heldout_h_authorized(forward) is True


def test_freeze_fails_closed_on_missing_or_duplicate_cell() -> None:
    cells = _cells()
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells[:-1])
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells + [copy.deepcopy(cells[0])])


def test_freeze_fails_closed_on_budget_checkpoint_or_terminal_rule_drift() -> None:
    for field, value in (
        ("classical_evaluations", 339),
        ("checkpoint_trainings", 63),
        ("terminal_selection_rule", "neural_rerank"),
    ):
        cells = _cells()
        cells[0][field] = value
        with pytest.raises(ValueError):
            freeze_phase2g_terminals(cells)

    cells = _cells()
    cells[0]["checkpoints"] = list(cells[0]["checkpoints"])[:-1]
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells)


def test_h_authorization_fails_closed_on_any_freeze_tamper() -> None:
    frozen = freeze_phase2g_terminals(_cells())
    for field, value in (
        ("cell_count", 35),
        ("heldout_accessed", True),
        ("heldout_training_count", 1),
        ("terminal_freeze_sha256", "0" * 64),
    ):
        tampered = copy.deepcopy(frozen)
        tampered[field] = value
        assert heldout_h_authorized(tampered) is False
