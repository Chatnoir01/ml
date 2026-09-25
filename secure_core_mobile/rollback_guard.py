"""Rollback-detection contract for monotonic state.

The in-memory implementation is development-only. Durable/hardware monotonic
storage must implement the same interface inside the stronger boundary.
"""

from __future__ import annotations
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class MonotonicSnapshot:
    epoch: int
    counter: int


class InMemoryRollbackGuard:
    hardware_resistant = False

    def __init__(self, *, epoch: int = 1) -> None:
        if epoch <= 0:
            raise ValueError("invalid epoch")
        self._epoch = epoch
        self._counter = 0
        self._lock = Lock()

    def advance(self) -> MonotonicSnapshot:
        with self._lock:
            self._counter += 1
            return MonotonicSnapshot(self._epoch, self._counter)

    def validate(self, snapshot: MonotonicSnapshot) -> None:
        with self._lock:
            if snapshot.epoch != self._epoch or snapshot.counter < self._counter:
                raise ValueError("rollback detected")
            if snapshot.counter > self._counter:
                raise ValueError("future monotonic state rejected")
