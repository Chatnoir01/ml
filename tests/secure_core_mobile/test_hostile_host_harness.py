from __future__ import annotations

from secure_core_mobile.authorization import AuthorizationService
from secure_core_mobile.evidence import experiment_receipt
from secure_core_mobile.freshness import InMemoryFreshnessStore
from secure_core_mobile.hostile_host import AttackKind, observe
from secure_core_mobile.key_lifecycle import KeyRegistry
from secure_core_mobile.policy import AuthorizationRequest, Policy
from secure_core_mobile.provider import DevelopmentProvider


def _stack():
    registry = KeyRegistry()
    key = registry.create(provider_id="development")
    provider = DevelopmentProvider()
    service = AuthorizationService(
        freshness=InMemoryFreshnessStore(), provider=provider, registry=registry
    )
    return registry, key, provider, service


def test_unknown_handle_attack_is_denied_before_provider():
    _, _, provider, service = _stack()
    obs, _ = observe(
        kind=AttackKind.UNKNOWN_HANDLE,
        service=service,
        provider=provider,
        request=AuthorizationRequest("sign", "scm_fake", 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert obs.denied is True
    assert obs.provider_reached is False


def test_policy_rollback_attack_is_denied_before_provider():
    _, key, provider, service = _stack()
    obs, _ = observe(
        kind=AttackKind.POLICY_VERSION_ROLLBACK,
        service=service,
        provider=provider,
        request=AuthorizationRequest("sign", key.handle, 0, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert obs.denied is True
    assert obs.provider_reached is False


def test_operation_substitution_is_denied():
    _, key, provider, service = _stack()
    obs, _ = observe(
        kind=AttackKind.OPERATION_SUBSTITUTION,
        service=service,
        provider=provider,
        request=AuthorizationRequest("decrypt", key.handle, 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    assert obs.denied is True
    assert obs.provider_reached is False


def test_hardware_capability_lie_is_denied():
    _, key, provider, service = _stack()
    obs, _ = observe(
        kind=AttackKind.HARDWARE_CAPABILITY_LIE,
        service=service,
        provider=provider,
        request=AuthorizationRequest("sign", key.handle, 1, "n1", True),
        policy=Policy(1, frozenset({"sign"}), require_hardware_backed=True),
        payload=b"x",
    )
    assert obs.denied is True
    assert obs.provider_reached is False


def test_experiment_receipt_cannot_claim_pkvm_evidence():
    _, _, provider, service = _stack()
    obs, _ = observe(
        kind=AttackKind.UNKNOWN_HANDLE,
        service=service,
        provider=provider,
        request=AuthorizationRequest("sign", "scm_fake", 1, "n1"),
        policy=Policy(1, frozenset({"sign"})),
        payload=b"x",
    )
    receipt = experiment_receipt([obs])
    assert receipt["qualifies_as_pkvm_evidence"] is False
    assert receipt["scope"] == "development-host-only"
    assert len(receipt["sha256"]) == 64
