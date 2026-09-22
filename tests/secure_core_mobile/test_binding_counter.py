from __future__ import annotations

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.counter import InMemoryMonotonicCounter
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.policy import AuthorizationRequest, Decision, KeyState, Policy
from secure_core_mobile.provider import DevelopmentProvider
from secure_core_mobile.request_binding import request_digest


def _request(nonce: str) -> AuthorizationRequest:
    return AuthorizationRequest("sign", "key-1", 1, nonce)


def test_binding_changes_when_payload_changes():
    request = _request("n1")
    assert request_digest(request, payload=b"A") != request_digest(request, payload=b"B")


def test_binding_changes_when_security_relevant_request_field_changes():
    base = _request("n1")
    altered = AuthorizationRequest("decrypt", "key-1", 1, "n1")
    assert request_digest(base, payload=b"x") != request_digest(altered, payload=b"x")


def test_counter_rejects_stale_expected_value():
    counter = InMemoryMonotonicCounter()
    assert counter.advance(0) == 1
    assert counter.advance(0) is None
    assert counter.value == 1


def test_stale_counter_never_reaches_provider():
    provider = DevelopmentProvider()
    counter = InMemoryMonotonicCounter()
    service = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, counter=counter
    )
    policy = Policy(1, frozenset({"sign"}))
    first = service.execute(
        request=_request("n1"), policy=policy, key_state=KeyState.ACTIVE,
        payload=b"x", expected_counter=0,
    )
    stale = service.execute(
        request=_request("n2"), policy=policy, key_state=KeyState.ACTIVE,
        payload=b"x", expected_counter=0,
    )
    assert first.decision is Decision.ALLOW
    assert stale.decision is Decision.DENY
    assert provider.call_count == 1


def test_receipt_binds_exact_payload_without_recording_payload():
    provider = DevelopmentProvider()
    service = AuthorizationService(freshness=InMemoryFreshnessStore(), provider=provider)
    result = service.execute(
        request=_request("n1"), policy=Policy(1, frozenset({"sign"})),
        key_state=KeyState.ACTIVE, payload=b"secret-message",
    )
    receipt = result.receipt["payload"]
    assert "payload" not in receipt
    assert receipt["request_binding_sha256"] == request_digest(_request("n1"), payload=b"secret-message")
