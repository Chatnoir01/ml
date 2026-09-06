"""Red-first contract tests for Phase 2A-D depth attenuation."""

from adversarial_sbox.phase2ad import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PRIMARY_ATTENUATION_RATIO_MAX,
    PRIMARY_PERMUTATION_SEED,
    SECONDARY_PERMUTATION_SEED,
    TOTAL_TRAININGS,
    classify_depth_attenuation,
    paired_dispersion_attenuation_p,
)


def test_phase2ad_frozen_contract_constants():
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert DATASET_SEEDS == (
        73009,
        73013,
        73019,
        73037,
        73039,
        73043,
        73061,
        73063,
        73079,
        73091,
    )
    assert MODEL_SEEDS == (
        83003,
        83009,
        83023,
        83047,
        83059,
        83063,
        83071,
        83077,
        83089,
        83101,
    )
    assert TOTAL_TRAININGS == 360
    assert PRIMARY_ATTENUATION_RATIO_MAX == 0.75
    assert PRIMARY_PERMUTATION_SEED == 92045
    assert SECONDARY_PERMUTATION_SEED == 92034


def test_phase2ad_primary_classification_is_frozen():
    assert (
        classify_depth_attenuation(
            requirements_pass=False,
            delta45=1.0,
            p45=0.001,
            variance_ratio45=0.2,
        )
        == "phase2ad_inconclusive_baseline_or_provenance"
    )
    assert (
        classify_depth_attenuation(
            requirements_pass=True,
            delta45=0.1,
            p45=0.01,
            variance_ratio45=0.70,
        )
        == "phase2ad_depth_attenuation_supported"
    )
    assert (
        classify_depth_attenuation(
            requirements_pass=True,
            delta45=0.1,
            p45=0.06,
            variance_ratio45=0.70,
        )
        == "phase2ad_depth_attenuation_not_supported"
    )
    assert (
        classify_depth_attenuation(
            requirements_pass=True,
            delta45=0.1,
            p45=0.01,
            variance_ratio45=0.80,
        )
        == "phase2ad_depth_attenuation_not_supported"
    )
    assert (
        classify_depth_attenuation(
            requirements_pass=True,
            delta45=0.0,
            p45=0.001,
            variance_ratio45=0.1,
        )
        == "phase2ad_depth_attenuation_not_supported"
    )


def test_phase2ad_paired_attenuation_test_is_deterministic_and_detects_strong_collapse():
    strong = [[0.10, 0.20, 0.30, 0.40, 0.50, 0.60] for _ in range(20)]
    collapsed = [[0.300, 0.305, 0.310, 0.315, 0.320, 0.325] for _ in range(20)]

    first = paired_dispersion_attenuation_p(
        strong,
        collapsed,
        repetitions=2_000,
        seed=12345,
    )
    second = paired_dispersion_attenuation_p(
        strong,
        collapsed,
        repetitions=2_000,
        seed=12345,
    )

    assert first == second
    delta, p_value, left_variance, right_variance = first
    assert delta > 0.0
    assert left_variance > right_variance
    assert p_value < 0.05
