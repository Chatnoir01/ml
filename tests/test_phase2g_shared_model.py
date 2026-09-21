from dataclasses import FrozenInstanceError

import pytest

from adversarial_sbox.phase2g_shared_model import (
    CURRICULUM_SIZE,
    PAIRS_PER_CURRICULUM_SBOX,
    TRAIN_PAIRS_PER_SBOX,
    VALIDATION_PAIRS_PER_SBOX,
    TEST_PAIRS_PER_SBOX,
    SHARED_TRAIN_SIZE,
    SHARED_VALIDATION_SIZE,
    SHARED_TEST_SIZE,
    SCORING_PAIRS_PER_MODEL_CANDIDATE,
    SharedModelState,
    checkpoint_model_key,
    score_cache_key,
)


def test_shared_training_geometry_is_exactly_preregistered():
    assert CURRICULUM_SIZE == 20
    assert PAIRS_PER_CURRICULUM_SBOX == 400
    assert (TRAIN_PAIRS_PER_SBOX, VALIDATION_PAIRS_PER_SBOX, TEST_PAIRS_PER_SBOX) == (
        280,
        60,
        60,
    )
    assert (SHARED_TRAIN_SIZE, SHARED_VALIDATION_SIZE, SHARED_TEST_SIZE) == (
        5600,
        1200,
        1200,
    )
    assert SCORING_PAIRS_PER_MODEL_CANDIDATE == 400


def test_shared_model_state_is_immutable_and_checkpoint_scoped():
    state = SharedModelState(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=5,
        difference=0x00000001,
        replicate=3,
        dataset_seed=777043,
        model_seed=787047,
        curriculum_digest_sha256="a" * 64,
        state_sha256="b" * 64,
        state_bytes=b"frozen-model-state",
    )

    assert state.checkpoint_generation == 5
    assert state.replicate == 3
    with pytest.raises(FrozenInstanceError):
        state.checkpoint_generation = 10


def test_model_and_score_cache_keys_include_checkpoint_identity():
    model_key = checkpoint_model_key(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=10,
        difference=0x00000100,
        replicate=7,
    )
    assert model_key == ("A", 726011, 10, 0x00000100, 7)

    key_a = score_cache_key(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=10,
        candidate_fingerprint="abc123",
    )
    key_b = score_cache_key(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=15,
        candidate_fingerprint="abc123",
    )
    assert key_a == ("A", 726011, 10, "abc123")
    assert key_a != key_b
