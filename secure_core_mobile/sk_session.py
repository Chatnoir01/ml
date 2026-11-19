"""Executable Secretkeeper session core aligned with AOSP SkSession semantics.

Maintains independent request/response AES-256 keys and independent outgoing/
incoming sequence counters. Transport is injected; this is not a Binder HAL.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

from .cose_encrypt0 import Encrypt0Packet, ExternalAadMode, decrypt, encrypt


class SecretkeeperTransport(Protocol):
    def transact(self, request: Encrypt0Packet) -> Encrypt0Packet: ...


@dataclass
class SecretkeeperSessionCore:
    encryption_key: bytes
    decryption_key: bytes
    session_id: bytes
    outgoing_sequence: int = 0
    incoming_sequence: int = 0
    aad_mode: ExternalAadMode = ExternalAadMode.REQUEST_SEQNUM_U64

    def __post_init__(self) -> None:
        if len(self.encryption_key) != 32 or len(self.decryption_key) != 32:
            raise ValueError("Secretkeeper session requires two AES-256 keys")
        if not self.session_id:
            raise ValueError("Secretkeeper session id required")

    def protect_request(self, plaintext: bytes, *, iv: bytes | None = None) -> Encrypt0Packet:
        seq = self.outgoing_sequence
        packet = encrypt(
            key=self.encryption_key, session_id=self.session_id,
            sequence_number=seq, plaintext=plaintext, iv=iv,
            aad_mode=self.aad_mode,
        )
        self.outgoing_sequence += 1
        return packet

    def open_response(self, packet: Encrypt0Packet) -> bytes:
        seq = self.incoming_sequence
        plaintext = decrypt(
            key=self.decryption_key, packet=packet,
            expected_session_id=self.session_id,
            expected_sequence_number=seq, aad_mode=self.aad_mode,
        )
        self.incoming_sequence += 1
        return plaintext

    def request(self, transport: SecretkeeperTransport, plaintext: bytes) -> bytes:
        return self.open_response(transport.transact(self.protect_request(plaintext)))
