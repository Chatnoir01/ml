"""Stable fingerprints for research provenance and reproducibility receipts."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha3_256

from .cryptoshield import validate_sbox
from .datasets import PairSample


def fingerprint_sbox(sbox: Sequence[int]) -> str:
    """Return the SHA3-256 digest of the canonical 256-byte S-Box."""

    return sha3_256(bytes(validate_sbox(sbox))).hexdigest()


def fingerprint_dataset(samples: Sequence[PairSample]) -> str:
    """Return an order-sensitive SHA3-256 digest of canonical samples."""

    digest = sha3_256()
    for sample in samples:
        digest.update(sample.left.to_bytes(4, "big"))
        digest.update(sample.right.to_bytes(4, "big"))
        digest.update(bytes((sample.label,)))
    return digest.hexdigest()
