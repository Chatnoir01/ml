from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID, ObjectIdentifier

from secure_core_mobile.avf_extension import AVF_ATTESTATION_OID
from secure_core_mobile.avf_platform_verifier import (
    AndroidAvfAuthoritativeVerifier,
    AuthoritativeAvfTrustProfile,
    AvfTrustProfile,
    _issue_preprovisioned_avf_profile_pin_for_test,
    authoritative_profile_sha256,
    verify_avf_platform,
)
from secure_core_mobile.avf_policy import AvfComponentPolicy, ExpectedVmComponent
from secure_core_mobile.cert_chain import CertificateTrustStore
from secure_core_mobile.platform_evidence import PlatformEvidenceLevel


def _len(n: int) -> bytes:
    return bytes([n]) if n < 128 else b"\x81" + bytes([n])


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _len(len(value)) + value


def _avf_extension(challenge: bytes) -> bytes:
    component = _tlv(
        0x30,
        _tlv(0x0C, b"payload.apk")
        + _tlv(0x02, b"\x01")
        + _tlv(0x04, b"c" * 32)
        + _tlv(0x04, b"a" * 32),
    )
    return _tlv(
        0x30,
        _tlv(0x04, challenge)
        + _tlv(0x01, b"\xff")
        + _tlv(0x30, component),
    )


def _certificates(challenge: bytes = b"fresh") -> tuple[bytes, bytes]:
    now = datetime.now(timezone.utc)
    root_key = ed25519.Ed25519PrivateKey.generate()
    leaf_key = ed25519.Ed25519PrivateKey.generate()

    root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-avf-root")])
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-avf-leaf")])

    root = (
        x509.CertificateBuilder()
        .subject_name(root_name)
        .issuer_name(root_name)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(root_key, algorithm=None)
    )
    leaf = (
        x509.CertificateBuilder()
        .subject_name(leaf_name)
        .issuer_name(root_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=1))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.UnrecognizedExtension(
                ObjectIdentifier(AVF_ATTESTATION_OID),
                _avf_extension(challenge),
            ),
            critical=False,
        )
        .sign(root_key, algorithm=None)
    )
    return (
        leaf.public_bytes(serialization.Encoding.DER),
        root.public_bytes(serialization.Encoding.DER),
    )


def _policy() -> AvfComponentPolicy:
    return AvfComponentPolicy((
        ExpectedVmComponent("payload.apk", 1, b"c" * 32, b"a" * 32),
    ))


def test_authoritative_profile_requires_exact_anchor_pin() -> None:
    _, root = _certificates()
    store = CertificateTrustStore((root,))
    with pytest.raises(TypeError, match="protected AVF profile pin"):
        AuthoritativeAvfTrustProfile(store, "0" * 64)

    wrong = _issue_preprovisioned_avf_profile_pin_for_test("0" * 64)
    with pytest.raises(ValueError, match="pin mismatch"):
        AuthoritativeAvfTrustProfile(store, wrong)


def test_generic_chain_verification_never_becomes_platform_verified() -> None:
    leaf, root = _certificates()
    result = verify_avf_platform(
        chain_der=(leaf,),
        challenge=b"fresh",
        component_policy=_policy(),
        trust_profile=AvfTrustProfile(CertificateTrustStore((root,))),
    )
    assert result.level is PlatformEvidenceLevel.CRYPTOGRAPHICALLY_VERIFIED
    assert result.qualifies_as_android_avf is False


def test_pre_pinned_profile_can_issue_platform_verified_token() -> None:
    leaf, root = _certificates()
    store = CertificateTrustStore((root,))
    profile = AuthoritativeAvfTrustProfile(
        store,
        _issue_preprovisioned_avf_profile_pin_for_test(
            authoritative_profile_sha256(store)
        ),
    )
    result = AndroidAvfAuthoritativeVerifier(profile).verify(
        chain_der=(leaf,),
        challenge=b"fresh",
        component_policy=_policy(),
    )
    assert result.level is PlatformEvidenceLevel.PLATFORM_VERIFIED
    assert result.qualifies_as_android_avf is True
    assert len(result.evidence_sha256) == 64


def test_authoritative_verifier_rejects_challenge_substitution() -> None:
    leaf, root = _certificates(challenge=b"fresh")
    store = CertificateTrustStore((root,))
    profile = AuthoritativeAvfTrustProfile(
        store,
        _issue_preprovisioned_avf_profile_pin_for_test(
            authoritative_profile_sha256(store)
        ),
    )
    with pytest.raises(ValueError, match="challenge"):
        AndroidAvfAuthoritativeVerifier(profile).verify(
            chain_der=(leaf,),
            challenge=b"attacker",
            component_policy=_policy(),
        )


def test_profile_pin_changes_when_anchor_bundle_changes() -> None:
    _, first_root = _certificates()
    _, second_root = _certificates()
    first = CertificateTrustStore((first_root,))
    second = CertificateTrustStore((second_root,))
    assert authoritative_profile_sha256(first) != authoritative_profile_sha256(second)
