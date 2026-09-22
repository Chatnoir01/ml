"""Explicit lifecycle state machine. Invalid transitions fail closed."""

from __future__ import annotations
from enum import StrEnum


class LifecycleState(StrEnum):
    ABSENT = "ABSENT"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    DESTROYED = "DESTROYED"


_TRANSITIONS = {
    (LifecycleState.ABSENT, "create"): LifecycleState.ACTIVE,
    (LifecycleState.ACTIVE, "rotate"): LifecycleState.ACTIVE,
    (LifecycleState.ACTIVE, "revoke"): LifecycleState.REVOKED,
    (LifecycleState.ACTIVE, "destroy"): LifecycleState.DESTROYED,
    (LifecycleState.REVOKED, "destroy"): LifecycleState.DESTROYED,
}


def transition(state: LifecycleState, event: str) -> LifecycleState:
    try:
        return _TRANSITIONS[(state, event)]
    except KeyError as exc:
        raise ValueError(f"forbidden lifecycle transition: {state}/{event}") from exc
