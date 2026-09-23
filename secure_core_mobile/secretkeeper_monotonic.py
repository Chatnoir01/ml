"""Fail-closed Secretkeeper monotonic-root integration boundary."""
from __future__ import annotations
from .monotonic_root import MonotonicRootSnapshot
from .secretkeeper import SecretkeeperCapability

class SecretkeeperMonotonicRoot:
    def __init__(self,*,capability:SecretkeeperCapability):
        if not capability.qualifies_for_monotonic_security_state:
            raise ValueError("Secretkeeper capability is not sufficient for monotonic security state")
        # These flags describe the required Secretkeeper contract only. The
        # methods remain fail-closed until the native backend is implemented.
        self.hardware_resistant=True
        self.boundary_owned=True
        self._capability=capability
    def advance(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
    def current(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
