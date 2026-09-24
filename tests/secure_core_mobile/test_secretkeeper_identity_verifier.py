from __future__ import annotations

import hashlib

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from secure_core_mobile.authgraph_session import PvmfwValidatedSecretkeeperKey
from secure_core_mobile.secretkeeper_identity_verifier import (
    PvmfwSecretkeeperBindingEvidence,
    PvmfwSecretkeeperEvidenceProviderUnavailable,
    PvmfwSecretkeeperIdentityVerifier,
    _EVIDENCE_ISSUER_KEY,
)


def _head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes(((major << 5) | n,))
    return bytes(((major << 5) | 24, n))


def _int(v: int) -> bytes:
    return _head(0, v) if v >= 0 else _head(1, -1 - v)


def _bstr(v: bytes) -> bytes:
    return _head(2, len(v)) + v


def _valid_p256_key() -> bytes:
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


def _evidence(encoded: bytes) -> PvmfwSecretkeeperBindingEvidence:
    return PvmfwSecretkeeperBindingEvidence(
        _key=_EVIDENCE_ISSUER_KEY,
        public_key_sha256=hashlib.sha256(encoded).hexdigest(),
        reference_dt_evidence_sha256="a" * 64,
    )


def test_caller_cannot_self_issue_pvmfw_binding_evidence() -> None:
    with pytest.raises(TypeError, match="verifier-issued"):
        PvmfwSecretkeeperBindingEvidence(
            _key=object(),
            public_key_sha256="b" * 64,
            reference_dt_evidence_sha256="a" * 64,
        )


def test_native_pvmfw_evidence_provider_remains_fail_closed() -> None:
    key = PvmfwValidatedSecretkeeperKey(_valid_p256_key())
    with pytest.raises(RuntimeError, match="not implemented"):
        PvmfwSecretkeeperEvidenceProviderUnavailable().collect(key)


def test_pvmfw_binding_evidence_can_issue_authgraph_identity_token() -> None:
    encoded = _valid_p256_key()
    key = PvmfwValidatedSecretkeeperKey(encoded)
    identity = PvmfwSecretkeeperIdentityVerifier().verify(key, _evidence(encoded))

    assert identity.public_key_sha256 == hashlib.sha256(encoded).hexdigest()
    assert identity.provenance.startswith("pvmfw-reference-dt-verified:")


def test_binding_evidence_for_different_key_is_rejected() -> None:
    expected = _valid_p256_key()
    actual = _valid_p256_key()

    with pytest.raises(ValueError, match="does not match"):
        PvmfwSecretkeeperIdentityVerifier().verify(
            PvmfwValidatedSecretkeeperKey(actual),
            _evidence(expected),
        )


def test_malformed_key_cannot_cross_identity_trust_transition() -> None:
    encoded = b"not-a-cose-key"
    with pytest.raises(ValueError):
        PvmfwSecretkeeperIdentityVerifier().verify(
            PvmfwValidatedSecretkeeperKey(encoded),
            _evidence(encoded),
        )
