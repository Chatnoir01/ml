"""Versioned trust-anchor policy for Secure Core Mobile.

No Android/AVF root certificates are bundled here. Anchors must be provisioned
from authoritative platform material and pinned by SHA-256.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib

from cryptography import x509
from cryptography.hazmat.primitives import hashes

from .cert_chain import CertificateTrustStore


@dataclass(frozen=True)
class TrustAnchorRecord:
    der: bytes
    sha256: str
    source: str
    policy_version: int

    @classmethod
    def from_der(cls, *, der: bytes, expected_sha256: str, source: str,
                 policy_version: int) -> "TrustAnchorRecord":
        if not source or policy_version <= 0:
            raise ValueError("invalid trust-anchor provenance")
        cert = x509.load_der_x509_certificate(der)
        actual = cert.fingerprint(hashes.SHA256()).hex()
        if actual != expected_sha256.lower():
            raise ValueError("trust-anchor fingerprint mismatch")
        return cls(der=der, sha256=actual, source=source, policy_version=policy_version)


class VersionedTrustPolicy:
    def __init__(self, *, version: int, anchors: tuple[TrustAnchorRecord, ...]) -> None:
        if version <= 0 or not anchors:
            raise ValueError("trust policy requires version and anchors")
        if any(a.policy_version != version for a in anchors):
            raise ValueError("trust-anchor policy version mismatch")
        self.version = version
        self.anchors = anchors

    def certificate_store(self) -> CertificateTrustStore:
        return CertificateTrustStore(tuple(a.der for a in self.anchors))

    @property
    def manifest_sha256(self) -> str:
        body = "\n".join(sorted(f"{a.sha256}:{a.source}:{a.policy_version}" for a in self.anchors))
        return hashlib.sha256(body.encode()).hexdigest()
