from __future__ import annotations

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.key_lifecycle import KeyRegistry
from secure_core_mobile.managed_keys import ManagedKeyService
from secure_core_mobile.opaque_provider import OpaqueEd25519Provider
from secure_core_mobile.policy import AuthorizationRequest, Decision, Policy


def test_authorization_uses_provider_owned_registry_handle():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    managed = ManagedKeyService(registry=registry, provider=provider).create()
    service = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, registry=registry
    )
    result = service.execute(
        request=AuthorizationRequest(
            operation="sign", key_handle=managed.record.handle,
            policy_version=1, nonce="n1",
        ),
        policy=Policy(1, frozenset({"sign"})), payload=b"payload",
    )
    assert result.decision is Decision.ALLOW
    assert result.output is not None


def test_provider_registry_divergence_denies_before_crypto():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    managed = ManagedKeyService(registry=registry, provider=provider).create()
    provider.destroy(managed.record.handle)
    service = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, registry=registry
    )
    before = provider.call_count
    result = service.execute(
        request=AuthorizationRequest(
            operation="sign", key_handle=managed.record.handle,
            policy_version=1, nonce="n1",
        ),
        policy=Policy(1, frozenset({"sign"})), payload=b"payload",
    )
    assert result.decision is Decision.DENY
    assert provider.call_count == before
