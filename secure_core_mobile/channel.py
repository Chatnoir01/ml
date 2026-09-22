"""Authenticated session framing for host-to-boundary transport.

This development implementation uses HMAC-SHA256 with an injected session key
to exercise channel semantics. It is NOT a pVM key exchange or hardware-rooted
channel and must not be treated as such.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
from threading import Lock

from .rpc import RpcEnvelope
from .transport import decode_envelope, encode_envelope


@dataclass(frozen=True)
class AuthenticatedFrame:
    session_id: str
    sequence: int
    envelope: bytes
    tag_sha256: str


def _mac_input(session_id: str, sequence: int, envelope: bytes) -> bytes:
    header = json.dumps(
        {"session_id": session_id, "sequence": sequence},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    return header + b"\n" + envelope


def authenticate_frame(*, session_id: str, sequence: int, envelope: RpcEnvelope, key: bytes) -> AuthenticatedFrame:
    if not session_id or sequence < 0 or not key:
        raise ValueError("invalid authenticated-frame input")
    encoded = encode_envelope(envelope)
    tag = hmac.new(key, _mac_input(session_id, sequence, encoded), hashlib.sha256).hexdigest()
    return AuthenticatedFrame(session_id, sequence, encoded, tag)


class SessionVerifier:
    def __init__(self, *, session_id: str, key: bytes) -> None:
        if not session_id or not key:
            raise ValueError("session id and key required")
        self._session_id = session_id
        self._key = bytes(key)
        self._next_sequence = 0
        self._lock = Lock()

    def verify_and_decode(self, frame: AuthenticatedFrame) -> RpcEnvelope:
        with self._lock:
            if frame.session_id != self._session_id:
                raise ValueError("session mismatch")
            if frame.sequence != self._next_sequence:
                raise ValueError("replayed, skipped, or reordered frame")
            expected = hmac.new(
                self._key,
                _mac_input(frame.session_id, frame.sequence, frame.envelope),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, frame.tag_sha256):
                raise ValueError("frame authentication failed")
            envelope = decode_envelope(frame.envelope)
            self._next_sequence += 1
            return envelope
