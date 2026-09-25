"""Provider capability evidence; never infer hardware protection from caller input."""

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


class ProtectionLevel(StrEnum):
    SOFTWARE = "SOFTWARE"
    HARDWARE_BACKED = "HARDWARE_BACKED"
    STRONGBOX = "STRONGBOX"


@dataclass(frozen=True)
class CapabilityEvidence:
    provider_id: str
    protection: ProtectionLevel
    evidence_source: str
    verified: bool

    @property
    def hardware_backed(self) -> bool:
        return self.verified and self.protection in {
            ProtectionLevel.HARDWARE_BACKED,
            ProtectionLevel.STRONGBOX,
        }

    @property
    def strongbox(self) -> bool:
        return self.verified and self.protection is ProtectionLevel.STRONGBOX


def development_capability(provider_id: str = "development") -> CapabilityEvidence:
    return CapabilityEvidence(
        provider_id=provider_id,
        protection=ProtectionLevel.SOFTWARE,
        evidence_source="development-provider",
        verified=True,
    )
