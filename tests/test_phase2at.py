from adversarial_sbox.phase2at import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PAIRED_REPLICATES,
    PERMUTATION_REPETITIONS,
    PERMUTATION_SEEDS,
    TOTAL_TRAININGS,
    classify_depth_profile,
)


def test_phase2at_frozen_contract():
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert DATASET_SEEDS == (73003, 73019, 73031, 73043, 73061, 73079, 73091, 73103)
    assert MODEL_SEEDS == (83003, 83017, 83029, 83047, 83059, 83071, 83089, 83101)
    assert PERMUTATION_SEEDS == {3: 93001, 4: 93011, 5: 93023}
    assert PAIRED_REPLICATES == 8
    assert PERMUTATION_REPETITIONS == 10_000
    assert TOTAL_TRAININGS == 288


def test_phase2at_classification_is_frozen():
    h_peak = {3: 1.0, 4: 3.0, 5: 2.0}
    r_peak = {3: 0.01, 4: 0.08, 5: 0.03}
    m_ordered = {3: 0.90, 4: 0.30, 5: 0.05}

    assert (
        classify_depth_profile(True, h_peak, r_peak, m_ordered, 0.01)
        == "phase2at_depth4_peak_replicated"
    )
    assert (
        classify_depth_profile(True, h_peak, r_peak, m_ordered, 0.20)
        == "phase2at_peak_direction_only"
    )

    h_not_peak = {3: 4.0, 4: 3.0, 5: 2.0}
    assert (
        classify_depth_profile(True, h_not_peak, r_peak, m_ordered, 0.01)
        == "phase2at_depth_profile_not_replicated"
    )
    assert (
        classify_depth_profile(False, h_peak, r_peak, m_ordered, 0.01)
        == "phase2at_inconclusive_prerequisites"
    )
