"""Red-first contract tests for Phase 2A-R rank-instability decomposition."""

from adversarial_sbox.phase2ar import (
    DATASET_SEEDS,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    RANK_STABILITY_THRESHOLD,
    REGIMES,
    TOTAL_TRAININGS,
    classify_diagnostic,
)


def test_phase2ar_frozen_contract_constants():
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert DATASET_SEEDS == (71001, 71009, 71023, 71039, 71059)
    assert MODEL_SEEDS == (81001, 81013, 81031, 81041, 81047)
    assert RANK_STABILITY_THRESHOLD == 0.60
    assert TOTAL_TRAININGS == 240
    assert REGIMES == (
        ("A", "bit_relu_mlp", 4, (0x00000001, 0x00000100)),
        ("B", "byte_tanh_mlp", 4, (0x00000001, 0x00000100)),
        ("C", "byte_tanh_mlp", 5, (0x00000001, 0x00000100)),
        ("D", "byte_tanh_mlp", 5, (0x00010000, 0x01000000)),
    )


def test_phase2ar_diagnostic_classification_is_frozen():
    assert classify_diagnostic(True, 0.2, 0.8, 0.9) == "phase2ar_architecture_transition_localized"
    assert classify_diagnostic(True, 0.8, 0.2, 0.9) == "phase2ar_round_transition_localized"
    assert classify_diagnostic(True, 0.8, 0.9, 0.2) == "phase2ar_difference_transition_localized"
    assert classify_diagnostic(True, 0.2, 0.3, 0.9) == "phase2ar_multiple_instabilities"
    assert classify_diagnostic(True, 0.8, 0.9, 0.7) == "phase2ar_no_adjacent_instability"
    assert classify_diagnostic(False, 0.9, 0.9, 0.9) == "phase2ar_inconclusive_signal"
