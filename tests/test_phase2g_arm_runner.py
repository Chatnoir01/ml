"""RED contract for one complete held-out-blind Phase 2G arm/seed runner.

Synthetic only. No real neural training or held-out H access. The runner must
compose the frozen checkpoint lifecycle into one complete 20-generation cell and
fail closed unless exact classical/training budgets and classical-only terminal
selection are receipted.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_arm_runner import run_phase2g_arm


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _population(offset: int) -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox((offset + index) % 256) for index in range(20))


@dataclass(frozen=True)
class FakeBundle:
    checkpoint_generation: int
    training_count: int = 16


def test_complete_arm_enforces_20_generations_340_classical_and_64_trainings() -> None:
    seed = EVOLUTION_SEEDS[0]
    initial = _population(0)
    train_calls: list[int] = []
    block_calls: list[tuple[int, int]] = []
    terminal_calls: list[tuple[tuple[int, ...], ...]] = []

    def train_checkpoint(*, arm, evolution_seed, checkpoint_generation, curriculum):
        assert arm == "A"
        assert evolution_seed == seed
        assert len(curriculum) == 20
        train_calls.append(checkpoint_generation)
        return FakeBundle(checkpoint_generation=checkpoint_generation)

    def evolve_block(*, population, start_generation, end_generation, selection_enabled, model, shuffle_stream):
        assert selection_enabled is True
        assert shuffle_stream is None
        assert model.checkpoint_generation == start_generation
        block_calls.append((start_generation, end_generation))
        # Five generations × 16 unique proposals = 80 new classical evaluations.
        return {
            "population": _population(40 + end_generation),
            "classical_evaluations": 80,
            "generation_count": 5,
            "selection_events": [],
        }

    def select_terminal_classical_only(population):
        frozen = tuple(population)
        terminal_calls.append(frozen)
        return frozen[0]

    result = run_phase2g_arm(
        arm="A",
        evolution_seed=seed,
        initial_population=initial,
        train_checkpoint=train_checkpoint,
        evolve_block=evolve_block,
        select_terminal_classical_only=select_terminal_classical_only,
    )

    assert train_calls == [0, 5, 10, 15]
    assert block_calls == [(0, 5), (5, 10), (10, 15), (15, 20)]
    assert len(terminal_calls) == 1
    assert result["phase"] == "2G"
    assert result["generation_count"] == 20
    assert result["classical_evaluations"] == 340
    assert result["checkpoint_training_count"] == 64
    assert result["terminal_selection_rule"] == "historical_classical_only"
    assert result["heldout_accessed"] is False
    assert len(result["terminal_sbox"]) == 256
    assert len(result["scientific_payload_sha256"]) == 64


def test_complete_arm_fails_closed_on_budget_or_generation_drift() -> None:
    seed = EVOLUTION_SEEDS[1]
    initial = _population(0)

    def train_checkpoint(**kwargs):
        return FakeBundle(checkpoint_generation=kwargs["checkpoint_generation"])

    def bad_block(**kwargs):
        return {
            "population": _population(80 + kwargs["end_generation"]),
            "classical_evaluations": 79,
            "generation_count": 5,
            "selection_events": [],
        }

    with pytest.raises(RuntimeError):
        run_phase2g_arm(
            arm="F",
            evolution_seed=seed,
            initial_population=initial,
            train_checkpoint=train_checkpoint,
            evolve_block=bad_block,
            select_terminal_classical_only=lambda population: tuple(population)[0],
        )


def test_control_arm_still_trains_64_audit_models_but_selection_is_disabled() -> None:
    seen_selection_flags: list[bool] = []

    def train_checkpoint(**kwargs):
        return FakeBundle(checkpoint_generation=kwargs["checkpoint_generation"])

    def evolve_block(**kwargs):
        seen_selection_flags.append(bool(kwargs["selection_enabled"]))
        return {
            "population": _population(120 + kwargs["end_generation"]),
            "classical_evaluations": 80,
            "generation_count": 5,
            "selection_events": [],
        }

    result = run_phase2g_arm(
        arm="C",
        evolution_seed=EVOLUTION_SEEDS[2],
        initial_population=_population(0),
        train_checkpoint=train_checkpoint,
        evolve_block=evolve_block,
        select_terminal_classical_only=lambda population: tuple(population)[0],
    )
    assert seen_selection_flags == [False, False, False, False]
    assert result["checkpoint_training_count"] == 64
