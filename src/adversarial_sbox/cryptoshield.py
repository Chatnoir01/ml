"""Classical S-Box measurements used as hard scientific gates.

The implementation deliberately has no ML dependency.  Phase 0 must be able to
verify classical properties independently before any learned oracle is added.
"""

from __future__ import annotations

from collections.abc import Sequence

SBOX_SIZE = 256


def validate_sbox(sbox: Sequence[int]) -> tuple[int, ...]:
    """Validate and freeze an 8x8 S-Box.

    A research candidate is required to map bytes to bytes.  Bijectivity is
    checked separately because some metrics are also meaningful for non-
    permutations.
    """

    if len(sbox) != SBOX_SIZE:
        raise ValueError(f"expected 256 entries, got {len(sbox)}")
    values = tuple(int(v) for v in sbox)
    if any(v < 0 or v > 0xFF for v in values):
        raise ValueError("all S-Box values must be bytes in [0, 255]")
    return values


def is_bijective(sbox: Sequence[int]) -> bool:
    values = validate_sbox(sbox)
    return len(set(values)) == SBOX_SIZE


def _parity(value: int) -> int:
    return value.bit_count() & 1


def differential_distribution_table(sbox: Sequence[int]) -> list[list[int]]:
    """Return the 256x256 differential distribution table (DDT)."""

    values = validate_sbox(sbox)
    table = [[0] * SBOX_SIZE for _ in range(SBOX_SIZE)]
    for input_difference in range(SBOX_SIZE):
        row = table[input_difference]
        for x in range(SBOX_SIZE):
            output_difference = values[x] ^ values[x ^ input_difference]
            row[output_difference] += 1
    return table


def differential_uniformity(sbox: Sequence[int]) -> int:
    """Maximum non-trivial DDT entry.

    The zero input-difference row is excluded by definition.
    """

    table = differential_distribution_table(sbox)
    return max(max(row) for row in table[1:])


def _fwht(values: list[int]) -> list[int]:
    """In-place Fast Walsh-Hadamard transform, returned for convenience."""

    out = values[:]
    width = 1
    n = len(out)
    while width < n:
        step = width * 2
        for start in range(0, n, step):
            for offset in range(width):
                i = start + offset
                j = i + width
                left = out[i]
                right = out[j]
                out[i] = left + right
                out[j] = left - right
        width = step
    return out


def linear_approximation_table(sbox: Sequence[int]) -> list[list[int]]:
    """Return Walsh correlations LAT[a][b] for input mask a/output mask b.

    Values are correlations in [-256, 256], not count biases.  Using a Walsh
    transform for each output mask keeps Phase-0 tests fast and deterministic.
    """

    values = validate_sbox(sbox)
    table = [[0] * SBOX_SIZE for _ in range(SBOX_SIZE)]
    for output_mask in range(SBOX_SIZE):
        signs = [
            1 if _parity(output_mask & values[x]) == 0 else -1
            for x in range(SBOX_SIZE)
        ]
        spectrum = _fwht(signs)
        for input_mask, correlation in enumerate(spectrum):
            table[input_mask][output_mask] = correlation
    return table


def max_linear_correlation(sbox: Sequence[int]) -> int:
    """Largest absolute non-trivial Walsh correlation."""

    table = linear_approximation_table(sbox)
    best = 0
    for input_mask in range(SBOX_SIZE):
        for output_mask in range(SBOX_SIZE):
            if input_mask == 0 and output_mask == 0:
                continue
            best = max(best, abs(table[input_mask][output_mask]))
    return best


