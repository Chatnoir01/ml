import pytest

from secure_core_mobile.platform_evidence import (
    PlatformEvidenceLevel,
    PlatformVerification,
    generic_crypto_result,
)


def test_generic_certificate_success_is_not_android_avf_proof():
    evidence = generic_crypto_result(verified=True, evidence_sha256="a"*64)
    assert evidence.level is PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED
    assert evidence.qualifies_as_android_avf is False


def test_caller_cannot_construct_platform_verified_evidence():
    with pytest.raises(TypeError, match="verifier-issued"):
        PlatformVerification(
            PlatformEvidenceLevel.PLATFORM_VERIFIED,
            "android-avf-authoritative",
            "a" * 64,
            _key=object(),
        )


def test_generic_evidence_rejects_malformed_digest():
    with pytest.raises(ValueError, match="SHA-256"):
        generic_crypto_result(verified=True, evidence_sha256="not-a-digest")
