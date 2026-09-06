from adversarial_sbox.phase2as import (
    DEPTHS,
    DIFFERENCES,
    PANEL_DIGEST_SHA256,
    PERMUTATION_REPETITIONS,
    TOTAL_TRAININGS,
    classify_depth_signal,
)


def test_phase2as_frozen_contract():
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert PERMUTATION_REPETITIONS == 10_000
    assert TOTAL_TRAININGS == 180


def test_phase2as_primary_classification_is_frozen():
    assert classify_depth_signal({3: True, 4: True, 5: False}) == "phase2as_depth_attenuation_supported"
    assert classify_depth_signal({3: True, 4: False, 5: False}) == "phase2as_early_attenuation_supported"
    assert classify_depth_signal({3: True, 4: True, 5: True}) == "phase2as_no_reliability_loss"
    assert classify_depth_signal({3: False, 4: True, 5: False}) == "phase2as_nonmonotone_signal"
    assert classify_depth_signal({3: False, 4: False, 5: True}) == "phase2as_nonmonotone_signal"
    assert classify_depth_signal({3: False, 4: False, 5: False}) == "phase2as_inconclusive"
