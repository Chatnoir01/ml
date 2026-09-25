"""Authenticated persistent-state envelope.

This detects tampering with serialized state using an injected MAC key. It does
not by itself prevent rollback: rollback resistance requires an independently
monotonic value owned by the stronger boundary.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json


@dataclass(frozen=True)
class AuthenticatedState:
    schema_version: int
    epoch: int
    counter: int
    payload_sha256: str
    tag_sha256: str

    def canonical_unsigned(self) -> bytes:
        return json.dumps({
            "schema_version": self.schema_version,
            "epoch": self.epoch,
            "counter": self.counter,
            "payload_sha256": self.payload_sha256,
        }, sort_keys=True, separators=(",", ":")).encode()


class StateAuthenticator:
    def __init__(self, key: bytes) -> None:
        if len(key) < 32:
            raise ValueError("state authentication key must be at least 32 bytes")
        self._key = key

    def seal(self, *, epoch: int, counter: int, payload: bytes) -> AuthenticatedState:
        if epoch <= 0 or counter < 0:
            raise ValueError("invalid monotonic coordinates")
        draft = AuthenticatedState(
            1, epoch, counter, hashlib.sha256(payload).hexdigest(), ""
        )
        tag = hmac.new(self._key, draft.canonical_unsigned(), hashlib.sha256).hexdigest()
        return AuthenticatedState(
            draft.schema_version, draft.epoch, draft.counter,
            draft.payload_sha256, tag,
        )

    def verify(self, state: AuthenticatedState, *, payload: bytes) -> None:
        if state.schema_version != 1:
            raise ValueError("unsupported authenticated-state schema")
        if hashlib.sha256(payload).hexdigest() != state.payload_sha256:
            raise ValueError("persistent payload digest mismatch")
        expected = hmac.new(
            self._key, state.canonical_unsigned(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, state.tag_sha256):
            raise ValueError("persistent state authentication failed")
