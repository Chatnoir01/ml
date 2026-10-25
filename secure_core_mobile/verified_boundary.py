"""Promotion from verified attestation to boundary evidence.

Only a fully verified cryptographic result may assert host isolation.
"""

from __future__ import annotations
from .hostile_boundary import BoundaryEvidence
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
    # PvmVerificationResult is a public, freely constructible dataclass.
    # Neither its booleans nor evidence_bytes establish authoritative Android
    # AVF/RKP provenance or execution inside a protected pVM.  In particular,
    # an arbitrary caller can construct all four True flags without executing
    # PvmAttestationVerifier.  Until a real protected, independently verified
    # issuer is integrated, do not manufacture qualifying BoundaryEvidence.
    raise ValueError("authoritative Android pVM boundary attestation not provisioned")
