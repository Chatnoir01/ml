"""Promotion from verified attestation to boundary evidence.

Only a fully verified cryptographic result may assert host isolation.
"""

from __future__ import annotations
import hashlib

from .hostile_boundary import BoundaryEvidence, BoundaryKind
from .pvm_attestation import PvmAttestationStatement
from .pvm_verifier import PvmVerificationResult


def boundary_from_verified_attestation(
    *, statement: PvmAttestationStatement, result: PvmVerificationResult,
    evidence_bytes: bytes,
) -> BoundaryEvidence:
    if not result.verified:
        raise ValueError("unverified attestation cannot create trusted boundary")
    if not statement.authorization_state_inside_boundary:
        raise ValueError("authorization state not owned by protected boundary")
    if not statement.monotonic_state_inside_boundary:
        raise ValueError("monotonic state not owned by protected boundary")
    if not evidence_bytes:
        raise ValueError("missing attestation evidence bytes")
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id=statement.boundary_id,
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256=hashlib.sha256(evidence_bytes).hexdigest(),
    )
