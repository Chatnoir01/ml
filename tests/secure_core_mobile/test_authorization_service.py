from __future__ import annotations

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.policy import AuthorizationRequest, Decision, KeyState, Policy
from secure_core_mobile.provider import DevelopmentProvider


def _request(nonce="n-1", hardware_backed=False):
    return AuthorizationRequest("sign", "key-1", 1, nonce, hardware_backed)


def test_provider_never_called_when_policy_denies():
    provider = DevelopmentProvider()
    service = AuthorizationService(freshness=InMemoryFreshnessStore(), provider=provider)
    result = service.execute(
        request=_request(),
        policy=Policy(1, frozenset({"decrypt"})),
        key_state=KeyState.ACTIVE,
        payload=b"x",
    )
    assert result.decision is Decision.DENY
    assert result.output is None
    assert provider.call_count == 0


def test_nonce_is_single_use_and_replay_never_reaches_provider():
    provider = DevelopmentProvider()
    service = AuthorizationService(freshness=InMemoryFreshnessStore(), provider=provider)
    policy = Policy(1, frozenset({"sign"}))

    first = service.execute(request=_request(), policy=policy, key_state=KeyState.ACTIVE, payload=b"x")
    replay = service.execute(request=_request(), policy=policy, key_state=KeyState.ACTIVE, payload=b"x")

    assert first.decision is Decision.ALLOW
    assert replay.decision is Decision.DENY
    assert provider.call_count == 1


def test_caller_cannot_lie_about_hardware_capability():
    provider = DevelopmentProvider(hardware_backed=False)
    service = AuthorizationService(freshness=InMemoryFreshnessStore(), provider=provider)
    result = service.execute(
        request=_request(hardware_backed=True),
        policy=Policy(1, frozenset({"sign"}), require_hardware_backed=True),
        key_state=KeyState.ACTIVE,
        payload=b"x",
    )
    assert result.decision is Decision.DENY
    assert provider.call_count == 0


def test_denied_request_does_not_burn_nonce():
    provider = DevelopmentProvider()
    freshness = InMemoryFreshnessStore()
    service = AuthorizationService(freshness=freshness, provider=provider)
    denied = service.execute(
        request=_request("n-retry"),
        policy=Policy(1, frozenset({"decrypt"})),
        key_state=KeyState.ACTIVE,
        payload=b"x",
    )
    allowed = service.execute(
        request=_request("n-retry"),
        policy=Policy(1, frozenset({"sign"})),
        key_state=KeyState.ACTIVE,
        payload=b"x",
    )
    assert denied.decision is Decision.DENY
    assert allowed.decision is Decision.ALLOW
    assert provider.call_count == 1
