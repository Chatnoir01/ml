"""Pinned policy for AVF VM components extracted from remote attestation."""

from __future__ import annotations
from dataclasses import dataclass
import hmac

from .avf_extension import AvfAttestationExtension, VmComponent


@dataclass(frozen=True)
class ExpectedVmComponent:
    name: str
    minimum_security_version: int
    code_hash: bytes
    authority_hash: bytes


@dataclass(frozen=True)
class AvfComponentPolicy:
    components: tuple[ExpectedVmComponent, ...]
    reject_unexpected_components: bool = True

    def verify(self, attestation: AvfAttestationExtension) -> None:
        actual = {c.name: c for c in attestation.vm_components}
        if len(actual) != len(attestation.vm_components):
            raise ValueError("duplicate AVF VM component name")
        expected = {c.name: c for c in self.components}
        if set(expected) - set(actual):
            raise ValueError("required AVF VM component missing")
        if self.reject_unexpected_components and set(actual) != set(expected):
            raise ValueError("unexpected AVF VM component")
        for name, policy in expected.items():
            component = actual[name]
            if component.security_version < policy.minimum_security_version:
                raise ValueError("AVF VM component security version rollback")
            if not hmac.compare_digest(component.code_hash, policy.code_hash):
                raise ValueError("AVF VM component code hash mismatch")
            if not hmac.compare_digest(component.authority_hash, policy.authority_hash):
                raise ValueError("AVF VM component authority hash mismatch")
