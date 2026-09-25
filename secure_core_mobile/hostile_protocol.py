"""Protocol-level eligibility gate for hostile-host experiments."""

from __future__ import annotations
from dataclasses import dataclass

from .hostile_boundary import BoundaryEvidence


@dataclass(frozen=True)
class HostileHostProtocol:
    protocol_version: int
    boundary: BoundaryEvidence
    frozen: bool = True

    def authorize_execution(self) -> None:
        if not self.frozen:
            raise ValueError("hostile-host protocol must be frozen before execution")
        if self.protocol_version <= 0:
            raise ValueError("invalid hostile-host protocol version")
        if not self.boundary.qualifies_for_hostile_host_experiment:
            raise ValueError("boundary evidence insufficient for hostile-host experiment")
