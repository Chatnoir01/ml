"""Secretkeeper integration contract derived from AOSP security semantics.

This module models the required trust boundary only. It does not implement the
Android HAL/AuthGraph transport and therefore cannot claim rollback protection.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac


@dataclass(frozen=True)
class DicePolicy:
    instance_id_sha256: str
    authority_hashes: tuple[str, ...]
    minimum_security_versions: tuple[int, ...]

    def validate(self) -> None:
        try:
            if len(self.instance_id_sha256) != 64 or len(bytes.fromhex(self.instance_id_sha256)) != 32:
                raise ValueError
            for value in self.authority_hashes:
                if len(value) != 64 or len(bytes.fromhex(value)) != 32:
                    raise ValueError
        except ValueError as exc:
            raise ValueError("invalid DICE policy digest") from exc
        if not self.authority_hashes:
            raise ValueError("DICE policy requires authority hashes")
        if len(self.authority_hashes) != len(self.minimum_security_versions):
            raise ValueError("DICE policy vectors mismatch")
        if any(v < 0 for v in self.minimum_security_versions):
            raise ValueError("invalid DICE security version")


@dataclass(frozen=True)
class SecretkeeperCapability:
    identity_verified: bool
    authgraph_channel_established: bool
    policy_gated_storage: bool
    rollback_protected_storage: bool

    @property
    def qualifies_for_monotonic_security_state(self) -> bool:
        return all((
            self.identity_verified,
            self.authgraph_channel_established,
            self.policy_gated_storage,
            self.rollback_protected_storage,
        ))


class SecretkeeperUnavailable:
    """Fail-closed placeholder until a real Android HAL/AuthGraph client exists."""

    capability = SecretkeeperCapability(False, False, False, False)

    def store(self, *, entry_id: bytes, secret: bytes, policy: DicePolicy) -> None:
        raise RuntimeError("Secretkeeper Android HAL/AuthGraph backend not implemented")

    def get(self, *, entry_id: bytes, policy: DicePolicy) -> bytes:
        raise RuntimeError("Secretkeeper Android HAL/AuthGraph backend not implemented")
