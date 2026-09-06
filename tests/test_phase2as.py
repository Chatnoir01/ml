from adversarial_sbox.phase2as import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    H5_H4_MAX_RATIO,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PAIRED_REPLICATES,
    PERMUTATION_REPETITIONS,
    R5_R4_MAX_RATIO,
    TOTAL_TRAININGS,
    classify_depth_attenuation,
)


def test_phase2as_frozen_contract():
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert DATASET_SEEDS == (72001, 72019, 72031, 72043, 72053, 72071, 72089, 72101)
    assert MODEL_SEEDS == (82003, 82013, 82021, 82037, 82051, 82067, 82073, 82087)
    assert PAIRED_REPLICATES == 8
    assert PERMUTATION_REPETITIONS == 10_000
    assert TOTAL_TRAININGS == 288
    assert H5_H4_MAX_RATIO == 0.50
    assert R5_R4_MAX_RATIO == 0.75


def test_phase2as_primary_classification_is_frozen():
    h_supported = {3: 0.0040, 4: 0.0020, 5: 0.0008}
    r_supported = {3: 0.120, 4: 0.100, 5: 0.070}
    assert (
        classify_depth_attenuation(True, h_supported, r_supported)
        == "phase2as_depth_attenuation_supported"
    )

    h_weak = {3: 0.0040, 4: 0.0020, 5: 0.0012}
    r_weak = {3: 0.120, 4: 0.100, 5: 0.080}
    assert classify_depth_attenuation(True, h_weak, r_weak) == "phase2as_weak_attenuation"

    h_nonmonotone = {3: 0.0040, 4: 0.0010, 5: 0.0015}
    assert (
        classify_depth_attenuation(True, h_nonmonotone, r_supported)
        == "phase2as_depth_attenuation_not_supported"
    )

    assert (
        classify_depth_attenuation(False, h_supported, r_supported)
        == "phase2as_inconclusive_prerequisites"
    )
