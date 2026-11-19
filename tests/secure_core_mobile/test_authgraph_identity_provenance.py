import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from secure_core_mobile.authgraph_session import (
    AuthGraphSession,
    PvmfwValidatedSecretkeeperKey,
    SecretkeeperIdentityVerifierUnavailable,
    VerifiedSecretkeeperIdentity,
)
from secure_core_mobile.secretkeeper_dt import read_pvmfw_secretkeeper_key


def _valid_ed25519_cose_key() -> bytes:
    public_key = ed25519.Ed25519PrivateKey.generate().public_key()
    x = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    # {1: 1, 3: -8, -1: 6, -2: bstr(32)}
    return b"\xa4\x01\x01\x03\x27\x20\x06\x21\x58\x20" + x


def test_caller_cannot_construct_verified_secretkeeper_identity():
    with pytest.raises(TypeError, match="verifier-issued"):
        VerifiedSecretkeeperIdentity(
            _key=object(),
            public_key_sha256="00" * 32,
            provenance="forged",
        )


def test_raw_identity_bytes_cannot_be_pinned():
    session = AuthGraphSession()
    with pytest.raises(TypeError, match="pvmfw-validated"):
        session.pin_secretkeeper_identity(b"attacker-controlled-key")


def test_caller_cannot_construct_pvmfw_provenance_token():
    with pytest.raises(TypeError, match="reader-issued"):
        PvmfwValidatedSecretkeeperKey(
            _valid_ed25519_cose_key(),
            source_path="/proc/device-tree/avf/secretkeeper_public_key",
            _key=object(),
        )


def test_pinning_reader_issued_key_is_still_not_identity_verification():
    key = read_pvmfw_secretkeeper_key(
        reader=lambda path: _valid_ed25519_cose_key()
    )
    session = AuthGraphSession()
    session.pin_secretkeeper_identity(key)
    with pytest.raises(TypeError, match="verifier-issued"):
        session.mark_native_exchange_established(
            verified_identity=True,
            session_id=b"sid",
        )


def test_platform_identity_verifier_fails_closed_until_implemented():
    key = read_pvmfw_secretkeeper_key(
        reader=lambda path: _valid_ed25519_cose_key()
    )
    with pytest.raises(RuntimeError, match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(key)
