"""Explicit lifecycle state machine. Invalid transitions fail closed."""

from __future__ import annotations
try:
    from enum import StrEnum
except ImportError:  # Python 3.10 compatibility
    from enum import Enum

    class StrEnum(str, Enum):
        """Compatibility shim matching Python 3.11 enum.StrEnum values."""

        def __str__(self) -> str:
            return str(self.value)


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
