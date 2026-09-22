from secure_core_mobile.platform_evidence import (
    PlatformEvidenceLevel, generic_crypto_result,
)


def test_generic_certificate_success_is_not_android_avf_proof():
    evidence = generic_crypto_result(verified=True, evidence_sha256="a"*64)
    assert evidence.level is PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED
    assert evidence.qualifies_as_android_avf is False
