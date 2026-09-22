"""Adapter from verified Secretkeeper capability to monotonic-root contract."""

from __future__ import annotations
from dataclasses import dataclass

from .monotonic_root import MonotonicRootSnapshot
from .secretkeeper import SecretkeeperCapability


class SecretkeeperMonotonicRoot:
    def __init__(self, *, capability: SecretkeeperCapability) -> None:
        if not capability.qualifies_for_monotonic_security_state:
            raise ValueError("Secretkeeper capability not sufficient for rollback protection")
        self.hardware_resistant = True
        self.boundary_owned = True
        self._capability = capability

    def advance(self) -> MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")

    def current(self) -> MonotonicRootSnapshot:
        raise RuntimeError("Secretkeeper monotonic transaction backend not implemented")
