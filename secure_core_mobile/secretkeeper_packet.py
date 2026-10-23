"""Fail-closed model of AOSP SecretManagement protected-packet metadata.

AOSP uses untagged COSE_Encrypt0, AES-GCM-256, a 12-byte IV, the AuthGraph
session ID as kid, and a request sequence number as external AAD in current
SecretManagement.cddl. This module validates bindings; native CBOR/AEAD remains
a separate integration step.
"""

from __future__ import annotations
from dataclasses import dataclass
import hmac
from threading import Lock

AES_GCM_256_COSE_ALG = 3
IV_BYTES = 12
MAX_SEQUENCE_NUMBER = (1 << 64) - 1
MAX_SESSION_ID_BYTES = 65535  # Maximum length supported by the COSE CBOR encoder.


@dataclass(frozen=True)
class ProtectedPacketBinding:
    session_id: bytes
    sequence_number: int
    iv: bytes
    algorithm: int = AES_GCM_256_COSE_ALG

    def validate(self) -> None:
        if type(self.algorithm) is not int or self.algorithm != AES_GCM_256_COSE_ALG:
            raise ValueError("Secretkeeper requires COSE algorithm 3")
        if (
            not isinstance(self.session_id, bytes)
            or not (1 <= len(self.session_id) <= MAX_SESSION_ID_BYTES)
        ):
            raise ValueError("AuthGraph session id must be nonempty bytes within CBOR bounds")
        if type(self.sequence_number) is not int or not (
            0 <= self.sequence_number <= MAX_SEQUENCE_NUMBER
        ):
            raise ValueError("SecretManagement sequence must be a uint64")
        if not isinstance(self.iv, bytes) or len(self.iv) != IV_BYTES:
            raise ValueError("Secretkeeper AES-GCM IV must be 12 bytes")


class SequenceWindow:
    """Strict per-session anti-replay sequence verifier."""

    def __init__(self) -> None:
        self._next = 0
        self._lock = Lock()

    @property
    def next_sequence_number(self) -> int:
        with self._lock:
            return self._next

    def consume(self, sequence_number: int) -> None:
        """Advance exactly once for a previously authenticated uint64 sequence.

        Never call this before successful cryptographic verification.
        A development-only in-memory window is not rollback-protected state.
        """
        if type(sequence_number) is not int or not (
            0 <= sequence_number <= MAX_SEQUENCE_NUMBER
        ):
            raise ValueError("SecretManagement sequence must be a uint64")
        with self._lock:
            if self._next > MAX_SEQUENCE_NUMBER:
                raise ValueError("SecretManagement sequence exhausted")
            if sequence_number != self._next:
                raise ValueError("SecretManagement replay/out-of-order sequence")
            self._next += 1


def verify_session_binding(expected_session_id: bytes, packet: ProtectedPacketBinding) -> None:
    packet.validate()
    if not isinstance(expected_session_id, bytes):
        raise TypeError("expected AuthGraph session id must be bytes")
    if not hmac.compare_digest(expected_session_id, packet.session_id):
        raise ValueError("SecretManagement AuthGraph session mismatch")
