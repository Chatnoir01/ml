from __future__ import annotations

import pytest

from adversarial_sbox.phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    EVOLUTION_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    SCORING_DATASET_BASE_SEEDS,
    HELDOUT_DATASET_SEEDS,
    HELDOUT_MODEL_SEEDS,
    CHECKPOINT_TRAININGS_PER_CELL,
    TOTAL_CHECKPOINT_TRAININGS,
    TOTAL_HELDOUT_TRAININGS,
    TOTAL_SCIENTIFIC_TRAININGS,
    SUPPORT_CHECKS,
    expanded_checkpoint_seed_block,
    phase2g_verdict,
)
from adversarial_sbox.phase2_evolution_seed_registry import (
    PHASE2G_RESERVED_EVOLUTION_SEEDS,
    phase2g_evolution_seeds_are_fresh,
)
from adversarial_sbox.phase2_neural_seed_registry import registry_is_disjoint


def test_phase2g_frozen_identity():
    assert ARMS == ("C", "F", "A", "S")
    assert CHECKPOINT_GENERATIONS == (0, 5, 10, 15)
    assert EVOLUTION_SEEDS == (
        726011,
        726023,
        726037,
        726049,
        726061,
        726073,
        726087,
        726099,
        726113,
    )
    assert EVOLUTION_SEEDS == PHASE2G_RESERVED_EVOLUTION_SEEDS
    assert phase2g_evolution_seeds_are_fresh(EVOLUTION_SEEDS)


def test_phase2g_checkpoint_seed_bases_and_expansion_are_frozen():
    assert TRAINING_DATASET_BASE_SEEDS == (
        776003,
        776017,
        776031,
        776043,
        776059,
        776071,
        776083,
        776097,
    )
    assert TRAINING_MODEL_BASE_SEEDS == (
        786009,
        786021,
        786033,
        786047,
        786061,
        786073,
        786087,
        786101,
    )
    assert SCORING_DATASET_BASE_SEEDS == (
        796003,
        796017,
        796029,
        796043,
        796057,
        796071,
        796083,
        796099,
    )
    assert expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, 0) == TRAINING_DATASET_BASE_SEEDS
    assert expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, 3) == tuple(
        value + 3000 for value in TRAINING_DATASET_BASE_SEEDS
    )
    with pytest.raises(ValueError):
        expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, 4)


def test_phase2g_heldout_seed_block_is_frozen_and_disjoint():
    assert HELDOUT_DATASET_SEEDS == (
        876003,
        876017,
        876029,
        876043,
        876057,
        876071,
        876083,
        876099,
    )
    assert HELDOUT_MODEL_SEEDS == (
        886007,
        886019,
        886031,
        886043,
        886061,
        886073,
        886091,
        886103,
    )

    checkpoint_values = set()
    for checkpoint in range(4):
        checkpoint_values.update(expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, checkpoint))
        checkpoint_values.update(expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, checkpoint))
        checkpoint_values.update(expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, checkpoint))

    heldout_values = set(HELDOUT_DATASET_SEEDS + HELDOUT_MODEL_SEEDS)
    assert checkpoint_values.isdisjoint(heldout_values)
    assert registry_is_disjoint(
        tuple(sorted(checkpoint_values)),
        tuple(sorted(heldout_values)),
        before="phase2g",
    )


def test_phase2g_exact_training_budget():
    assert CHECKPOINT_TRAININGS_PER_CELL == 64
    assert TOTAL_CHECKPOINT_TRAININGS == 2304
    assert TOTAL_HELDOUT_TRAININGS == 576
    assert TOTAL_SCIENTIFIC_TRAININGS == 2880


def test_phase2g_verdict_is_fail_closed():
    assert len(SUPPORT_CHECKS) == 10
    all_green = {name: True for name in SUPPORT_CHECKS}

    assert phase2g_verdict(False, all_green) == "phase2g_inconclusive_prerequisites"
    assert phase2g_verdict(True, all_green) == "phase2g_adaptive_coevolution_supported"

    one_red = dict(all_green)
    one_red[SUPPORT_CHECKS[1]] = False
    assert phase2g_verdict(True, one_red) == "phase2g_adaptive_coevolution_not_supported"

    with pytest.raises(ValueError):
        phase2g_verdict(True, {name: True for name in SUPPORT_CHECKS[:-1]})
