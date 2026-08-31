"""Small reversible 32-bit SPN used only as an experimental test vehicle.

This is deliberately not a production cipher. Its role is to provide a fixed,
fully controlled environment in which only the S-Box changes between research
candidates. A 32-bit state is used so later neural datasets can contain large
numbers of distinct pairs without the immediate collision ceiling of a 16-bit
state.
"""

from __future__ import annotations

from collections.abc import Sequence

from .cryptoshield import is_bijective, validate_sbox

MASK32 = 0xFFFFFFFF


def _rotl32(value: int, amount: int) -> int:
    amount %= 32
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def _rotr32(value: int, amount: int) -> int:
    amount %= 32
    return ((value >> amount) | (value << (32 - amount))) & MASK32


class ToySPN:
    """Four-byte educational substitution-permutation network.

    The construction is intentionally simple and must not be used as a real
    cipher. It exists only to isolate S-Box changes in controlled experiments.
    """

    def __init__(self, sbox: Sequence[int], round_keys: Sequence[int]):
        self.sbox = validate_sbox(sbox)
        if not is_bijective(self.sbox):
            raise ValueError("ToySPN requires a bijective S-Box")
        self.inverse_sbox = self._inverse(self.sbox)
        self.round_keys = tuple(int(k) for k in round_keys)
        if len(self.round_keys) < 2:
            raise ValueError("at least two round keys are required")
        if any(k < 0 or k > MASK32 for k in self.round_keys):
            raise ValueError("round keys must be 32-bit integers")
        self.rounds = len(self.round_keys) - 1

    @staticmethod
    def _inverse(sbox: Sequence[int]) -> tuple[int, ...]:
        inverse = [0] * 256
        for x, y in enumerate(sbox):
            inverse[y] = x
        return tuple(inverse)

    @staticmethod
    def _substitute(value: int, box: Sequence[int]) -> int:
        out = 0
        for shift in (24, 16, 8, 0):
            out |= box[(value >> shift) & 0xFF] << shift
        return out

    def encrypt_block(self, plaintext: int) -> int:
        if plaintext < 0 or plaintext > MASK32:
            raise ValueError("plaintext must be a 32-bit integer")
        state = plaintext
        for round_index in range(self.rounds):
            state ^= self.round_keys[round_index]
            state = self._substitute(state, self.sbox)
            if round_index != self.rounds - 1:
                state = _rotl32(state, 11)
        return state ^ self.round_keys[-1]

    def decrypt_block(self, ciphertext: int) -> int:
        if ciphertext < 0 or ciphertext > MASK32:
            raise ValueError("ciphertext must be a 32-bit integer")
        state = ciphertext ^ self.round_keys[-1]
        for round_index in range(self.rounds - 1, -1, -1):
            if round_index != self.rounds - 1:
                state = _rotr32(state, 11)
            state = self._substitute(state, self.inverse_sbox)
            state ^= self.round_keys[round_index]
        return state
