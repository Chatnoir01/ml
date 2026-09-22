import pytest
from secure_core_mobile.authgraph_session import AuthGraphSession, AuthGraphSessionState
from secure_core_mobile.secretkeeper_protocol import StoreSecretRequest, GetSecretRequest


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
        session.mark_native_exchange_established(peer_identity_verified=True)
    session.pin_secretkeeper_identity(b"cbor-cose-key")
    with pytest.raises(ValueError, match="failed"):
        session.mark_native_exchange_established(peer_identity_verified=False)
    assert session.state is AuthGraphSessionState.PEER_IDENTITY_PINNED
    session.mark_native_exchange_established(peer_identity_verified=True)
    assert session.can_process_secret_management


def test_closed_session_erases_pinned_identity_and_cannot_process():
    session = AuthGraphSession()
    session.pin_secretkeeper_identity(b"key")
    session.mark_native_exchange_established(peer_identity_verified=True)
    session.close()
    assert session.secretkeeper_public_key_cbor is None
    assert not session.can_process_secret_management
