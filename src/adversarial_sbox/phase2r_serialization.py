"""Canonical byte digest for *future* Phase-2R ciphertext-pair datasets.

Pure serialization only. NEVER trains models or modifies frozen Phase 2G.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Sequence

from .datasets import PairSample

_MAGIC = b"phase2r-pair-split-v1\x00"
_PARTS = ("train", "validation", "test")


def serialize_pair_split(samples: Sequence[PairSample], *, split: str) -> bytes:
    """Preserve order and all 32-bit ciphertext words + 1-byte binary label.

    Format: magic + ASCII split name + NUL + uint32-le count + N records
    each (uint32-le left, uint32-le right, uint8 label). Different split
    names cannot silently share the same reported digest.
    """
    if split not in _PARTS:
        raise ValueError("invalid Phase-2R split identity")
    if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes, bytearray)):
        raise ValueError("sample split must be a sequence of PairSample records")
    if not 0 < len(samples) <= (2 ** 32 - 1):
        raise ValueError("sample split must be nonempty and fit uint32")
    encoded = bytearray(_MAGIC)
    encoded.extend(split.encode("ascii"))
    encoded.append(0)
    encoded.extend(struct.pack("<I", len(samples)))
    for sample in samples:
        if not isinstance(sample, PairSample):
            raise ValueError("sample is not a PairSample record")
        # Exclude bool to ensure canonical integer ciphertext/label provenance.
        if any(type(v) is not int for v in (sample.left, sample.right, sample.label)):
            raise ValueError("invalid sample integer type")
        if not (0 <= sample.left <= 0xFFFFFFFF and 0 <= sample.right <= 0xFFFFFFFF):
            raise ValueError("sample ciphertext word out of uint32 bounds")
        if sample.label not in (0, 1):
            raise ValueError("invalid sample binary label")
        encoded.extend(struct.pack("<IIB", sample.left, sample.right, sample.label))
    return bytes(encoded)


def hash_pair_split(samples: Sequence[PairSample], *, split: str) -> str:
    """SHA-256 over versioned, explicit little-endian ciphertext data bytes."""
    return hashlib.sha256(serialize_pair_split(samples, split=split)).hexdigest()
