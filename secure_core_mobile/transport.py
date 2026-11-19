"""Transport-neutral codec for the protected-boundary RPC contract.

Framing is strict and size-bounded. Authentication/encryption belongs to the
future Android/pVM transport and is not claimed by this codec.
"""

from __future__ import annotations
import json

from .rpc import RpcEnvelope

MAX_FRAME_BYTES = 64 * 1024
_REQUIRED = {
    "version", "method", "request_id", "operation", "key_handle",
    "policy_version", "nonce", "payload_sha256",
}


def encode_envelope(envelope: RpcEnvelope) -> bytes:
    frame = envelope.canonical_bytes()
    if len(frame) > MAX_FRAME_BYTES:
        raise ValueError("rpc frame too large")
    return frame


def decode_envelope(frame: bytes) -> RpcEnvelope:
    if not frame or len(frame) > MAX_FRAME_BYTES:
        raise ValueError("invalid rpc frame size")
    try:
        body = json.loads(frame.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed rpc frame") from exc
    if not isinstance(body, dict) or set(body) != _REQUIRED:
        raise ValueError("rpc schema mismatch")
    if not all(isinstance(body[k], str) for k in (
        "method", "request_id", "operation", "key_handle", "nonce", "payload_sha256"
    )):
        raise ValueError("rpc field type mismatch")
    if type(body["version"]) is not int or type(body["policy_version"]) is not int:
        raise ValueError("rpc integer field type mismatch")
    if len(body["payload_sha256"]) != 64:
        raise ValueError("invalid payload digest")
    return RpcEnvelope(**body)
