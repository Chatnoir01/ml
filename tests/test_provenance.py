from adversarial_sbox.datasets import generate_balanced_pairs
from adversarial_sbox.provenance import fingerprint_dataset, fingerprint_sbox
from adversarial_sbox.references import AES_SBOX
from adversarial_sbox.spn import ToySPN


ROUND_KEYS = (0x12345678, 0xBEEFCAFE, 0x0BADF00D, 0xCAFEBABE, 0x55AA55AA)


def test_sbox_fingerprint_is_stable_and_content_sensitive():
    original = fingerprint_sbox(AES_SBOX)
    assert len(original) == 64

    mutated = list(AES_SBOX)
    mutated[0], mutated[1] = mutated[1], mutated[0]
    assert fingerprint_sbox(mutated) != original


def test_dataset_fingerprint_is_reproducible():
    cipher = ToySPN(AES_SBOX, ROUND_KEYS)
    first = generate_balanced_pairs(
        cipher, pair_count=200, input_difference=0x40, seed=42
    )
    second = generate_balanced_pairs(
        cipher, pair_count=200, input_difference=0x40, seed=42
    )
    assert fingerprint_dataset(first) == fingerprint_dataset(second)
    assert len(fingerprint_dataset(first)) == 64


def test_dataset_fingerprint_is_order_sensitive():
    cipher = ToySPN(AES_SBOX, ROUND_KEYS)
    samples = generate_balanced_pairs(
        cipher, pair_count=200, input_difference=0x40, seed=42
    )
    assert fingerprint_dataset(samples) != fingerprint_dataset(tuple(reversed(samples)))
