import hashlib

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from secure_core_mobile.authgraph_session import (
    AuthGraphSession,
    AuthGraphSessionState,
    PvmfwValidatedSecretkeeperKey,
)
from secure_core_mobile.secretkeeper_dt import read_pvmfw_secretkeeper_key
from secure_core_mobile.secretkeeper_identity_verifier import (
    PvmfwSecretkeeperBindingEvidence,
    PvmfwSecretkeeperIdentityVerifier,
    _EVIDENCE_ISSUER_KEY,
)
from secure_core_mobile.secretkeeper_protocol import GetSecretRequest, StoreSecretRequest


def _head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes(((major << 5) | n,))
    return bytes(((major << 5) | 24, n))


def _int(v: int) -> bytes:
    return _head(0, v) if v >= 0 else _head(1, -1 - v)


def _bstr(v: bytes) -> bytes:
    return _head(2, len(v)) + v


def _valid_p256_cose_key() -> bytes:
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


def _pvmfw(encoded: bytes | None = None) -> PvmfwValidatedSecretkeeperKey:
    value = encoded or _valid_p256_cose_key()
    return read_pvmfw_secretkeeper_key(reader=lambda path: value)


def _verified(key: PvmfwValidatedSecretkeeperKey):
    digest = hashlib.sha256(key.public_key_cbor).hexdigest()
    evidence = PvmfwSecretkeeperBindingEvidence(
        _key=_EVIDENCE_ISSUER_KEY,
        public_key_sha256=digest,
        platform_evidence_sha256="a" * 64,
    )
    return PvmfwSecretkeeperIdentityVerifier().verify(key, evidence)


def test_secret_management_sizes_match_aosp_contract():
    StoreSecretRequest(b"i"*64, b"s"*32, b"policy").validate()
    GetSecretRequest(b"i"*64).validate()
    with pytest.raises(ValueError, match="64"):
        GetSecretRequest(b"short").validate()
    with pytest.raises(ValueError, match="32"):
        StoreSecretRequest(b"i"*64, b"short", b"policy").validate()


def test_authgraph_requires_pinned_and_verified_secretkeeper_identity():
    session = AuthGraphSession()
    key = _pvmfw()
    wrong_key = _pvmfw()

    with pytest.raises(ValueError, match="pinned"):
        session.mark_native_exchange_established(
            verified_identity=_verified(key), session_id=b"sid"
        )

    session.pin_secretkeeper_identity(key)

    with pytest.raises(ValueError, match="does not match"):
        session.mark_native_exchange_established(
            verified_identity=_verified(wrong_key), session_id=b"sid"
        )

    assert session.state is AuthGraphSessionState.PEER_IDENTITY_PINNED
    session.mark_native_exchange_established(
        verified_identity=_verified(key), session_id=b"sid"
    )
    assert session.can_process_secret_management


def test_closed_session_erases_pinned_identity_and_cannot_process():
    session = AuthGraphSession()
    key = _pvmfw()
    session.pin_secretkeeper_identity(key)
    session.mark_native_exchange_established(
        verified_identity=_verified(key), session_id=b"sid"
    )
    session.close()
    assert session.secretkeeper_public_key_cbor is None
    assert not session.can_process_secret_management


def test_authgraph_allocates_monotonic_request_sequence_per_session():
    session = AuthGraphSession()
    key = _pvmfw()
    session.pin_secretkeeper_identity(key)
    session.mark_native_exchange_established(
        verified_identity=_verified(key), session_id=b"sid"
    )
    assert session.allocate_request_sequence() == 0
    assert session.allocate_request_sequence() == 1
    session.close()
    with pytest.raises(RuntimeError, match="not established"):
        session.allocate_request_sequence()
