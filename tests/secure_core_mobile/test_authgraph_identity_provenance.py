import pytest
from secure_core_mobile.authgraph_session import (
    AuthGraphSession, SecretkeeperIdentityVerifierUnavailable, VerifiedSecretkeeperIdentity
)

def test_caller_cannot_construct_verified_secretkeeper_identity():
    with pytest.raises(TypeError,match="verifier-issued"):
        VerifiedSecretkeeperIdentity(_key=object(),public_key_sha256="00"*32,provenance="forged")

def test_pinning_identity_bytes_is_not_verification():
    s=AuthGraphSession(); s.pin_secretkeeper_identity(b"attacker-controlled-key")
    with pytest.raises(TypeError,match="verifier-issued"):
        s.mark_native_exchange_established(verified_identity=True,session_id=b"sid")

def test_platform_identity_verifier_fails_closed_until_implemented():
    with pytest.raises(RuntimeError,match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(b"cose-key")
