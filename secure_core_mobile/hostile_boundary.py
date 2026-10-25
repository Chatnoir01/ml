"""Contract for a future stronger hostile-host trust boundary.

No pKVM/pVM implementation is claimed here. The interface forces explicit
boundary identity, isolation evidence and monotonic-state ownership.
"""

from __future__ import annotations
from dataclasses import dataclass
from .compat import StrEnum


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
        """No self-asserted Python record can authorize a hardware security claim.

        This dataclass is freely constructible by an untrusted caller. Its
        booleans and evidence digest are unverified descriptive fields, not
        native Android/AVF provenance. Until a separate protected verifier
        issues an authenticated capability, refuse all qualification.
        Do not turn this into a boolean or user-provided-token override.
        """
        return False


def development_boundary() -> BoundaryEvidence:
    return BoundaryEvidence(
        kind=BoundaryKind.DEVELOPMENT_HOST,
        boundary_id="python-development-host",
        isolated_from_host=False,
        owns_authorization_state=False,
        owns_monotonic_state=False,
        evidence_sha256="0" * 64,
    )
