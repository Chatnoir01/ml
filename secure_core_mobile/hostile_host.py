"""Hostile-host experiment harness.

This harness models adversarial API requests against the authorization boundary.
It is not evidence of pKVM/pVM isolation and cannot promote SCM-I10 by itself.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

from .authorization import AuthorizationResult, AuthorizationService
from .policy import AuthorizationRequest, KeyState, Policy


class AttackKind(StrEnum):
    UNKNOWN_HANDLE = "UNKNOWN_HANDLE"
    POLICY_VERSION_ROLLBACK = "POLICY_VERSION_ROLLBACK"
    NONCE_REPLAY = "NONCE_REPLAY"
    OPERATION_SUBSTITUTION = "OPERATION_SUBSTITUTION"
    HARDWARE_CAPABILITY_LIE = "HARDWARE_CAPABILITY_LIE"


@dataclass(frozen=True)
class AttackObservation:
    kind: AttackKind
    denied: bool
    provider_calls_before: int
    provider_calls_after: int
    receipt_sha256: str

    @property
    def provider_reached(self) -> bool:
        return self.provider_calls_after > self.provider_calls_before


def observe(
    *,
    kind: AttackKind,
    service: AuthorizationService,
    provider: object,
    request: AuthorizationRequest,
    policy: Policy,
    payload: bytes,
    key_state: KeyState | None = None,
    expected_counter: int | None = None,
) -> tuple[AttackObservation, AuthorizationResult]:
    before = int(getattr(provider, "call_count", 0))
    result = service.execute(
        request=request,
        policy=policy,
        key_state=key_state,
        payload=payload,
        expected_counter=expected_counter,
    )
    after = int(getattr(provider, "call_count", 0))
    return (
        AttackObservation(
            kind=kind,
            denied=result.decision.value == "DENY",
            provider_calls_before=before,
            provider_calls_after=after,
            receipt_sha256=str(result.receipt["sha256"]),
        ),
        result,
    )
