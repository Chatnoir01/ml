"""Red-first frozen scientific contract for Phase 2A-P."""

from adversarial_sbox.phase2ap import (
    ALPHA_PER_SIDE,
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    EFFECT_RATIO_MAX,
    HETEROGENEITY_PERMUTATION_SEEDS,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PEAK_PERMUTATION_SEEDS,
    PERMUTATION_REPETITIONS,
    TOTAL_TRAININGS,
    classify_peak,
)


def test_phase2ap_frozen_contract_constants():
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert DATASET_SEEDS == (
        74003, 74011, 74017, 74021, 74027, 74047, 74051, 74071, 74077, 74093,
        74101, 74131, 74143, 74149, 74161, 74167, 74179, 74189, 74197, 74201,
    )
    assert MODEL_SEEDS == (
        84011, 84017, 84029, 84037, 84047, 84053, 84059, 84061, 84067, 84083,
        84089, 84101, 84109, 84127, 84131, 84137, 84143, 84163, 84179, 84181,
    )
    assert PERMUTATION_REPETITIONS == 20_000
    assert PEAK_PERMUTATION_SEEDS == {(4, 3): 94043, (4, 5): 94045}
    assert HETEROGENEITY_PERMUTATION_SEEDS == {3: 95003, 4: 95004, 5: 95005}
    assert ALPHA_PER_SIDE == 0.025
    assert EFFECT_RATIO_MAX == 0.75
    assert TOTAL_TRAININGS == 720


def test_phase2ap_verdict_logic_is_frozen():
    assert classify_peak(requirements_pass=False, side43_pass=True, side45_pass=True) == "phase2ap_inconclusive_prerequisite"
    assert classify_peak(requirements_pass=True, side43_pass=True, side45_pass=True) == "phase2ap_r4_peak_supported"
    assert classify_peak(requirements_pass=True, side43_pass=True, side45_pass=False) == "phase2ap_r4_peak_not_supported"
    assert classify_peak(requirements_pass=True, side43_pass=False, side45_pass=True) == "phase2ap_r4_peak_not_supported"
    assert classify_peak(requirements_pass=True, side43_pass=False, side45_pass=False) == "phase2ap_r4_peak_not_supported"
