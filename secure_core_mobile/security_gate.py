"""Central claim gate for high-assurance capabilities."""

from __future__ import annotations
from dataclasses import dataclass

from .hostile_boundary import BoundaryEvidence


@dataclass(frozen=True)
class SecurityCapability:
    boundary: BoundaryEvidence
    monotonic_hardware_resistant: bool
    monotonic_boundary_owned: bool
    attestation_verified: bool
    secretkeeper_verified: bool = False

    @property
    def hostile_host_ready(self) -> bool:
        return (
            self.boundary.qualifies_for_hostile_host_experiment
            and self.monotonic_hardware_resistant
            and self.monotonic_boundary_owned
            and self.attestation_verified
            and self.secretkeeper_verified
        )


def require_hostile_host_ready(capability: SecurityCapability) -> None:
    if not capability.hostile_host_ready:
        raise RuntimeError("hostile-host security capability not established")
