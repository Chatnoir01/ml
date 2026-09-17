"""Contracts for the Phase 2G arm-runner / scientific-cell / freeze boundary.

Synthetic only. The low-level arm runner proves lifecycle budgets and receipts but
is intentionally insufficient for held-out authorization until the scientific-cell
composer adds the preregistered full provenance. No real training or H access.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import pytest

from adversarial_sbox.phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2g_arm_runner import TerminalClassicalMetrics, run_phase2g_arm
from adversarial_sbox.phase2g_terminal_freeze import (
    freeze_phase2g_terminals,
    heldout_h_authorized,
)
from phase2g_full_fixture import make_full_cell


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _population(offset: int) -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox((offset + index) % 256) for index in range(20))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FakeBundle:
    arm: str
    evolution_seed: int
    checkpoint_generation: int
    training_receipt_sha256: str
    training_count: int = 16


def _run_cell(seed: int, arm: str) -> dict[str, object]:
    initial = _population(seed % 31)

    def train_checkpoint(*, arm, evolution_seed, checkpoint_generation, curriculum):
        return FakeBundle(
            arm=arm,
            evolution_seed=evolution_seed,
            checkpoint_generation=checkpoint_generation,
            training_receipt_sha256=_sha(
                f"phase2g:{arm}:{evolution_seed}:{checkpoint_generation}:16-model-grid"
            ),
        )

    def evolve_block(*, population, start_generation, end_generation, **_kwargs):
        return {
            "population": _population((seed + end_generation) % 211),
            "classical_evaluations": 80,
            "generation_count": 5,
            "selection_events": [],
        }

    def select_terminal_classical_only(population):
        return tuple(population)[0]

    terminal_classical_metrics: TerminalClassicalMetrics

    def terminal_classical_metrics(_candidate):
        return {
            "admissible": True,
            "nonlinearity": 104,
            "differential_uniformity": 4,
            "max_abs_lat": 32,
            "algebraic_degree": 7,
        }

    return run_phase2g_arm(
        arm=arm,
        evolution_seed=seed,
        initial_population=initial,
        train_checkpoint=train_checkpoint,
        evolve_block=evolve_block,
        select_terminal_classical_only=select_terminal_classical_only,
        terminal_classical_metrics=terminal_classical_metrics,
    )


def test_low_level_arm_result_has_base_receipts_but_cannot_authorize_h_without_full_provenance() -> None:
    cells = [_run_cell(seed, arm) for seed in EVOLUTION_SEEDS for arm in ARMS]

    for cell in cells:
        assert cell["checkpoint_trainings"] == 64
        assert len(cell["initial_population_digest_sha256"]) == 64
        assert len(cell["scientific_payload_sha256"]) == 64
        checkpoints = cell["checkpoints"]
        assert [row["generation"] for row in checkpoints] == list(CHECKPOINT_GENERATIONS)
        assert all(row["training_count"] == 16 for row in checkpoints)

    with pytest.raises(ValueError, match="provenance"):
        freeze_phase2g_terminals(cells)


def test_full_scientific_cell_receipts_freeze_without_extra_evaluation_or_training() -> None:
    cells = [
        make_full_cell(seed=int(seed), arm=arm, arm_index=arm_index)
        for seed in EVOLUTION_SEEDS
        for arm_index, arm in enumerate(ARMS)
    ]
    frozen = freeze_phase2g_terminals(cells)
    assert frozen["cell_count"] == 36
    assert frozen["checkpoint_training_count"] == 36 * 64
    assert frozen["heldout_accessed"] is False
    assert heldout_h_authorized(frozen) is True


def test_matched_arms_share_initial_population_digest_per_seed() -> None:
    cells = [_run_cell(EVOLUTION_SEEDS[0], arm) for arm in ARMS]
    assert len({cell["initial_population_digest_sha256"] for cell in cells}) == 1
