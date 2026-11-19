"""Single-use freshness store.

The in-memory backend is DEVELOPMENT-ONLY. It proves API semantics, not rollback
resistance against a compromised host.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class InMemoryFreshnessStore:
    _consumed: set[str] = field(default_factory=set)
    _lock: Lock = field(default_factory=Lock)

    def consume(self, nonce: str) -> bool:
        if not nonce:
            return False
        with self._lock:
            if nonce in self._consumed:
                return False
            self._consumed.add(nonce)
            return True
