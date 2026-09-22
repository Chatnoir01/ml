"""Contract for a future stronger hostile-host trust boundary.

No pKVM/pVM implementation is claimed here. The interface forces explicit
boundary identity, isolation evidence and monotonic-state ownership.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class BoundaryKind(StrEnum):
    DEVELOPMENT_HOST = "DEVELOPMENT_HOST"
    ANDROID_PVM = "ANDROID_PVM"


@dataclass(frozen=True)
class BoundaryEvidence:
    kind: BoundaryKind
    boundary_id: str
    isolated_from_host: bool
    owns_authorization_state: bool
    owns_monotonic_state: bool
    evidence_sha256: str

    @property
    def qualifies_for_hostile_host_experiment(self) -> bool:
        return (
            self.kind is BoundaryKind.ANDROID_PVM
            and self.isolated_from_host
            and self.owns_authorization_state
            and self.owns_monotonic_state
            and len(self.evidence_sha256) == 64
        )


def development_boundary() -> BoundaryEvidence:
    return BoundaryEvidence(
        kind=BoundaryKind.DEVELOPMENT_HOST,
        boundary_id="python-development-host",
        isolated_from_host=False,
        owns_authorization_state=False,
        owns_monotonic_state=False,
        evidence_sha256="0" * 64,
    )
