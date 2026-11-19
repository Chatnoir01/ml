from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.key_lifecycle import KeyRegistry
from secure_core_mobile.policy import AuthorizationRequest, Decision, Policy
from secure_core_mobile.provider import DevelopmentProvider


def _service():
    registry = KeyRegistry()
    record = registry.create(provider_id="development")
    provider = DevelopmentProvider()
    service = AuthorizationService(
        freshness=InMemoryFreshnessStore(),
        provider=provider,
        registry=registry,
    )
    return registry, record, provider, service


def test_unknown_registry_handle_never_reaches_provider():
    registry, _, provider, service = _service()
    result = service.execute(
        request=AuthorizationRequest("sign", "scm_unknown", 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert result.decision is Decision.DENY
    assert provider.call_count == 0


def test_revoked_registry_key_never_reaches_provider():
    registry, record, provider, service = _service()
    registry.revoke(record.handle)
    result = service.execute(
        request=AuthorizationRequest("sign", record.handle, 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert result.decision is Decision.DENY
    assert provider.call_count == 0


def test_destroyed_registry_key_never_reaches_provider():
    registry, record, provider, service = _service()
    registry.destroy(record.handle)
    result = service.execute(
        request=AuthorizationRequest("sign", record.handle, 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert result.decision is Decision.DENY
    assert provider.call_count == 0


def test_concurrent_replay_allows_at_most_one_provider_call():
    registry, record, provider, service = _service()
    request = AuthorizationRequest("sign", record.handle, 1, "same-nonce")
    policy = Policy(1, frozenset({"sign"}))

    def run():
        return service.execute(request=request, policy=policy, payload=b"x").decision

    with ThreadPoolExecutor(max_workers=16) as pool:
        decisions = list(pool.map(lambda _: run(), range(32)))

    assert decisions.count(Decision.ALLOW) == 1
    assert decisions.count(Decision.DENY) == 31
    assert provider.call_count == 1
