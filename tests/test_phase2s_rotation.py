"""RAVEN-independent Phase 2S-C ToySPN rotation ablation regression suite."""
import json

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.neural_heterogeneity import ROUND_KEYS
from adversarial_sbox.phase2s_rotation import (
    ROTATIONS, RotatedToySPN, active_bytes, rotl32, rotr32,
    run_cell, run_experiment,
)
from adversarial_sbox.phase2s_singlebit import run_cell as classical_baseline
from adversarial_sbox.spn import MASK32, ToySPN


@pytest.mark.parametrize("depth", [3, 4, 5])
def test_rotation_11_is_byte_exactly_the_original_toyspn(depth):
    keys = ROUND_KEYS[:depth+1]
    for item in CANDIDATES:
        original = ToySPN(item["sbox"], keys)
        independent = RotatedToySPN(item["sbox"], keys, 11)
        for p in (0,1,2,3,0x12345678,0xABCDABCD,0xFFFFFFFF):
            assert original.encrypt_block(p) == independent.encrypt_block(p)
            c = original.encrypt_block(p)
            assert independent.decrypt_block(c) == p


@pytest.mark.parametrize("rotation", ROTATIONS)
def test_variable_rotation_cipher_roundtrips(rotation):
    for depth in (3, 4, 5):
        cipher = RotatedToySPN(CANDIDATES[0]["sbox"],
                               ROUND_KEYS[:depth+1], rotation)
        for block in (0,1,42,0xDEADBEEF,0xFFFFFFFF):
            assert cipher.decrypt_block(cipher.encrypt_block(block)) == block


def test_11_bit_rotation_metric_matches_unmodified_baseline_exactly():
    for d in (1,256):
        for depth in (3,4,5):
            baseline = classical_baseline(
                candidate_index=0, depth=depth, difference=d,
                key_schedule="historical",
                train_per_label=64, test_per_label=128,
            )
            variant = run_cell(
                candidate_index=0, rounds=depth, difference=d, rotation=11,
                train_per_label=64, test_per_label=128,
            )
            assert variant["signed_holdout_advantage"] == baseline["test_signed_advantage"]
            assert variant["best_train_bit"] == baseline["selected_bit"]


def test_rotation_is_an_actual_cipher_factor_not_just_a_label():
    sbox = CANDIDATES[0]["sbox"]
    keys = ROUND_KEYS[:5]
    rotated7 = RotatedToySPN(sbox,keys,7)
    rotated11 = RotatedToySPN(sbox,keys,11)
    rotated13 = RotatedToySPN(sbox,keys,13)
    values = {f.encrypt_block(0x12345678) for f in (rotated7,rotated11,rotated13)}
    assert len(values) >= 2


def test_active_output_byte_counter_has_an_exact_interpretable_range():
    assert active_bytes(0) == 0
    assert active_bytes(0x00000001) == 1
    assert active_bytes(0x0000FFFF) == 2
    assert active_bytes(0xFFFFFFFF) == 4
    with pytest.raises(ValueError):
        active_bytes(-1)
    with pytest.raises(ValueError):
        active_bytes(True)


@pytest.mark.parametrize("rot", ROTATIONS)
def test_rotate_inverse_identity(rot):
    for value in (0,1,0x00010000,0xABCD0123,0xFFFFFFFF):
        assert rotr32(rotl32(value,rot),rot) == value


def test_all_conditions_are_distinct_and_no_nn_training():
    summary=run_experiment(train_per_label=64,test_per_label=128)
    assert summary["new_neural_trainings"] == 0
    assert summary["cell_count"] == 108
    assert len(summary["cells"]) == 108
    assert len(summary["summary"]) == 18
    assert summary["rotations"] == [7,11,13]
    assert summary["depths"] == [3,4,5]
    assert summary["differences"] == [1,256]
    assert summary["inference"].startswith("EXPLORATORY_")
    assert len(summary["receipt_sha256"]) == 64
    assert "private_weights" not in json.dumps(summary)
    for cell in summary["cells"]:
        assert -1.0 <= cell["signed_holdout_advantage"] <= 1.0
        assert -1.0 <= cell["shuffled_label_control"] <= 1.0
        assert 0 <= cell["best_train_bit"] < 32
        assert 0 <= cell["mean_positive_active_bytes"] <= 4
        assert 0 <= cell["mean_negative_active_bytes"] <= 4


def test_invalid_rotation_and_input_blocks_are_rejected():
    with pytest.raises(ValueError):
        RotatedToySPN(CANDIDATES[0]["sbox"], ROUND_KEYS[:4], 8)
    with pytest.raises(ValueError):
        RotatedToySPN(CANDIDATES[0]["sbox"], ROUND_KEYS[:4], True)
    cipher = RotatedToySPN(CANDIDATES[0]["sbox"], ROUND_KEYS[:4], 7)
    with pytest.raises(ValueError):
        cipher.encrypt_block(True)
    with pytest.raises(ValueError):
        cipher.decrypt_block(-1)
    with pytest.raises(ValueError):
        run_cell(candidate_index=0,rounds=4,difference=1,rotation=9,
                 train_per_label=64,test_per_label=128)
