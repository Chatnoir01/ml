"""Authorization service enforcing policy -> state -> freshness -> binding -> provider."""

from __future__ import annotations
from dataclasses import dataclass

from .counter import InMemoryMonotonicCounter
from .freshness import InMemoryFreshnessStore
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
    ):
        self._freshness = freshness
        self._provider = provider
        self._counter = counter or InMemoryMonotonicCounter()

    def execute(
        self,
        *,
        request: AuthorizationRequest,
        policy: Policy,
        key_state: KeyState,
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
        decision = evaluate(effective, policy, key_state)
        if decision is Decision.DENY:
            return self._result(effective, decision, None, binding, None)

        if not self._freshness.consume(effective.nonce):
            return self._result(effective, Decision.DENY, None, binding, None)

        previous = self._counter.value if expected_counter is None else expected_counter
        counter_value = self._counter.advance(previous)
        if counter_value is None:
            return self._result(effective, Decision.DENY, None, binding, None)

        output = self._provider.operate(
            operation=effective.operation,
            key_handle=effective.key_handle,
            payload=payload,
        )
        return self._result(effective, Decision.ALLOW, output, binding, counter_value)

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
