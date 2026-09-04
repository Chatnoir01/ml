import math

import pytest

from adversarial_sbox.cryptoshield import (
    algebraic_degree,
    differential_distribution_table,
    differential_uniformity,
    improved_transparency_order,
    is_bijective,
    linear_approximation_table,
    max_linear_correlation,
    nonlinearity,
    sac_score,
    validate_sbox,
)
from adversarial_sbox.references import AES_SBOX


def test_aes_reference_is_bijective():
    assert is_bijective(AES_SBOX)


def test_aes_reference_nonlinearity_is_112():
    assert nonlinearity(AES_SBOX) == 112


def test_aes_reference_differential_uniformity_is_4():
    assert differential_uniformity(AES_SBOX) == 4


def test_aes_reference_max_linear_correlation_is_32():
    assert max_linear_correlation(AES_SBOX) == 32


def test_aes_reference_algebraic_degree_is_7():
    assert algebraic_degree(AES_SBOX) == 7


def test_aes_improved_transparency_order_matches_reference():
    assert improved_transparency_order(AES_SBOX) == pytest.approx(6.916054, abs=1e-6)


def test_improved_transparency_order_rejects_non_balanced_8x8_mapping():
    non_balanced = tuple(0 for _ in range(256))
    with pytest.raises(ValueError, match="balanced"):
        improved_transparency_order(non_balanced)


def test_aes_sac_scalar_is_close_to_half():
    score = sac_score(AES_SBOX)
    assert 0.49 <= score <= 0.52


def test_ddt_rows_sum_to_256():
    table = differential_distribution_table(AES_SBOX)
    assert all(sum(row) == 256 for row in table)
    assert table[0][0] == 256
    assert sum(table[0][1:]) == 0


def test_lat_trivial_entry_and_shape():
    table = linear_approximation_table(AES_SBOX)
    assert len(table) == 256
    assert all(len(row) == 256 for row in table)
    assert table[0][0] == 256


def test_invalid_sbox_length_is_rejected():
    with pytest.raises(ValueError):
        validate_sbox(range(255))


def test_out_of_range_value_is_rejected():
    candidate = list(range(256))
    candidate[-1] = 256
    with pytest.raises(ValueError):
        validate_sbox(candidate)


def test_identity_sbox_is_linear_and_weak():
    identity = tuple(range(256))
    assert is_bijective(identity)
    assert nonlinearity(identity) == 0
    assert differential_uniformity(identity) == 256
    assert max_linear_correlation(identity) == 256
    assert algebraic_degree(identity) == 1
    assert math.isclose(sac_score(identity), 0.125)
