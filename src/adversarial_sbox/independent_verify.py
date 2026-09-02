"""Independent reference verifier for final S-box evidence.

This module deliberately does not import ``cryptoshield`` or ``evolution``.  It
recomputes the project gates from the mathematical definitions using a separate,
straightforward implementation.  It is intentionally slower than CryptoShield and
is meant for confirmation receipts, not for search fitness.
"""

from __future__ import annotations

from dataclasses import dataclass

SBOX_SIZE = 256


@dataclass(frozen=True, slots=True)
class IndependentMetrics:
    nonlinearity: int
    differential_uniformity: int
    max_linear_correlation: int
    sac_score: float
    algebraic_degree: int


def _freeze_permutation(sbox) -> tuple[int, ...]:
    values = tuple(int(value) for value in sbox)
    if len(values) != SBOX_SIZE:
        raise ValueError(f"expected 256 entries, got {len(values)}")
    if any(value < 0 or value >= SBOX_SIZE for value in values):
        raise ValueError("S-box entries must be bytes")
    if len(set(values)) != SBOX_SIZE:
        raise ValueError("independent verifier requires a permutation")
    return values


def _parity(value: int) -> int:
    return value.bit_count() & 1


def independent_differential_uniformity(sbox) -> int:
    values = _freeze_permutation(sbox)
    maximum = 0
    for dx in range(1, SBOX_SIZE):
        counts = [0] * SBOX_SIZE
        for x in range(SBOX_SIZE):
            counts[values[x] ^ values[x ^ dx]] += 1
        row_max = max(counts)
        if row_max > maximum:
            maximum = row_max
    return maximum


def independent_linear_metrics(sbox) -> tuple[int, int]:
    """Return (vectorial nonlinearity, max absolute Walsh correlation).

    This is a direct definition-level implementation: no FWHT and no code shared
    with CryptoShield.  For each non-zero component mask b, correlations are
    accumulated directly over all 256 inputs for every input mask a.
    """

    values = _freeze_permutation(sbox)
    global_max = 0
    for output_mask in range(1, SBOX_SIZE):
        component_signs = [
            1 if _parity(output_mask & values[x]) == 0 else -1
            for x in range(SBOX_SIZE)
        ]
        for input_mask in range(SBOX_SIZE):
            correlation = 0
            for x, sign in enumerate(component_signs):
                correlation += sign if _parity(input_mask & x) == 0 else -sign
            magnitude = abs(correlation)
            if magnitude > global_max:
                global_max = magnitude
    return (SBOX_SIZE // 2) - (global_max // 2), global_max


def independent_sac_score(sbox) -> float:
    values = _freeze_permutation(sbox)
    changed = 0
    trials = 0
    for input_bit in range(8):
        delta = 1 << input_bit
        for x in range(SBOX_SIZE):
            changed += (values[x] ^ values[x ^ delta]).bit_count()
            trials += 8
    return changed / trials


def independent_algebraic_degree(sbox) -> int:
    values = _freeze_permutation(sbox)
    maximum_degree = 0
    for output_bit in range(8):
        anf = [(value >> output_bit) & 1 for value in values]
        # Direct Möbius transform, independently expressed from CryptoShield.
        stride = 1
        while stride < SBOX_SIZE:
            block = stride * 2
            for start in range(0, SBOX_SIZE, block):
                for offset in range(stride):
                    anf[start + stride + offset] ^= anf[start + offset]
            stride = block
        for monomial_mask, coefficient in enumerate(anf):
            if coefficient:
                degree = monomial_mask.bit_count()
                if degree > maximum_degree:
                    maximum_degree = degree
    return maximum_degree


def verify_independently(sbox) -> IndependentMetrics:
    values = _freeze_permutation(sbox)
    nonlinearity, max_corr = independent_linear_metrics(values)
    return IndependentMetrics(
        nonlinearity=nonlinearity,
        differential_uniformity=independent_differential_uniformity(values),
        max_linear_correlation=max_corr,
        sac_score=independent_sac_score(values),
        algebraic_degree=independent_algebraic_degree(values),
    )
