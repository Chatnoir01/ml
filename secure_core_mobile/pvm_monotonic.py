"""Contract for a monotonic root owned by the isolated pVM boundary.

No production implementation is provided until Android/pVM storage semantics
are backed by platform evidence.
"""

from __future__ import annotations
from typing import Protocol

from .hostile_boundary import BoundaryEvidence
from .monotonic_root import MonotonicRootSnapshot


class MonotonicRoot(Protocol):
    hardware_resistant: bool
    boundary_owned: bool
    def advance(self) -> MonotonicRootSnapshot: ...
    def current(self) -> MonotonicRootSnapshot: ...


class PvmMonotonicRootUnavailable:
    """Fail-closed placeholder: never masquerades as protected persistence."""

    hardware_resistant = False
    boundary_owned = False

    def __init__(self, boundary: BoundaryEvidence) -> None:
        if not boundary.qualifies_for_hostile_host_experiment:
            raise ValueError("qualified pVM boundary required")
        self._boundary = boundary

    def advance(self) -> MonotonicRootSnapshot:
        raise RuntimeError("pVM monotonic storage backend not implemented")

    def current(self) -> MonotonicRootSnapshot:
        raise RuntimeError("pVM monotonic storage backend not implemented")
