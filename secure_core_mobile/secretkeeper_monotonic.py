"""Fail-closed Secretkeeper monotonic-root integration boundary."""
from __future__ import annotations
from .monotonic_root import MonotonicRootSnapshot
from .secretkeeper import SecretkeeperCapability

class SecretkeeperMonotonicRoot:
    def __init__(self,*,capability:SecretkeeperCapability):
        self.hardware_resistant=False
        self.boundary_owned=False
        self._capability=capability
    def advance(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
    def current(self)->MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
