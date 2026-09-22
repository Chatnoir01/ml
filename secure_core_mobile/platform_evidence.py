"""Android platform evidence classification.

A generic cryptographic certificate-chain success is not sufficient to claim
Android AVF platform attestation. Platform evidence requires an explicitly
provisioned authoritative verifier profile.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class PlatformEvidenceLevel(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    CRYPTOGRAPHICALLY_VERIFIED = "CRYPTOGRAPHICALLY_VERIFIED"
    PLATFORM_VERIFIED = "PLATFORM_VERIFIED"


@dataclass(frozen=True)
class PlatformVerification:
    level: PlatformEvidenceLevel
    authority: str | None
    evidence_sha256: str

    @property
    def qualifies_as_android_avf(self) -> bool:
        return (
            self.level is PlatformEvidenceLevel.PLATFORM_VERIFIED
            and self.authority == "android-avf-authoritative"
            and len(self.evidence_sha256) == 64
        )


def generic_crypto_result(*, verified: bool, evidence_sha256: str) -> PlatformVerification:
    return PlatformVerification(
        PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED if verified
        else PlatformEvidenceLevel.UNVERIFIED,
        None,
        evidence_sha256,
    )
