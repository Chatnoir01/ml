"""Bind trusted session establishment to verified pVM evidence."""

from __future__ import annotations
import hashlib
import hmac

from .hostile_boundary import BoundaryEvidence
from .session import SessionContext, establish_boundary_session


def derive_session_key_for_test_only(*, boundary: BoundaryEvidence, secret: bytes,
                                     challenge: bytes) -> bytes:
    """Deterministic development KDF for protocol tests only; not pVM key exchange."""
    if not boundary.qualifies_for_hostile_host_experiment:
        raise ValueError("unqualified boundary")
    if len(secret) < 32 or not challenge:
        raise ValueError("insufficient test KDF input")
    return hmac.new(secret, boundary.evidence_sha256.encode() + challenge, hashlib.sha256).digest()


def establish_verified_session_for_test_only(*, boundary: BoundaryEvidence,
                                             secret: bytes, challenge: bytes) -> SessionContext:
    key = derive_session_key_for_test_only(
        boundary=boundary, secret=secret, challenge=challenge
    )
    return establish_boundary_session(boundary=boundary, derived_key=key)
