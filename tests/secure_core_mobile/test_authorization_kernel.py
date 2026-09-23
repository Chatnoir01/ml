from __future__ import annotations
import pytest
from secure_core_mobile.policy import AuthorizationRequest, Decision, KeyState, Policy, evaluate
from secure_core_mobile.receipts import authorization_receipt
from secure_core_mobile.state_machine import LifecycleState, transition


def _request(**changes):
    values = dict(operation="sign", key_handle="key-1", policy_version=1, nonce="n-1", hardware_backed=True)
    values.update(changes)
    return AuthorizationRequest(**values)


def test_known_active_operation_can_be_authorized():
    policy = Policy(1, frozenset({"sign"}), require_hardware_backed=True)
    assert evaluate(_request(), policy, KeyState.ACTIVE) is Decision.ALLOW


@pytest.mark.parametrize("auth_request", [
    _request(operation=""),
    _request(key_handle=""),
    _request(nonce=""),
    _request(operation="decrypt"),
    _request(policy_version=2),
    _request(hardware_backed=False),
])
def test_invalid_or_unknown_request_denied(auth_request):
    policy = Policy(1, frozenset({"sign"}), require_hardware_backed=True)
    assert evaluate(request, policy, KeyState.ACTIVE) is Decision.DENY


@pytest.mark.parametrize("state", [KeyState.REVOKED, KeyState.DESTROYED])
def test_non_active_key_denied(state):
    assert evaluate(_request(), Policy(1, frozenset({"sign"})), state) is Decision.DENY


def test_state_machine_rejects_resurrection():
    with pytest.raises(ValueError, match="forbidden"):
        transition(LifecycleState.REVOKED, "create")


def test_receipt_is_deterministic_and_rejects_secret_fields():
    payload = {"operation": "sign", "key_handle": "key-1", "decision": "DENY", "policy_version": 1}
    assert authorization_receipt(payload) == authorization_receipt(dict(reversed(list(payload.items()))))
    with pytest.raises(ValueError, match="secret-bearing"):
        authorization_receipt({"private_key": "never-log-this"})
