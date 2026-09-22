"""Composite AVF verifier: X.509 chain + documented leaf claims + component policy.

A caller-supplied generic root does not become Android authority. Platform
qualification is only emitted when the trust authority is explicitly the
authoritative Android AVF profile.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib

from .avf_certificate import verify_avf_leaf_claims
from .avf_policy import AvfComponentPolicy
from .cert_chain import CertificateTrustStore, verify_certificate_chain
from .platform_evidence import PlatformEvidenceLevel, PlatformVerification


@dataclass(frozen=True)
class AvfTrustProfile:
    certificate_store: CertificateTrustStore
    authority: str
    profile_version: int

    @property
    def authoritative(self) -> bool:
        return self.authority == "android-avf-authoritative" and self.profile_version > 0


def verify_avf_platform(
    *, chain_der: tuple[bytes, ...], challenge: bytes,
    component_policy: AvfComponentPolicy, trust_profile: AvfTrustProfile,
) -> PlatformVerification:
    if not chain_der:
        raise ValueError("empty AVF certificate chain")
    verify_certificate_chain(chain_der, trust_profile.certificate_store)
    claims = verify_avf_leaf_claims(chain_der[0], expected_challenge=challenge)
    component_policy.verify(claims)
    evidence_sha = hashlib.sha256(b"".join(chain_der)).hexdigest()
    if not trust_profile.authoritative:
        return PlatformVerification(
            PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED, None, evidence_sha
        )
    return PlatformVerification(
        PlatformEvidenceLevel.PLATFORM_VERIFIED,
        "android-avf-authoritative",
        evidence_sha,
    )
