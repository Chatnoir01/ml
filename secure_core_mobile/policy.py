"""Fail-closed authorization policy kernel for Secure Core Mobile."""

from __future__ import annotations
from dataclasses import dataclass
try:
    from enum import StrEnum
except ImportError:  # Python 3.10 compatibility
    from enum import Enum

    class StrEnum(str, Enum):
        """Compatibility shim matching Python 3.11 enum.StrEnum values."""

        def __str__(self) -> str:
            return str(self.value)


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class KeyState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    DESTROYED = "DESTROYED"


@dataclass(frozen=True)
class AuthorizationRequest:
    operation: str
    key_handle: str
    policy_version: int
    nonce: str
    hardware_backed: bool = False


@dataclass(frozen=True)
class Policy:
    version: int
    allowed_operations: frozenset[str]
    require_hardware_backed: bool = False


def evaluate(request: AuthorizationRequest, policy: Policy, key_state: KeyState) -> Decision:
    """Pure deny-by-default decision. No cryptographic side effect occurs here."""
    if not request.operation or not request.key_handle or not request.nonce:
        return Decision.DENY
    if request.policy_version != policy.version:
        return Decision.DENY
    if key_state is not KeyState.ACTIVE:
        return Decision.DENY
    if request.operation not in policy.allowed_operations:
        return Decision.DENY
    if policy.require_hardware_backed and not request.hardware_backed:
        return Decision.DENY
    return Decision.ALLOW
