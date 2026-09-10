from __future__ import annotations

from adversarial_sbox.phase2g import (
    SCORING_DATASET_BASE_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
)
from adversarial_sbox.phase2_neural_seed_registry import (
    complete_seed_registry_through_phase2f,
    phase2g_checkpoint_seed_registry_is_valid,
    phase2g_checkpoint_seed_roles,
    phase2g_checkpoint_seed_values,
)


def _expanded(base: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(value + 1000 * checkpoint for checkpoint in range(4) for value in base)


def test_phase2g_materializes_exact_96_checkpoint_seeds_by_role():
    expected_t = _expanded(TRAINING_DATASET_BASE_SEEDS)
    expected_m = _expanded(TRAINING_MODEL_BASE_SEEDS)
    expected_q = _expanded(SCORING_DATASET_BASE_SEEDS)

    assert phase2g_checkpoint_seed_roles() == (
        ("T", expected_t),
        ("M", expected_m),
        ("Q", expected_q),
    )

    assert len(expected_t) == len(set(expected_t)) == 32
    assert len(expected_m) == len(set(expected_m)) == 32
    assert len(expected_q) == len(set(expected_q)) == 32

    assert set(expected_t).isdisjoint(expected_m)
    assert set(expected_t).isdisjoint(expected_q)
    assert set(expected_m).isdisjoint(expected_q)

    expected_all = tuple(sorted((*expected_t, *expected_m, *expected_q)))
    assert len(expected_all) == len(set(expected_all)) == 96
    assert phase2g_checkpoint_seed_values() == expected_all


def test_phase2g_checkpoint_registry_is_fresh_against_all_prior_phase2_seeds():
    current = set(phase2g_checkpoint_seed_values())
    prior = set(complete_seed_registry_through_phase2f())

    assert current.isdisjoint(prior)
    assert phase2g_checkpoint_seed_registry_is_valid()
