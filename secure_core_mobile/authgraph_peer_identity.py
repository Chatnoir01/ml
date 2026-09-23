"""Bind Secretkeeper authorization identity to AuthGraph peer_identity.

AOSP Secretkeeper uses peer_identity returned by AuthGraph as the client's DICE
chain for policy-gated storage. This module prevents substituting a separately
supplied DICE chain after the authenticated key exchange.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, hmac


@dataclass(frozen=True)
class AuthGraphPeerIdentity:
    dice_chain: bytes
    session_id: bytes
    peer_identity_sha256: str

    @classmethod
    def from_exchange(cls, *, dice_chain: bytes, session_id: bytes) -> "AuthGraphPeerIdentity":
        if not dice_chain or not session_id:
            raise ValueError("AuthGraph peer identity and session id are required")
        return cls(bytes(dice_chain), bytes(session_id), hashlib.sha256(dice_chain).hexdigest())

    def require_same_chain(self, candidate: bytes) -> None:
        if not hmac.compare_digest(hashlib.sha256(candidate).digest(), hashlib.sha256(self.dice_chain).digest()):
            raise ValueError("DICE chain substitution: not AuthGraph peer_identity")


@dataclass(frozen=True)
class PolicyAuthorizationContext:
    peer: AuthGraphPeerIdentity
    session_id: bytes

    def validate(self, *, candidate_dice_chain: bytes) -> None:
        if not hmac.compare_digest(self.session_id, self.peer.session_id):
            raise ValueError("AuthGraph session/identity mismatch")
        self.peer.require_same_chain(candidate_dice_chain)
