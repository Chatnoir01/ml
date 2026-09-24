"""AuthGraph/Secretkeeper session state machine.

AOSP trust rule: pinning bytes is not identity verification. Only a future
native/platform verifier may create the private verification token accepted by
the session establishment transition.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib

class AuthGraphSessionState(str,Enum):
    NEW="NEW"; PEER_IDENTITY_PINNED="PEER_IDENTITY_PINNED"; ESTABLISHED="ESTABLISHED"; CLOSED="CLOSED"

_TOKEN_KEY=object()

class VerifiedSecretkeeperIdentity:
    __slots__=("public_key_sha256","provenance")
    def __init__(self,*,_key,public_key_sha256:str,provenance:str):
        if _key is not _TOKEN_KEY: raise TypeError("VerifiedSecretkeeperIdentity is verifier-issued only")
        self.public_key_sha256=public_key_sha256
        self.provenance=provenance

@dataclass(frozen=True)
class PvmfwValidatedSecretkeeperKey:
    """Key bytes read from the pvmfw-sanitized trusted /avf DT path."""
    public_key_cbor: bytes
    source_path: str = "/proc/device-tree/avf/secretkeeper_public_key"
    def __post_init__(self):
        if not self.public_key_cbor:
            raise ValueError("empty Secretkeeper public key")
        if self.source_path != "/proc/device-tree/avf/secretkeeper_public_key":
            raise ValueError("Secretkeeper key must come from trusted /avf DT path")

class SecretkeeperIdentityVerifierUnavailable:
    def verify(self,public_key:PvmfwValidatedSecretkeeperKey)->VerifiedSecretkeeperIdentity:
        raise RuntimeError("protected AVF Secretkeeper identity verifier not implemented")

@dataclass
class AuthGraphSession:
    state:AuthGraphSessionState=AuthGraphSessionState.NEW
    secretkeeper_public_key_cbor:bytes|None=None
    session_id:bytes|None=None
    request_sequence_number:int=0

    def pin_secretkeeper_identity(
        self,
        public_key: PvmfwValidatedSecretkeeperKey,
    ) -> None:
        if self.state is not AuthGraphSessionState.NEW:
            raise ValueError("invalid Secretkeeper identity transition")
        if not isinstance(public_key, PvmfwValidatedSecretkeeperKey):
            raise TypeError("pvmfw-validated Secretkeeper key required")
        self.secretkeeper_public_key_cbor = bytes(public_key.public_key_cbor)
        self.state = AuthGraphSessionState.PEER_IDENTITY_PINNED

    def mark_native_exchange_established(self,*,verified_identity:VerifiedSecretkeeperIdentity,session_id:bytes=b"")->None:
        if self.state is not AuthGraphSessionState.PEER_IDENTITY_PINNED:
            raise ValueError("Secretkeeper identity must be pinned before AuthGraph")
        if not isinstance(verified_identity,VerifiedSecretkeeperIdentity):
            raise TypeError("verifier-issued Secretkeeper identity required")
        actual=hashlib.sha256(self.secretkeeper_public_key_cbor or b"").hexdigest()
        if verified_identity.public_key_sha256!=actual:
            raise ValueError("verified Secretkeeper identity does not match pinned key")
        if not session_id: raise ValueError("AuthGraph session id required")
        self.session_id=bytes(session_id);self.request_sequence_number=0
        self.state=AuthGraphSessionState.ESTABLISHED

    @property
    def can_process_secret_management(self)->bool:
        return self.state is AuthGraphSessionState.ESTABLISHED

    def allocate_request_sequence(self)->int:
        if not self.can_process_secret_management: raise RuntimeError("AuthGraph session not established")
        value=self.request_sequence_number;self.request_sequence_number+=1;return value

    def close(self)->None:
        self.secretkeeper_public_key_cbor=None;self.session_id=None;self.state=AuthGraphSessionState.CLOSED
