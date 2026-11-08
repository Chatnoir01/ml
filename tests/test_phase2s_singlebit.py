"""Tests for a NON-NEURAL, POSTHOC ToySPN single-bit differential baseline."""
import json
import math

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.neural_heterogeneity import ROUND_KEYS
from adversarial_sbox.phase2s_singlebit import (
    DEFAULT_TRAIN_PER_LABEL, DEFAULT_TEST_PER_LABEL, DEPTHS, DIFFERENCES,
    SCHEDULES, BitDecision, _control_shuffled_test, bit_frequencies,
    ciphertext_differences, learn_one_bit, matched_pairs, plaintext_pairs,
    run_cell, run_experiment, schedule, signed_test_advantage,
)
from adversarial_sbox.spn import MASK32, ToySPN


def _flatten(pairs):
    return {x for pair in pairs for x in pair}


def test_prepared_pairs_disjoint_across_labels_and_holdout():
    for delta in DIFFERENCES:
        tp, tn, hp, hn = matched_pairs(delta, 128, 256)
        assert len(tp) == len(tn) == 128
        assert len(hp) == len(hn) == 256
        assert all(x ^ y == delta for x, y in (*tp, *hp))
        assert all(x != y and x ^ y != delta for x, y in (*tn, *hn))
        blocks = [x for pairs in (tp, tn, hp, hn) for p in pairs for x in p]
        assert len(blocks) == len(set(blocks))


def test_plaintext_pair_generation_repeats_and_respects_excluded_blocks():
    first = plaintext_pairs(difference=1, per_label=128, seed=1234)
    assert first == plaintext_pairs(difference=1, per_label=128, seed=1234)
    excluded = _flatten(first[0]) | _flatten(first[1])
    second = plaintext_pairs(difference=1, per_label=128,
                             seed=1235, excluded_blocks=excluded)
    assert not excluded.intersection(_flatten(second[0]) | _flatten(second[1]))


def test_historic_and_alternative_schedules_are_distinct():
    assert schedule("historical") == ROUND_KEYS
    assert len({schedule(k) for k in SCHEDULES}) == 3
    for keys in (schedule(x) for x in SCHEDULES):
        assert len(keys) == 6
        assert all(type(v) is int and 0 <= v <= MASK32 for v in keys)
    with pytest.raises(ValueError, match="unregistered"):
        schedule("arbitrary")


def test_all_six_candidates_roundtrip_under_each_schedule():
    for scheme in SCHEDULES:
        for depth in DEPTHS:
            for item in CANDIDATES:
                cipher = ToySPN(item["sbox"], schedule(scheme)[:depth+1])
                for block in (0, 1, 0xF00DBABE):
                    assert cipher.decrypt_block(cipher.encrypt_block(block)) == block


def test_bit_frequency_and_train_only_selection():
    positive = (0b1000, 0b1010, 0b1000, 0b1010)
    negative = (0b0000, 0b0010, 0b0000, 0b0010)
    decision = learn_one_bit(positive, negative)
    assert decision == BitDecision(position=3, sign=1, train_gap=1.0)
    assert bit_frequencies(positive)[3] == 1.0
    assert signed_test_advantage(decision, positive, negative) == 1.0


def test_holdout_sign_can_reverse_without_selection_leakage():
    decision = learn_one_bit((1, 1, 1, 1), (0, 0, 0, 0))
    assert decision.position == 0 and decision.sign == 1
    # An unexpected opposite sign on test is RECORDED AS NEGATIVE.
    assert signed_test_advantage(decision, (0, 0), (1, 1)) == -1.0


def test_shuffled_label_control_zero_on_a_constant_bit():
    pos = (0,) * 100
    neg = (0,) * 100
    choice = BitDecision(0, 1, 0.)
    assert _control_shuffled_test(choice, pos, neg, seed=123) == 0.0


def test_explicitly_no_neural_training_in_a_single_smoke_cell():
    cell = run_cell(candidate_index=0, depth=4, difference=1,
                    key_schedule="historical",
                    train_per_label=64, test_per_label=128)
    assert cell["depth"] == 4
    assert cell["fingerprint"] == CANDIDATES[0]["fingerprint"]
    assert 0 <= cell["selected_bit"] < 32
    assert 0 <= cell["train_signed_gap"] <= 1.0
    assert -1.0 <= cell["test_signed_advantage"] <= 1.0
    assert -1.0 <= cell["test_label_shuffle_control"] <= 1.0


def test_full_grid_smoke_receipts_and_immutability():
    data = run_experiment(train_per_label=64, test_per_label=128)
    assert data["trained_neural_networks"] == 0
    assert data["new_neural_seed_count"] == 0
    assert data["cells"] == 6 * 3 * 2 * 3 == 108
    assert data["candidate_count"] == 6
    assert len(data["results"]) == 108
    assert len(data["summary"]) == 18
    assert data["frozen_neural_scores_are_posthoc_reference"] is True
    assert all(row["r_vs_frozen_neural_candidate_scores"] is None
               or -1.0 <= row["r_vs_frozen_neural_candidate_scores"] <= 1.0
               for row in data["summary"])
    assert set(data["schedules"]) == set(SCHEDULES)
    assert set(data["depths"]) == set(DEPTHS)
    assert set(data["differences"]) == set(DIFFERENCES)
    assert data["interpretation"].startswith("POSTHOC_")
    assert len(data["receipt_sha256"]) == 64
    assert "train_samples" not in json.dumps(data)
    assert "private_weights" not in json.dumps(data)
    assert not any(not math.isfinite(row["test_signed_advantage"])
                   for row in data["results"])


def test_determinism_independent_of_repeated_calls():
    first = run_cell(candidate_index=1, depth=3, difference=256,
                     key_schedule="rotated_perturbed",
                     train_per_label=64, test_per_label=128)
    second = run_cell(candidate_index=1, depth=3, difference=256,
                      key_schedule="rotated_perturbed",
                      train_per_label=64, test_per_label=128)
    assert first == second


@pytest.mark.parametrize("difference", [-1, 0, 2, 0xFFFFFFFF, True])
def test_unregistered_differences_rejected(difference):
    with pytest.raises(ValueError):
        plaintext_pairs(difference=difference, per_label=12, seed=10)


@pytest.mark.parametrize("count", [-1, 0, 50001, 1.5, True])
def test_invalid_pair_counts_rejected(count):
    with pytest.raises(ValueError):
        plaintext_pairs(difference=1, per_label=count, seed=10)


def test_invalid_random_seed_rejected():
    with pytest.raises(ValueError):
        plaintext_pairs(difference=1, per_label=2, seed=True)


def test_wrong_cipher_cell_rejected():
    with pytest.raises(ValueError):
        run_cell(candidate_index=6, depth=4, difference=1,
                 key_schedule="historical", train_per_label=64,
                 test_per_label=128)
    with pytest.raises(ValueError):
        run_cell(candidate_index=0, depth=6, difference=1,
                 key_schedule="historical", train_per_label=64,
                 test_per_label=128)


def test_differences_from_toy_cipher_are_unsigned_32bit():
    cipher = ToySPN(CANDIDATES[0]["sbox"], schedule("historical")[:4])
    samples, _ = plaintext_pairs(difference=1, per_label=16, seed=123)
    result = ciphertext_differences(cipher, samples)
    assert len(result) == 16
    assert all(0 <= value <= MASK32 for value in result)
