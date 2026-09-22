"""Authorization service enforcing registry -> policy -> freshness -> binding -> provider."""

from __future__ import annotations
from dataclasses import dataclass

from .counter import InMemoryMonotonicCounter
from .freshness import InMemoryFreshnessStore
from .key_lifecycle import KeyRegistry, StoredKeyState
from .policy import AuthorizationRequest, Decision, KeyState, Policy, evaluate
from .provider import CryptoProvider
from .receipts import authorization_receipt
from .request_binding import request_digest


@dataclass
class AuthorizationResult:
    decision: Decision
    output: bytes | None
    receipt: dict


class AuthorizationService:
    def __init__(
        self,
        *,
        freshness: InMemoryFreshnessStore,
        provider: CryptoProvider,
        counter: InMemoryMonotonicCounter | None = None,
        registry: KeyRegistry | None = None,
    ):
        self._freshness = freshness
        self._provider = provider
        self._counter = counter or InMemoryMonotonicCounter()
        self._registry = registry

    def execute(
        self,
        *,
        request: AuthorizationRequest,
        policy: Policy,
        key_state: KeyState | None = None,
        payload: bytes,
        expected_counter: int | None = None,
    ) -> AuthorizationResult:
        effective = AuthorizationRequest(
            operation=request.operation,
            key_handle=request.key_handle,
            policy_version=request.policy_version,
            nonce=request.nonce,
            hardware_backed=bool(self._provider.hardware_backed),
        )
        binding = request_digest(effective, payload=payload)

        resolved_state = self._resolve_key_state(effective.key_handle, key_state)
        if resolved_state is None:
            return self._result(effective, Decision.DENY, None, binding, None)

        decision = evaluate(effective, policy, resolved_state)
        if decision is Decision.DENY:
            return self._result(effective, decision, None, binding, None)

        if not self._freshness.consume(effective.nonce):
            return self._result(effective, Decision.DENY, None, binding, None)

        previous = self._counter.value if expected_counter is None else expected_counter
        counter_value = self._counter.advance(previous)
        if counter_value is None:
            return self._result(effective, Decision.DENY, None, binding, None)

        # Re-read lifecycle immediately before crossing the provider boundary.
        # This narrows the revoke-vs-use race; stronger atomicity belongs in the
        # future stronger trust boundary, not in this development host registry.
        if self._registry is not None:
            current = self._registry.get(effective.key_handle)
            if current is None or current.state is not StoredKeyState.ACTIVE:
                return self._result(effective, Decision.DENY, None, binding, counter_value)
            provider_id = getattr(self._provider, "provider_id", None)
            if provider_id is not None and current.provider_id != provider_id:
                return self._result(effective, Decision.DENY, None, binding, counter_value)
            has_key = getattr(self._provider, "has_key", None)
            if callable(has_key) and not has_key(effective.key_handle):
                return self._result(effective, Decision.DENY, None, binding, counter_value)

        output = self._provider.operate(
            operation=effective.operation,
            key_handle=effective.key_handle,
            payload=payload,
        )
        return self._result(effective, Decision.ALLOW, output, binding, counter_value)

    def _resolve_key_state(self, handle: str, supplied: KeyState | None) -> KeyState | None:
        if self._registry is None:
            return supplied
        record = self._registry.get(handle)
        if record is None:
            return None
        return {
            StoredKeyState.ACTIVE: KeyState.ACTIVE,
            StoredKeyState.REVOKED: KeyState.REVOKED,
            StoredKeyState.DESTROYED: KeyState.DESTROYED,
        }[record.state]

    @staticmethod
    def _result(
        request: AuthorizationRequest,
        decision: Decision,
        output: bytes | None,
        binding: str,
        counter_value: int | None,
    ) -> AuthorizationResult:
        receipt = authorization_receipt({
            "operation": request.operation,
            "key_handle": request.key_handle,
            "policy_version": request.policy_version,
            "request_binding_sha256": binding,
            "decision": decision.value,
            "hardware_backed": request.hardware_backed,
            "authorization_counter": counter_value,
        })
        return AuthorizationResult(decision=decision, output=output, receipt=receipt)
