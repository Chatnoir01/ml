from __future__ import annotations
import pytest

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.boundary_service import BoundaryService
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.key_lifecycle import KeyRegistry
from secure_core_mobile.policy import Decision, Policy
from secure_core_mobile.provider import DevelopmentProvider
from secure_core_mobile.rpc import RpcEnvelope, build_envelope


def _stack():
    registry = KeyRegistry()
    key = registry.create(provider_id="development")
    provider = DevelopmentProvider()
    auth = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, registry=registry
    )
    return key, provider, BoundaryService(auth)


def test_rpc_has_single_authorized_crypto_entrypoint():
    key, provider, boundary = _stack()
    envelope = build_envelope(
        request_id="r1", operation="sign", key_handle=key.handle,
        policy_version=1, nonce="n1", payload=b"A",
    )
    result = boundary.dispatch(
        envelope=envelope, policy=Policy(1, frozenset({"sign"})), payload=b"A"
    )
    assert result.decision is Decision.ALLOW
    assert provider.call_count == 1
    assert not hasattr(boundary, "sign")
    assert not hasattr(boundary, "decrypt")


def test_payload_substitution_is_rejected_before_provider():
    key, provider, boundary = _stack()
    envelope = build_envelope(
        request_id="r1", operation="sign", key_handle=key.handle,
        policy_version=1, nonce="n1", payload=b"A",
    )
    with pytest.raises(ValueError, match="substitution"):
        boundary.dispatch(
            envelope=envelope, policy=Policy(1, frozenset({"sign"})), payload=b"B"
        )
    assert provider.call_count == 0


def test_direct_crypto_rpc_method_is_forbidden():
    key, provider, boundary = _stack()
    good = build_envelope(
        request_id="r1", operation="sign", key_handle=key.handle,
        policy_version=1, nonce="n1", payload=b"A",
    )
    forged = RpcEnvelope(
        version=good.version, method="sign_direct", request_id=good.request_id,
        operation=good.operation, key_handle=good.key_handle,
        policy_version=good.policy_version, nonce=good.nonce,
        payload_sha256=good.payload_sha256,
    )
    with pytest.raises(ValueError, match="direct crypto"):
        boundary.dispatch(
            envelope=forged, policy=Policy(1, frozenset({"sign"})), payload=b"A"
        )
    assert provider.call_count == 0


def test_rpc_version_mismatch_is_rejected():
    key, provider, boundary = _stack()
    good = build_envelope(
        request_id="r1", operation="sign", key_handle=key.handle,
        policy_version=1, nonce="n1", payload=b"A",
    )
    forged = RpcEnvelope(
        version=99, method=good.method, request_id=good.request_id,
        operation=good.operation, key_handle=good.key_handle,
        policy_version=good.policy_version, nonce=good.nonce,
        payload_sha256=good.payload_sha256,
    )
    with pytest.raises(ValueError, match="version"):
        boundary.dispatch(
            envelope=forged, policy=Policy(1, frozenset({"sign"})), payload=b"A"
        )
    assert provider.call_count == 0
