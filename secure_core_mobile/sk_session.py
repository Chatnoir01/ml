"""Experimental Secretkeeper session state with fail-closed sequence/IV invariants.

Independent request/response AES-256 keys and counters. A development-only
in-memory object, NOT an Android pVM key exchange, monotonic hardware counter
or production Secretkeeper client. Requires a negotiated seqnum-AAD profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
import os
from typing import Protocol

from .cose_encrypt0 import (
    Encrypt0Packet,
    ExternalAadMode,
    decrypt_and_consume,
    encrypt,
)
from .secretkeeper_packet import MAX_SEQUENCE_NUMBER, SequenceWindow


class SecretkeeperTransport(Protocol):
    def transact(self, request: Encrypt0Packet) -> Encrypt0Packet: ...


@dataclass(repr=False, eq=False)
class SecretkeeperSessionCore:
    encryption_key: bytes
    decryption_key: bytes
    session_id: bytes
    outgoing_sequence: int = 0
    incoming_sequence: int = 0
    aad_mode: ExternalAadMode = ExternalAadMode.REQUEST_SEQNUM_U64

    _send_lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)
    _receive_lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)
    _exchange_lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)
    _seen_send_ivs: set[bytes] = field(default_factory=set, init=False, repr=False, compare=False)
    _receive_window: SequenceWindow = field(
        default_factory=SequenceWindow, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.encryption_key, bytes)
            or not isinstance(self.decryption_key, bytes)
            or len(self.encryption_key) != 32
            or len(self.decryption_key) != 32
        ):
            raise ValueError("Secretkeeper session requires two AES-256 keys")
        if self.encryption_key == self.decryption_key:
            raise ValueError("Secretkeeper requires distinct request/response keys")
        if not isinstance(self.session_id, bytes) or not 1 <= len(self.session_id) <= 65535:
            raise ValueError("Secretkeeper session id must be nonempty bounded bytes")
        if self.aad_mode is not ExternalAadMode.REQUEST_SEQNUM_U64:
            raise ValueError("Secretkeeper session requires authenticated sequence AAD mode")
        if type(self.outgoing_sequence) is not int or self.outgoing_sequence != 0:
            raise ValueError("Secretkeeper outgoing session counter must start at zero")
        if type(self.incoming_sequence) is not int or self.incoming_sequence != 0:
            raise ValueError("Secretkeeper incoming session counter must start at zero")

    def protect_request(self, plaintext: bytes, *, iv: bytes | None = None) -> Encrypt0Packet:
        """Send in strict counter order without reusing an IV in this live object.

        The caller/native transport still must guarantee globally unique key
        material and authenticated session binding across process restarts.
        """
        if not isinstance(plaintext, bytes):
            raise TypeError("Secretkeeper request plaintext must be bytes")
        with self._send_lock:
            sequence = self.outgoing_sequence
            if type(sequence) is not int or not 0 <= sequence <= MAX_SEQUENCE_NUMBER:
                raise ValueError("Secretkeeper outgoing sequence exhausted or invalid")
            selected_iv = os.urandom(12) if iv is None else iv
            if not isinstance(selected_iv, bytes) or len(selected_iv) != 12:
                raise ValueError("Secretkeeper outgoing IV must be 12 bytes")
            if selected_iv in self._seen_send_ivs:
                raise ValueError("Secretkeeper AES-GCM IV reused within session")
            packet = encrypt(
                key=self.encryption_key,
                session_id=self.session_id,
                sequence_number=sequence,
                plaintext=plaintext,
                iv=selected_iv,
                aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64,
            )
            self._seen_send_ivs.add(selected_iv)
            self.outgoing_sequence = sequence + 1
            return packet

    def open_response(self, packet: Encrypt0Packet) -> bytes:
        """Verify ciphertext, session and seqnum AAD before advancing once."""
        with self._receive_lock:
            if self.incoming_sequence != self._receive_window.next_sequence_number:
                raise ValueError("Secretkeeper incoming counter state mismatch")
            plaintext = decrypt_and_consume(
                key=self.decryption_key,
                packet=packet,
                expected_session_id=self.session_id,
                window=self._receive_window,
            )
            self.incoming_sequence = self._receive_window.next_sequence_number
            return plaintext

    def request(self, transport: SecretkeeperTransport, plaintext: bytes) -> bytes:
        """Serialize complete exchanges so responses cannot reorder locally."""
        with self._exchange_lock:
            return self.open_response(
                transport.transact(self.protect_request(plaintext))
            )
