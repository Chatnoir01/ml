"""Secretkeeper identity verification boundary for pvmfw evidence.

This module binds pvmfw/reference-DT semantics to authoritative AVF platform
evidence. It does not create that platform evidence itself; the authoritative
Android AVF verifier remains the upstream trust gate.
"""

from __future__ import annotations

import hashlib

from .authgraph_session import (
    PvmfwValidatedSecretkeeperKey,
    VerifiedSecretkeeperIdentity,
    _TOKEN_KEY,
)
from .secretkeeper_cose_key import parse_secretkeeper_cose_key
from .platform_evidence import PlatformVerification


_EVIDENCE_ISSUER_KEY = object()
PVMFW_BINDING_PROVENANCE = "pvmfw-reference-dt-bound-to-platform-evidence"


def _require_sha256(value: str, *, label: str) -> None:
    try:
        if len(value) != 64 or len(bytes.fromhex(value)) != 32:
            raise ValueError
    except ValueError as exc:
        raise ValueError(f"invalid {label} SHA-256") from exc


class PvmfwSecretkeeperBindingEvidence:
    """Verifier-issued evidence binding the trusted DT property to one key."""

    __slots__ = (
        "public_key_sha256",
        "platform_evidence_sha256",
        "provenance",
    )

    def __init__(
        self,
        *,
        _key: object,
        public_key_sha256: str,
        platform_evidence_sha256: str,
        provenance: str = PVMFW_BINDING_PROVENANCE,
    ) -> None:
        if _key is not _EVIDENCE_ISSUER_KEY:
            raise TypeError("pvmfw Secretkeeper binding evidence is verifier-issued only")
        _require_sha256(public_key_sha256, label="Secretkeeper public key")
        _require_sha256(platform_evidence_sha256, label="AVF platform evidence")
        if provenance != PVMFW_BINDING_PROVENANCE:
            raise ValueError("unexpected pvmfw Secretkeeper evidence provenance")
        self.public_key_sha256 = public_key_sha256
        self.platform_evidence_sha256 = platform_evidence_sha256
        self.provenance = provenance


class PvmfwSecretkeeperEvidenceProvider:
    """Bind a trusted-DT key to authoritative AVF execution evidence.

    pvmfw validates the trusted property during pVM boot. This provider does not
    independently re-run pvmfw; it requires an authoritative AVF platform token
    from the platform verifier and binds that evidence digest to the exact key.
    """

    def collect(
        self,
        public_key: PvmfwValidatedSecretkeeperKey,
        platform_verification: PlatformVerification,
    ) -> PvmfwSecretkeeperBindingEvidence:
        if not isinstance(public_key, PvmfwValidatedSecretkeeperKey):
            raise TypeError("pvmfw-validated Secretkeeper key required")
        if not isinstance(platform_verification, PlatformVerification):
            raise TypeError("verifier-issued AVF platform evidence required")
        if not platform_verification.qualifies_as_android_avf:
            raise ValueError("authoritative Android AVF platform evidence required")

        parse_secretkeeper_cose_key(public_key.public_key_cbor)
        return PvmfwSecretkeeperBindingEvidence(
            _key=_EVIDENCE_ISSUER_KEY,
            public_key_sha256=hashlib.sha256(public_key.public_key_cbor).hexdigest(),
            platform_evidence_sha256=platform_verification.evidence_sha256,
        )


class PvmfwSecretkeeperIdentityVerifier:
    """Bind verifier-issued pvmfw evidence to the exact DT key bytes."""

    def verify(
        self,
        public_key: PvmfwValidatedSecretkeeperKey,
        evidence: PvmfwSecretkeeperBindingEvidence,
    ) -> VerifiedSecretkeeperIdentity:
        if not isinstance(public_key, PvmfwValidatedSecretkeeperKey):
            raise TypeError("pvmfw-validated Secretkeeper key required")
        if not isinstance(evidence, PvmfwSecretkeeperBindingEvidence):
            raise TypeError("verifier-issued pvmfw Secretkeeper evidence required")

        # Re-validate the key profile at the trust transition as defense in
        # depth; callers may have constructed the provenance wrapper directly.
        parse_secretkeeper_cose_key(public_key.public_key_cbor)
        actual = hashlib.sha256(public_key.public_key_cbor).hexdigest()
        if evidence.public_key_sha256 != actual:
            raise ValueError("pvmfw Secretkeeper evidence does not match DT key")

        return VerifiedSecretkeeperIdentity(
            _key=_TOKEN_KEY,
            public_key_sha256=actual,
            provenance=(
                f"{evidence.provenance}:"
                f"{evidence.platform_evidence_sha256}"
            ),
        )
