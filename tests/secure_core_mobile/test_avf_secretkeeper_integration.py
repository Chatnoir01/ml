from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.x509.oid import NameOID, ObjectIdentifier

from secure_core_mobile.authgraph_session import AuthGraphSession
from secure_core_mobile.avf_extension import AVF_ATTESTATION_OID
from secure_core_mobile.avf_platform_verifier import (
    AndroidAvfAuthoritativeVerifier,
    AuthoritativeAvfTrustProfile,
    authoritative_profile_sha256,
)
from secure_core_mobile.avf_policy import AvfComponentPolicy, ExpectedVmComponent
from secure_core_mobile.cert_chain import CertificateTrustStore
from secure_core_mobile.secretkeeper_dt import read_pvmfw_secretkeeper_key
from secure_core_mobile.secretkeeper_identity_verifier import (
    PvmfwSecretkeeperEvidenceProvider,
    PvmfwSecretkeeperIdentityVerifier,
)


def _test_pin(profile_sha256: str):
    from secure_core_mobile import avf_platform_verifier as verifier

    return verifier.PreprovisionedAvfProfilePin(
        profile_sha256=profile_sha256,
        provenance="synthetic-test-only",
        _key=verifier._AVF_PROFILE_PIN_ISSUER_KEY,
    )

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


def _attestation_chain(challenge: bytes) -> tuple[bytes, bytes]:
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


def _head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes(((major << 5) | n,))
    return bytes(((major << 5) | 24, n))


def _int(v: int) -> bytes:
    return _head(0, v) if v >= 0 else _head(1, -1 - v)


def _bstr(v: bytes) -> bytes:
    return _head(2, len(v)) + v


def _secretkeeper_p256_key() -> bytes:
    numbers = ec.generate_private_key(ec.SECP256R1()).public_key().public_numbers()
    entries = [
        (_int(1), _int(2)),
        (_int(3), _int(-7)),
        (_int(-1), _int(1)),
        (_int(-2), _bstr(numbers.x.to_bytes(32, "big"))),
        (_int(-3), _bstr(numbers.y.to_bytes(32, "big"))),
    ]
    entries.sort(key=lambda pair: pair[0])
    return _head(5, len(entries)) + b"".join(k + v for k, v in entries)


def test_authoritative_avf_to_authgraph_identity_chain() -> None:
    challenge = b"fresh-third-party-challenge"
    leaf, root = _attestation_chain(challenge)
    store = CertificateTrustStore((root,))
    profile = AuthoritativeAvfTrustProfile(
        store,
        _test_pin(
            authoritative_profile_sha256(store)
        ),
    )
    platform = AndroidAvfAuthoritativeVerifier(profile).verify(
        chain_der=(leaf,),
        challenge=challenge,
        component_policy=AvfComponentPolicy((
            ExpectedVmComponent("payload.apk", 1, b"c" * 32, b"a" * 32),
        )),
    )

    key = read_pvmfw_secretkeeper_key(
        reader=lambda path: _secretkeeper_p256_key()
    )
    binding = PvmfwSecretkeeperEvidenceProvider().collect(key, platform)
    identity = PvmfwSecretkeeperIdentityVerifier().verify(key, binding)

    session = AuthGraphSession()
    session.pin_secretkeeper_identity(key)
    session.mark_native_exchange_established(
        verified_identity=identity,
        session_id=b"authgraph-session",
    )

    assert platform.qualifies_as_android_avf is True
    assert identity.public_key_sha256 == binding.public_key_sha256
    assert session.can_process_secret_management is True
