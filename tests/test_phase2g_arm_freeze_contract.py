"""RED contract for direct Phase 2G arm-runner -> terminal-freeze compatibility.

Synthetic only. No real neural training, GA scientific execution, or held-out H
access. A completed arm cell must already contain every receipt needed by the
36-cell pre-H terminal freeze; freezing must not require extra evaluation/training.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from adversarial_sbox.phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2g_arm_runner import TerminalClassicalMetrics, run_phase2g_arm
from adversarial_sbox.phase2g_terminal_freeze import (
    freeze_phase2g_terminals,
    heldout_h_authorized,
)


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


def test_arm_result_is_directly_freeze_compatible_without_extra_work() -> None:
    cells = [_run_cell(seed, arm) for seed in EVOLUTION_SEEDS for arm in ARMS]

    for cell in cells:
        assert cell["checkpoint_trainings"] == 64
        assert len(cell["initial_population_digest_sha256"]) == 64
        assert len(cell["scientific_payload_sha256"]) == 64
        assert set(cell["terminal_classical"]) >= {
            "admissible",
            "nonlinearity",
            "differential_uniformity",
            "max_abs_lat",
            "algebraic_degree",
        }
        checkpoints = cell["checkpoints"]
        assert [row["generation"] for row in checkpoints] == list(CHECKPOINT_GENERATIONS)
        assert all(row["training_count"] == 16 for row in checkpoints)
        assert all(len(row["training_receipt_sha256"]) == 64 for row in checkpoints)

    frozen = freeze_phase2g_terminals(cells)
    assert frozen["cell_count"] == 36
    assert frozen["checkpoint_training_count"] == 36 * 64
    assert frozen["heldout_accessed"] is False
    assert heldout_h_authorized(frozen) is True


def test_matched_arms_share_initial_population_digest_per_seed() -> None:
    cells = [_run_cell(EVOLUTION_SEEDS[0], arm) for arm in ARMS]
    assert len({cell["initial_population_digest_sha256"] for cell in cells}) == 1
