"""Deterministic dataset generation for neural-distinguisher experiments.

The factory deliberately works on the fixed ToySPN interface and records only
ciphertext pairs plus labels. Positive samples are generated from a fixed input
difference; negative samples use an independently sampled second plaintext and
explicitly avoid accidentally matching that difference.
"""

from __future__ import annotations

from dataclasses import dataclass
import random

from .spn import MASK16, ToySPN


@dataclass(frozen=True, slots=True)
class PairSample:
    left: int
    right: int
    label: int

    def __post_init__(self) -> None:
        if not (0 <= self.left <= MASK16 and 0 <= self.right <= MASK16):
            raise ValueError("sample values must be 16-bit integers")
        if self.label not in (0, 1):
            raise ValueError("label must be 0 or 1")


def generate_balanced_pairs(
    cipher: ToySPN,
    *,
    pair_count: int,
    input_difference: int,
    seed: int,
    shuffle: bool = True,
) -> tuple[PairSample, ...]:
    """Generate an exactly balanced binary classification dataset.

    ``pair_count`` must be a positive even number. For label 1, plaintext pairs
    satisfy ``p0 ^ p1 == input_difference``. For label 0, the second plaintext
    is sampled independently while explicitly excluding that relation. The same
    cipher instance is used for both classes, preventing key/cipher identity from
    becoming a trivial label leak.
    """

    if pair_count <= 0 or pair_count % 2:
        raise ValueError("pair_count must be a positive even integer")
    if input_difference <= 0 or input_difference > MASK16:
        raise ValueError("input_difference must be in [1, 65535]")

    rng = random.Random(seed)
    half = pair_count // 2
    samples: list[PairSample] = []

    for _ in range(half):
        p0 = rng.randrange(MASK16 + 1)
        p1 = p0 ^ input_difference
        samples.append(
            PairSample(cipher.encrypt_block(p0), cipher.encrypt_block(p1), 1)
        )

    for _ in range(half):
        p0 = rng.randrange(MASK16 + 1)
        forbidden = p0 ^ input_difference
        p1 = rng.randrange(MASK16 + 1)
        while p1 == forbidden:
            p1 = rng.randrange(MASK16 + 1)
        samples.append(
            PairSample(cipher.encrypt_block(p0), cipher.encrypt_block(p1), 0)
        )

    if shuffle:
        rng.shuffle(samples)
    return tuple(samples)


def split_dataset(
    samples: tuple[PairSample, ...],
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> tuple[tuple[PairSample, ...], tuple[PairSample, ...], tuple[PairSample, ...]]:
    """Split an already-shuffled immutable dataset without overlap."""

    if not samples:
        raise ValueError("samples must not be empty")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0, 1)")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train + validation fractions must be < 1")

    n = len(samples)
    train_end = int(n * train_fraction)
    validation_end = train_end + int(n * validation_fraction)
    return (
        samples[:train_end],
        samples[train_end:validation_end],
        samples[validation_end:],
    )
