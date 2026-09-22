"""AuthGraph/Secretkeeper session state machine.

Models the AOSP role split: pVM client=P1/source, Secretkeeper=P2/sink.
No cryptographic success can be asserted until the native AuthGraph exchange
verifies the Secretkeeper identity supplied through the protected AVF path.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AuthGraphSessionState(str, Enum):
    NEW = "NEW"
    PEER_IDENTITY_PINNED = "PEER_IDENTITY_PINNED"
    ESTABLISHED = "ESTABLISHED"
    CLOSED = "CLOSED"


@dataclass
class AuthGraphSession:
    state: AuthGraphSessionState = AuthGraphSessionState.NEW
    secretkeeper_public_key_cbor: bytes | None = None

    def pin_secretkeeper_identity(self, public_key_cbor: bytes) -> None:
        if self.state is not AuthGraphSessionState.NEW or not public_key_cbor:
            raise ValueError("invalid Secretkeeper identity transition")
        self.secretkeeper_public_key_cbor = bytes(public_key_cbor)
        self.state = AuthGraphSessionState.PEER_IDENTITY_PINNED

    def mark_native_exchange_established(self, *, peer_identity_verified: bool) -> None:
        if self.state is not AuthGraphSessionState.PEER_IDENTITY_PINNED:
            raise ValueError("Secretkeeper identity must be pinned before AuthGraph")
        if not peer_identity_verified:
            raise ValueError("AuthGraph peer identity verification failed")
        self.state = AuthGraphSessionState.ESTABLISHED

    @property
    def can_process_secret_management(self) -> bool:
        return self.state is AuthGraphSessionState.ESTABLISHED

    def close(self) -> None:
        self.secretkeeper_public_key_cbor = None
        self.state = AuthGraphSessionState.CLOSED
