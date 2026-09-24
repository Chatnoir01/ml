import pytest
from secure_core_mobile.authgraph_session import (
    AuthGraphSession,
    PvmfwValidatedSecretkeeperKey,
    SecretkeeperIdentityVerifierUnavailable,
    VerifiedSecretkeeperIdentity,
)
from secure_core_mobile.secretkeeper_dt import read_pvmfw_secretkeeper_key

def test_caller_cannot_construct_verified_secretkeeper_identity():
    with pytest.raises(TypeError,match="verifier-issued"):
        VerifiedSecretkeeperIdentity(_key=object(),public_key_sha256="00"*32,provenance="forged")

def test_raw_identity_bytes_cannot_be_pinned():
    s = AuthGraphSession()
    with pytest.raises(TypeError, match="pvmfw-validated"):
        s.pin_secretkeeper_identity(b"attacker-controlled-key")


def test_caller_cannot_construct_pvmfw_provenance_token():
    with pytest.raises(TypeError, match="reader-issued"):
        PvmfwValidatedSecretkeeperKey(
            b"attacker-controlled-key",
            source_path="/proc/device-tree/avf/secretkeeper_public_key",
            _key=object(),
        )


def test_pinning_pvmfw_key_is_still_not_identity_verification():
    s = AuthGraphSession()
    # a5010203262001215820 + 32 bytes x + 225820 + 32 bytes y is not needed here;
    # the identity-verification API itself is exercised with a reader-issued token
    # in the dedicated Secretkeeper protocol tests.
    with pytest.raises(ValueError):
        read_pvmfw_secretkeeper_key(reader=lambda path: b"cose-key")
def test_platform_identity_verifier_fails_closed_until_implemented():
    with pytest.raises(RuntimeError,match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(
            read_pvmfw_secretkeeper_key(reader=lambda path: b"cose-key")
        )
