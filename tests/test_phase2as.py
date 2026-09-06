from __future__ import annotations


def test_phase2as_frozen_contract() -> None:
    from adversarial_sbox.phase2as import (
        ARCHITECTURE,
        DATASET_SEEDS,
        DEPTHS,
        DIFFERENCES,
        MODEL_SEEDS,
        PERMUTATIONS,
        TOTAL_TRAININGS,
        classify_depth_signal,
    )

    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTHS == (3, 4, 5)
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert DATASET_SEEDS == (72001, 72019, 72031, 72043, 72053, 72077, 72089, 72101, 72109, 72139)
    assert MODEL_SEEDS == (82003, 82013, 82021, 82037, 82051, 82067, 82073, 82091, 82109, 82129)
    assert PERMUTATIONS == 10_000
    assert TOTAL_TRAININGS == 360

    supported = classify_depth_signal(
        {
            3: {"signal_pass": True, "effect": 1.2, "score_range": 0.08},
            4: {"signal_pass": True, "effect": 1.0, "score_range": 0.06},
            5: {"signal_pass": False, "effect": 0.4, "score_range": 0.02},
        }
    )
    assert supported == "phase2as_depth_attenuation_supported"

    assert classify_depth_signal(
        {
            3: {"signal_pass": True, "effect": 1.2, "score_range": 0.08},
            4: {"signal_pass": True, "effect": 1.0, "score_range": 0.06},
            5: {"signal_pass": True, "effect": 0.9, "score_range": 0.05},
        }
    ) == "phase2as_signal_persists_to_5_rounds"

    assert classify_depth_signal(
        {
            3: {"signal_pass": False, "effect": 0.2, "score_range": 0.01},
            4: {"signal_pass": True, "effect": 1.0, "score_range": 0.06},
            5: {"signal_pass": False, "effect": 0.4, "score_range": 0.02},
        }
    ) == "phase2as_inconclusive_baseline_signal"
