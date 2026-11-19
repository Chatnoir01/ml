"""Android platform evidence classification.

A generic cryptographic certificate-chain success is not sufficient to claim
Android AVF platform attestation. Platform evidence requires an explicitly
provisioned authoritative verifier profile.

PlatformVerification objects are issuer-created capability tokens, not caller
assertions. This is a software contract only; the real trust boundary still
depends on the authoritative verifier executing in the intended protected
environment.
"""

from __future__ import annotations

from enum import Enum


class PlatformEvidenceLevel(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    CRYPTOGRAPHICALLY_VERIFIED = "CRYPTOGRAPHICALLY_VERIFIED"
    PLATFORM_VERIFIED = "PLATFORM_VERIFIED"


_PLATFORM_EVIDENCE_ISSUER_KEY = object()
_ANDROID_AVF_AUTHORITY = "android-avf-authoritative"


def _validate_sha256(value: str) -> None:
    try:
        if len(value) != 64 or len(bytes.fromhex(value)) != 32:
            raise ValueError
    except ValueError as exc:
        raise ValueError("invalid platform evidence SHA-256") from exc


class PlatformVerification:
    __slots__ = ("level", "authority", "evidence_sha256")

    def __init__(
        self,
        level: PlatformEvidenceLevel,
        authority: str | None,
        evidence_sha256: str,
        *,
        _key: object,
    ) -> None:
        if _key is not _PLATFORM_EVIDENCE_ISSUER_KEY:
            raise TypeError("PlatformVerification is verifier-issued only")
        _validate_sha256(evidence_sha256)
        if level is PlatformEvidenceLevel.PLATFORM_VERIFIED:
            if authority != _ANDROID_AVF_AUTHORITY:
                raise ValueError("platform-verified AVF evidence requires authoritative origin")
        elif authority is not None:
            raise ValueError("non-authoritative evidence cannot carry platform authority")

        self.level = level
        self.authority = authority
        self.evidence_sha256 = evidence_sha256

    @property
    def qualifies_as_android_avf(self) -> bool:
        return (
            self.level is PlatformEvidenceLevel.PLATFORM_VERIFIED
            and self.authority == _ANDROID_AVF_AUTHORITY
        )


def generic_crypto_result(*, verified: bool, evidence_sha256: str) -> PlatformVerification:
    return PlatformVerification(
        PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED if verified
        else PlatformEvidenceLevel.UNVERIFIED,
        None,
        evidence_sha256,
        _key=_PLATFORM_EVIDENCE_ISSUER_KEY,
    )


def _issue_android_avf_platform_verification(
    *,
    evidence_sha256: str,
) -> PlatformVerification:
    """Internal issuance hook reserved for the authoritative AVF verifier."""
    return PlatformVerification(
        PlatformEvidenceLevel.PLATFORM_VERIFIED,
        _ANDROID_AVF_AUTHORITY,
        evidence_sha256,
        _key=_PLATFORM_EVIDENCE_ISSUER_KEY,
    )
