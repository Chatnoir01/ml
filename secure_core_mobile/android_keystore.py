"""Android Keystore/StrongBox boundary contract.

No Android API is emulated here. Unsupported runtime means unsupported, never a
simulated hardware-backed success.
"""

from __future__ import annotations
from dataclasses import dataclass

from .capabilities import CapabilityEvidence, ProtectionLevel


class AndroidKeystoreUnavailable(RuntimeError):
    pass


@dataclass
class AndroidKeystoreBackend:
    runtime_available: bool = False

    @property
    def hardware_backed(self) -> bool:
        # Until platform evidence is implemented and verified, fail closed.
        return False

    def capability_evidence(self) -> CapabilityEvidence:
        if not self.runtime_available:
            raise AndroidKeystoreUnavailable("Android Keystore runtime unavailable")
        return CapabilityEvidence(
            provider_id="android-keystore",
            protection=ProtectionLevel.SOFTWARE,
            evidence_source="android-runtime-present-but-hardware-unverified",
            verified=False,
        )

    def operate(self, *, operation: str, key_handle: str, payload: bytes) -> bytes:
        raise AndroidKeystoreUnavailable(
            "real Android Keystore operation not implemented; simulated success forbidden"
        )
