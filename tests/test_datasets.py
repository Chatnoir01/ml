import pytest

from adversarial_sbox.datasets import PairSample, generate_balanced_pairs, split_dataset
from adversarial_sbox.references import AES_SBOX
from adversarial_sbox.spn import ToySPN


ROUND_KEYS = (0x12345678, 0xBEEFCAFE, 0x0BADF00D, 0xCAFEBABE, 0x55AA55AA)


def _cipher() -> ToySPN:
    return ToySPN(AES_SBOX, ROUND_KEYS)


def _unordered_pair(sample):
    return tuple(sorted((sample.left, sample.right)))


def _blocks(samples):
    return {block for sample in samples for block in (sample.left, sample.right)}


def test_dataset_is_exactly_balanced_and_deterministic():
    first = generate_balanced_pairs(
        _cipher(), pair_count=1000, input_difference=0x00400000, seed=20260831
    )
    second = generate_balanced_pairs(
        _cipher(), pair_count=1000, input_difference=0x00400000, seed=20260831
    )
    assert first == second
    assert sum(sample.label for sample in first) == 500
    assert len(first) == 1000


def test_dataset_contains_no_pair_or_block_duplicates():
    samples = generate_balanced_pairs(
        _cipher(), pair_count=4000, input_difference=0x00400000, seed=7
    )
    identities = {_unordered_pair(sample) for sample in samples}
    blocks = _blocks(samples)
    assert len(identities) == len(samples)
    assert len(blocks) == len(samples) * 2
    assert all(sample.left != sample.right for sample in samples)


def test_split_has_no_cross_partition_block_leakage():
    samples = generate_balanced_pairs(
        _cipher(), pair_count=2000, input_difference=0x00000040, seed=99
    )
    train, validation, test = split_dataset(samples)

    assert len(train) == 1400
    assert len(validation) == 300
    assert len(test) == 300

    train_blocks = _blocks(train)
    validation_blocks = _blocks(validation)
    test_blocks = _blocks(test)

    assert train_blocks.isdisjoint(validation_blocks)
    assert train_blocks.isdisjoint(test_blocks)
    assert validation_blocks.isdisjoint(test_blocks)


def test_generator_rejects_invalid_counts_and_differences():
    with pytest.raises(ValueError):
        generate_balanced_pairs(_cipher(), pair_count=999, input_difference=1, seed=1)
    with pytest.raises(ValueError):
        generate_balanced_pairs(_cipher(), pair_count=1000, input_difference=0, seed=1)
    with pytest.raises(ValueError):
        generate_balanced_pairs(
            _cipher(), pair_count=1000, input_difference=0x100000000, seed=1
        )


def test_split_rejects_overlapping_fraction_definition():
    samples = generate_balanced_pairs(
        _cipher(), pair_count=100, input_difference=1, seed=1
    )
    with pytest.raises(ValueError):
        split_dataset(samples, train_fraction=0.9, validation_fraction=0.2)


def test_split_rejects_reused_ciphertext_blocks():
    invalid = (
        PairSample(1, 2, 0),
        PairSample(2, 3, 1),
        PairSample(4, 5, 0),
        PairSample(6, 7, 1),
    )
    with pytest.raises(ValueError, match="reuse"):
        split_dataset(invalid)
