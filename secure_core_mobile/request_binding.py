"""Canonical request binding for authorization evidence."""

from __future__ import annotations
import hashlib
import json

from .policy import AuthorizationRequest


def request_digest(request: AuthorizationRequest, *, payload: bytes) -> str:
    """Bind authorization to the exact operation, key, policy, nonce and payload."""
    body = {
        "operation": request.operation,
        "key_handle": request.key_handle,
        "policy_version": request.policy_version,
        "nonce": request.nonce,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()
