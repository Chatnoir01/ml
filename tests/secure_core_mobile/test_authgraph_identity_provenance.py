import pytest
from secure_core_mobile.authgraph_session import (
    AuthGraphSession,
    PvmfwValidatedSecretkeeperKey,
    SecretkeeperIdentityVerifierUnavailable,
    VerifiedSecretkeeperIdentity,
)

def test_caller_cannot_construct_verified_secretkeeper_identity():
    with pytest.raises(TypeError,match="verifier-issued"):
        VerifiedSecretkeeperIdentity(_key=object(),public_key_sha256="00"*32,provenance="forged")

def test_raw_identity_bytes_cannot_be_pinned():
    s = AuthGraphSession()
    with pytest.raises(TypeError, match="pvmfw-validated"):
        s.pin_secretkeeper_identity(b"attacker-controlled-key")


def test_pinning_pvmfw_key_is_still_not_identity_verification():
    s = AuthGraphSession()
    s.pin_secretkeeper_identity(PvmfwValidatedSecretkeeperKey(b"cose-key"))
    with pytest.raises(TypeError, match="verifier-issued"):
        s.mark_native_exchange_established(verified_identity=True, session_id=b"sid")

def test_platform_identity_verifier_fails_closed_until_implemented():
    with pytest.raises(RuntimeError,match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(
            PvmfwValidatedSecretkeeperKey(b"cose-key")
        )
