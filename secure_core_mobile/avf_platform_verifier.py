"""Composite AVF verifier with fail-closed platform provenance.

Generic trust stores can establish cryptographic validity only. PLATFORM_VERIFIED
requires an authoritative profile whose exact anchor bundle is bound to a
pre-provisioned SHA-256 pin. This repository intentionally ships no Android/RKP
trust anchors or production pin.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json

from .avf_certificate import verify_avf_leaf_claims
from .avf_policy import AvfComponentPolicy
from .cert_chain import CertificateTrustStore, verify_certificate_chain
from .platform_evidence import (
    PlatformVerification,
    _issue_android_avf_platform_verification,
    generic_crypto_result,
)


@dataclass(frozen=True)
class AvfTrustProfile:
    certificate_store: CertificateTrustStore
    profile_version: int = 1

    def __post_init__(self) -> None:
        if self.profile_version <= 0:
            raise ValueError("AVF trust profile version must be positive")


def authoritative_profile_sha256(
    certificate_store: CertificateTrustStore,
    *,
    profile_version: int = 1,
) -> str:
    if profile_version <= 0:
        raise ValueError("AVF trust profile version must be positive")
    if not certificate_store.anchors_der:
        raise ValueError("authoritative AVF trust profile requires anchors")

    anchor_digests = sorted(
        hashlib.sha256(anchor).hexdigest()
        for anchor in certificate_store.anchors_der
    )
    if len(anchor_digests) != len(set(anchor_digests)):
        raise ValueError("duplicate authoritative AVF trust anchor")

    payload = json.dumps(
        {
            "schema_version": 1,
            "profile_version": profile_version,
            "anchor_sha256": anchor_digests,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AuthoritativeAvfTrustProfile:
    """Exact pinned root-of-trust configuration for Android AVF verification.

    expected_profile_sha256 must be provisioned from outside attacker-controlled
    runtime state, for example as immutable pVM image configuration.
    """

    certificate_store: CertificateTrustStore
    expected_profile_sha256: str
    profile_version: int = 1

    def __post_init__(self) -> None:
        try:
            if (
                len(self.expected_profile_sha256) != 64
                or len(bytes.fromhex(self.expected_profile_sha256)) != 32
            ):
                raise ValueError
        except ValueError as exc:
            raise ValueError("invalid authoritative AVF profile pin") from exc

        actual = authoritative_profile_sha256(
            self.certificate_store,
            profile_version=self.profile_version,
        )
        if not hmac.compare_digest(actual, self.expected_profile_sha256):
            raise ValueError("authoritative AVF trust profile pin mismatch")

    @property
    def profile_sha256(self) -> str:
        return self.expected_profile_sha256


class AndroidAvfAuthoritativeVerifierUnavailable:
    """Fail-closed default when no authoritative profile has been provisioned."""

    def verify(self, *args, **kwargs):
        raise RuntimeError("authoritative Android AVF/RKP verifier not implemented/configured")


class AndroidAvfAuthoritativeVerifier:
    """Verify AVF evidence against an exact pre-pinned trust profile."""

    def __init__(self, trust_profile: AuthoritativeAvfTrustProfile) -> None:
        if not isinstance(trust_profile, AuthoritativeAvfTrustProfile):
            raise TypeError("authoritative AVF trust profile required")
        self._trust_profile = trust_profile

    def verify(
        self,
        *,
        chain_der: tuple[bytes, ...],
        challenge: bytes,
        component_policy: AvfComponentPolicy,
    ) -> PlatformVerification:
        if not chain_der:
            raise ValueError("empty AVF certificate chain")

        verify_certificate_chain(
            chain_der,
            self._trust_profile.certificate_store,
        )
        claims = verify_avf_leaf_claims(
            chain_der[0],
            expected_challenge=challenge,
        )
        component_policy.verify(claims)

        digest = hashlib.sha256()
        digest.update(b"SCM-ANDROID-AVF-AUTHORITATIVE-V1\x00")
        digest.update(bytes.fromhex(self._trust_profile.profile_sha256))
        for cert in chain_der:
            digest.update(len(cert).to_bytes(8, "big"))
            digest.update(cert)

        return _issue_android_avf_platform_verification(
            evidence_sha256=digest.hexdigest(),
        )


def verify_avf_platform(
    *,
    chain_der: tuple[bytes, ...],
    challenge: bytes,
    component_policy: AvfComponentPolicy,
    trust_profile: AvfTrustProfile,
) -> PlatformVerification:
    """Generic cryptographic AVF validation; never platform-authoritative."""
    if not chain_der:
        raise ValueError("empty AVF certificate chain")
    verify_certificate_chain(chain_der, trust_profile.certificate_store)
    claims = verify_avf_leaf_claims(chain_der[0], expected_challenge=challenge)
    component_policy.verify(claims)
    evidence_sha = hashlib.sha256(b"".join(chain_der)).hexdigest()
    return generic_crypto_result(
        verified=True,
        evidence_sha256=evidence_sha,
    )
