"""Monotonic authorization-counter contract.

InMemoryMonotonicCounter is DEVELOPMENT-ONLY and provides no hostile-host
rollback resistance. A hardware/stronger-boundary backend must replace it before
SCM-I6 can be considered adversarially tested.
"""

from __future__ import annotations
from dataclasses import dataclass
from threading import Lock


@dataclass
class InMemoryMonotonicCounter:
    _value: int = 0

    def __post_init__(self) -> None:
        self._lock = Lock()

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def advance(self, expected_previous: int) -> int | None:
        if expected_previous < 0:
            return None
        with self._lock:
            if expected_previous != self._value:
                return None
            self._value += 1
            return self._value