def nonlinearity(sbox: Sequence[int]) -> int:
    """Vectorial nonlinearity: minimum over non-zero component masks."""

    values = validate_sbox(sbox)
    minimum = SBOX_SIZE
    for output_mask in range(1, SBOX_SIZE):
        signs = [
            1 if _parity(output_mask & values[x]) == 0 else -1
            for x in range(SBOX_SIZE)
        ]
        max_abs_walsh = max(abs(v) for v in _fwht(signs))
        component_nonlinearity = (SBOX_SIZE // 2) - (max_abs_walsh // 2)
        minimum = min(minimum, component_nonlinearity)
    return minimum


def sac_score(sbox: Sequence[int]) -> float:
    """Average output-bit flip probability under one-bit input flips.

    An ideal strict-avalanche score is 0.5.  This scalar is intentionally kept
    separate from per-bit SAC matrices so callers cannot mistake it for a hard
    security proof.
    """

    values = validate_sbox(sbox)
    changed_bits = 0
    trials = 0
    for input_bit in range(8):
        delta = 1 << input_bit
        for x in range(SBOX_SIZE):
            diff = values[x] ^ values[x ^ delta]
            changed_bits += diff.bit_count()
            trials += 8
    return changed_bits / trials


def algebraic_degree(sbox: Sequence[int]) -> int:
    """Maximum algebraic degree among the eight coordinate functions."""

    values = validate_sbox(sbox)
    best = 0
    for output_bit in range(8):
        coefficients = [(value >> output_bit) & 1 for value in values]
        # Möbius transform from truth table to ANF coefficients.
        for bit in range(8):
            step = 1 << bit
            for mask in range(SBOX_SIZE):
                if mask & step:
                    coefficients[mask] ^= coefficients[mask ^ step]
        for monomial, coefficient in enumerate(coefficients):
            if coefficient:
                best = max(best, monomial.bit_count())
    return best


def improved_transparency_order(sbox: Sequence[int]) -> float:
    """Return the Improved Transparency Order (ITO) of a balanced 8x8 S-Box.

    This is the corrected transparency-order criterion of Chakraborty et al.
    based on cross-correlations between coordinate functions.  For a balanced
    8x8 mapping, lower values indicate lower modeled leakage under the metric;
    ITO is not a standalone proof of physical side-channel resistance.

    The core implementation is intentionally dependency-free so Phase 0 remains
    reproducible without NumPy or any ML stack.
    """

    values = validate_sbox(sbox)
    if not is_bijective(values):
        raise ValueError(
            "improved transparency order requires a balanced 8x8 S-Box"
        )

    output_bits = 8
    component_signs = tuple(
        tuple(1 if ((value >> bit) & 1) == 0 else -1 for value in values)
        for bit in range(output_bits)
    )

    # C_Fi,Fj(a) = sum_x (-1)^(Fi(x) xor Fj(x xor a)), for a != 0.
    cross_correlations: list[list[list[int]]] = []
    for input_difference in range(1, SBOX_SIZE):
        matrix = [[0] * output_bits for _ in range(output_bits)]
        for left_bit in range(output_bits):
            left_signs = component_signs[left_bit]
            for right_bit in range(output_bits):
                right_signs = component_signs[right_bit]
                matrix[left_bit][right_bit] = sum(
                    left_signs[x] * right_signs[x ^ input_difference]
                    for x in range(SBOX_SIZE)
                )
        cross_correlations.append(matrix)

    denominator = SBOX_SIZE * (SBOX_SIZE - 1)  # 2^(2n) - 2^n for n=8.
    best = float("-inf")

    for beta in range(SBOX_SIZE):
        beta_signs = tuple(
            -1 if beta & (1 << bit) else 1 for bit in range(output_bits)
        )
        absolute_sum = 0

        for matrix in cross_correlations:
            for right_bit in range(output_bits):
                right_beta_sign = beta_signs[right_bit]
                weighted_correlation = sum(
                    beta_signs[left_bit]
                    * right_beta_sign
                    * matrix[left_bit][right_bit]
                    for left_bit in range(output_bits)
                )
                absolute_sum += abs(weighted_correlation)

        score = output_bits - (absolute_sum / denominator)
        best = max(best, score)

    return best
