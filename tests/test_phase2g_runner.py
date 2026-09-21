"""RED contract for the Phase 2G adaptive checkpoint lifecycle runner.

Synthetic only: no real neural training, no held-out H, and no scientific GA run.
The runner must orchestrate the frozen 0/5/10/15 checkpoint lifecycle and keep
arm semantics C/F/A/S exact before a real GA adapter is allowed to exist.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from adversarial_sbox.phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2g_runner import run_phase2g_checkpoint_lifecycle
from adversarial_sbox.provenance import fingerprint_sbox


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _population(offset: int) -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox((offset + index) % 256) for index in range(20))


@dataclass(frozen=True)
class FakeModel:
    checkpoint_generation: int
    curriculum_digest: tuple[str, ...]


def _trainer_calls():
    calls: list[tuple[str, int, int, tuple[str, ...]]] = []

    def trainer(*, arm, evolution_seed, checkpoint_generation, curriculum):
        digest = tuple(fingerprint_sbox(candidate) for candidate in curriculum)
        calls.append((arm, evolution_seed, checkpoint_generation, digest))
        return FakeModel(checkpoint_generation, digest)

    return calls, trainer


def _block_calls():
    calls: list[dict[str, object]] = []

    def evolve_block(*, population, start_generation, end_generation, selection_enabled, model, shuffle_stream):
        calls.append(
            {
                "population": tuple(population),
                "start_generation": start_generation,
                "end_generation": end_generation,
                "selection_enabled": selection_enabled,
                "checkpoint_generation": model.checkpoint_generation,
                "shuffle_stream": shuffle_stream,
            }
        )
        # Deterministically change the population after every block so adaptive
        # curricula can be distinguished from the initial fixed curriculum.
        return _population(40 + end_generation)

    return calls, evolve_block


@pytest.mark.parametrize("arm", ["C", "F", "A", "S"])
def test_runner_executes_exact_four_five_generation_blocks(arm: str) -> None:
    seed = EVOLUTION_SEEDS[0]
    initial = _population(0)
    train_calls, trainer = _trainer_calls()
    block_calls, evolve_block = _block_calls()

    result = run_phase2g_checkpoint_lifecycle(
        arm=arm,
        evolution_seed=seed,
        initial_population=initial,
        train_checkpoint=trainer,
        evolve_block=evolve_block,
    )

    assert [call[2] for call in train_calls] == list(CHECKPOINT_GENERATIONS)
    assert [(call["start_generation"], call["end_generation"]) for call in block_calls] == [
        (0, 5),
        (5, 10),
        (10, 15),
        (15, 20),
    ]
    assert result["phase"] == "2G-lifecycle"
    assert result["arm"] == arm
    assert result["seed"] == seed
    assert result["checkpoint_count"] == 4
    assert result["generation_count"] == 20
    assert result["heldout_accessed"] is False


def test_f_curriculum_is_initial_at_every_checkpoint_but_a_tracks_current_population() -> None:
    seed = EVOLUTION_SEEDS[1]
    initial = _population(0)

    f_train_calls, f_trainer = _trainer_calls()
    _, f_evolve = _block_calls()
    run_phase2g_checkpoint_lifecycle(
        arm="F",
        evolution_seed=seed,
        initial_population=initial,
        train_checkpoint=f_trainer,
        evolve_block=f_evolve,
    )

    a_train_calls, a_trainer = _trainer_calls()
    _, a_evolve = _block_calls()
    run_phase2g_checkpoint_lifecycle(
        arm="A",
        evolution_seed=seed,
        initial_population=initial,
        train_checkpoint=a_trainer,
        evolve_block=a_evolve,
    )

    initial_digest = tuple(sorted(fingerprint_sbox(candidate) for candidate in initial))
    assert all(call[3] == initial_digest for call in f_train_calls)
    assert a_train_calls[0][3] == initial_digest
    assert any(call[3] != initial_digest for call in a_train_calls[1:])


def test_c_trains_audit_models_but_never_enables_neural_selection() -> None:
    calls, trainer = _trainer_calls()
    block_calls, evolve = _block_calls()
    run_phase2g_checkpoint_lifecycle(
        arm="C",
        evolution_seed=EVOLUTION_SEEDS[2],
        initial_population=_population(0),
        train_checkpoint=trainer,
        evolve_block=evolve,
    )
    assert len(calls) == 4
    assert all(call["selection_enabled"] is False for call in block_calls)
    assert all(call["shuffle_stream"] is None for call in block_calls)


def test_s_uses_one_persistent_shuffle_stream_per_checkpoint_and_a_f_do_not() -> None:
    _, trainer = _trainer_calls()
    s_blocks, evolve_s = _block_calls()
    run_phase2g_checkpoint_lifecycle(
        arm="S",
        evolution_seed=EVOLUTION_SEEDS[3],
        initial_population=_population(0),
        train_checkpoint=trainer,
        evolve_block=evolve_s,
    )
    streams = [call["shuffle_stream"] for call in s_blocks]
    assert all(stream is not None for stream in streams)
    assert len({id(stream) for stream in streams}) == 4

    for arm in ("F", "A"):
        _, trainer2 = _trainer_calls()
        blocks, evolve = _block_calls()
        run_phase2g_checkpoint_lifecycle(
            arm=arm,
            evolution_seed=EVOLUTION_SEEDS[4],
            initial_population=_population(0),
            train_checkpoint=trainer2,
            evolve_block=evolve,
        )
        assert all(call["selection_enabled"] is True for call in blocks)
        assert all(call["shuffle_stream"] is None for call in blocks)


def test_runner_fails_closed_on_invalid_arm_seed_or_population() -> None:
    _, trainer = _trainer_calls()
    _, evolve = _block_calls()
    with pytest.raises(ValueError):
        run_phase2g_checkpoint_lifecycle(
            arm="X",
            evolution_seed=EVOLUTION_SEEDS[0],
            initial_population=_population(0),
            train_checkpoint=trainer,
            evolve_block=evolve,
        )
    with pytest.raises(ValueError):
        run_phase2g_checkpoint_lifecycle(
            arm="A",
            evolution_seed=-1,
            initial_population=_population(0),
            train_checkpoint=trainer,
            evolve_block=evolve,
        )
    with pytest.raises(ValueError):
        run_phase2g_checkpoint_lifecycle(
            arm="A",
            evolution_seed=EVOLUTION_SEEDS[0],
            initial_population=_population(0)[:-1],
            train_checkpoint=trainer,
            evolve_block=evolve,
        )
