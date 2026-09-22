"""Canonical host-to-boundary RPC envelope.

The boundary accepts authorization requests, not raw crypto commands.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json


RPC_VERSION = 1
ALLOWED_METHOD = "authorize_and_operate"


@dataclass(frozen=True)
class RpcEnvelope:
    version: int
    method: str
    request_id: str
    operation: str
    key_handle: str
    policy_version: int
    nonce: str
    payload_sha256: str

    def canonical_bytes(self) -> bytes:
        body = {
            "version": self.version,
            "method": self.method,
            "request_id": self.request_id,
            "operation": self.operation,
            "key_handle": self.key_handle,
            "policy_version": self.policy_version,
            "nonce": self.nonce,
            "payload_sha256": self.payload_sha256,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def build_envelope(*, request_id: str, operation: str, key_handle: str,
                   policy_version: int, nonce: str, payload: bytes) -> RpcEnvelope:
    return RpcEnvelope(
        version=RPC_VERSION,
        method=ALLOWED_METHOD,
        request_id=request_id,
        operation=operation,
        key_handle=key_handle,
        policy_version=policy_version,
        nonce=nonce,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
    )


def validate_envelope(envelope: RpcEnvelope, *, payload: bytes) -> None:
    if envelope.version != RPC_VERSION:
        raise ValueError("unsupported rpc version")
    if envelope.method != ALLOWED_METHOD:
        raise ValueError("direct crypto rpc forbidden")
    if not envelope.request_id or not envelope.operation or not envelope.key_handle or not envelope.nonce:
        raise ValueError("missing rpc security field")
    if envelope.policy_version < 0:
        raise ValueError("invalid policy version")
    if hashlib.sha256(payload).hexdigest() != envelope.payload_sha256:
        raise ValueError("rpc payload substitution detected")
