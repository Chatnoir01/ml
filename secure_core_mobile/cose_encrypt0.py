"""AOSP-aligned COSE_Encrypt0 cryptographic core for Secretkeeper.

Current AOSP SecretManagement uses untagged COSE_Encrypt0 with protected
{1:3, 4:session_id}, unprotected {5:iv}, AES-256-GCM, and an Enc_structure.
The external AAD mode is explicit because AOSP branches exist both with empty
external_aad and RequestSeqNum-bound external_aad.
"""

from __future__ import annotations
from dataclasses import dataclass
import os
from enum import Enum
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .secretkeeper_packet import ProtectedPacketBinding

AES256_KEY_BYTES = 32


class ExternalAadMode(str, Enum):
    EMPTY = "EMPTY"
    REQUEST_SEQNUM_U64 = "REQUEST_SEQNUM_U64"


def external_aad(sequence_number: int, mode: ExternalAadMode) -> bytes:
    if mode is ExternalAadMode.EMPTY:
        return b""
    if sequence_number < 0 or sequence_number > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("sequence out of uint64 range")
    return sequence_number.to_bytes(8, "big")


def _head(major: int, n: int) -> bytes:
    if n < 24: return bytes(((major << 5) | n,))
    if n <= 0xff: return bytes(((major << 5) | 24, n))
    if n <= 0xffff: return bytes(((major << 5) | 25,)) + n.to_bytes(2, "big")
    raise ValueError("CBOR field too large")


def _bstr(v: bytes) -> bytes: return _head(2, len(v)) + v
def _tstr(v: str) -> bytes:
    raw=v.encode(); return _head(3,len(raw))+raw


def protected_header(binding: ProtectedPacketBinding) -> bytes:
    binding.validate()
    # canonical CBOR {1:3,4:bstr(session_id)}
    return b"\xa2\x01\x03\x04" + _bstr(binding.session_id)


def enc_structure(protected: bytes, aad: bytes) -> bytes:
    return b"\x83" + _tstr("Encrypt0") + _bstr(protected) + _bstr(aad)


@dataclass(frozen=True)
class Encrypt0Packet:
    binding: ProtectedPacketBinding
    ciphertext: bytes


def encrypt(*, key: bytes, session_id: bytes, sequence_number: int, plaintext: bytes,
            iv: bytes | None = None, aad_mode: ExternalAadMode = ExternalAadMode.EMPTY) -> Encrypt0Packet:
    if len(key) != AES256_KEY_BYTES:
        raise ValueError("AES-256-GCM key must be 32 bytes")
    binding=ProtectedPacketBinding(session_id,sequence_number,iv or os.urandom(12))
    header=protected_header(binding)
    aad=enc_structure(header, external_aad(sequence_number,aad_mode))
    return Encrypt0Packet(binding,AESGCM(key).encrypt(binding.iv,plaintext,aad))


def decrypt(*, key: bytes, packet: Encrypt0Packet, expected_session_id: bytes,
            expected_sequence_number: int, aad_mode: ExternalAadMode = ExternalAadMode.EMPTY) -> bytes:
    if len(key) != AES256_KEY_BYTES:
        raise ValueError("AES-256-GCM key must be 32 bytes")
    packet.binding.validate()
    if packet.binding.session_id != expected_session_id:
        raise ValueError("COSE session binding mismatch")
    if packet.binding.sequence_number != expected_sequence_number:
        raise ValueError("COSE sequence binding mismatch")
    header=protected_header(packet.binding)
    aad=enc_structure(header, external_aad(expected_sequence_number,aad_mode))
    return AESGCM(key).decrypt(packet.binding.iv,packet.ciphertext,aad)
