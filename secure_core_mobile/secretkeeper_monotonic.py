"""Fail-closed Secretkeeper monotonic-root integration boundary."""
from __future__ import annotations
from .monotonic_root import MonotonicRootSnapshot
from .secretkeeper import SecretkeeperCapability

class SecretkeeperMonotonicRoot:
    def __init__(self,*,capability:SecretkeeperCapability):
        if not capability.qualifies_for_monotonic_security_state:
            raise ValueError("Secretkeeper capability is not sufficient for monotonic security state")
        # Capability metadata is necessary but not authoritative evidence that
        # this Python object itself owns a hardware-backed monotonic root.
        # Stay fail-closed until the native AVF/Secretkeeper backend supplies
        # independently verified boundary evidence.
        self.hardware_resistant=False
        self.boundary_owned=False
        self._capability=capability
    def advance(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
    def current(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
