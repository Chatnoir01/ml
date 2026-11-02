"""Phase 2T: pre-neural plaintext-source and model-initialization audit.

No neural training happens here. Dataset fingerprints are recomputed from the
actual generate_balanced_pairs function and ToySPN decryption, not invented
from seed names. A future runner must bind each run to these receipts.

Source-plaintext identifiers should be invariant across S-Boxes for the same
seed/difference/split, while ciphertext-dependent fingerprints may differ.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import struct
from typing import Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .neural100 import PAIR_COUNT
from .neural_heterogeneity import BYTE_HIDDEN_1, BYTE_HIDDEN_2, ROUND_KEYS
from .spn import MASK32, ToySPN

DOMAIN = b"Phase2T/source-provenance/v1\0"
MODEL_DOMAIN = b"Phase2T/byte-tanh-initial-weights/v1\0"


def _bytes_record(left: int, right: int, label: int) -> bytes:
    if not 0 <= left <= MASK32 or not 0 <= right <= MASK32 or label not in (0, 1):
        raise ValueError("unexpected pair value")
    return struct.pack(">IIB", left, right, label)


def digest_pairs(samples, *, decrypt_cipher=None) -> str:
    stream = hashlib.sha256(DOMAIN + (b"plaintext" if decrypt_cipher else b"ciphertext"))
    stream.update(len(samples).to_bytes(8, "big"))
    for sample in samples:
        left = int(sample.left)
        right = int(sample.right)
        if decrypt_cipher is not None:
            left = decrypt_cipher.decrypt_block(left)
            right = decrypt_cipher.decrypt_block(right)
        stream.update(_bytes_record(left, right, int(sample.label)))
    return stream.hexdigest()


def source_receipt(
    *, sbox: Sequence[int], difference: int, seed: int, pair_count: int = PAIR_COUNT,
) -> dict:
    if type(difference) is not int or difference not in (1, 256):
        raise ValueError("unregistered plaintext difference")
    if type(seed) is not int or seed < 0:
        raise ValueError("invalid dataset seed")
    if type(pair_count) is not int or pair_count < 4 or pair_count % 2:
        raise ValueError("balanced even dataset required")
    cipher = ToySPN(sbox, ROUND_KEYS[:5])
    samples = generate_balanced_pairs(
        cipher, pair_count=pair_count, input_difference=difference, seed=seed,
    )
    train, validation, test = split_dataset(samples)
    return {
        "dataset_seed": seed, "difference": difference, "pair_count": pair_count,
        "plain_source_sha256": digest_pairs(samples, decrypt_cipher=cipher),
        "cipher_dataset_sha256": digest_pairs(samples),
        "train_source_sha256": digest_pairs(train, decrypt_cipher=cipher),
        "validation_source_sha256": digest_pairs(validation, decrypt_cipher=cipher),
        "test_source_sha256": digest_pairs(test, decrypt_cipher=cipher),
        "train_cipher_sha256": digest_pairs(train),
        "validation_cipher_sha256": digest_pairs(validation),
        "test_cipher_sha256": digest_pairs(test),
        "split_sizes": (len(train), len(validation), len(test)),
    }


def audit_paired_sources(
    *, sboxes: Sequence[Sequence[int]], difference: int, seed: int,
    pair_count: int = PAIR_COUNT,
) -> list[dict]:
    if len(sboxes) < 2:
        raise ValueError("at least two independent candidates required")
    results = [
        source_receipt(sbox=s, difference=difference, seed=seed, pair_count=pair_count)
        for s in sboxes
    ]
    for field in (
        "plain_source_sha256", "train_source_sha256",
        "validation_source_sha256", "test_source_sha256", "split_sizes",
    ):
        if any(result[field] != results[0][field] for result in results[1:]):
            raise RuntimeError(f"paired input provenance drift: {field}")
    return results


def model_initial_state_fingerprint(model_seed: int) -> dict:
    """Recreate EXACT frozen byte-tanh network initialization draws.

    This does not inspect or change the actual trainer; independent source
    review and library-version checks remain necessary for real guarantees.
    """
    if type(model_seed) is not int or model_seed < 0:
        raise ValueError("invalid neural model seed")
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("NumPy required for initial-weight provenance, not training") from exc
    rng = np.random.default_rng(int(model_seed))
    w1 = rng.normal(
        0.0, math.sqrt(1.0 / 12.0), size=(12, BYTE_HIDDEN_1),
    ).astype(np.float32)
    b1 = np.zeros(BYTE_HIDDEN_1, dtype=np.float32)
    w2 = rng.normal(
        0.0, math.sqrt(1.0 / BYTE_HIDDEN_1),
        size=(BYTE_HIDDEN_1, BYTE_HIDDEN_2),
    ).astype(np.float32)
    b2 = np.zeros(BYTE_HIDDEN_2, dtype=np.float32)
    w3 = rng.normal(
        0.0, math.sqrt(1.0 / BYTE_HIDDEN_2), size=(BYTE_HIDDEN_2,),
    ).astype(np.float32)
    b3 = np.float32(0.0)
    h = hashlib.sha256(MODEL_DOMAIN)
    for name, weights in (("w1", w1), ("b1", b1), ("w2", w2),
                          ("b2", b2), ("w3", w3)):
        h.update(name.encode("ascii") + b"\0")
        h.update(str(tuple(weights.shape)).encode("ascii") + b"\0")
        h.update(weights.tobytes(order="C"))
    h.update(b"b3\0" + b3.tobytes())
    source = Path(__file__).with_name("neural_heterogeneity.py").read_bytes()
    return {
        "seed": model_seed,
        "architecture": "byte_tanh_mlp",
        "initial_state_sha256": h.hexdigest(),
        "trainer_source_sha256": hashlib.sha256(source).hexdigest(),
        "numpy_version": np.__version__,
        "training_executed": False,
    }
