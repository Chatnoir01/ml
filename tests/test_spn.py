import random

import pytest

from adversarial_sbox.references import AES_SBOX
from adversarial_sbox.spn import ToySPN


ROUND_KEYS = (0x12345678, 0xBEEFCAFE, 0x0BADF00D, 0xCAFEBABE, 0x55AA55AA)


def test_spn_round_trip_fixed_vectors():
    cipher = ToySPN(AES_SBOX, ROUND_KEYS)
    for plaintext in (
        0x00000000,
        0x00000001,
        0x000000FF,
        0x12345678,
        0x80000000,
        0xFFFFFFFF,
    ):
        ciphertext = cipher.encrypt_block(plaintext)
        assert cipher.decrypt_block(ciphertext) == plaintext


def test_spn_round_trip_deterministic_random_sample():
    cipher = ToySPN(AES_SBOX, ROUND_KEYS)
    rng = random.Random(1337)
    for _ in range(1024):
        plaintext = rng.randrange(0x100000000)
        assert cipher.decrypt_block(cipher.encrypt_block(plaintext)) == plaintext


def test_spn_rejects_non_bijective_sbox():
    invalid = list(AES_SBOX)
    invalid[0] = invalid[1]
    with pytest.raises(ValueError, match="bijective"):
        ToySPN(invalid, ROUND_KEYS)


def test_spn_rejects_out_of_range_block():
    cipher = ToySPN(AES_SBOX, ROUND_KEYS)
    with pytest.raises(ValueError):
        cipher.encrypt_block(0x100000000)
    with pytest.raises(ValueError):
        cipher.decrypt_block(-1)
