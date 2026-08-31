"""Small reversible SPN used only as an experimental test vehicle.

This is deliberately not a production cipher.  Its role is to provide a fixed,
fully controlled environment in which only the S-Box changes between research
candidates.
"""

from __future__ import annotations

from collections.abc import Sequence

from .cryptoshield import is_bijective, validate_sbox

MASK16 = 0xFFFF


def _rotl16(value: int, amount: int) -> int:
    amount %= 16
    return ((value << amount) | (value >> (16 - amount))) & MASK16


def _rotr16(value: int, amount: int) -> int:
    amount %= 16
    return ((value >> amount) | (value << (16 - amount))) & MASK16


class ToySPN:
    """Two-byte educational substitution-permutation network."""

    def __init__(self, sbox: Sequence[int], round_keys: Sequence[int]):
        self.sbox = validate_sbox(sbox)
        if not is_bijective(self.sbox):
            raise ValueError("ToySPN requires a bijective S-Box")
        self.inverse_sbox = self._inverse(self.sbox)
        self.round_keys = tuple(int(k) for k in round_keys)
        if len(self.round_keys) < 2:
            raise ValueError("at least two round keys are required")
        if any(k < 0 or k > MASK16 for k in self.round_keys):
            raise ValueError("round keys must be 16-bit integers")
        self.rounds = len(self.round_keys) - 1

    @staticmethod
    def _inverse(sbox: Sequence[int]) -> tuple[int, ...]:
        inverse = [0] * 256
        for x, y in enumerate(sbox):
            inverse[y] = x
        return tuple(inverse)

    @staticmethod
    def _substitute(value: int, box: Sequence[int]) -> int:
        high = box[(value >> 8) & 0xFF]
        low = box[value & 0xFF]
        return (high << 8) | low

    def encrypt_block(self, plaintext: int) -> int:
        if plaintext < 0 or plaintext > MASK16:
            raise ValueError("plaintext must be a 16-bit integer")
        state = plaintext
        for round_index in range(self.rounds):
            state ^= self.round_keys[round_index]
            state = self._substitute(state, self.sbox)
            if round_index != self.rounds - 1:
                state = _rotl16(state, 5)
        return state ^ self.round_keys[-1]

    def decrypt_block(self, ciphertext: int) -> int:
        if ciphertext < 0 or ciphertext > MASK16:
            raise ValueError("ciphertext must be a 16-bit integer")
        state = ciphertext ^ self.round_keys[-1]
        for round_index in range(self.rounds - 1, -1, -1):
            if round_index != self.rounds - 1:
                state = _rotr16(state, 5)
            state = self._substitute(state, self.inverse_sbox)
            state ^= self.round_keys[round_index]
        return state
