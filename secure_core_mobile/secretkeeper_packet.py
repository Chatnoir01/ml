"""Fail-closed model of AOSP SecretManagement protected-packet metadata.

AOSP uses untagged COSE_Encrypt0, AES-GCM-256, a 12-byte IV, the AuthGraph
session ID as kid, and a request sequence number as external AAD in current
SecretManagement.cddl. This module validates bindings; native CBOR/AEAD remains
a separate integration step.
"""

from __future__ import annotations
from dataclasses import dataclass
import hmac

AES_GCM_256_COSE_ALG = 3
IV_BYTES = 12


@dataclass(frozen=True)
class ProtectedPacketBinding:
    session_id: bytes
    sequence_number: int
    iv: bytes
    algorithm: int = AES_GCM_256_COSE_ALG

    def validate(self) -> None:
        if self.algorithm != AES_GCM_256_COSE_ALG:
            raise ValueError("Secretkeeper requires COSE algorithm 3")
        if not self.session_id:
            raise ValueError("AuthGraph session id is required")
        if self.sequence_number < 0:
            raise ValueError("negative SecretManagement sequence number")
        if len(self.iv) != IV_BYTES:
            raise ValueError("Secretkeeper AES-GCM IV must be 12 bytes")


class SequenceWindow:
    """Strict per-session anti-replay sequence verifier."""

    def __init__(self) -> None:
        self._next = 0

    @property
    def next_sequence_number(self) -> int:
        return self._next

    def consume(self, sequence_number: int) -> None:
        if sequence_number != self._next:
            raise ValueError("SecretManagement replay/out-of-order sequence")
        self._next += 1


def verify_session_binding(expected_session_id: bytes, packet: ProtectedPacketBinding) -> None:
    packet.validate()
    if not hmac.compare_digest(expected_session_id, packet.session_id):
        raise ValueError("SecretManagement AuthGraph session mismatch")
