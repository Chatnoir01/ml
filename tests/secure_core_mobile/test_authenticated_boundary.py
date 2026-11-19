from __future__ import annotations
from dataclasses import replace
import pytest

from secure_core_mobile.authenticated_boundary import AuthenticatedBoundary
from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.boundary_service import BoundaryService
from secure_core_mobile.channel import SessionVerifier, authenticate_frame
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.key_lifecycle import KeyRegistry
from secure_core_mobile.policy import Decision, Policy
from secure_core_mobile.provider import DevelopmentProvider
from secure_core_mobile.rpc import build_envelope


KEY = b"development-test-session-key"


def _stack():
    registry = KeyRegistry()
    key = registry.create(provider_id="development")
    provider = DevelopmentProvider()
    auth = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, registry=registry
    )
    boundary = AuthenticatedBoundary(
        verifier=SessionVerifier(session_id="s1", key=KEY),
        boundary=BoundaryService(auth),
    )
    return key, provider, boundary


def _frame(key_handle, *, sequence=0, nonce="n1", payload=b"x"):
    envelope = build_envelope(
        request_id=f"r{sequence}", operation="sign", key_handle=key_handle,
        policy_version=1, nonce=nonce, payload=payload,
    )
    return authenticate_frame(
        session_id="s1", sequence=sequence, envelope=envelope, key=KEY
    )


def test_authenticated_frame_reaches_authorization_then_provider():
    key, provider, boundary = _stack()
    result = boundary.receive(
        frame=_frame(key.handle),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert result.decision is Decision.ALLOW
    assert provider.call_count == 1


def test_bad_tag_cannot_reach_authorization_provider():
    key, provider, boundary = _stack()
    forged = replace(_frame(key.handle), tag_sha256="0" * 64)
    with pytest.raises(ValueError, match="authentication"):
        boundary.receive(
            frame=forged,
            policy=Policy(1, frozenset({"sign"})),
            payload=b"x",
        )
    assert provider.call_count == 0


def test_replayed_authenticated_frame_cannot_reach_provider_twice():
    key, provider, boundary = _stack()
    frame = _frame(key.handle)
    first = boundary.receive(
        frame=frame, policy=Policy(1, frozenset({"sign"})), payload=b"x"
    )
    assert first.decision is Decision.ALLOW
    with pytest.raises(ValueError, match="replayed"):
        boundary.receive(
            frame=frame, policy=Policy(1, frozenset({"sign"})), payload=b"x"
        )
    assert provider.call_count == 1


def test_authenticated_payload_substitution_still_fails_rpc_binding():
    key, provider, boundary = _stack()
    frame = _frame(key.handle, payload=b"A")
    with pytest.raises(ValueError, match="substitution"):
        boundary.receive(
            frame=frame, policy=Policy(1, frozenset({"sign"})), payload=b"B"
        )
    assert provider.call_count == 0
