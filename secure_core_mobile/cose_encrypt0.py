"""Minimal deterministic COSE_Encrypt0 codec for Secretkeeper integration tests.

Implements the COSE Enc_structure and AES-256-GCM primitive. The outer wire
container remains an explicit project codec until byte-for-byte AOSP vectors
are imported; therefore this module is not platform evidence.
"""

from __future__ import annotations
from dataclasses import dataclass
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .secretkeeper_packet import ProtectedPacketBinding

AES256_KEY_BYTES = 32


def _u64(value: int) -> bytes:
    if value < 0 or value > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("sequence out of uint64 range")
    return value.to_bytes(8, "big")


def external_aad(sequence_number: int) -> bytes:
    return _u64(sequence_number)


def protected_header(binding: ProtectedPacketBinding) -> bytes:
    binding.validate()
    # Canonical CBOR map {1: 3, 4: bstr(session_id)}.
    # Major types used here have compact deterministic encodings.
    sid = binding.session_id
    if len(sid) > 23:
        raise ValueError("session id too long for minimal codec")
    return bytes((0xA2, 0x01, 0x03, 0x04, 0x40 + len(sid))) + sid


def enc_structure(protected: bytes, aad: bytes) -> bytes:
    # Canonical CBOR ["Encrypt0", protected-bstr, external_aad-bstr].
    context = b"Encrypt0"
    if len(protected) > 23 or len(aad) > 23:
        raise ValueError("field too long for minimal codec")
    return (
        b"\x83" + bytes((0x60 + len(context),)) + context
        + bytes((0x40 + len(protected),)) + protected
        + bytes((0x40 + len(aad),)) + aad
    )


@dataclass(frozen=True)
class Encrypt0Packet:
    binding: ProtectedPacketBinding
    ciphertext: bytes


def encrypt(*, key: bytes, session_id: bytes, sequence_number: int, plaintext: bytes, iv: bytes | None = None) -> Encrypt0Packet:
    if len(key) != AES256_KEY_BYTES:
        raise ValueError("AES-256-GCM key must be 32 bytes")
    binding = ProtectedPacketBinding(session_id, sequence_number, iv or os.urandom(12))
    header = protected_header(binding)
    aad = enc_structure(header, external_aad(sequence_number))
    return Encrypt0Packet(binding, AESGCM(key).encrypt(binding.iv, plaintext, aad))


def decrypt(*, key: bytes, packet: Encrypt0Packet, expected_session_id: bytes, expected_sequence_number: int) -> bytes:
    if len(key) != AES256_KEY_BYTES:
        raise ValueError("AES-256-GCM key must be 32 bytes")
    packet.binding.validate()
    if packet.binding.session_id != expected_session_id:
        raise ValueError("COSE session binding mismatch")
    if packet.binding.sequence_number != expected_sequence_number:
        raise ValueError("COSE sequence binding mismatch")
    header = protected_header(packet.binding)
    aad = enc_structure(header, external_aad(expected_sequence_number))
    return AESGCM(key).decrypt(packet.binding.iv, packet.ciphertext, aad)
