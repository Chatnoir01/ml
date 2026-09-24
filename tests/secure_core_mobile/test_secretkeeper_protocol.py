import hashlib
import pytest
from secure_core_mobile.authgraph_session import (
    AuthGraphSession,
    AuthGraphSessionState,
    VerifiedSecretkeeperIdentity,
    _TOKEN_KEY,
)
from secure_core_mobile.secretkeeper_protocol import StoreSecretRequest, GetSecretRequest


def _verified(key: bytes) -> VerifiedSecretkeeperIdentity:
    return VerifiedSecretkeeperIdentity(
        _key=_TOKEN_KEY,
        public_key_sha256=hashlib.sha256(key).hexdigest(),
        provenance="unit-test-verifier",
    )


def test_secret_management_sizes_match_aosp_contract():
    StoreSecretRequest(b"i"*64, b"s"*32, b"policy").validate()
    GetSecretRequest(b"i"*64).validate()
    with pytest.raises(ValueError, match="64"):
        GetSecretRequest(b"short").validate()
    with pytest.raises(ValueError, match="32"):
        StoreSecretRequest(b"i"*64, b"short", b"policy").validate()


def test_authgraph_requires_pinned_and_verified_secretkeeper_identity():
    session = AuthGraphSession()
    with pytest.raises(ValueError, match="pinned"):
        session.mark_native_exchange_established(
            verified_identity=_verified(b"cbor-cose-key"), session_id=b"sid"
        )
    session.pin_secretkeeper_identity(b"cbor-cose-key")
    with pytest.raises(ValueError, match="does not match"):
        session.mark_native_exchange_established(
            verified_identity=_verified(b"wrong-key"), session_id=b"sid"
        )
    assert session.state is AuthGraphSessionState.PEER_IDENTITY_PINNED
    session.mark_native_exchange_established(
        verified_identity=_verified(b"cbor-cose-key"), session_id=b"sid"
    )
    assert session.can_process_secret_management


def test_closed_session_erases_pinned_identity_and_cannot_process():
    session = AuthGraphSession()
    session.pin_secretkeeper_identity(b"key")
    session.mark_native_exchange_established(
        verified_identity=_verified(b"key"), session_id=b"sid"
    )
    session.close()
    assert session.secretkeeper_public_key_cbor is None
    assert not session.can_process_secret_management


def test_authgraph_allocates_monotonic_request_sequence_per_session():
    session = AuthGraphSession()
    session.pin_secretkeeper_identity(b"key")
    session.mark_native_exchange_established(
        verified_identity=_verified(b"key"), session_id=b"sid"
    )
    assert session.allocate_request_sequence() == 0
    assert session.allocate_request_sequence() == 1
    session.close()
    with pytest.raises(RuntimeError, match="not established"):
        session.allocate_request_sequence()
