"""Cryptographic provider boundary.

Providers receive opaque key handles only. The development provider deliberately
does not implement real cryptography or claim hardware protection.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


class CryptoProvider(Protocol):
    hardware_backed: bool

    def operate(self, *, operation: str, key_handle: str, payload: bytes) -> bytes: ...


@dataclass
class DevelopmentProvider:
    hardware_backed: bool = False
    call_count: int = 0

    def operate(self, *, operation: str, key_handle: str, payload: bytes) -> bytes:
        self.call_count += 1
        # Marker output only: this backend is SIMULATED and not cryptographic.
        return b"SIMULATED:" + operation.encode() + b":" + key_handle.encode()
