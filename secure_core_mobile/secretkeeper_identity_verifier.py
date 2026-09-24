"""Secretkeeper identity verification boundary for pvmfw evidence.

The native/platform evidence provider is deliberately unavailable. This module
only implements the deterministic binding check that converts verifier-issued
pvmfw/reference-DT semantics plus authoritative AVF platform evidence into the
token accepted by AuthGraphSession.
"""

from __future__ import annotations

import hashlib

from .authgraph_session import (
    PvmfwValidatedSecretkeeperKey,
    VerifiedSecretkeeperIdentity,
    _TOKEN_KEY,
)
from .secretkeeper_cose_key import parse_secretkeeper_cose_key


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


class PvmfwSecretkeeperEvidenceProviderUnavailable:
    """Placeholder for the future native pvmfw/AVF platform evidence provider."""

    def collect(
        self,
        public_key: PvmfwValidatedSecretkeeperKey,
    ) -> PvmfwSecretkeeperBindingEvidence:
        raise RuntimeError(
            "authoritative AVF-bound Secretkeeper identity evidence provider not implemented"
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
