"""Red-first scientific contract for Phase 2A-S depth attenuation."""

from adversarial_sbox.phase2as import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    INPUT_DIFFERENCES,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PERMUTATION_REPETITIONS,
    PRIMARY_ATTENUATION_RATIO,
    PRIMARY_PERMUTATION_SEED,
    TOTAL_TRAININGS,
    classify_depth_attenuation,
)


def test_phase2as_frozen_constants():
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTHS == (3, 4, 5)
    assert INPUT_DIFFERENCES == (0x00000001, 0x00000100)
    assert DATASET_SEEDS == (72001, 72011, 72019, 72031, 72043, 72053, 72071, 72083, 72091, 72101)
    assert MODEL_SEEDS == (82003, 82013, 82021, 82037, 82051, 82067, 82073, 82087, 82099, 82109)
    assert PERMUTATION_REPETITIONS == 10_000
    assert PRIMARY_PERMUTATION_SEED == 92011
    assert PRIMARY_ATTENUATION_RATIO == 0.60
    assert TOTAL_TRAININGS == 360


def test_phase2as_verdict_logic_is_frozen():
    assert classify_depth_attenuation(False, 0.001, 0.2) == "phase2as_inconclusive_prerequisite"
    assert classify_depth_attenuation(True, 0.01, 0.50) == "phase2as_depth5_attenuation_confirmed"
    assert classify_depth_attenuation(True, 0.20, 0.50) == "phase2as_depth5_attenuation_not_confirmed"
    assert classify_depth_attenuation(True, 0.01, 0.80) == "phase2as_depth5_attenuation_not_confirmed"
    assert classify_depth_attenuation(True, 0.01, 0.70) == "phase2as_depth5_attenuation_inconclusive"
