"""Synthetic, training-free proof of Phase-2R canonical dataset-byte hashes."""

from __future__ import annotations

import hashlib
import struct

import pytest

from adversarial_sbox.datasets import PairSample
from adversarial_sbox.phase2r_serialization import hash_pair_split, serialize_pair_split


def test_exact_wire_format_little_endian_and_one_byte_label() -> None:
    samples = (PairSample(0x01020304, 0xA0B0C0D0, 1),)
    raw = serialize_pair_split(samples, split="train")
    assert raw == (
        b"phase2r-pair-split-v1\x00train\x00"
        + struct.pack("<I", 1)
        + struct.pack("<IIB", 0x01020304, 0xA0B0C0D0, 1)
    )
    assert hash_pair_split(samples, split="train") == hashlib.sha256(raw).hexdigest()


def test_order_and_labels_change_dataset_hash() -> None:
    a = PairSample(1, 2, 0)
    b = PairSample(3, 4, 1)
    assert hash_pair_split((a, b), split="train") != hash_pair_split((b, a), split="train")
    assert hash_pair_split((a, b), split="train") != hash_pair_split(
        (PairSample(1, 2, 1), b), split="train"
    )


def test_split_is_domain_separated() -> None:
    samples = (PairSample(12, 34, 1),)
    hashes = [hash_pair_split(samples, split=name) for name in ("train", "validation", "test")]
    assert len(set(hashes)) == 3


def test_identical_inputs_are_reproducible() -> None:
    one = (PairSample(0, 0xFFFFFFFF, 0), PairSample(1, 12, 1))
    two = tuple(PairSample(x.left, x.right, x.label) for x in one)
    assert serialize_pair_split(one, split="validation") == serialize_pair_split(
        two, split="validation"
    )


def test_empty_or_unknown_split_is_rejected() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        serialize_pair_split((), split="test")
    with pytest.raises(ValueError, match="invalid"):
        serialize_pair_split((PairSample(1, 2, 1),), split="heldout")


def test_unstructured_or_malformed_samples_are_rejected() -> None:
    with pytest.raises(ValueError, match="sequence"):
        serialize_pair_split("not samples", split="train")
    with pytest.raises(ValueError, match="PairSample"):
        serialize_pair_split(((1, 2, 1),), split="train")
