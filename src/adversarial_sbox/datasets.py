"""Deterministic dataset generation for neural-distinguisher experiments.

The factory works on the fixed ToySPN interface and records ciphertext pairs
plus labels. It enforces unique plaintext blocks globally before splitting, so
no exact block or pair can reappear across train, validation, and test.
"""

from __future__ import annotations

from dataclasses import dataclass
import random

from .spn import MASK32, ToySPN


@dataclass(frozen=True, slots=True)
class PairSample:
    left: int
    right: int
    label: int

    def __post_init__(self) -> None:
        if not (0 <= self.left <= MASK32 and 0 <= self.right <= MASK32):
            raise ValueError("sample values must be 32-bit integers")
        if self.label not in (0, 1):
            raise ValueError("label must be 0 or 1")


def _pair_id(left: int, right: int) -> tuple[int, int]:
    return (left, right) if left <= right else (right, left)


def generate_balanced_pairs(
    cipher: ToySPN,
    *,
    pair_count: int,
    input_difference: int,
    seed: int,
    shuffle: bool = True,
) -> tuple[PairSample, ...]:
    """Generate an exactly balanced, block-disjoint classification dataset.

    Positive plaintext pairs satisfy ``p0 ^ p1 == input_difference``. Negative
    pairs are independent while excluding both that relation and equal-block
    pairs. Every plaintext block is used at most once in the whole dataset; as
    ToySPN is a permutation, every resulting ciphertext block is therefore also
    globally unique. The same cipher/key is used for both labels.
    """

    if pair_count <= 0 or pair_count % 2:
        raise ValueError("pair_count must be a positive even integer")
    if input_difference <= 0 or input_difference > MASK32:
        raise ValueError("input_difference must be in [1, 2**32 - 1]")

    rng = random.Random(seed)
    half = pair_count // 2
    samples: list[PairSample] = []
    seen_plaintexts: set[int] = set()

    while len(samples) < half:
        p0 = rng.randrange(MASK32 + 1)
        p1 = p0 ^ input_difference
        if p0 in seen_plaintexts or p1 in seen_plaintexts:
            continue
        seen_plaintexts.add(p0)
        seen_plaintexts.add(p1)
        samples.append(PairSample(cipher.encrypt_block(p0), cipher.encrypt_block(p1), 1))

    while len(samples) < pair_count:
        p0 = rng.randrange(MASK32 + 1)
        p1 = rng.randrange(MASK32 + 1)
        if p1 == p0 or (p0 ^ p1) == input_difference:
            continue
        if p0 in seen_plaintexts or p1 in seen_plaintexts:
            continue
        seen_plaintexts.add(p0)
        seen_plaintexts.add(p1)
        samples.append(PairSample(cipher.encrypt_block(p0), cipher.encrypt_block(p1), 0))

    if shuffle:
        rng.shuffle(samples)
    return tuple(samples)


def _validate_block_disjoint(samples: tuple[PairSample, ...]) -> None:
    seen: set[int] = set()
    for sample in samples:
        if sample.left == sample.right:
            raise ValueError("sample contains an identical left/right block")
        if sample.left in seen or sample.right in seen:
            raise ValueError("samples reuse a ciphertext block")
        seen.add(sample.left)
        seen.add(sample.right)


def split_dataset(
    samples: tuple[PairSample, ...],
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> tuple[tuple[PairSample, ...], tuple[PairSample, ...], tuple[PairSample, ...]]:
    """Split an immutable block-disjoint dataset into disjoint slices."""

    if not samples:
        raise ValueError("samples must not be empty")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0, 1)")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train + validation fractions must be < 1")

    _validate_block_disjoint(samples)

    n = len(samples)
    train_end = int(n * train_fraction)
    validation_end = train_end + int(n * validation_fraction)
    return (
        samples[:train_end],
        samples[train_end:validation_end],
        samples[validation_end:],
    )
