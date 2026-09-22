"""Authorization service enforcing policy -> state -> freshness -> provider."""

from __future__ import annotations
from dataclasses import dataclass

from .freshness import InMemoryFreshnessStore
from .policy import AuthorizationRequest, Decision, KeyState, Policy, evaluate
from .provider import CryptoProvider
from .receipts import authorization_receipt


@dataclass
class AuthorizationResult:
    decision: Decision
    output: bytes | None
    receipt: dict


class AuthorizationService:
    def __init__(self, *, freshness: InMemoryFreshnessStore, provider: CryptoProvider):
        self._freshness = freshness
        self._provider = provider

    def execute(
        self,
        *,
        request: AuthorizationRequest,
        policy: Policy,
        key_state: KeyState,
        payload: bytes,
    ) -> AuthorizationResult:
        # Provider capability is authoritative; caller-supplied capability is not.
        effective = AuthorizationRequest(
            operation=request.operation,
            key_handle=request.key_handle,
            policy_version=request.policy_version,
            nonce=request.nonce,
            hardware_backed=bool(self._provider.hardware_backed),
        )
        decision = evaluate(effective, policy, key_state)

        if decision is Decision.DENY:
            return self._result(effective, decision, None)

        # Freshness is consumed only after all static policy/state gates pass and
        # immediately before the provider boundary.
        if not self._freshness.consume(effective.nonce):
            return self._result(effective, Decision.DENY, None)

        output = self._provider.operate(
            operation=effective.operation,
            key_handle=effective.key_handle,
            payload=payload,
        )
        return self._result(effective, Decision.ALLOW, output)

    @staticmethod
    def _result(request: AuthorizationRequest, decision: Decision, output: bytes | None) -> AuthorizationResult:
        receipt = authorization_receipt({
            "operation": request.operation,
            "key_handle": request.key_handle,
            "policy_version": request.policy_version,
            "nonce_sha256": __import__("hashlib").sha256(request.nonce.encode()).hexdigest(),
            "decision": decision.value,
            "hardware_backed": request.hardware_backed,
        })
        return AuthorizationResult(decision=decision, output=output, receipt=receipt)
